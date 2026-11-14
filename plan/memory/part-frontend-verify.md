# Front end and verification parts (2.1, 3.x)

Front end files are in `frontend/src/demo/`: `useRagDemo.js` (all state and API calls; the `ask` function and the `thread` list), `limits.js`, `AskPanel.jsx` (the hint line), `Thread.jsx`, `Workspace.jsx`. Run from `frontend/`: `npm run lint`, `npm run build`.

### 2.1 Front end: send the last 5 turns
- Status: done
- Does: every question the visitor sends also carries their last 5 successful question-and-answer pairs, so follow-ups work. The visitor sees a short hint that follow-ups are understood, and Clear history truly forgets.
- Does not: no storage in the browser (no local storage or cookies for history), no change to the 20-turn on-screen thread, to what is displayed, or to the removed-document note.
- Needs: 1.3
- Inputs and outputs: `POST /ask` body `{question, history}` where `history` is the last 5 thread turns with status `done`, oldest first, excluding the turn being asked, each `{question, answer}` with the question trimmed and the answer cut to its first 600 characters (counted in code points, like the 500-character check). An empty array when there is nothing.
- Design: follow A6. Build the list from the `thread` at the moment of the send (a "Try again" sends the last 5 successful turns currently in the thread, excluding the failed turn, matching what is on screen). Add `sentHistoryTurns: 5` and `historyAnswerChars: 600` to `limits.js`, named clearly apart from the on-screen `historyTurns`. One short hint sentence is added to the ask hint, for example "Follow-up questions work: the last 5 questions are remembered until you refresh or clear history." Keep it inside the existing layout (check at 390 px).
- Build steps: add constants; build the history list in `ask` from the `thread` BEFORE calling `setThread`, keeping only items with kind `turn` and status `done` (skip removal notes), trimming the question at build time (a retried turn has moved to the end of the thread, as on screen, so it is never included while being retried); send it; add the hint; update the now-false comment about earlier turns never being sent (`useRagDemo.js`, about line 89; `Thread.jsx` has no such comment); lint and build.
- Checks: `npm run lint` and `npm run build` clean. The behaviour check is 3.1. Pass: both clean.
- Done when: the request body carries the right history and lint and build are clean.
- If it goes wrong: with an empty thread the body has `history: []`; never block a question because of history.

### 3.1 Browser check with a mocked back end
- Status: done (script in the scratchpad, not in the repo; mobile hint un-hidden, see handover)
- Does: proves in a real browser, with a stand-in back end, that the page sends the right history and forgets it on Clear history.
- Does not: no real back end, no real OpenAI, no quality check of real answers.
- Needs: 2.1
- Inputs and outputs: the built front end served as the allowed origin `http://localhost:5173` (as in the earlier browser checks, see `plan/handover.md`); a mocked back end reached through Playwright `page.route` interception: `/health`, `/documents` (one document) and `/ask` that records each request body and answers "Answer 1", "Answer 2", and so on. Screenshots in the scratchpad.
- Design: Playwright installed outside the repo. Scenarios: (a) the first question sends `history: []`; (b) after 7 questions in turn the 7th body has exactly questions 2 to 6 with their answers, oldest first; (c) an answer over 600 characters is sent cut to 600; (d) one question mocked to 429 and one to 500: the next request contains neither; (e) Try again after a 500 sends the last 5 successful turns currently in the thread, excluding the failed turn; (f) Clear history, then the next body has `history: []`; (g) after a page refresh the next body has `history: []`; (h) removing the document keeps the history being sent, and the existing removal note still shows; (i) the new hint is visible and not clipped at 1440 and 390 widths, and nothing scrolls sideways; (j) the on-screen thread still shows up to 20 turns.
- Build steps: write the script in the scratchpad; run; fix front end defects; rerun.
- Checks: scripted assertions plus a look at the screenshots. Pass: every assertion true and the screenshots clean.
- Done when: all scenarios pass.
- If it goes wrong: record any scenario that could not be run in the handover; do not claim it passed.

### 3.2 Independent review and repairs
- Status: not started
- Does: a fresh reviewer (the reviewer role, not the builder; if no agent can be spawned, re-read the diff yourself as a fresh reviewer and record that in the handover, then continue) checks the whole change against this plan: prompt safety (escaping, separate blocks, history never evidence), no new server storage, rate limit unchanged, first-question path unchanged, validation caps and messages, front end sends only successful turns, copy is honest. Confirmed findings are repaired and rechecked once.
- Does not: no review of the landing page or unchanged code.
- Needs: 3.1
- Inputs and outputs: this plan, the diff and the test results; a findings list.
- Design: give the reviewer requirements and the diff only, never the builder's reasoning. After repairs the builder runs three mutation checks: removing the escape on history must fail a test; sending failed turns must fail the browser check; counting the rewrite as a second rate-limit unit must fail a test. Restore each change after.
- Build steps: spawn the reviewer; repair confirmed findings; focused recheck; run the mutation checks.
- Checks: agent review plus the mutation checks. Pass: no unresolved confirmed finding.
- Done when: the reviewer reports no confirmed issues, or the rest are listed in the handover.
- If it goes wrong: after two rounds list what is unresolved.

### 3.3 Final local check (stop before pushing)
- Status: not started
- Does: runs every check once more, replaces the README line that says there is no conversation memory (about line 119) with one saying follow-ups use the last 5 questions, kept only in the browser, updates the handover and writes the owner report, then stops. Pushing is the owner's decision; commit locally only if told.
- Does not: no commit unless told, never a push, no live-site changes.
- Needs: 3.2
- Inputs and outputs: a plain-English report for the owner: what changed, checks run and results, what could not be verified (answer quality of real follow-ups, real cost and delay), the manual script from the master plan section 5, and the owner's open to-dos from the launch handover (spend cap, Python version on Render, push when ready).
- Design: the report states honestly that follow-up quality needs real OpenAI and the owner's manual script.
- Build steps: run the full back end suite, front end lint and build, and the 3.1 browser check again; update the README and handover; report.
- Checks: plain: `.venv\Scripts\python.exe -m pytest` all green; `npm run lint` and `npm run build` clean; 3.1 passes again; `git status` shows no changes beyond the pre-existing uncommitted work (the landing files, `plan/handover.md`, `plan/memory/`) plus this work. Pass: all true.
- Done when: all checks pass and the report is written; nothing pushed.
- If it goes wrong: list failures in the handover and stop.
