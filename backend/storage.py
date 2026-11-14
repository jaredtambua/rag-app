"""Per-visitor document storage with expiry.

Files live in DATA_DIR/documents/<visitor id>/<doc id>.pdf and the search
index entries live in the shared Chroma collection, tagged with visitor_id
and doc_id. One process-wide lock guards every file and index operation
(uploads, deletes, index reads and the cleanup sweeper). The list of
documents is held in memory, which is fine because uploads never survive a
restart.
"""

import logging
import shutil
import threading
import uuid
from dataclasses import dataclass

import clients
import clock
import config
import vector_store
import pdf_parser
from document_processing import build_chunk_records
from uploads import (
    MSG_DUPLICATE,
    MSG_NO_TEXT,
    MSG_PROCESSING_FAILED,
    MSG_TOO_MANY_FILES,
    MSG_TOO_MUCH_TEXT,
    UploadRejected,
)

logger = logging.getLogger(__name__)

LOCK = threading.RLock()


@dataclass
class Document:
    id: str
    name: str
    uploaded_at: float


# visitor id -> doc id -> Document
_registry: dict[str, dict[str, Document]] = {}


class DocumentNotFound(Exception):
    pass


def _expires_at(doc: Document) -> float:
    return doc.uploaded_at + config.upload_ttl()


def _is_expired(doc: Document, now: float) -> bool:
    return now >= _expires_at(doc)


def _visitor_dir(visitor_id: str):
    return config.documents_root() / visitor_id


def _file_path(visitor_id: str, doc_id: str):
    return _visitor_dir(visitor_id) / f"{doc_id}.pdf"


def _live_documents(visitor_id: str) -> list[Document]:
    now = clock.now()
    docs = [
        doc
        for doc in _registry.get(visitor_id, {}).values()
        if not _is_expired(doc, now)
    ]
    return sorted(docs, key=lambda doc: (doc.uploaded_at, doc.name))


def list_documents(visitor_id: str) -> list[dict]:
    """The visitor's unexpired documents, oldest first."""
    now = clock.now()

    with LOCK:
        return [
            {
                "id": doc.id,
                "name": doc.name,
                "uploaded_at": doc.uploaded_at,
                "seconds_left": max(0, int(_expires_at(doc) - now)),
            }
            for doc in _live_documents(visitor_id)
        ]


def has_documents(visitor_id: str) -> bool:
    with LOCK:
        return bool(_live_documents(visitor_id))


def _check_room(visitor_id: str, display_name: str) -> None:
    """Refuse a fourth file or a duplicate name. Call with the lock held."""
    current = _live_documents(visitor_id)

    if len(current) >= config.MAX_FILES_PER_VISITOR:
        raise UploadRejected(409, MSG_TOO_MANY_FILES)

    if any(doc.name.lower() == display_name.lower() for doc in current):
        raise UploadRejected(400, MSG_DUPLICATE)


def add_document(
    visitor_id: str, display_name: str, data: bytes, on_validated=None, owner=None
) -> dict:
    """Check, save and index one PDF for a visitor.

    The slow work (reading the PDF in a separate process, embedding) happens
    OUTSIDE the lock so one upload never stalls other visitors. The lock is held
    only for the room check and the index and list writes, and the room check is
    repeated there so two simultaneous uploads cannot both pass.

    on_validated, if given, is called once the file has passed every check
    and before the (paid) embedding starts; it may raise to stop the upload.
    owner is the client address, used to give each client one PDF read at a time.

    Raises UploadRejected with a user-facing message. Whatever happens, a
    failed upload leaves no file and no index entries behind.
    """
    doc_id = uuid.uuid4().hex

    # A cheap early refusal, before any work is done.
    with LOCK:
        _check_room(visitor_id, display_name)

    path = _file_path(visitor_id, doc_id)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

        pages = pdf_parser.parse_pdf(path, owner)
        chunk_records = build_chunk_records(pages, doc_id, display_name)

        if not chunk_records:
            raise UploadRejected(400, MSG_NO_TEXT)

        if len(chunk_records) > config.MAX_CHUNKS:
            raise UploadRejected(400, MSG_TOO_MUCH_TEXT)

        if on_validated:
            on_validated()

        uploaded_at = clock.now()

        try:
            embeddings = vector_store.embed_records(chunk_records)
        except Exception as error:
            logger.error("Embedding failed (%s)", type(error).__name__)
            raise UploadRejected(500, MSG_PROCESSING_FAILED)

        with LOCK:
            _check_room(visitor_id, display_name)

            try:
                vector_store.add_document(
                    visitor_id, doc_id, uploaded_at, display_name, chunk_records, embeddings
                )
            except Exception as error:
                logger.error("Indexing failed (%s)", type(error).__name__)
                raise UploadRejected(500, MSG_PROCESSING_FAILED)

            _registry.setdefault(visitor_id, {})[doc_id] = Document(
                doc_id, display_name, uploaded_at
            )
    except BaseException:
        _discard(visitor_id, doc_id)
        raise

    return {"id": doc_id, "name": display_name, "uploaded_at": uploaded_at}


def _discard(visitor_id: str, doc_id: str) -> bool:
    """Remove a document's file and index entries. True if both succeeded."""
    ok = True

    try:
        with LOCK:
            vector_store.delete_document(visitor_id, doc_id)
    except Exception as error:
        ok = False
        logger.error("Index cleanup failed (%s)", type(error).__name__)

    try:
        _file_path(visitor_id, doc_id).unlink(missing_ok=True)
        folder = _visitor_dir(visitor_id)
        if folder.exists() and not any(folder.iterdir()):
            folder.rmdir()
    except OSError as error:
        ok = False
        logger.error("File cleanup failed (%s)", type(error).__name__)

    return ok


def delete_document(visitor_id: str, doc_id: str) -> dict:
    """Delete one of the visitor's own documents, found only by their list."""
    with LOCK:
        doc = _registry.get(visitor_id, {}).get(doc_id)

        if doc is None or _is_expired(doc, clock.now()):
            raise DocumentNotFound(doc_id)

        _discard(visitor_id, doc_id)
        del _registry[visitor_id][doc_id]

        if not _registry[visitor_id]:
            del _registry[visitor_id]

    return {"id": doc.id, "name": doc.name}


def sweep() -> None:
    """Remove expired documents from disk and index. Never raises."""
    try:
        with LOCK:
            now = clock.now()

            for visitor_id in list(_registry):
                for doc in list(_registry[visitor_id].values()):
                    if not _is_expired(doc, now):
                        continue

                    if _discard(visitor_id, doc.id):
                        del _registry[visitor_id][doc.id]

                if not _registry[visitor_id]:
                    del _registry[visitor_id]
    except Exception as error:
        logger.error("Sweep failed (%s)", type(error).__name__)


def reset_all() -> None:
    """Startup wipe: forget everything and empty the data folder."""
    root = config.data_dir()

    if not config.data_dir_is_safe_to_wipe(root):
        raise RuntimeError(
            "Refusing to wipe a data folder that is not a dedicated folder."
        )

    with LOCK:
        clients.reset_clients()
        _registry.clear()

        if root.exists():
            shutil.rmtree(root, ignore_errors=True)

        root.mkdir(parents=True, exist_ok=True)


class Sweeper:
    """Background thread that runs the given jobs on an interval."""

    def __init__(self, interval: float, jobs=None):
        self._interval = interval
        self._jobs = jobs or [sweep]
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name="upload-sweeper", daemon=True
        )

    def _run(self):
        while not self._stop.wait(self._interval):
            for job in self._jobs:
                try:
                    job()
                except Exception as error:
                    logger.error("Background job failed (%s)", type(error).__name__)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5)
