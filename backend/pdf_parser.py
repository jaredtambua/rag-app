"""Reads an untrusted PDF safely: separate process, time limit, size caps, few at once."""

import json
import logging
import subprocess
import sys
import threading
from pathlib import Path

import config
from uploads import (
    MSG_BUSY,
    MSG_INVALID_PDF,
    MSG_PARSE_TIMEOUT,
    MSG_TOO_MANY_PAGES,
    MSG_TOO_MUCH_TEXT,
    UploadRejected,
)

logger = logging.getLogger(__name__)

WORKER = Path(__file__).resolve().parent / "pdf_worker.py"

# Only a couple of PDFs are read at the same time; the rest are told to wait.
SLOTS = threading.BoundedSemaphore(config.MAX_CONCURRENT_PARSES)

_ERRORS = {
    "invalid": (400, MSG_INVALID_PDF),
    "pages": (400, MSG_TOO_MANY_PAGES),
    "text": (400, MSG_TOO_MUCH_TEXT),
    "content": (400, MSG_TOO_MUCH_TEXT),
}


def parse_pdf(path) -> list[dict]:
    """Return [{"page": n, "text": ...}] for pages that have text, or raise UploadRejected."""
    if not SLOTS.acquire(blocking=False):
        raise UploadRejected(503, MSG_BUSY)

    try:
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
            done = subprocess.run(
                command,
                capture_output=True,
                timeout=config.PARSE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise UploadRejected(400, MSG_PARSE_TIMEOUT)
        except OSError as error:
            logger.error("Could not start the PDF reader (%s)", type(error).__name__)
            raise UploadRejected(500, "We could not process this file. Please try again.")
    finally:
        SLOTS.release()

    try:
        result = json.loads(done.stdout)
    except ValueError:
        # The process crashed (for example it ran out of memory).
        raise UploadRejected(400, MSG_INVALID_PDF)

    if "error" in result:
        status, message = _ERRORS.get(result["error"], (400, MSG_INVALID_PDF))
        raise UploadRejected(status, message)

    return result["pages"]
