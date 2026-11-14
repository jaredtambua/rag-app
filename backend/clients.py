"""Lazily created OpenAI and Chroma clients.

Nothing is created at import time, so the app and the tests import safely
without an OpenAI key or a data folder.
"""

import chromadb
from chromadb.config import Settings
from openai import OpenAI

import config

_client = None
_chroma_client = None
_collection = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def get_collection():
    """The one shared Chroma collection for all visitors."""
    global _chroma_client, _collection
    if _collection is None:
        path = config.vectorstore_path()
        path.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(path), settings=Settings(anonymized_telemetry=False)
        )
        _collection = _chroma_client.get_or_create_collection(
            name=config.COLLECTION_NAME
        )
    return _collection


def reset_clients() -> None:
    """Forget the cached clients (startup wipe and tests)."""
    global _client, _chroma_client, _collection
    _client = None
    _chroma_client = None
    _collection = None
