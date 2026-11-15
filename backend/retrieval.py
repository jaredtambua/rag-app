import clock
import config
import storage
from embeddings import embed_text
from config import (
    MAX_CONTEXT_CHARACTERS,
    MAX_DISTANCE,
    MAX_SELECTED,
    MIN_RESULTS,
    NEIGHBOR_WINDOW,
    RETRIEVAL_CANDIDATES,
)

from models import ContextBlock, RetrievedChunk

from vector_store import get_chunk, retrieve_chunks


def select_relevant_chunks(results):
    """
    Keep chunks that pass our distance threshold, at most MAX_SELECTED.

    If too few chunks pass, retain at least MIN_RESULTS
    from the original similarity-ranked results.
    The results arrive best first, so the cap keeps the best-scoring chunks.
    """
    selected = []

    for distance, record in results:
        if distance <= MAX_DISTANCE:
            selected.append((distance, record))

    if len(selected) < MIN_RESULTS:
        selected = results[:MIN_RESULTS]

    return selected[:MAX_SELECTED]


def expand_with_neighbor_chunks(visitor_id, results):
    """
    For every retrieved chunk, include nearby chunks from
    the same document to restore surrounding context.
    """
    expanded = []
    seen = set()

    for distance, record in results:
        doc_id = record["doc_id"]
        chunk_index = record["chunk_index"]

        start_index = max(
            0,
            chunk_index - NEIGHBOR_WINDOW,
        )

        end_index = chunk_index + NEIGHBOR_WINDOW

        for neighbor_index in range(
            start_index,
            end_index + 1,
        ):
            key = (doc_id, neighbor_index)

            if key in seen:
                continue

            seen.add(key)

            neighbor_record = get_chunk(
                visitor_id,
                doc_id,
                neighbor_index,
            )

            if neighbor_record:
                expanded.append((distance, neighbor_record))

    return expanded


def build_context_block(group):
    """
    Group contiguous chunks while preserving each chunk's
    individual text and provenance.
    """
    distances = [distance for distance, _ in group]

    records = [record for _, record in group]

    chunks = [
        RetrievedChunk(
            page=record["page"],
            chunk_index=record["chunk_index"],
            text=record["text"],
            distance=distance,
        )
        for distance, record in group
    ]

    return ContextBlock(
        source=records[0]["source"],
        chunks=chunks,
        distance=min(distances),
    )


def group_contiguous_chunks(results):
    """
    Combine neighboring chunks from the same document
    into coherent context blocks.
    """
    if not results:
        return []

    # First group all chunks by their document.
    by_document = {}

    for distance, record in results:
        doc_id = record["doc_id"]

        if doc_id not in by_document:
            by_document[doc_id] = []

        by_document[doc_id].append((distance, record))

    context_blocks = []

    for source_results in by_document.values():

        # Similarity search gives us relevance order.
        # To find neighboring chunks, restore document order.
        source_results.sort(key=lambda item: item[1]["chunk_index"])

        current_group = []

        for item in source_results:
            distance, record = item

            if not current_group:
                current_group.append(item)
                continue

            previous_record = current_group[-1][1]

            is_contiguous = record["chunk_index"] == previous_record["chunk_index"] + 1

            if is_contiguous:
                current_group.append(item)

            else:
                context_blocks.append(build_context_block(current_group))

                current_group = [item]

        # Don't forget the final group.
        if current_group:
            context_blocks.append(build_context_block(current_group))

    # We temporarily reordered things by document position.
    # Put the resulting blocks back into relevance order.
    context_blocks.sort(key=lambda block: block.distance)

    return context_blocks


def _size(chunks):
    return sum(len(chunk.text) for chunk in chunks)


def _trim_block(block, budget):
    """
    Shrink a block to fit the budget by dropping chunks from its ends,
    always the end whose chunk matched worst (the farthest neighbour).
    Only ends are dropped so the remaining chunks stay contiguous and in
    document order. Returns None if nothing fits.
    """
    chunks = list(block.chunks)

    while chunks and _size(chunks) > budget:
        if len(chunks) == 1:
            return None
        if chunks[0].distance > chunks[-1].distance:
            chunks.pop(0)
        else:
            chunks.pop()

    if not chunks:
        return None

    return ContextBlock(
        source=block.source,
        chunks=chunks,
        distance=min(chunk.distance for chunk in chunks),
    )


def limit_context_size(context_blocks):
    """
    Keep the strongest context blocks while staying within our context
    budget. A block that does not fit is trimmed, never dropped whole.
    """
    limited = []
    total_characters = 0

    for block in context_blocks:
        remaining = MAX_CONTEXT_CHARACTERS - total_characters

        if _size(block.chunks) > remaining:
            block = _trim_block(block, remaining)

            if block is None:
                continue

        limited.append(block)
        total_characters += _size(block.chunks)

    return limited


def retrieve_context(visitor_id: str, question: str) -> list[ContextBlock]:
    """
    Public interface for the retrieval pipeline.

    Only the given visitor's unexpired documents are searched.
    The API layer should call this function rather than
    knowing about the individual retrieval stages.
    """

    if not storage.has_documents(visitor_id):
        return []

    # Embed outside the lock: it is a slow network call.
    question_embedding = embed_text(question)

    with storage.LOCK:
        candidates = retrieve_chunks(
            visitor_id,
            question_embedding,
            newer_than=clock.now() - config.upload_ttl(),
            limit=RETRIEVAL_CANDIDATES,
        )

        selected = select_relevant_chunks(candidates)

        expanded = expand_with_neighbor_chunks(visitor_id, selected)

    context_blocks = group_contiguous_chunks(expanded)

    limited_context = limit_context_size(context_blocks)

    return limited_context
