"""The model's JSON reply: requested as JSON, parsed tolerantly, refused politely."""

import json

import pytest

import rag
from conftest import StubClient, ask, uploaded_visitor

BS = "\\"  # one backslash character


def test_valid_json_still_parses():
    reply = json.dumps({"answer": "A " + BS + " backslash and \"quotes\"\n", "citations": []})
    assert rag.parse_answer(reply)["answer"] == "A " + BS + ' backslash and "quotes"\n'


def test_stray_backslash_is_repaired():
    reply = '{"answer": "Pay C:' + BS + "Users or 50" + BS + '% of fees", "citations": []}'
    with pytest.raises(json.JSONDecodeError):
        json.loads(reply)
    assert rag.parse_answer(reply)["answer"] == "Pay C:" + BS + "Users or 50" + BS + "% of fees"


def test_repair_leaves_valid_escapes_alone():
    # \n, \\, é, \" are valid; the final \x is stray
    reply = (
        '{"answer": "line' + BS + "nbreak " + BS + BS + " " + BS + "u00e9 " + BS + '"q' + BS + '" stray' + BS + 'x", "citations": []}'
    )
    assert rag.parse_answer(reply)["answer"] == "line\nbreak " + BS + " é \"q\" stray" + BS + "x"


def test_garbage_still_gives_the_friendly_error():
    with pytest.raises(rag.AnswerError) as error:
        rag.parse_answer("this is not json {")
    assert error.value.message == rag.MSG_BAD_REPLY


def test_request_asks_for_json_mode(client, stubbed):
    reply = json.dumps({"answer": "x", "citations": []})
    stub = stubbed(StubClient(reply=reply))
    assert ask(client, uploaded_visitor(client)).status_code == 200
    (call,) = stub.chat_calls
    assert call["response_format"] == {"type": "json_object"}


def test_end_to_end_stray_backslash_reply_is_answered(client, stubbed):
    stubbed(StubClient(reply='{"answer": "It costs 5' + BS + '% more.", "citations": []}'))
    response = ask(client, uploaded_visitor(client))
    assert response.status_code == 200
    assert response.json()["answer"] == "It costs 5" + BS + "% more."
