"""Conversation memory: checking the earlier turns sent with a question."""

import config


class HistoryRejected(Exception):
    """The earlier turns were refused. message is safe to show the user."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


MSG_TOO_MANY = f"Only the last {config.MAX_HISTORY_TURNS} questions are remembered."
MSG_TOO_LONG = "An earlier question or answer was too long."
MSG_UNREADABLE = "The earlier conversation could not be read."


def clean_history(turns) -> list[tuple[str, str]]:
    """Validate the earlier turns and return them as (question, answer) pairs.

    Refusal order: turn count, then for each turn its question, then its answer.
    Lengths are counted in code points, after stripping spaces.
    """
    if not turns:
        return []

    if len(turns) > config.MAX_HISTORY_TURNS:
        raise HistoryRejected(MSG_TOO_MANY)

    cleaned = []
    for turn in turns:
        question = turn.question.strip()
        answer = turn.answer.strip()

        if not question:
            raise HistoryRejected(MSG_UNREADABLE)
        if len(question) > config.MAX_HISTORY_QUESTION_CHARS:
            raise HistoryRejected(MSG_TOO_LONG)
        if len(answer) > config.MAX_HISTORY_ANSWER_CHARS:
            raise HistoryRejected(MSG_TOO_LONG)

        cleaned.append((question, answer))

    return cleaned
