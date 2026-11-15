"""The system prompt must forbid answering from general knowledge."""

import rag


def test_prompt_forbids_general_knowledge_answers():
    prompt = " ".join(rag.SYSTEM_PROMPT.split())
    assert "Never answer from general knowledge, not even for trivial questions" in prompt
    assert "arithmetic" in prompt
    assert 'give the "could not find" reply' in prompt


def test_prompt_tells_the_model_not_to_mention_evidence_or_retrieval():
    prompt = " ".join(rag.SYSTEM_PROMPT.split())
    assert 'Never mention "evidence", "sections provided", "chunks"' in prompt
    assert 'Speak of "the uploaded documents" instead' in prompt


def test_prompt_tells_the_model_to_ask_when_a_reference_is_unclear():
    prompt = " ".join(rag.SYSTEM_PROMPT.split())
    assert "do not guess" in prompt
    assert '"the second one", "that", "it", "explain that"' in prompt
    assert "there is no History block, or the History block does not make clear" in prompt
    assert "return an empty citations list" in prompt
    assert "resolve the reference from it as before" in prompt


def test_clarification_reply_with_no_citations_passes_through_untouched(client, stubbed):
    import json

    from conftest import StubClient, ask, uploaded_visitor

    text = "Could you say which document, clause or topic you mean?"
    stubbed(StubClient(reply=json.dumps({"answer": text, "citations": []})))
    response = ask(client, uploaded_visitor(client), q="What about the second one?")
    assert response.status_code == 200
    assert response.json() == {"answer": text, "citations": []}
