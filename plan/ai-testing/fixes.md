# Fixes from the real-AI testing (branch fix/retrieval-and-citations)

Source diagnosis: p2b.md (scratchpad aitest results). Backend tests: `.venv\Scripts\python.exe -m pytest -q`.

## 1. Retrieval size bug (backend/retrieval.py, config.py, models.py)
- Why: on a small document nearly every chunk counted as relevant, the merged block went over the 12,000 character limit and the whole block was dropped, so the model got no context and the app said "not found".
- Fix: at most MAX_SELECTED (6) best chunks are kept before neighbours are added. A block over the budget is now trimmed from its ends (the worst-matching end first) instead of dropped. Chunks carry the distance of their match so trimming knows which end is weakest.
- Retest: ask the three failed paper questions (how many people took part, what dose, how much faster at week 8); run the fact set (expect 24 of 24) and a summary question per document.

## 2. Prompt grounding line (backend/rag.py)
- Why: "15 multiplied by 12" was answered 180 from general knowledge.
- Fix: the Grounding section now says never to answer from general knowledge, even for trivial questions, and to give the "could not find" reply instead.
- Retest: off-topic, not-in-document and fact sets, plus a few extra sums or trivia.

## 3. No citations on a "not found" answer (backend/rag.py, says_information_is_absent)
- Why: the model hedged ("not mentioned") and still listed four unrelated quotes.
- Fix: a text rule drops citations only when the answer is under 400 characters, is plain prose with no digits or list lines, has no rule-style words (allow, without, unless, consent...), and says the documents lack the thing. When in doubt citations are kept.
- Retest: the non-compete question (no citations), the arbitration question (citation kept), all fact answers (citations kept).

## 4. Quote validation (backend/rag.py, check_citations)
- Why: the model shortened a quote with "...".
- Fix: each quote must appear word for word (whitespace ignored) in the evidence for its source and page. A quote with "..." is split and only the matching pieces are kept, joined with " ... ". No match: the citation is dropped (the answer stays). If the text is on another page of the same source, the page is corrected.
- Retest: run the citation check over the harness (target: every quote verbatim).
