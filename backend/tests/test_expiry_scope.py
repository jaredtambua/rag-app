"""Expiry and scoping at the index level: an expired document must never be returned or cited."""

from conftest import headers, make_pdf, new_visitor, upload

FALCONS = make_pdf(["Falcon notes. Falcons nest on cliffs and dive fast. " * 25] * 2)
WHALES = make_pdf(["Whale notes. Whales sing and travel across oceans. " * 25] * 2)


def all_chunks(visitor):
    import clients

    return clients.get_collection().get(where={"visitor_id": visitor})


def test_expired_first_document_is_not_returned_or_cited_but_the_live_one_is(client, clock):
    import retrieval

    v = new_visitor()
    assert upload(client, v, "falcons.pdf", FALCONS).status_code == 200
    clock.advance(1000)
    assert upload(client, v, "whales.pdf", WHALES).status_code == 200
    clock.advance(801)  # falcons is now 1801 s old (expired), whales 801 s (live); no sweep has run

    assert [d["name"] for d in client.get("/documents", headers=headers(v)).json()["documents"]] == ["whales.pdf"]
    assert any(m["source"] == "falcons.pdf" for m in all_chunks(v)["metadatas"])  # still in the index

    # a question that matches the expired document best
    blocks = retrieval.retrieve_context(v, "Falcons nest on cliffs and dive fast")
    assert blocks
    for block in blocks:
        assert block.source == "whales.pdf"
        assert all("falcon" not in chunk.text.lower() for chunk in block.chunks)

    answer = client.post("/ask", json={"question": "Falcons nest on cliffs"}, headers=headers(v)).json()
    assert answer["citations"]
    assert {c["source"] for c in answer["citations"]} == {"whales.pdf"}
    assert "falcon" not in answer["answer"].lower()

    live = client.post("/ask", json={"question": "Whales sing and travel"}, headers=headers(v)).json()
    assert {c["source"] for c in live["citations"]} == {"whales.pdf"}


def test_query_filters_out_chunks_older_than_the_cutoff(client, clock):
    import embeddings
    import vector_store

    v = new_visitor()
    upload(client, v, "falcons.pdf", FALCONS)
    embedding = embeddings.embed_text("Falcons nest on cliffs")

    uploaded_at = clock()
    assert vector_store.retrieve_chunks(v, embedding, newer_than=uploaded_at - 1)
    # a cutoff at or after the upload time must exclude every chunk of it
    assert vector_store.retrieve_chunks(v, embedding, newer_than=uploaded_at) == []
    assert vector_store.retrieve_chunks(v, embedding, newer_than=uploaded_at + 5) == []


def test_delete_document_is_scoped_to_the_visitor(client):
    import vector_store

    a, b = new_visitor(), new_visitor()
    upload(client, a, "falcons.pdf", FALCONS)
    upload(client, b, "whales.pdf", WHALES)
    doc_a = client.get("/documents", headers=headers(a)).json()["documents"][0]["id"]
    before = len(all_chunks(a)["ids"])
    assert before > 0

    # another visitor naming A's document id must not remove any of A's chunks
    vector_store.delete_document(b, doc_a)
    assert len(all_chunks(a)["ids"]) == before
    assert len(all_chunks(b)["ids"]) > 0

    vector_store.delete_document(a, doc_a)
    assert len(all_chunks(a)["ids"]) == 0
    assert len(all_chunks(b)["ids"]) > 0
