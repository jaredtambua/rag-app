"""A small document where everything is 'relevant' must still give the model context."""

import retrieval
from config import MAX_CONTEXT_CHARACTERS, MAX_SELECTED
from models import ContextBlock, RetrievedChunk


def record(i, size=800, page=None):
    return {
        "doc_id": "d1",
        "chunk_index": i,
        "page": page if page is not None else i // 4 + 1,
        "source": "paper.pdf",
        "text": f"chunk{i} " + "x" * (size - len(f"chunk{i} ")),
    }


def small_document(count=20):
    return [record(i) for i in range(count)]


def test_selection_is_capped_to_the_best_chunks():
    results = [(0.5 + i * 0.01, record(i)) for i in range(17)]  # all under the distance limit
    selected = retrieval.select_relevant_chunks(results)
    assert len(selected) == MAX_SELECTED
    assert [r["chunk_index"] for _, r in selected] == list(range(MAX_SELECTED))


def test_fallback_still_returns_the_best_three_when_none_are_close():
    results = [(1.5 + i * 0.01, record(i)) for i in range(10)]
    assert len(retrieval.select_relevant_chunks(results)) == 3


def test_small_document_all_relevant_still_yields_context(monkeypatch):
    chunks = small_document()  # 20 x 800 = 16,000 characters, more than the limit
    assert sum(len(c["text"]) for c in chunks) > MAX_CONTEXT_CHARACTERS
    # every chunk is close; the best are chunks 10, 0, 5 ... in that order
    order = [10, 0, 5, 15, 1, 11] + [i for i in range(20) if i not in (10, 0, 5, 15, 1, 11)]
    candidates = [(0.4 + n * 0.02, chunks[i]) for n, i in enumerate(order)]

    monkeypatch.setattr(retrieval.storage, "has_documents", lambda v: True)
    monkeypatch.setattr(retrieval, "embed_text", lambda q: [0.0])
    monkeypatch.setattr(retrieval, "retrieve_chunks", lambda *a, **k: candidates)
    monkeypatch.setattr(retrieval, "get_chunk", lambda v, d, i: chunks[i] if 0 <= i < 20 else None)

    blocks = retrieval.retrieve_context("v", "how many people took part?")
    assert blocks
    text = " ".join(c.text for b in blocks for c in b.chunks)
    for top in (10, 0, 5, 15, 1, 11):
        assert f"chunk{top} " in text
    assert sum(len(c.text) for b in blocks for c in b.chunks) <= MAX_CONTEXT_CHARACTERS


def make_block(indexes, distances):
    return ContextBlock(
        source="a.pdf",
        chunks=[
            RetrievedChunk(page=i, chunk_index=i, text="y" * 800, distance=d)
            for i, d in zip(indexes, distances)
        ],
        distance=min(distances),
    )


def test_oversize_block_is_trimmed_not_dropped_and_keeps_best_chunk():
    # 20 contiguous chunks (16,000 chars); chunk 10 matched best, neighbours inherit worse scores
    distances = [0.9 - 0.04 * min(i, 20 - i) for i in range(20)]
    block = make_block(range(20), distances)
    limited = retrieval.limit_context_size([block])
    assert len(limited) == 1
    kept = limited[0].chunks
    assert sum(len(c.text) for c in kept) <= MAX_CONTEXT_CHARACTERS
    indexes = [c.chunk_index for c in kept]
    assert 10 in indexes
    assert indexes == sorted(indexes) and indexes == list(range(indexes[0], indexes[-1] + 1))
    assert [c.page for c in kept] == indexes  # page labels stay with their chunks


def test_second_block_is_trimmed_to_the_remaining_budget():
    first = make_block(range(0, 10), [0.5] * 10)  # 8,000
    second = make_block(range(30, 40), [0.7 + 0.01 * i for i in range(10)])  # 8,000
    limited = retrieval.limit_context_size([first, second])
    assert len(limited) == 2
    assert sum(len(c.text) for b in limited for c in b.chunks) <= MAX_CONTEXT_CHARACTERS
    # the worst-scoring end (highest distance) is what was dropped
    assert [c.chunk_index for c in limited[1].chunks][0] == 30


def test_blocks_that_fit_are_untouched():
    block = make_block(range(5), [0.5] * 5)
    assert retrieval.limit_context_size([block]) == [block]
