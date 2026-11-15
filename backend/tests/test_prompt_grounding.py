"""The system prompt must forbid answering from general knowledge."""

import rag


def test_prompt_forbids_general_knowledge_answers():
    prompt = " ".join(rag.SYSTEM_PROMPT.split())
    assert "Never answer from general knowledge, not even for trivial questions" in prompt
    assert "arithmetic" in prompt
    assert 'give the "could not find" reply' in prompt

