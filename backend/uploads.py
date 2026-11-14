"""Checks on one uploaded file that need no stored state."""

import re

import config

MSG_NOT_PDF_TYPE = "Only PDF files are supported."
MSG_INVALID_PDF = "This file is not a valid PDF."
MSG_TOO_BIG = "This file is larger than 5 MB."
MSG_TOO_MANY_PAGES = "This PDF has more than 30 pages."
MSG_TOO_MANY_FILES = "You can have up to 3 files at a time. Delete one to add another."
MSG_NO_TEXT = "No readable text found in this PDF. Scanned documents are not supported."
MSG_TOO_MUCH_TEXT = (
    "This document has too much text for the demo. Try a shorter or simpler PDF."
)
MSG_TOO_COMPLEX = "This PDF is too complex or too large for the demo. Try a simpler file."
MSG_BUSY = "The demo is busy reading other files. Please try again in a moment."
MSG_DUPLICATE = "You have already uploaded a file with this name."
MSG_PROCESSING_FAILED = "We could not process this file. Please try again."

_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class UploadRejected(Exception):
    """A file was refused. status is the HTTP code, message is shown to the user."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def clean_display_name(raw_name: str | None) -> str:
    """Return a safe display name, or raise UploadRejected if it is not a PDF."""
    # Keep only the last path part, whichever separator was used.
    name = re.split(r"[\\/]", raw_name or "")[-1]
    name = _CONTROL.sub("", name).strip().rstrip(". ")

    if len(name) <= 4 or not name.lower().endswith(".pdf"):
        raise UploadRejected(400, MSG_NOT_PDF_TYPE)

    extension = name[-4:]
    limit = config.MAX_DISPLAY_NAME_CHARACTERS

    if len(name) > limit:
        name = name[: limit - 4].rstrip() + extension

    return name


def read_limited(stream) -> bytes:
    """Read an upload, stopping as soon as it passes the size limit."""
    limit = config.MAX_FILE_BYTES
    parts = []
    total = 0

    while True:
        part = stream.read(64 * 1024)

        if not part:
            break

        total += len(part)

        if total > limit:
            raise UploadRejected(413, MSG_TOO_BIG)

        parts.append(part)

    data = b"".join(parts)

    if not data.startswith(b"%PDF"):
        raise UploadRejected(400, MSG_INVALID_PDF)

    return data
