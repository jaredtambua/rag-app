"""Deterministic stand-ins for OpenAI, used by tests and local QA.

Switched on with FAKE_OPENAI=1. Never used when the switch is off.
"""

import hashlib
import math
import re

DIMENSIONS = 256
_WORD = re.compile(r"[a-z0-9]+")


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def fake_embedding(text: str) -> list[float]:
    """Hash of the words in the text: texts sharing words are close."""
    vector = [0.0] * DIMENSIONS
    for word in _words(text):
        digest = hashlib.sha256(word.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % DIMENSIONS] += 1.0
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        vector[0] = 1.0
        return vector
    return [v / norm for v in vector]


def fake_embeddings(texts: list[str]) -> list[list[float]]:
    return [fake_embedding(text) for text in texts]


def fake_answer(question: str, context_blocks) -> dict:
    """Quote the best-matching retrieved chunk with its page citation."""
    question_words = set(_words(question))
    best = None
    best_score = -1
    for block in context_blocks:
        for chunk in block.chunks:
            score = len(question_words & set(_words(chunk.text)))
            if score > best_score:
                best_score = score
                best = (block, chunk)
    if best is None:
        return {
            "answer": "I could not find this in the uploaded documents.",
            "citations": [],
        }
    block, chunk = best
    quote = chunk.text.strip().split("\n")[0][:200]
    return {
        "answer": f"According to the document: {quote}",
        "citations": [{"source": block.source, "page": chunk.page, "quote": quote}],
    }
