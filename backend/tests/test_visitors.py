"""Part 2.1: private per-visitor storage with expiry."""

import pytest

from conftest import headers, make_pdf, new_visitor, upload

ALPHA = make_pdf(
    [
        "Alpha document about falcons. " * 40,
        "Falcons nest on cliffs and eat birds. " * 40,
        "Alpha final page about falcon speed. " * 40,
    ]
)
BRAVO = make_pdf(
    [
        "Bravo document about whales. " * 40,
        "Whales sing and travel far across oceans. " * 40,
        "Bravo final page about whale songs. " * 40,
    ]
)


def listing(client, visitor):
    response = client.get("/documents", headers=headers(visitor))
    assert response.status_code == 200
    return response.json()["documents"]


def chunk_count(visitor=None):
    import clients

    collection = clients.get_collection()
    if visitor is None:
        return len(collection.get()["ids"])
    return len(collection.get(where={"visitor_id": visitor})["ids"])


def test_same_file_name_two_visitors_stay_separate(client):
    a, b = new_visitor(), new_visitor()
    assert upload(client, a, "notes.pdf", ALPHA).status_code == 200
    assert upload(client, b, "notes.pdf", BRAVO).status_code == 200

    docs_a, docs_b = listing(client, a), listing(client, b)
    assert [d["name"] for d in docs_a] == ["notes.pdf"]
    assert [d["name"] for d in docs_b] == ["notes.pdf"]
    assert docs_a[0]["id"] != docs_b[0]["id"]

    # Retrieval (including neighbour expansion) only returns the caller's text.
    import retrieval

    for visitor, forbidden, required in ((a, "whale", "falcon"), (b, "falcon", "whale")):
        blocks = retrieval.retrieve_context(visitor, "tell me about the animals")
        texts = [c.text.lower() for blk in blocks for c in blk.chunks]
        assert texts
        assert all(forbidden not in t for t in texts)
        assert any(required in t for t in texts)

    answer = client.post("/ask", json={"question": "falcons nest"}, headers=headers(a))
    assert answer.status_code == 200
    assert "whale" not in answer.json()["answer"].lower()


def test_other_visitor_cannot_list_ask_or_delete(client):
    a, b = new_visitor(), new_visitor()
    upload(client, a, "secret.pdf", ALPHA)
    doc_id = listing(client, a)[0]["id"]
    chunks_before = chunk_count(a)
    assert chunks_before > 0

    assert listing(client, b) == []

    ask = client.post("/ask", json={"question": "falcons"}, headers=headers(b))
    assert ask.status_code == 200
    assert ask.json() == {
        "answer": "I could not find this in the uploaded documents.",
        "citations": [],
    }

    delete = client.delete(f"/documents/{doc_id}", headers=headers(b))
    assert delete.status_code == 404
    assert [d["id"] for d in listing(client, a)] == [doc_id]
    assert chunk_count(a) == chunks_before


def test_owner_can_delete_own_file(client, data_dir):
    a, b = new_visitor(), new_visitor()
    upload(client, a, "one.pdf", ALPHA)
    upload(client, b, "one.pdf", BRAVO)
    doc_id = listing(client, a)[0]["id"]

    response = client.delete(f"/documents/{doc_id}", headers=headers(a))
    assert response.status_code == 200
    assert listing(client, a) == []
    assert chunk_count(a) == 0
    assert chunk_count(b) > 0
    assert not (data_dir / "documents" / a).exists()
    assert len(listing(client, b)) == 1


def test_list_entry_shape(client, clock):
    a = new_visitor()
    upload(client, a, "shape.pdf", ALPHA)
    clock.advance(60)
    (doc,) = listing(client, a)
    assert set(doc) == {"id", "name", "uploaded_at", "seconds_left"}
    assert doc["name"] == "shape.pdf"
    assert doc["uploaded_at"] == 1_000_000.0
    assert doc["seconds_left"] == 1740


def test_expired_file_hidden_then_swept_from_disk_and_index(client, clock, data_dir):
    a, b = new_visitor(), new_visitor()
    upload(client, a, "old.pdf", ALPHA)
    clock.advance(600)
    upload(client, b, "newer.pdf", BRAVO)
    assert (data_dir / "documents" / a).exists()

    clock.advance(1200 + 1)  # a: 1801 s old, b: 1201 s old

    # Hidden and ignored immediately, before any sweep.
    assert listing(client, a) == []
    ask = client.post("/ask", json={"question": "falcons"}, headers=headers(a))
    assert ask.json()["citations"] == []
    assert chunk_count(a) > 0  # still in the index until swept

    import storage

    storage.sweep()

    assert chunk_count(a) == 0
    assert not (data_dir / "documents" / a).exists()
    assert len(listing(client, b)) == 1
    assert chunk_count(b) > 0


def test_file_not_expired_at_29_minutes(client, clock):
    a = new_visitor()
    upload(client, a, "x.pdf", ALPHA)
    clock.advance(1799)
    assert len(listing(client, a)) == 1


def test_startup_wipes_data_folder(tmp_path, monkeypatch, clock):
    import clients
    import api
    from fastapi.testclient import TestClient

    data = tmp_path / "data"
    stale = data / "documents" / new_visitor()
    stale.mkdir(parents=True)
    (stale / "left-over.pdf").write_bytes(b"%PDF-old")
    (data / "vectorstore").mkdir()
    (data / "vectorstore" / "junk.bin").write_bytes(b"x")
    monkeypatch.setenv("DATA_DIR", str(data))
    clients.reset_clients()

    with TestClient(api.app):
        assert not (stale / "left-over.pdf").exists()
        assert not (data / "vectorstore" / "junk.bin").exists()
    clients.reset_clients()


def test_wipe_refuses_a_shared_folder(tmp_path):
    import tempfile
    from pathlib import Path

    import config

    # A dedicated folder is fine: one called "data", or anything inside the temp folder.
    assert config.data_dir_is_safe_to_wipe(config.DEFAULT_DATA_DIR)
    assert config.data_dir_is_safe_to_wipe(tmp_path / "anything")
    # Shared places are refused, wherever the project is checked out.
    home = Path.home()
    for shared in (home, home / "Documents", Path(home.anchor), Path(tempfile.gettempdir())):
        assert not config.data_dir_is_safe_to_wipe(shared), shared


@pytest.mark.parametrize(
    "bad", [None, "", "not-a-uuid", "12345", "../../etc/passwd", "g" * 36]
)
def test_missing_or_bad_visitor_id_is_400(client, bad):
    hdrs = {} if bad is None else {"X-Visitor-Id": bad}
    calls = [
        client.get("/documents", headers=hdrs),
        client.post("/ask", json={"question": "hi"}, headers=hdrs),
        client.delete("/documents/" + "a" * 32, headers=hdrs),
        client.post(
            "/upload",
            files=[("files", ("a.pdf", make_pdf(), "application/pdf"))],
            headers=hdrs,
        ),
    ]
    for response in calls:
        assert response.status_code == 400
        assert "visitor" in response.json()["detail"].lower()


def test_health_needs_no_visitor_id(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_sweeper_error_does_not_crash_or_block_others(client, clock, monkeypatch):
    a, b = new_visitor(), new_visitor()
    upload(client, a, "a.pdf", ALPHA)
    upload(client, b, "b.pdf", BRAVO)
    clock.advance(2000)

    import storage
    import vector_store

    def boom(*args, **kwargs):
        raise RuntimeError("index exploded")

    monkeypatch.setattr(vector_store, "delete_document", boom)
    storage.sweep()  # must not raise
    assert client.get("/health").status_code == 200
    assert listing(client, b) == []  # expired anyway; app still serves requests
