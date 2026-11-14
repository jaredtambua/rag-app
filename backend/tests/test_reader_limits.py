"""Second repair round: memory and time limits on the PDF reader, and fair reader slots."""

import threading
import time

import psutil
import pytest

from bombs import DRAWING_UNIT, make_stream_bomb
from bombs2 import make_form_bomb, make_nested_forms
from conftest import headers, make_pdf, new_visitor, upload

TOO_COMPLEX = "This PDF is too complex or too large for the demo. Try a simpler file."
MB = 1024 * 1024


def nothing_left(client, data_dir, v):
    import clients

    assert client.get("/documents", headers=headers(v)).json()["documents"] == []
    assert len(clients.get_collection().get()["ids"]) == 0
    root = data_dir / "documents"
    assert not (root.exists() and [p for p in root.rglob("*") if p.is_file()])


def readers_running(data_dir):
    """Reader processes started for this test (their command line names its own temp folder)."""
    found = []
    for proc in psutil.process_iter(["cmdline"]):
        try:
            line = " ".join(proc.info["cmdline"] or [])
        except psutil.Error:
            continue
        if "pdf_worker.py" in line and str(data_dir) in line:
            found.append(proc.pid)
    return found


def test_form_object_bomb_refused_and_memory_stays_low(client, data_dir):
    import pdf_parser

    v = new_visitor()
    data = make_form_bomb(150)
    assert len(data) < 1_000_000
    started = time.time()
    response = upload(client, v, "form.pdf", data)
    assert time.time() - started < 20
    assert response.status_code == 400
    assert response.json()["detail"].startswith("This document has too much")
    assert (pdf_parser.LAST_PEAK_BYTES or 0) < 450 * MB
    assert readers_running(data_dir) == []
    nothing_left(client, data_dir, v)


def test_huge_drawing_stream_is_not_decompressed_before_the_size_check(client, data_dir):
    import pdf_parser

    v = new_visitor()
    data = make_stream_bomb(300, DRAWING_UNIT)
    response = upload(client, v, "draw.pdf", data)
    assert response.status_code == 400
    assert (pdf_parser.LAST_PEAK_BYTES or 0) < 450 * MB
    nothing_left(client, data_dir, v)


def test_nested_forms_bomb_is_killed_with_a_friendly_message(client, data_dir):
    import pdf_parser

    v = new_visitor()
    data = make_nested_forms(12, 10)
    assert len(data) < 10_000
    started = time.time()
    response = upload(client, v, "nested.pdf", data)
    assert time.time() - started < 20
    assert response.status_code == 400
    assert response.json()["detail"] == TOO_COMPLEX
    assert (pdf_parser.LAST_PEAK_BYTES or 0) < 600 * MB
    assert readers_running(data_dir) == []
    nothing_left(client, data_dir, v)


def test_memory_limit_kills_the_reader(client, data_dir, monkeypatch):
    import config

    monkeypatch.setattr(config, "MAX_PARSE_MEMORY_BYTES", 20 * MB)
    v = new_visitor()
    response = upload(client, v, "ok.pdf", make_pdf(["some text"]))
    assert response.status_code == 400
    assert response.json()["detail"] == TOO_COMPLEX
    assert readers_running(data_dir) == []
    nothing_left(client, data_dir, v)


def test_time_limit_message_and_defaults(client, data_dir, monkeypatch):
    import config

    assert config.PARSE_TIMEOUT_SECONDS == 5
    assert config.MAX_PARSE_MEMORY_BYTES == 350 * MB
    monkeypatch.setattr(config, "PARSE_TIMEOUT_SECONDS", 0.001)
    response = upload(client, new_visitor(), "slow.pdf", make_pdf(["some text"]))
    assert response.status_code == 400
    assert response.json()["detail"] == TOO_COMPLEX
    assert readers_running(data_dir) == []


def test_normal_pdfs_still_pass_with_the_limits(client):
    pages = [f"Page {i}. " + "Ordinary words fill the page. " * 20 for i in range(30)]
    started = time.time()
    assert upload(client, new_visitor(), "ok.pdf", make_pdf(pages)).status_code == 200
    assert time.time() - started < 20


# ---- fair reader slots ----


class HeldReader:
    """Makes every read wait until released, and counts how many reads have started."""

    def __init__(self):
        self.release = threading.Event()
        self.started = 0
        self._lock = threading.Lock()
        self.changed = threading.Condition(self._lock)

    def reader(self, real):
        def held(path):
            with self.changed:
                self.started += 1
                self.changed.notify_all()
            assert self.release.wait(30)
            return real(path)

        return held

    def wait_started(self, count):
        with self.changed:
            assert self.changed.wait_for(lambda: self.started >= count, timeout=20)


@pytest.fixture
def held(monkeypatch):
    import pdf_parser

    hold = HeldReader()
    monkeypatch.setattr(pdf_parser, "_run_worker", hold.reader(pdf_parser._run_worker))
    yield hold
    hold.release.set()


def post(client, name, ip):
    return client.post(
        "/upload",
        files=[("files", (name, make_pdf([f"text of {name}"]), "application/pdf"))],
        headers={**headers(new_visitor()), "X-Forwarded-For": ip},
    )


def post_in_background(client, name, ip):
    box = {}
    thread = threading.Thread(target=lambda: box.update(response=post(client, name, ip)))
    thread.start()
    return thread, box


def test_one_reader_slot_per_address(client, held):
    ip = "203.0.113.1"
    first, box = post_in_background(client, "a.pdf", ip)
    held.wait_started(1)
    second = post(client, "b.pdf", ip)
    held.release.set()
    first.join()
    assert box["response"].status_code == 200
    assert second.status_code == 503
    assert second.json()["detail"] == (
        "The demo is busy reading other files. Please try again in a moment."
    )


def test_two_addresses_can_read_at_once_a_third_waits(client, held):
    a, box_a = post_in_background(client, "a.pdf", "203.0.113.1")
    b, box_b = post_in_background(client, "b.pdf", "203.0.113.2")
    held.wait_started(2)
    third = post(client, "c.pdf", "203.0.113.3")
    held.release.set()
    a.join()
    b.join()
    assert box_a["response"].status_code == 200
    assert box_b["response"].status_code == 200
    assert third.status_code == 503


def test_busy_refusals_do_not_count_as_attempts(client, held, monkeypatch):
    import config

    monkeypatch.setattr(config, "UPLOAD_ATTEMPT_LIMIT_PER_IP", 2)
    ip = "203.0.113.9"
    first, box = post_in_background(client, "a.pdf", ip)
    held.wait_started(1)
    refused = post(client, "b.pdf", ip)
    held.release.set()
    first.join()
    assert box["response"].status_code == 200
    assert refused.status_code == 503
    # Attempts so far: a (counted) and b (refunded). One attempt is left, then none.
    assert post(client, "c.pdf", ip).status_code == 200
    assert post(client, "d.pdf", ip).status_code == 429


def test_slot_is_released_after_a_failure(client):
    ip = "203.0.113.20"
    assert post(client, "x.pdf", ip).status_code == 200
    bad = client.post(
        "/upload",
        files=[("files", ("bad.pdf", b"%PDF-1.4 garbage", "application/pdf"))],
        headers={**headers(new_visitor()), "X-Forwarded-For": ip},
    )
    assert bad.status_code == 400
    assert post(client, "y.pdf", ip).status_code == 200
