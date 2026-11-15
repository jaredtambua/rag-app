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


def small_document(count=60):
    return [record(i) for i in range(count)]


def test_selection_is_capped_to_the_best_chunks():
    results = [(0.5 + i * 0.01, record(i)) for i in range(MAX_SELECTED + 7)]  # all under the distance limit
    selected = retrieval.select_relevant_chunks(results)
    assert len(selected) == MAX_SELECTED
    assert [r["chunk_index"] for _, r in selected] == list(range(MAX_SELECTED))


def test_distances_above_one_are_no_longer_dropped():
    results = [(1.0 + i * 0.1, record(i)) for i in range(10)]  # 1.0 to 1.9
    selected = retrieval.select_relevant_chunks(results)
    assert [r["chunk_index"] for _, r in selected] == list(range(10))


def test_even_the_worst_possible_distance_is_kept():
    assert len(retrieval.select_relevant_chunks([(4.0, record(0))])) == 1


def test_small_document_with_far_chunks_includes_every_chunk_up_to_the_cap(monkeypatch):
    chunks = [record(i, size=100) for i in range(25)]
    candidates = [(1.2 + i * 0.03, chunks[i]) for i in range(25)]  # all above 1.0
    monkeypatch.setattr(retrieval.storage, "has_documents", lambda v: True)
    monkeypatch.setattr(retrieval, "embed_text", lambda q: [0.0])
    monkeypatch.setattr(retrieval, "retrieve_chunks", lambda *a, **k: candidates)
    monkeypatch.setattr(retrieval, "get_chunk", lambda v, d, i: chunks[i] if 0 <= i < 25 else None)
    blocks = retrieval.retrieve_context("v", "an unrelated question")
    assert [c.chunk_index for b in blocks for c in b.chunks] == list(range(25))


def test_small_document_all_relevant_still_yields_context(monkeypatch):
    chunks = small_document()  # 60 x 800 = 48,000 characters, more than the limit
    assert sum(len(c["text"]) for c in chunks) > MAX_CONTEXT_CHARACTERS
    # every chunk is close; the best are chunks 10, 0, 5 ... in that order
    order = [10, 0, 5, 15, 1, 11] + [i for i in range(60) if i not in (10, 0, 5, 15, 1, 11)]
    candidates = [(0.4 + n * 0.02, chunks[i]) for n, i in enumerate(order)]

    monkeypatch.setattr(retrieval.storage, "has_documents", lambda v: True)
    monkeypatch.setattr(retrieval, "embed_text", lambda q: [0.0])
    monkeypatch.setattr(retrieval, "retrieve_chunks", lambda *a, **k: candidates)
    monkeypatch.setattr(retrieval, "get_chunk", lambda v, d, i: chunks[i] if 0 <= i < 60 else None)

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
    # 50 contiguous chunks (40,000 chars); chunk 25 matched best, neighbours inherit worse scores
    distances = [0.9 - 0.01 * min(i, 50 - i) for i in range(50)]
    block = make_block(range(50), distances)
    limited = retrieval.limit_context_size([block])
    assert len(limited) == 1
    kept = limited[0].chunks
    assert sum(len(c.text) for c in kept) <= MAX_CONTEXT_CHARACTERS
    indexes = [c.chunk_index for c in kept]
    assert 25 in indexes
    assert indexes == sorted(indexes) and indexes == list(range(indexes[0], indexes[-1] + 1))
    assert [c.page for c in kept] == indexes  # page labels stay with their chunks


def test_second_block_is_trimmed_to_the_remaining_budget():
    first = make_block(range(0, 20), [0.5] * 20)  # 16,000
    second = make_block(range(30, 50), [0.7 + 0.01 * i for i in range(20)])  # 16,000
    limited = retrieval.limit_context_size([first, second])
    assert len(limited) == 2
    assert sum(len(c.text) for b in limited for c in b.chunks) <= MAX_CONTEXT_CHARACTERS
    # the worst-scoring end (highest distance) is what was dropped
    assert [c.chunk_index for c in limited[1].chunks][0] == 30


def test_blocks_that_fit_are_untouched():
    block = make_block(range(5), [0.5] * 5)
    assert retrieval.limit_context_size([block]) == [block]


def test_a_document_of_about_15000_characters_is_sent_whole(monkeypatch):
    chunks = [record(i) for i in range(19)]  # 19 x 800 = 15,200 characters
    # the ten best chunks are every other chunk, so their neighbours cover the lot
    best = list(range(0, 19, 2))
    rest = [i for i in range(19) if i not in best]
    candidates = [(0.4 + n * 0.02, chunks[i]) for n, i in enumerate((best + rest)[:20])]

    monkeypatch.setattr(retrieval.storage, "has_documents", lambda v: True)
    monkeypatch.setattr(retrieval, "embed_text", lambda q: [0.0])
    monkeypatch.setattr(retrieval, "retrieve_chunks", lambda *a, **k: candidates)
    monkeypatch.setattr(retrieval, "get_chunk", lambda v, d, i: chunks[i] if 0 <= i < 19 else None)

    blocks = retrieval.retrieve_context("v", "summarise the document")
    assert len(blocks) == 1
    assert [c.chunk_index for c in blocks[0].chunks] == list(range(19))
    assert [c.page for c in blocks[0].chunks] == [i // 4 + 1 for i in range(19)]


def test_forty_candidates_are_fetched_and_the_best_thirty_kept(monkeypatch):
    from config import RETRIEVAL_CANDIDATES

    assert RETRIEVAL_CANDIDATES == 40 and MAX_SELECTED == 30
    chunks = [record(i, size=100) for i in range(60)]
    candidates = [(0.3 + i * 0.01, chunks[i]) for i in range(40)]  # all close; ranked best first
    asked = {}

    def fake_retrieve(visitor_id, embedding, newer_than, limit):
        asked["limit"] = limit
        return candidates

    monkeypatch.setattr(retrieval.storage, "has_documents", lambda v: True)
    monkeypatch.setattr(retrieval, "embed_text", lambda q: [0.0])
    monkeypatch.setattr(retrieval, "retrieve_chunks", fake_retrieve)
    monkeypatch.setattr(retrieval, "get_chunk", lambda v, d, i: chunks[i] if 0 <= i < 60 else None)

    selected = retrieval.select_relevant_chunks(candidates)
    assert [r["chunk_index"] for _, r in selected] == list(range(30))  # best 30 of 40

    blocks = retrieval.retrieve_context("v", "two part question")
    assert asked["limit"] == 40  # more than the old 20 are considered
    assert blocks
