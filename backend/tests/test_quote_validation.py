"""Citation quotes must really be in the evidence the model was given."""

import json

import rag
from conftest import MARKER, StubClient, ask, uploaded_visitor
from models import ContextBlock, RetrievedChunk

TEXT_1 = "Northfield Analytics Ltd agrees to supply the services\nto Crestline Holdings from 1 March."
TEXT_2 = "The notice period is sixty days   and must be in writing."

BLOCKS = [
    ContextBlock(
        source="a.pdf",
        distance=0.5,
        chunks=[
            RetrievedChunk(page=1, chunk_index=0, text=TEXT_1),
            RetrievedChunk(page=2, chunk_index=1, text=TEXT_2),
        ],
    )
]


def cite(quote, page=1, source="a.pdf"):
    return {"source": source, "page": page, "quote": quote}


def check(*citations):
    return rag.check_citations(list(citations), BLOCKS)


def test_verbatim_quote_is_kept_unchanged():
    quote = "Northfield Analytics Ltd agrees to supply the services"
    assert check(cite(quote)) == [cite(quote)]


def test_quote_matches_across_line_breaks_and_extra_spaces():
    assert check(cite("supply the services to Crestline Holdings")) == [
        cite("supply the services to Crestline Holdings")
    ]
    assert check(cite("sixty days and must be in writing", page=2)) == [
        cite("sixty days and must be in writing", page=2)
    ]


def test_quote_shortened_with_dots_is_kept_as_its_matching_pieces():
    got = check(cite("Northfield Analytics Ltd... and Crestline Holdings from 1 March"))
    # "and Crestline..." is not verbatim (text says "to Crestline"), so only the first piece stays
    assert got == [cite("Northfield Analytics Ltd")]


def test_both_pieces_kept_and_joined_when_both_match():
    got = check(cite("Northfield Analytics Ltd agrees\u2026 to Crestline Holdings from 1 March."))
    assert got == [cite("Northfield Analytics Ltd agrees ... to Crestline Holdings from 1 March.")]
    got = check(cite("Northfield Analytics Ltd agrees ... to Crestline Holdings"))
    assert got[0]["quote"] == "Northfield Analytics Ltd agrees ... to Crestline Holdings"


def test_invented_quote_is_dropped():
    assert check(cite("The supplier shall pay a penalty of ten percent")) == []
    assert check(cite("Totally invented ... and also invented here")) == []


def test_wrong_source_is_dropped():
    assert check(cite("Northfield Analytics Ltd agrees to supply", source="other.pdf")) == []


def test_page_mismatch_is_corrected_to_where_the_text_is():
    got = check(cite("The notice period is sixty days", page=1))
    assert got == [cite("The notice period is sixty days", page=2)]


def test_malformed_citations_are_dropped_not_crashed_on():
    assert rag.check_citations(["x", {"source": "a.pdf"}, {"quote": 5}, None], BLOCKS) == []


def test_escaped_evidence_text_still_matches():
    blocks = [
        ContextBlock(source="a.pdf", distance=0, chunks=[RetrievedChunk(page=1, chunk_index=0, text="Use <b>bold</b> text here.")])
    ]
    assert rag.check_citations([cite("Use &lt;b&gt;bold&lt;/b&gt; text")], blocks)
    assert rag.check_citations([cite("Use <b>bold</b> text")], blocks)


def test_end_to_end_invented_quote_is_dropped_but_answer_kept(client, stubbed):
    real = f"The {MARKER} is a striped animal."
    reply = json.dumps(
        {
            "answer": "It is a striped animal.",
            "citations": [
                {"source": "z.pdf", "page": 1, "quote": real},
                {"source": "z.pdf", "page": 1, "quote": "An invented sentence that is not in the file."},
            ],
        }
    )
    stubbed(StubClient(reply=reply))
    body = ask(client, uploaded_visitor(client)).json()
    assert body["answer"] == "It is a striped animal."
    assert body["citations"] == [{"source": "z.pdf", "page": 1, "quote": real}]
