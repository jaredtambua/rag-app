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


# Test-only record of the rewrite calls made in fake mode: (question, history).
REWRITE_CALLS: list = []


MAX_RECORDED_CALLS = 100


def record_rewrite(question, history) -> None:
    """Remember a rewrite call, keeping only the most recent ones."""
    REWRITE_CALLS.append((question, list(history)))
    del REWRITE_CALLS[:-MAX_RECORDED_CALLS]


def reset_calls() -> None:
    REWRITE_CALLS.clear()


def fake_rewrite(question: str, history) -> str:
    """Stand-in for the follow-up rewrite: the question plus the previous question."""
    if not history:
        return question
    return f"{question} {history[-1][0]}"


def fake_answer(question: str, context_blocks, history=None) -> dict:
    """Quote the best-matching retrieved chunk with its page citation.

    Scores against the original question only; history is ignored.
    """
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
    quote = " ".join(chunk.text.split())[:240]
    return {
        "answer": f"According to the document: {quote}",
        "citations": [{"source": block.source, "page": chunk.page, "quote": quote}],
    }
