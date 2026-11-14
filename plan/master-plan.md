# Master plan: Tessel demo, public MVP

## 1. Goal and decisions

Make the Tessel landing page plus RAG demo (React front end in `frontend/`, Python API in `backend/`, both on Render) safe, polished and shareable on LinkedIn in one sitting. A stranger lands on the site, uploads a document they know, asks questions, gets cited answers. The real product (not built here) would be a persistent, personalised knowledge base; the demo says so honestly.

Decisions (made with the user, do not reopen):
- **No ready-made documents.** Visitors start empty and upload their own PDF. The first-run screen guides them.
- **Private per visitor, temporary.** Each browser gets a random visitor ID. A visitor sees and can delete only their own uploads. Every upload (file and its search index) is removed 30 minutes after it was uploaded. The UI says this clearly, with time left per file.
- **Limits:** 5 MB per file, 30 pages, 3 files at a time per visitor, 20 questions per hour per visitor. Questions max 500 characters.
- **Render disk is ephemeral:** fine, because uploads are temporary by design. No persistent disk.
- **Scope:** safe, polished, shareable. Not in scope: accounts/login, streaming answers, hybrid search or reranking, answer-quality tuning, multi-turn chat history, a full test suite.
- **Existing stack stays:** React 19 + Vite, FastAPI, Chroma, OpenAI embeddings and answers, react-markdown. Tessel look and landing page are done and proven; leave them except the copy edits in 3.3.
- Live URLs: front end `https://rag-app-1-8mtr.onrender.com`, API `https://rag-app-1nxg.onrender.com`. Dev server must run on port 5173 (the API allows that origin).

## 2. Approved up front

- Install packages and tools (npm, pip) and run local servers, builds, lints and tests.
- Create, change and delete files inside this repo, including `backend/` code.
- Run checks with fake or stubbed OpenAI responses. NO real OpenAI calls, no paid usage.
- Do not touch Render settings, DNS or the OpenAI account. Never print or copy values from `backend/.env`.
- Install Playwright and its browser for screenshots.
- Leave the existing local `backend/documents/` and `backend/vectorstore/` data untouched (do not delete or move it). The new code uses a new git-ignored `backend/data/` folder instead.
- Git: commit on `master` as parts finish. Push to `origin master` ONCE, at part 6.1, after every check passes. Never force-push or rewrite history.
- Anything else of the same kind as the above is approved. Genuinely new and risky or hard to undo: skip it, note it in the handover, carry on.

## 3. How to work from this plan

- Read this plan, then `plan/handover.md`, then continue from the first part that is not done.
- Build a part, run its checks, and move on only when they pass. Fix failures before continuing.
- At each checkpoint update the part's status (checklist and the part's Status line) and the handover note, unless your brief says you are working under a lead orchestrator; then report to the lead and leave them alone.
- Work through the whole plan without stopping to ask. The "Approved up front" list is your permission.
- Never edit the plan to suit the code. If the plan seems wrong, write the proposed change in the handover note and carry on with another part, or stop and wait for the user.
- Stop only on a true block. Write what was tried, what is needed and what is next in the handover note.
- Commit and push only as the Approved list says.

## 4. Assumptions and open questions

- Assumption: visitor ID is a random UUID the browser makes and keeps in local storage, sent on every request as the `X-Visitor-Id` header. It is not a login; it only separates strangers. The server rejects missing or malformed IDs with a clear error.
- Assumption: limits and the 30-minute lifetime live in `backend/config.py` so they can change in one place, and the lifetime can be overridden with the `UPLOAD_TTL_SECONDS` environment variable (used by tests and QA).
- Design choice (settled): ONE shared Chroma collection for all visitors, every chunk tagged with its visitor ID and document ID, and every query filtered by the caller's visitor ID. Files live in `backend/data/documents/<visitor>/<doc id>.pdf`. One process-wide lock guards all Chroma and file operations (uploads, deletes, asks that touch the index, and the sweeper). The sweeper starts in the FastAPI lifespan. A `now()` clock function is injectable for tests.
- Identity (settled): chunk IDs are `<doc_id>-chunk-N`. Chunk metadata holds `visitor_id`, `doc_id`, `uploaded_at` and `source` (the display file name, used by citations and grouping). EVERY Chroma `get`, `query` and `delete` (including the neighbour-chunk lookup and delete-on-reindex) filters on `visitor_id` plus `doc_id` or `visitor_id` alone; two visitors uploading the same file name must never see or affect each other's chunks.
- Paths and restart (settled): data paths are anchored on the file location (`Path(__file__).parent`), never the working directory. New data root `backend/data/` (override with the `DATA_DIR` environment variable) holds `documents/` and `vectorstore/`. Tests set `DATA_DIR` to a temp folder. On every startup the app wipes `backend/data/` (uploads never survive a restart, matching the 30-minute promise); the old `backend/documents/` and `backend/vectorstore/` are never touched.
- Contract (settled): `GET /documents` returns `{"documents": [ ... ]}` (the same wrapper as today) where each entry is `{id, name, uploaded_at, seconds_left}`. `/upload` takes several files and processes them one at a time; the response keeps the current `{uploaded, skipped}` shape, with each rejected file (any validation reason, including the 3-file limit) listed in `skipped` with its reason; if every file is rejected, return a 4xx with the first reason. Rate-limit quota is consumed only by requests that pass validation (an empty or over-long question or a rejected upload costs nothing).
- `DELETE /documents/{id}` takes the document id; `/ask` keeps its current shape. Expiry is enforced at read time (expired files are hidden from the list and ignored by `/ask` immediately) as well as by the sweeper.
- Error codes (settled): 413 file too big; 400 for not a PDF, no readable text, too many pages, duplicate name, over-long or empty question, missing or bad visitor ID; 409 when the visitor already has 3 files; 429 for rate limits with `Retry-After`. The front end shows the backend's `detail` message for any 4xx.
- Python version: use the local Python version for the new `requirements.txt` and record it in the README; the owner must confirm Render uses a matching Python version (say so in the final report; do not touch Render).
- Assumption: rate-limit and expiry state is held in memory in one process (single Render instance). A restart clears it, which is acceptable.
- Defaults from plan review (builder uses these, no need to ask): sweeper runs every 60 seconds; delete is by document id everywhere (ignore any older wording about names); create the shared fake module and `backend/requirements-dev.txt` in 2.1 (2.4 only adds the `FAKE_OPENAI` switch and the `RENDER` guard); leave `app.py`, `reindex.py` and `display.py` alone until 4.2; the one lock is held for a whole upload (a short stall for other requests is acceptable in a demo); the startup wipe refuses to delete a `DATA_DIR` that is not a dedicated folder (its last part must be `data` or it must sit under the system temp folder); one upload-quota unit per request that passes validation; QA uses backend port 8010 with `VITE_API_URL=http://localhost:8010`; the demo polls `/health` first (no visitor ID needed there) for the waking message and retries, then loads documents once it answers; `requirements.txt` and `requirements-dev.txt` both live in `backend/` and CI installs both from there.
- Assumption: the site owner sets an OpenAI monthly spend cap in the OpenAI dashboard (tell the user in the final report; the agent cannot do it).
- Open: the user's GitHub/LinkedIn links are NOT in scope (user declined profile links); no footer links.

## 5. Build order

- [x] 1.1 Save the current UI work as a commit
- [x] 2.1 Per-visitor private storage with 30-minute expiry
- [x] 2.2 Upload limits and safe file handling
- [x] 2.3 Question limits and rate limiting
- [x] 2.4 Backend tidy: errors, logging, batching, hardening, settings
- [x] 3.1 Front end: visitor ID, limits, expiry countdown, new messages
- [ ] 3.2 Front end: server waking-up message
- [ ] 3.3 Front end: honest landing and demo copy
- [ ] 3.4 Share preview, favicon, dev port, unused files
- [ ] 4.1 README, licence, example settings
- [ ] 4.2 Repo tidy
- [ ] 5.1 Automated checks (backend tests, front end lint and build)
- [ ] 5.2 Security testing
- [ ] 5.3 Browser walk-through (QA)
- [ ] 5.4 Independent review and repairs
- [ ] 6.1 Final check, push and report

Part sections: `part-start.md` (1.1, 4.x), `part-backend.md` (2.x), `part-frontend.md` (3.x), `part-verify.md` (5.x, 6.1).
