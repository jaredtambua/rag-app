"""Conversation memory: history validation (1.1)."""

import json

import pytest

from conftest import (
    headers,
    uploaded_visitor,
)

TOO_MANY = {"detail": "Only the last 5 questions are remembered."}
TOO_LONG = {"detail": "An earlier question or answer was too long."}
UNREADABLE = {"detail": "The earlier conversation could not be read."}


def post(client, v, body):
    return client.post("/ask", json=body, headers=headers(v))


def turns(n, q="Who pays?", a="Acme pays."):
    return [{"question": q, "answer": a} for _ in range(n)]


# ---------------------------------------------------------------- 1.1 validation


def test_request_without_history_works_as_before(client):
    v = uploaded_visitor(client)
    response = post(client, v, {"question": "what is the zebra marker?"})
    assert response.status_code == 200
    assert response.json()["citations"][0]["page"] == 1


@pytest.mark.parametrize("history", [[], None])
def test_empty_or_null_history_is_none(client, history):
    v = uploaded_visitor(client)
    assert post(client, v, {"question": "zebra?", "history": history}).status_code == 200


def test_five_turns_are_accepted(client):
    v = uploaded_visitor(client)
    assert post(client, v, {"question": "zebra?", "history": turns(5)}).status_code == 200


def test_six_turns_are_refused_with_exact_message(client):
    v = uploaded_visitor(client)
    response = post(client, v, {"question": "zebra?", "history": turns(6)})
    assert response.status_code == 400
    assert response.json() == TOO_MANY


def test_earlier_question_of_501_characters_is_refused(client):
    v = uploaded_visitor(client)
    body = {"question": "zebra?", "history": turns(1, q="x" * 501)}
    response = post(client, v, body)
    assert response.status_code == 400
    assert response.json() == TOO_LONG


def test_earlier_question_of_500_characters_is_accepted(client):
    v = uploaded_visitor(client)
    body = {"question": "zebra?", "history": turns(1, q="x" * 500)}
    assert post(client, v, body).status_code == 200


def test_earlier_question_of_500_plus_trailing_spaces_is_accepted(client):
    v = uploaded_visitor(client)
    body = {"question": "zebra?", "history": turns(1, q="x" * 500 + "   ")}
    assert post(client, v, body).status_code == 200


def test_earlier_answer_of_1001_characters_is_refused(client):
    v = uploaded_visitor(client)
    body = {"question": "zebra?", "history": turns(1, a="y" * 1001)}
    response = post(client, v, body)
    assert response.status_code == 400
    assert response.json() == TOO_LONG


def test_earlier_answer_of_1000_characters_is_accepted(client):
    v = uploaded_visitor(client)
    body = {"question": "zebra?", "history": turns(1, a="y" * 1000)}
    assert post(client, v, body).status_code == 200


def test_characters_are_counted_as_code_points(client):
    v = uploaded_visitor(client)
    ok = {"question": "zebra?", "history": turns(1, q="\U0001F993" * 500)}
    assert post(client, v, ok).status_code == 200
    bad = {"question": "zebra?", "history": turns(1, q="\U0001F993" * 501)}
    assert post(client, v, bad).status_code == 400


@pytest.mark.parametrize("q", ["", "   ", "\n\t "])
def test_empty_earlier_question_is_refused(client, q):
    v = uploaded_visitor(client)
    response = post(client, v, {"question": "zebra?", "history": turns(1, q=q)})
    assert response.status_code == 400
    assert response.json() == UNREADABLE


def test_empty_earlier_answer_is_accepted(client):
    v = uploaded_visitor(client)
    body = {"question": "zebra?", "history": turns(1, a="")}
    assert post(client, v, body).status_code == 200


def test_refusal_order_count_then_question_then_answer(client):
    v = uploaded_visitor(client)
    # six turns, the first also has a bad question: the count wins
    bad_first = turns(6)
    bad_first[0]["question"] = ""
    assert post(client, v, {"question": "zebra?", "history": bad_first}).json() == TOO_MANY
    # an empty question in turn 1 beats a too-long answer in turn 1
    both = [{"question": " ", "answer": "y" * 1001}]
    assert post(client, v, {"question": "zebra?", "history": both}).json() == UNREADABLE
    # turn 1's too-long question beats turn 2's empty question
    two = [{"question": "x" * 501, "answer": ""}, {"question": "", "answer": ""}]
    assert post(client, v, {"question": "zebra?", "history": two}).json() == TOO_LONG


def test_wrong_shape_keeps_the_default_refusal(client):
    v = uploaded_visitor(client)
    assert post(client, v, {"question": "z", "history": "nope"}).status_code == 422
    assert post(client, v, {"question": "z", "history": [{"question": "a"}]}).status_code == 422


def test_refused_history_costs_no_quota(client):
    v = uploaded_visitor(client)
    for _ in range(25):
        assert post(client, v, {"question": "zebra?", "history": turns(6)}).status_code == 400
    for _ in range(20):
        assert post(client, v, {"question": "zebra?"}).status_code == 200
    assert post(client, v, {"question": "zebra?"}).status_code == 429


def _largest(chars):
    q, a = chars("q", 500), chars("a", 1000)
    return {
        "question": chars("q", 500),
        "history": [{"question": q, "answer": a} for _ in range(5)],
    }


@pytest.mark.parametrize(
    "unit", ["\U0001F993", '"', "\\", "€"], ids=["four-byte", "quote", "backslash", "euro"]
)
def test_largest_allowed_request_fits_the_body_limit(client, unit):
    v = uploaded_visitor(client)
    body = _largest(lambda _name, n: unit * n)
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    assert len(raw) < 64 * 1024
    response = client.post(
        "/ask",
        content=raw,
        headers={**headers(v), "Content-Type": "application/json"},
    )
    assert response.status_code == 200
