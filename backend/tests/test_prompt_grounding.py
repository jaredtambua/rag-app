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
