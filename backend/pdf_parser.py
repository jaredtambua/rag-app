"""Reads an untrusted PDF safely.

Separate process, watched for time and memory, killed (with its child
processes) if it goes over, and only a few reads at once: two in total and
one per client address.
"""

import json
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

import config
from uploads import (
    MSG_BUSY,
    MSG_INVALID_PDF,
    MSG_PROCESSING_FAILED,
    MSG_TOO_COMPLEX,
    MSG_TOO_MANY_PAGES,
    MSG_TOO_MUCH_TEXT,
    UploadRejected,
)

logger = logging.getLogger(__name__)

WORKER = Path(__file__).resolve().parent / "pdf_worker.py"

# Only a couple of PDFs are read at the same time; the rest are told to wait.
SLOTS = threading.BoundedSemaphore(config.MAX_CONCURRENT_PARSES)

# Client addresses that have a read running (one each, so one client cannot starve the rest).
_owners_busy: set[str] = set()
_owners_lock = threading.Lock()

# Highest memory (bytes, reader and its children) seen during the latest read; for tests and tuning.
LAST_PEAK_BYTES = None

POLL_SECONDS = 0.02

_ERRORS = {
    "invalid": (400, MSG_INVALID_PDF),
    "pages": (400, MSG_TOO_MANY_PAGES),
    "text": (400, MSG_TOO_MUCH_TEXT),
    "content": (400, MSG_TOO_MUCH_TEXT),
}


def _kill_tree(process: psutil.Process) -> None:
    """Kill the reader and anything it started (on Windows the venv launcher has a child)."""
    try:
        victims = process.children(recursive=True) + [process]
    except psutil.Error:
        victims = [process]

    for victim in victims:
        try:
            victim.kill()
        except psutil.Error:
            pass

    psutil.wait_procs(victims, timeout=3)


def _tree_memory(process: psutil.Process) -> int:
    total = 0

    try:
        members = [process] + process.children(recursive=True)
    except psutil.Error:
        return 0

    for member in members:
        try:
            total += member.memory_info().rss
        except psutil.Error:
            pass

    return total


def _run_worker(path) -> dict:
    """Run the reader process under a time and memory limit and return its JSON result."""
    global LAST_PEAK_BYTES

    command = [
        sys.executable,
        "-I",
        str(WORKER),
        str(path),
        str(config.MAX_PAGES),
        str(config.MAX_EXTRACTED_CHARACTERS),
        str(config.MAX_CONTENT_BYTES),
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        watched = psutil.Process(process.pid)
    except (OSError, psutil.Error) as error:
        logger.error("Could not start the PDF reader (%s)", type(error).__name__)
        raise UploadRejected(500, MSG_PROCESSING_FAILED)

    output = []
    # A thread drains the output so a large result can never block the reader.
    drain = threading.Thread(target=lambda: output.append(process.stdout.read()), daemon=True)
    drain.start()

    started = time.monotonic()
    peak = 0
    reason = None

    while drain.is_alive():
        peak = max(peak, _tree_memory(watched))

        if peak > config.MAX_PARSE_MEMORY_BYTES:
            reason = "memory"
            break

        if time.monotonic() - started > config.PARSE_TIMEOUT_SECONDS:
            reason = "time"
            break

        drain.join(POLL_SECONDS)

    if reason:
        _kill_tree(watched)
        drain.join(2)
    else:
        process.wait()

    LAST_PEAK_BYTES = peak
    process.stdout.close()

    if reason:
        logger.warning("PDF reader stopped: %s limit", reason)
        raise UploadRejected(400, MSG_TOO_COMPLEX)

    try:
        return json.loads(output[0] if output else b"")
    except ValueError:
        # The process crashed (for example it hit its own memory ceiling).
        raise UploadRejected(400, MSG_TOO_COMPLEX)


def parse_pdf(path, owner=None) -> list[dict]:
    """Return [{"page": n, "text": ...}] for pages that have text, or raise UploadRejected.

    owner is the client address; each owner may have one read at a time.
    """
    if owner is not None:
        with _owners_lock:
            if owner in _owners_busy:
                raise UploadRejected(503, MSG_BUSY)

            _owners_busy.add(owner)

    try:
        if not SLOTS.acquire(blocking=False):
            raise UploadRejected(503, MSG_BUSY)

        try:
            result = _run_worker(path)
        finally:
            SLOTS.release()
    finally:
        if owner is not None:
            with _owners_lock:
                _owners_busy.discard(owner)

    if "error" in result:
        status, message = _ERRORS.get(result["error"], (400, MSG_INVALID_PDF))
        raise UploadRejected(status, message)

    return result["pages"]
