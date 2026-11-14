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
from document_processing import build_chunk_records

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


def add_document(visitor_id: str, display_name: str, data: bytes) -> dict:
    """Save and index one PDF for a visitor. Cleans up fully on failure."""
    doc_id = uuid.uuid4().hex

    with LOCK:
        path = _file_path(visitor_id, doc_id)
        uploaded_at = clock.now()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

            chunk_records = build_chunk_records(path, doc_id, display_name)

            vector_store.add_document(
                visitor_id, doc_id, uploaded_at, display_name, chunk_records
            )
        except BaseException:
            _discard(visitor_id, doc_id)
            raise

        _registry.setdefault(visitor_id, {})[doc_id] = Document(
            doc_id, display_name, uploaded_at
        )

    return {"id": doc_id, "name": display_name, "uploaded_at": uploaded_at}


def _discard(visitor_id: str, doc_id: str) -> bool:
    """Remove a document's file and index entries. True if both succeeded."""
    ok = True

    try:
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
    """Background thread that calls sweep() on an interval."""

    def __init__(self, interval: float):
        self._interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name="upload-sweeper", daemon=True
        )

    def _run(self):
        while not self._stop.wait(self._interval):
            sweep()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=5)
