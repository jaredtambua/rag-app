"""Shared test setup. Everything runs against fakes: no OpenAI calls."""

import os
import uuid

# Set before any app module is imported.
os.environ["FAKE_OPENAI"] = "1"
os.environ.pop("RENDER", None)
os.environ.pop("UPLOAD_TTL_SECONDS", None)

import fitz  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def make_pdf(pages=("Hello world.",), extra_bytes=0) -> bytes:
    """Build a small real PDF; each entry in pages is the text of one page."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(fitz.Rect(50, 50, 550, 780), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    if extra_bytes:
        data += b"\n%" + b"x" * extra_bytes
    return data


def new_visitor() -> str:
    return str(uuid.uuid4())


class Clock:
    def __init__(self, start=1_000_000.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


@pytest.fixture
def clock():
    import clock as clock_module

    fake = Clock()
    clock_module.set_clock(fake)
    yield fake
    clock_module.set_clock(None)


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    path = tmp_path / "data"
    monkeypatch.setenv("DATA_DIR", str(path))
    import clients

    clients.reset_clients()
    yield path
    clients.reset_clients()


@pytest.fixture
def client(data_dir, clock):
    import api

    with TestClient(api.app) as test_client:
        yield test_client


def headers(visitor):
    return {"X-Visitor-Id": visitor}


def upload(client, visitor, name="doc.pdf", data=None, content_type="application/pdf"):
    if data is None:
        data = make_pdf()
    return client.post(
        "/upload",
        files=[("files", (name, data, content_type))],
        headers=headers(visitor),
    )
