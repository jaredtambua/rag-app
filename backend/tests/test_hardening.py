"""Part 2.4: errors, logging, batching, hardening, settings."""

import json
import logging
import math

import pytest
from fastapi.testclient import TestClient

from conftest import (  # noqa: F401
    INJECTION,
    MARKER,
    StubClient,
    ask,
    headers,
    make_pdf,
    new_visitor,
    upload,
    uploaded_visitor,
)

# ---- friendly errors ----


@pytest.mark.parametrize(
    "reply", ["this is not json", "", "[]", '{"foo": 1}', '{"answer": 5, "citations": []}',
              '{"answer": "ok", "citations": "none"}']
)
def test_bad_model_output_gives_friendly_error(client, stubbed, reply):
    v = uploaded_visitor(client)
    stubbed(StubClient(reply=reply))
    response = ask(client, v)
    assert response.status_code == 502
    assert response.json() == {
        "detail": "The answer service gave an unexpected reply. Please try again."
    }
    assert "Traceback" not in response.text and "JSON" not in response.text


def test_model_failure_gives_friendly_error_without_internals(client, stubbed):
    v = uploaded_visitor(client)
    stubbed(StubClient(chat_error=RuntimeError("sk-secret-internal-detail")))
    response = ask(client, v)
    assert response.status_code == 502
    assert response.json() == {
        "detail": "The answer service is unavailable right now. Please try again."
    }
    assert "secret" not in response.text


def test_good_model_output_and_code_fences_still_work(client, stubbed):
    v = uploaded_visitor(client)
    good = {"answer": "A zebra.", "citations": [{"source": "z.pdf", "page": 1, "quote": f"The {MARKER} is a striped animal."}]}
    stubbed(StubClient(reply="```json\n" + json.dumps(good) + "\n```"))
    response = ask(client, v)
    assert response.status_code == 200
    assert response.json() == good


# ---- prompt layout ----


def test_instructions_are_separate_from_document_text(client, stubbed):
    v = uploaded_visitor(client, text=f"{INJECTION}. The {MARKER} is striped. " * 15)
    stub = stubbed(StubClient(reply='{"answer": "x", "citations": []}'))
    assert ask(client, v).status_code == 200

    (call,) = stub.chat_calls
    system, user = call["messages"][0], call["messages"][1]
    assert system["role"] == "system" and user["role"] == "user"
    assert "ignore any instructions" in system["content"].lower()
    assert MARKER not in system["content"] and INJECTION not in system["content"]
    assert INJECTION in user["content"]
    start = user["content"].index("<evidence>")
    end = user["content"].index("</evidence>")
    assert start < user["content"].index(INJECTION) < end
    assert user["content"].index("what is the zebra marker?") > end


# ---- logging ----


def test_document_text_never_reaches_logs_or_stdout(client, stubbed, caplog, capsys):
    caplog.set_level(logging.DEBUG)
    v = uploaded_visitor(client)
    stubbed(StubClient(reply=f"not json {MARKER}"))
    assert ask(client, v).status_code == 502
    captured = capsys.readouterr()
    assert MARKER not in captured.out + captured.err
    assert MARKER not in caplog.text


def test_failed_upload_log_has_no_document_text(client, caplog, monkeypatch):
    import vector_store

    def boom(*a, **k):
        raise RuntimeError(f"failed on {MARKER}")

    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(vector_store, "add_document", boom)
    v = new_visitor()
    assert upload(client, v, "z.pdf", make_pdf([f"{MARKER} text"])).status_code == 500
    assert MARKER not in caplog.text


# ---- batching ----


def test_chunks_are_embedded_in_batches(client, stubbed):
    stub = stubbed(StubClient())
    import config

    text = "This sentence repeats to make some text. " * 42  # ~1700 characters
    v = new_visitor()
    assert upload(client, v, "big.pdf", make_pdf([text] * 30)).status_code == 200

    import clients

    chunks = len(clients.get_collection().get()["ids"])
    assert chunks > config.EMBEDDING_BATCH_SIZE
    assert len(stub.embedding_calls) == math.ceil(chunks / config.EMBEDDING_BATCH_SIZE)
    assert all(len(call) <= config.EMBEDDING_BATCH_SIZE for call in stub.embedding_calls)
    assert sum(len(call) for call in stub.embedding_calls) == chunks


# ---- CORS ----

LIVE = "https://rag-app-1-8mtr.onrender.com"


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173", LIVE])
def test_allowed_origins_get_cors_header(client, origin):
    response = client.get("/health", headers={"Origin": origin})
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize(
    "origin", ["http://evil.example", "https://rag-app-1-8mtr.onrender.com.evil.example", "null"]
)
def test_other_origins_get_no_cors_header(client, origin):
    response = client.get("/health", headers={"Origin": origin})
    assert "access-control-allow-origin" not in response.headers


def test_preflight_for_visitor_header(client):
    request = {
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "x-visitor-id",
    }
    ok = client.options("/documents", headers={"Origin": LIVE, **request})
    assert ok.status_code == 200
    assert ok.headers["access-control-allow-origin"] == LIVE
    assert "x-visitor-id" in ok.headers["access-control-allow-headers"].lower()
    bad = client.options("/documents", headers={"Origin": "http://evil.example", **request})
    assert bad.status_code == 400
    assert "access-control-allow-origin" not in bad.headers


def test_page_can_read_retry_after_on_a_429(client, monkeypatch):
    import config

    monkeypatch.setattr(config, "ASK_LIMIT_TOTAL", 0)
    response = client.post(
        "/ask",
        json={"question": "hi"},
        headers={**headers(new_visitor()), "Origin": LIVE},
    )
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == LIVE
    assert "retry-after" in response.headers["access-control-expose-headers"].lower()


def test_allowed_origins_setting(monkeypatch):
    import config

    assert config.allowed_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        LIVE,
    ]
    monkeypatch.setenv("ALLOWED_ORIGINS", " https://a.example , https://b.example ,, ")
    assert config.allowed_origins() == ["https://a.example", "https://b.example"]


# ---- hardening ----


def test_api_docs_are_off_by_default(client):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


def test_docs_flag(monkeypatch):
    import config

    assert config.docs_enabled() is False
    monkeypatch.setenv("ENABLE_API_DOCS", "1")
    assert config.docs_enabled() is True


def test_fake_openai_refused_on_render(data_dir, monkeypatch):
    import api

    monkeypatch.setenv("RENDER", "true")
    with pytest.raises(RuntimeError, match="FAKE_OPENAI"):
        with TestClient(api.app):
            pass


def test_fake_openai_ok_without_render(data_dir):
    import api

    with TestClient(api.app) as c:
        assert c.get("/health").status_code == 200


def test_oversized_upload_body_refused_before_processing(client, data_dir):
    v = new_visitor()
    body = b"%PDF" + b"0" * (21 * 1024 * 1024)
    response = client.post(
        "/upload", files=[("files", ("a.pdf", body, "application/pdf"))], headers=headers(v)
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "This file is larger than 5 MB."


def test_oversized_chunked_body_without_length_refused(client):
    v = new_visitor()

    def stream():
        yield b"--b\r\nContent-Disposition: form-data; name=\"files\"; filename=\"a.pdf\"\r\n\r\n%PDF"
        for _ in range(22):
            yield b"0" * (1024 * 1024)
        yield b"\r\n--b--\r\n"

    response = client.post(
        "/upload",
        content=stream(),
        headers={**headers(v), "Content-Type": "multipart/form-data; boundary=b"},
    )
    assert response.status_code == 413


def test_oversized_json_body_refused(client):
    v = new_visitor()
    response = client.post(
        "/ask", json={"question": "x" * 200_000}, headers=headers(v)
    )
    assert response.status_code == 413
