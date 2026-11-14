"""Part 2.2: upload limits and safe file handling."""

import threading

import pytest

from conftest import headers, make_pdf, new_visitor, upload

MB = 1024 * 1024


def listing(client, visitor):
    return client.get("/documents", headers=headers(visitor)).json()["documents"]


def chunk_count():
    import clients

    return len(clients.get_collection().get()["ids"])


def files_on_disk(data_dir):
    root = data_dir / "documents"
    return [p for p in root.rglob("*") if p.is_file()] if root.exists() else []


def nothing_left(client, data_dir, visitor):
    assert listing(client, visitor) == []
    assert files_on_disk(data_dir) == []
    assert chunk_count() == 0


def test_file_over_5mb_refused_with_413(client, data_dir):
    v = new_visitor()
    big = make_pdf(["tiny"], extra_bytes=5 * MB + 100_000)
    assert len(big) > 5 * MB  # 5.1 MB
    response = upload(client, v, "big.pdf", big)
    assert response.status_code == 413
    assert response.json()["detail"] == "This file is larger than 5 MB."
    nothing_left(client, data_dir, v)


def test_file_just_under_5mb_accepted(client):
    v = new_visitor()
    data = make_pdf(["tiny text here"], extra_bytes=5 * MB - 20_000)
    assert len(data) < 5 * MB
    assert upload(client, v, "ok.pdf", data).status_code == 200


def test_31_pages_refused_30_accepted(client, data_dir):
    v = new_visitor()
    response = upload(client, v, "long.pdf", make_pdf([f"page {i}" for i in range(31)]))
    assert response.status_code == 400
    assert response.json()["detail"] == "This PDF has more than 30 pages."
    nothing_left(client, data_dir, v)

    ok = upload(client, v, "thirty.pdf", make_pdf([f"page {i}" for i in range(30)]))
    assert ok.status_code == 200


def test_fourth_file_refused_with_409(client, data_dir):
    v = new_visitor()
    for i in range(3):
        assert upload(client, v, f"f{i}.pdf", make_pdf([f"text {i}"])).status_code == 200
    response = upload(client, v, "f3.pdf", make_pdf(["text 3"]))
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "You can have up to 3 files at a time. Delete one to add another."
    )
    assert len(listing(client, v)) == 3
    assert len(files_on_disk(data_dir)) == 3


def test_limit_is_per_visitor_and_frees_up_after_delete(client):
    a, b = new_visitor(), new_visitor()
    for i in range(3):
        upload(client, a, f"f{i}.pdf", make_pdf([f"t{i}"]))
    assert upload(client, b, "mine.pdf", make_pdf(["hi"])).status_code == 200

    doc_id = listing(client, a)[0]["id"]
    assert client.delete(f"/documents/{doc_id}", headers=headers(a)).status_code == 200
    assert upload(client, a, "new.pdf", make_pdf(["fresh"])).status_code == 200


def test_text_file_renamed_pdf_refused(client, data_dir):
    v = new_visitor()
    response = upload(client, v, "fake.pdf", b"just some plain text, not a pdf")
    assert response.status_code == 400
    assert response.json()["detail"] == "This file is not a valid PDF."
    nothing_left(client, data_dir, v)


def test_empty_file_refused(client, data_dir):
    v = new_visitor()
    assert upload(client, v, "empty.pdf", b"").status_code == 400
    nothing_left(client, data_dir, v)


def test_wrong_extension_refused(client, data_dir):
    v = new_visitor()
    response = upload(client, v, "notes.txt", make_pdf())
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are supported."
    nothing_left(client, data_dir, v)


@pytest.mark.parametrize(
    "sent, shown",
    [
        ("../evil.pdf", "evil.pdf"),
        ("..\\evil.pdf", "evil.pdf"),
        ("a/b.pdf", "b.pdf"),
        ("/etc/passwd.pdf", "passwd.pdf"),
        ("report #1 (final).pdf", "report #1 (final).pdf"),
    ],
)
def test_names_are_made_safe_and_cannot_escape(client, data_dir, sent, shown):
    v = new_visitor()
    assert upload(client, v, sent, make_pdf(["safe text"])).status_code == 200
    (doc,) = listing(client, v)
    assert doc["name"] == shown

    (stored,) = files_on_disk(data_dir)
    assert stored.parent == data_dir / "documents" / v
    assert stored.name == doc["id"] + ".pdf"
    assert not (data_dir.parent / "evil.pdf").exists()
    assert not (data_dir / "evil.pdf").exists()


@pytest.mark.parametrize(
    "raw, cleaned",
    [
        ("bad\x00name\x1f.pdf", "badname.pdf"),
        ("..\\..\\evil.pdf", "evil.pdf"),
        ("  spaced.pdf  ", "spaced.pdf"),
        ("dots.pdf...", "dots.pdf"),
        ("C:\\Users\\me\\doc.pdf", "doc.pdf"),
    ],
)
def test_clean_display_name(raw, cleaned):
    import uploads

    assert uploads.clean_display_name(raw) == cleaned


@pytest.mark.parametrize("raw", [None, "", ".pdf", "folder/", "x.pdf/", "noext", "a.pdf.exe"])
def test_clean_display_name_rejects(raw):
    import uploads

    with pytest.raises(uploads.UploadRejected):
        uploads.clean_display_name(raw)


def test_very_long_name_is_shortened(client):
    v = new_visitor()
    assert upload(client, v, "n" * 300 + ".pdf", make_pdf(["x y z"])).status_code == 200
    (doc,) = listing(client, v)
    assert len(doc["name"]) <= 100
    assert doc["name"].endswith(".pdf")


def test_corrupt_pdf_leaves_no_trace(client, data_dir):
    v = new_visitor()
    response = upload(client, v, "broken.pdf", b"%PDF-1.7\n" + b"garbage" * 200)
    assert response.status_code == 400
    assert response.json()["detail"] == "This file is not a valid PDF."
    nothing_left(client, data_dir, v)


def test_pdf_without_text_refused_and_cleaned(client, data_dir):
    v = new_visitor()
    response = upload(client, v, "blank.pdf", make_pdf(["", ""]))
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No readable text found in this PDF. Scanned documents are not supported."
    )
    nothing_left(client, data_dir, v)


def test_uppercase_extension_accepted(client):
    v = new_visitor()
    assert upload(client, v, "A.PDF", make_pdf(["upper"])).status_code == 200
    assert listing(client, v)[0]["name"] == "A.PDF"


def test_duplicate_name_refused_case_insensitively(client):
    v = new_visitor()
    assert upload(client, v, "Same.pdf", make_pdf(["one"])).status_code == 200
    response = upload(client, v, "same.PDF", make_pdf(["two"]))
    assert response.status_code == 400
    assert response.json()["detail"] == "You have already uploaded a file with this name."
    assert len(listing(client, v)) == 1


def test_same_name_allowed_for_different_visitors(client):
    a, b = new_visitor(), new_visitor()
    assert upload(client, a, "same.pdf", make_pdf(["one"])).status_code == 200
    assert upload(client, b, "same.pdf", make_pdf(["two"])).status_code == 200


def test_indexing_failure_cleans_up_and_is_friendly(client, data_dir, monkeypatch):
    import vector_store

    def boom(*args, **kwargs):
        raise RuntimeError("secret internal detail")

    v = new_visitor()
    monkeypatch.setattr(vector_store, "add_document", boom)
    response = upload(client, v, "x.pdf", make_pdf(["some text"]))
    assert response.status_code == 500
    assert response.json() == {
        "detail": "We could not process this file. Please try again."
    }
    assert "secret" not in response.text
    nothing_left(client, data_dir, v)


def test_partial_failure_during_indexing_removes_added_chunks(client, data_dir, monkeypatch):
    import clients
    import vector_store

    real_add = clients.get_collection().add
    calls = {"n": 0}

    class Flaky:
        def __getattr__(self, name):
            return getattr(clients.get_collection(), name)

        def add(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("second batch failed")
            return real_add(**kwargs)

    monkeypatch.setattr(vector_store, "get_collection", lambda: Flaky())
    monkeypatch.setattr(vector_store, "EMBEDDING_BATCH_SIZE", 1)
    v = new_visitor()
    long_text = "Sentence number one is here. " * 60
    response = upload(client, v, "multi.pdf", make_pdf([long_text, long_text]))
    assert response.status_code == 500
    assert calls["n"] >= 2
    nothing_left(client, data_dir, v)


def test_multi_file_request_reports_uploaded_and_skipped(client):
    v = new_visitor()
    response = client.post(
        "/upload",
        files=[
            ("files", ("good.pdf", make_pdf(["good text"]), "application/pdf")),
            ("files", ("bad.pdf", b"nope", "application/pdf")),
            ("files", ("notes.txt", b"nope", "text/plain")),
        ],
        headers=headers(v),
    )
    assert response.status_code == 200
    assert response.json() == {
        "uploaded": ["good.pdf"],
        "skipped": [
            {"filename": "bad.pdf", "reason": "This file is not a valid PDF."},
            {"filename": "notes.txt", "reason": "Only PDF files are supported."},
        ],
    }


def test_four_files_in_one_request_keeps_three(client):
    v = new_visitor()
    response = client.post(
        "/upload",
        files=[
            ("files", (f"f{i}.pdf", make_pdf([f"text {i}"]), "application/pdf"))
            for i in range(4)
        ],
        headers=headers(v),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["uploaded"] == ["f0.pdf", "f1.pdf", "f2.pdf"]
    assert body["skipped"] == [
        {
            "filename": "f3.pdf",
            "reason": "You can have up to 3 files at a time. Delete one to add another.",
        }
    ]


def test_all_rejected_returns_status_of_first_reason(client):
    v = new_visitor()
    response = client.post(
        "/upload",
        files=[
            ("files", ("a.pdf", b"nope", "application/pdf")),
            ("files", ("b.txt", b"nope", "text/plain")),
        ],
        headers=headers(v),
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "This file is not a valid PDF."


def test_two_simultaneous_uploads_cannot_both_pass_the_limit(client):
    v = new_visitor()
    for i in range(2):
        assert upload(client, v, f"f{i}.pdf", make_pdf([f"t{i}"])).status_code == 200

    results = []

    def go(name):
        results.append(upload(client, v, name, make_pdf([f"text {name}"])).status_code)

    threads = [threading.Thread(target=go, args=(n,)) for n in ("x.pdf", "y.pdf")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sorted(results) == [200, 409]
    assert len(listing(client, v)) == 3


def test_delete_with_odd_ids_is_404_and_harmless(client, data_dir):
    v = new_visitor()
    upload(client, v, "keep.pdf", make_pdf(["keep me"]))
    for bad in ("..", "%2e%2e", "keep.pdf", "a" * 32, "x" * 500):
        response = client.delete(f"/documents/{bad}", headers=headers(v))
        assert response.status_code in (404, 405)
    assert len(listing(client, v)) == 1
    assert len(files_on_disk(data_dir)) == 1
