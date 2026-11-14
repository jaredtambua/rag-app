"""All reads and writes of the shared Chroma collection.

Every call is scoped by visitor_id (and doc_id where it applies), so one
visitor can never see or change another visitor's chunks. Callers hold the
storage lock around these calls.
"""

import logging

from clients import get_collection
from config import EMBEDDING_BATCH_SIZE
from embeddings import embed_texts

logger = logging.getLogger(__name__)


def _scope(visitor_id, doc_id=None, extra=None):
    """Build a Chroma filter that always includes the visitor."""
    clauses = [{"visitor_id": {"$eq": visitor_id}}]

    if doc_id is not None:
        clauses.append({"doc_id": {"$eq": doc_id}})

    if extra:
        clauses.extend(extra)

    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def _record(chunk_id, text, metadata):
    return {
        "id": chunk_id,
        "text": text,
        "doc_id": metadata["doc_id"],
        "source": metadata["source"],
        "page": metadata["page"],
        "chunk_number": metadata["chunk_number"],
        "chunk_index": metadata["chunk_index"],
    }


def add_document(visitor_id, doc_id, uploaded_at, source, chunk_records):
    """Embed (in batches) and store all chunks of one document."""
    collection = get_collection()

    for start in range(0, len(chunk_records), EMBEDDING_BATCH_SIZE):
        batch = chunk_records[start : start + EMBEDDING_BATCH_SIZE]
        embeddings = embed_texts([record["text"] for record in batch])

        collection.add(
            ids=[record["id"] for record in batch],
            embeddings=embeddings,
            documents=[record["text"] for record in batch],
            metadatas=[
                {
                    "visitor_id": visitor_id,
                    "doc_id": doc_id,
                    "uploaded_at": uploaded_at,
                    "source": source,
                    "page": record["page"],
                    "chunk_number": record["chunk_number"],
                    "chunk_index": record["chunk_index"],
                }
                for record in batch
            ],
        )


def delete_document(visitor_id, doc_id):
    get_collection().delete(where=_scope(visitor_id, doc_id))


def retrieve_chunks(visitor_id, question_embedding, newer_than, limit=20):
    """Nearest chunks among this visitor's unexpired documents."""
    results = get_collection().query(
        query_embeddings=[question_embedding],
        n_results=limit,
        where=_scope(
            visitor_id, extra=[{"uploaded_at": {"$gt": newer_than}}]
        ),
    )

    retrieved = []

    for i in range(len(results["ids"][0])):
        record = _record(
            results["ids"][0][i],
            results["documents"][0][i],
            results["metadatas"][0][i],
        )
        retrieved.append((results["distances"][0][i], record))

    return retrieved


def get_chunk(visitor_id, doc_id, chunk_index):
    """One chunk of one of this visitor's documents, or None."""
    results = get_collection().get(
        where=_scope(
            visitor_id, doc_id, extra=[{"chunk_index": {"$eq": chunk_index}}]
        )
    )

    if not results["ids"]:
        return None

    return _record(results["ids"][0], results["documents"][0], results["metadatas"][0])
