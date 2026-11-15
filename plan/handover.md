# Handover

- **Last updated:** 2026-11-14, after launch. All parts 1.1 to 6.1 are done and pushed to master (commit 29b15e6). Live: https://rag-app-1-8mtr.onrender.com (API https://rag-app-1nxg.onrender.com).
- **Done so far:** 1.1, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 5.1, 5.2 (security test, two repair rounds), 5.3 (browser walk-through, 13 fixes), 5.4 (independent review, repairs), 6.1 (pushed, live site and API confirmed).
- **Done after launch (local commits, NOT pushed):** owner follow-ups 1, 2, 3 and 5. (1) Ask button is a compact pill centred in the bar. (2) Enter sends, Shift+Enter adds a line, no send during IME composition, Ctrl/Cmd+Enter still sends; hint reads "Enter to send, Shift+Enter for a new line. Up to 20 questions an hour." (3) The demo keeps a display-only thread of up to 20 question and answer pairs in memory (the backend and /ask are unchanged; earlier turns are not sent). 429 and other refusals keep the thread and show the banner (question goes back in the box); server or network faults show inline with Try again; Clear history link; the box clears when a question is sent. A deleted or expired document keeps the history and adds a small line "A document was removed. Earlier answers may cite it."; with no documents left it also offers Add a PDF. (5) Landing page is five scenes over six stops: hero (brain), one knowledge base (network), answers cite pages with an Example mirroring the app (ring), lawyers and scientists (grid, spiral, dot selector), lock and key with the privacy line and Try the Demo. The stack and sphere shapes and the old brain-to-stack and lock-to-sphere paths were removed; five transition paths now join the stops. Nav links: How it works = stops 2-3, Use cases = 4-5, Privacy = 6. og-image and meta copy unchanged (hero headline unchanged).
- **Landing revision (local, NOT pushed, after item 5):** now five scenes over five stops (n / 5): brain, network, ring with the Example (question, answer, Page 9 source card) inside its hole, lawyers and scientists together on one stop (grid, no dot selector), lock and key. Spiral shape and its two paths removed; Use cases link = stop 4, Privacy = stop 5; four transition paths. Checked at 1440 and 390 with Playwright (all stops, mid-transition frames both ways, buttons, arrow keys, nav links, reduced motion). The six-stop description above is superseded. Layout redesign of stops 2 to 4 (local): stop 2 network on the left with text in a right column; stop 3 headline in a left column and the Example inside a larger ring; stop 4 grid on the left with a hairline list for lawyers and scientists on the right. Layouts at 900 px wide and below use the stacked (cloud above, words below) layout; shape sizes are capped by width and height. Checked at 1440, 1024, 768 and 390; Later changes (local): the boxed Example was removed; stop 3 is now a centred ring with the headline and one muted line ("Every answer shows the file and page it came from.") in its hole; stop 4 headline is "Find the exact quote. Or explain your own jargon." with four rows (Lawyers, Scientists, Consultants, New hires). Checked at 1440, 1024, 768 and 390.
- **Next up (owner's own, not done):**
  4. Owner's own to-dos: set an OpenAI monthly spend cap; confirm Render's Python version matches the pinned 3.14.3; try the live site with a real PDF; check the link in LinkedIn's Post Inspector; check that Render's visitor address header is not shared (limits could hit many visitors at once).
  6. Roadmap idea (do NOT claim on the site yet): dedicated project folders to group documents.
  Also: review the new landing and demo in a real browser; push when approved.
- **Checks for these changes:** backend 132 passed; front end lint and build clean; browser checks with a mocked backend at 1440 and 390 (demo: keys, thread, 429, retry, cap at 20, removal note; landing: every stop, mid-transition frames, arrow keys, buttons, nav links, dots, reduced motion). Not checked: touch devices with a soft keyboard (Enter sends there; the Ask button also works), a real backend run for these changes.
- **Skill Vault:** the Tessel proof of concept (`design/` folder, local and untracked) was deleted from the skill-vault repo on 2026-11-14 at the owner's request.
- **Blocked or broken:** nothing.
- **Python version:** the project `.venv` runs Python 3.14.3 (system Python is 3.13.0). README and CI use 3.14. The owner must confirm Render uses a matching Python version.
- **How to run the checks:** from the repo root `.venv\Scripts\python.exe -m pytest` (132 tests, all fake OpenAI); `cd frontend; npm run lint; npm run build`.
- **How to run the app for QA (no OpenAI):** `cd backend; FAKE_OPENAI=1 DATA_DIR=<temp folder ending in data> UPLOAD_TTL_SECONDS=<optional> ..\.venv\Scripts\python.exe -m uvicorn api:app --port 8010`; front end built with `VITE_API_URL=http://localhost:8010`.

## Environment notes
- Ports 5173 and 8000 may be in use by other local programs. For the browser checks the built front end was served to Playwright as the origin `http://localhost:5173` (no port opened) against the real local backend on 8010; a second `npm run dev` on 5173 fails loudly (strictPort), checked.
- `npm run dev` for the README was checked by starting it from a fresh clone; the backend command was checked on port 8001.

## Changes proposed to the plan (none applied; for the owner or orchestrator)
- Added (not in the plan): a request-body size cap (20 MB for /upload, 64 KB elsewhere, counted while streaming) and `Access-Control-Expose-Headers: Retry-After` so the page can read retry times. Both have tests.
- Landing copy: besides the scenes the plan named, the use-case title "Make a shared drive answer back." was changed to "Make your team's documents answer back." because a shared drive implies a sync feature that does not exist. Revert if unwanted.
- Backend CORS now allows only GET, POST, DELETE, OPTIONS and the headers Content-Type and X-Visitor-Id.
- Old command-line scripts `app.py`, `reindex.py`, `display.py` were deleted in 4.2 (dead under the new design) rather than moved.
- The local `backend/documents/.gitkeep` is still tracked and the old local data folders are untouched.

## Flags for the security audit (5.2)
- Uploads: `uploads.py` (name cleaning, size read while streaming, `%PDF` check), `storage.add_document` (checks inside the lock, cleanup on every failure), `api.BodyLimitMiddleware` (413 before parsing; also covers bodies sent without a length).
- Visitor identity: `visitor.py` (UUID header, 400 otherwise); every Chroma get, query and delete is scoped by `visitor_id` (`vector_store._scope`); delete only finds ids in the caller's own list.
- Rate limits: `rate_limit.py`; client IP is the LAST X-Forwarded-For entry; totals are the cost ceiling; state is in memory and resets on restart. Check: a client that spoofs only the first entries, and what happens if the proxy does not append an address.
- Deletes: `DELETE /documents/{id}`, 404 for anything not the caller's.
- CORS: `config.allowed_origins()` and the middleware in `api.py`; no credentials allowed.
- Prompt injection: system/user split and `<evidence>` tags in `rag.py` (tags inside documents are stripped).
- `FAKE_OPENAI` is refused when `RENDER` is set (checked at startup in the lifespan).
- Not covered: no malware scanning; PyMuPDF parses untrusted PDFs (page cap and size cap are the only mitigations).

## Security-test repairs (after 5.2)
- Text and drawing bombs: PDFs are now read by `pdf_worker.py` in a separate process (`pdf_parser.py`): 10 s limit, at most 2 at once (503 when busy), caps of 30 pages, 200,000 characters, 8 MB decompressed page data, 500 chunks. The lock is held only for the room check and index and list writes (room check repeated there). Embedding also runs outside the lock.
- Upload attempts (accepted or rejected) are limited before parsing: 30 per hour per address, 120 per hour in total (`config.py`, README).
- `/health` is async and lock-free. `X-Forwarded-For` joins all header lines and takes the last entry. Every `<` and `>` in document text and source names is escaped in the prompt. Deep JSON gets a 400 (FastAPI already returned 400 at the depth tested here; a `RecursionError` handler was added anyway). Answers no longer render images. The FAKE_OPENAI guard now also fires on first use and for any non-empty `RENDER`.
- Accepted and left unfixed: bidi characters in display names, trailing-slash redirect, all-zero UUID, the `reset_all` folder-name rule.
- Not covered: a PDF whose single page takes under 10 s but uses lots of memory in the worker (no memory limit on Windows; the 8 MB content cap and timeout bound it).

## Second repair round (reader memory, fair slots)
- The PDF reader child is now watched by the parent every 20 ms (psutil, added to requirements.txt, pinned 7.2.2): killed with its child processes above 350 MB or after 5 s, with the friendly 400 "too complex or too large for the demo". On Linux the child also gets a hard 700 MB address-space ceiling (not tested here: this machine is Windows). Stream sizes are counted before decompression (bounded inflate, 1 MB at a time) for page contents and for all form objects; the 8 MB content cap covers both. Nested-form amplification is not counted; the memory and time kills cover it.
- Peak memory (reader plus children), before to after: nested forms 582 MB (ran the full 10 s) to 351 MB (killed at 4.6 s); 200 MB form object 2,994 MB to 50 MB (refused in 0.3 s); 1 GB drawing page 2,028 MB to 49 MB (refused in 0.3 s).
- One reader slot per client address (global stays 2). 503 "busy" refusals are refunded from the upload-attempt counts.
- backend/requirements.txt was UTF-16 in git (the earlier rewrite kept the old encoding); it is now UTF-8.
- Not fixed: the Linux address-space limit is untested; a legitimate form-heavy PDF over the 8 MB content cap is refused.
- RLIMIT_AS (Linux address-space ceiling) was removed from the PDF reader: untested, and it counts mapped libraries so it could break normal PDFs on Render. Protection is the 350 MB watcher, the 5 s limit and the stream caps.

## QA repairs (front end, after 5.3)
- Items 1 to 13 of the QA list done: balanced headings with a non-breaking space after the count, a rate-limit refusal keeps the previous answer (banner only), the 20-an-hour limit stated in the ask hint, icon-only "Back to site" below 350 px, focus moved after upload and after deleting the last file, Escape dismisses the banner, stale errors cleared on a new choice, dropping on a full upload zone shows the limit message, live 500-character counter with Ask disabled over the limit, upload confirmation inside the phone drawer and above the ask box on phones, answer cleared when a document is deleted or expires, one message when the server is unreachable, Cmd+Enter hint on Mac (both shortcuts work), copy "Answers cite the pages they used", landing left edges aligned to one gutter (64 px at 1440) and balanced ledes.
- Behaviour choice: a server-side fault (5xx) or network failure still shows the "No answer came back" panel (with its reason) and no banner; refusals (4xx, including 429) show the banner only.
- Not changed: triangles over text and the 390 px passage gap on the landing page. Checked with mocked backend and screenshots at 1440, 390 and 320 (2 rounds).

## Review repairs
- Reader tests now track only their own worker processes (matched by the test's own temp folder), use events instead of fixed sleeps, and have generous time limits; two full runs at the same time both pass (132 tests).
- Added `.python-version` (3.14.3) at the root and in `backend/`, and a Deployment section in the README (build and start commands, environment variables). Render itself was not touched.
- New tests: first of two documents expires while the second stays live (no expired chunk returned or cited), expiry filter in the query, and delete scoped to the visitor. Mutation checks: removing the visitor scope from `delete_document` fails 1 test; removing the `uploaded_at` filter from the query fails 2 tests.
- The 500-character limit is counted in code points in the front end.

## Branch workflow (2026-11-15)
- Work lives on branch `feature/landing-redesign-and-memory` (landing redesign + conversation memory, plan in plan/memory/). Master is untouched and still what the live site builds from. Owner is practising: branch, push, pull request, staging site, then merge. A Render staging service must be created by the owner in the Render dashboard.
