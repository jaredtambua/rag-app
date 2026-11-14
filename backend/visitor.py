"""Visitor identity: a random UUID the browser makes and sends on each request.

It is not a login. It only keeps strangers' uploads apart.
"""

import re

from fastapi import Header, HTTPException

_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

MESSAGE = "Missing or invalid visitor ID. Please reload the page."


def visitor_id(x_visitor_id: str | None = Header(default=None)) -> str:
    if not x_visitor_id or not _UUID.match(x_visitor_id):
        raise HTTPException(status_code=400, detail=MESSAGE)

    return x_visitor_id.lower()
