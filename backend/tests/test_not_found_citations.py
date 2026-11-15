"""An answer that says the documents lack the information must not carry citations."""

import json

import pytest

import rag
from models import ContextBlock, RetrievedChunk
from conftest import MARKER, StubClient, ask, uploaded_visitor

CITE = [{"source": "z.pdf", "page": 1, "quote": "something relevant"}]
BLOCKS = [ContextBlock(source="z.pdf", distance=0, chunks=[RetrievedChunk(page=1, chunk_index=0, text="here is something relevant")])]


@pytest.mark.parametrize(
    "answer",
    [
        "I could not find this in the uploaded documents.",
        "The documents do not mention a non-compete clause.",
        "There is no information about a non-compete in the documents.",
        "The contract does not contain any reference to arbitration.",
        "The notice period is not specified.",
        "The uploaded text has no reference to the budget.",
        "The paper does not address side effects.",
        "The agreement does not include a non-compete clause.",
        "This is not mentioned in the provided evidence.",
    ],
)
def test_absent_answers_lose_their_citations(answer):
    parsed = rag.clean_citations({"answer": answer, "citations": list(CITE)}, [])
    assert parsed["citations"] == []


@pytest.mark.parametrize(
    "answer",
    [
        "The agreement does not allow assignment without the other party's consent.",
        "The agreement does not allow subcontracting.",
        "The fee does not include VAT of 20 percent.",
        "The contract does not include a refund, unless the goods are faulty.",
        "Payment is due within 30 days. The agreement does not mention late fees.",
        "The paper reports 142 people took part.",
        "The report is long. " * 30 + "It could not find a way out.",
        "- The agreement does not mention fees.\n- It does not mention tax.",
    ],
)
def test_real_answers_keep_their_citations(answer):
    parsed = rag.clean_citations({"answer": answer, "citations": list(CITE)}, BLOCKS)
    assert parsed["citations"] == CITE


def test_end_to_end_absent_answer_has_no_citations(client, stubbed):
    reply = json.dumps(
        {
            "answer": "The documents do not mention a non-compete clause.",
            "citations": [{"source": "z.pdf", "page": 1, "quote": f"The {MARKER} is a striped animal."}],
        }
    )
    stubbed(StubClient(reply=reply))
    v = uploaded_visitor(client)
    body = ask(client, v).json()
    assert body["citations"] == []
    assert "non-compete" in body["answer"]


def test_end_to_end_rule_answer_keeps_its_citation(client, stubbed):
    quote = f"The {MARKER} is a striped animal."
    reply = json.dumps(
        {
            "answer": "The agreement does not allow assignment without consent.",
            "citations": [{"source": "z.pdf", "page": 1, "quote": quote}],
        }
    )
    stubbed(StubClient(reply=reply))
    v = uploaded_visitor(client)
    assert ask(client, v).json()["citations"] == [{"source": "z.pdf", "page": 1, "quote": quote}]
