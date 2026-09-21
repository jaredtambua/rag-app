from config import (
    MAX_CONTEXT_CHARACTERS,
    MAX_DISTANCE,
    MIN_RESULTS,
    NEIGHBOR_WINDOW,
    RETRIEVAL_CANDIDATES,
)

from models import ContextBlock, RetrievedChunk

from vector_store import (
    get_chunk_by_source_and_index,
    retrieve_chunks,
)


def select_relevant_chunks(results):
    """
    Keep chunks that pass our distance threshold.

    If too few chunks pass, retain at least MIN_RESULTS
    from the original similarity-ranked results.
    """
    selected = []

    for distance, record in results:
        if distance <= MAX_DISTANCE:
            selected.append((distance, record))

    if len(selected) < MIN_RESULTS:
        selected = results[:MIN_RESULTS]

    return selected


def expand_with_neighbor_chunks(results):
    """
    For every retrieved chunk, include nearby chunks from
    the same document to restore surrounding context.
    """
    expanded = []
    seen = set()

    for distance, record in results:
        source = record["source"]
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
            key = (source, neighbor_index)

            if key in seen:
                continue

            seen.add(key)

            neighbor_record = get_chunk_by_source_and_index(
                source,
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
        )
        for record in records
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

    # First group all chunks by their source document.
    by_source = {}

    for distance, record in results:
        source = record["source"]

        if source not in by_source:
            by_source[source] = []

        by_source[source].append((distance, record))

    context_blocks = []

    for source, source_results in by_source.items():

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


def limit_context_size(context_blocks):
    """
    Keep the strongest context blocks while staying
    approximately within our context budget.
    """
    limited = []
    total_characters = 0

    for block in context_blocks:
        block_size = sum(len(chunk.text) for chunk in block.chunks)

        if total_characters + block_size > MAX_CONTEXT_CHARACTERS:
            continue

        limited.append(block)
        total_characters += block_size

    return limited


def retrieve_context(question: str) -> list[ContextBlock]:
    """
    Public interface for the retrieval pipeline.

    The API layer should call this function rather than
    knowing about the individual retrieval stages.
    """

    candidates = retrieve_chunks(
        question,
        limit=RETRIEVAL_CANDIDATES,
    )

    selected = select_relevant_chunks(candidates)

    expanded = expand_with_neighbor_chunks(selected)

    context_blocks = group_contiguous_chunks(expanded)

    limited_context = limit_context_size(context_blocks)

    return limited_context
