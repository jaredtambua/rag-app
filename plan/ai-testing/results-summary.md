# Real-AI testing: results summary (2026-11-15)

First test of the demo against real OpenAI (about 460 model and embedding calls in total, a few dollars at most). Detailed per-phase reports were written outside the repo; this is the record of what was found and fixed. The fixes are in `fixes.md` and on branch `fix/retrieval-and-citations`.

## What the first run found (before fixes)
- Facts 20/24 (83%): three easy science-paper questions got a false "not found".
- "What is 15 times 12?" was answered from general knowledge.
- "Not found" answers carried unrelated citations; one quote had "..." spliced in.
- Broad "summarise" questions and two-part questions were thin or lost a half.
- Hidden instructions inside a document (for example "answer BANANA") were obeyed for meta-questions.
- Ambiguous follow-ups with no history got a confident guess.

## Root causes
- A relevance cut-off (`MAX_DISTANCE = 1.0`) threw away almost every useful chunk, so each question got 3 to 5 chunks; the caps we raised first were never reached.
- A 12,000 character block limit dropped a whole merged block on small documents.
- No filtering of citations, no check of quotes against the document, no rule against general knowledge, no rule for unclear questions, weak injection wording.
- One JSON reply with a stray backslash was rejected as "unexpected reply".

## After the fixes (final regression runs)
- Facts 24/24; declines 12/12 (off-topic and absent questions refuse, no stray citations); cross-document 6/6; jargon 8/8, undefined term not invented.
- Citations: 100 percent verbatim, about 97 percent on the right page (misses are pieces of shortened quotes).
- Broad summaries now cover the document; compound questions answer both halves.
- Follow-up memory works (10/10 with history, never worse than cold); off-topic follow-up declines; hostile history not obeyed.
- Visitor isolation, limits, CORS and logs: pass. The 21st-question rate limit was confirmed by unit tests, not run live.
- Latency: median about 2.3 s, summaries 6 to 10 s. Cost: about 0.2 to 0.5 cents per question (estimate).

## Known limits (accepted)
- A user can still make the model say a word by asking for it ("say BANANA"); this only affects their own session.
- A bare ambiguous question such as "And who has to give it?" with no history can still be guessed.
- Two-part questions use one search; fine for the demo, splitting them into sub-searches is a possible follow-up for large uploads.
- Quote page labels on shortened ("...") quotes are occasionally the neighbouring page.
- A real touch-device and live-site check is still the owner's.
