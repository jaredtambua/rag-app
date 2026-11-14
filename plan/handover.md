# Handover

- **Last updated:** after part 5.1 (parts 1.1 to 5.1 built by the coder; 5.2, 5.3, 5.4 and 6.1 are for the orchestrator).
- **Done so far:** 1.1, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 5.1. Nothing has been pushed.
- **Next up:** 5.2 security testing, then 5.3 browser walk-through, 5.4 review, 6.1 push.
- **Blocked or broken:** nothing.
- **Python version:** the project `.venv` runs Python 3.14.3 (system Python is 3.13.0). README and CI use 3.14. The owner must confirm Render uses a matching Python version.
- **How to run the checks:** from the repo root `.venv\Scripts\python.exe -m pytest` (99 tests, all fake OpenAI); `cd frontend; npm run lint; npm run build`.
- **How to run the app for QA (no OpenAI):** `cd backend; FAKE_OPENAI=1 DATA_DIR=<temp folder ending in data> UPLOAD_TTL_SECONDS=<optional> ..\.venv\Scripts\python.exe -m uvicorn api:app --port 8010`; front end built with `VITE_API_URL=http://localhost:8010`.

## Environment problems found
- Port 5173 is held by another project's dev server (apply-pilot, listening on 127.0.0.1:5173) and port 8000 by that project's API. Nothing of theirs was touched. Because of this the coder did NOT drive `npm run dev` in a browser on 5173; screenshots served the built `dist` to Playwright as the origin `http://localhost:5173` (no port opened) against the real local backend on 8010. A second `npm run dev` on 5173 fails loudly (strictPort), checked. Vite's own dev server binds `::1` alongside apply-pilot's `127.0.0.1`, so a browser on `localhost:5173` may reach the wrong one: stop apply-pilot's dev server before manual QA.
- `npm run dev` for the README was checked by starting it from a fresh clone (it answers on 5173); the backend command was checked on port 8001 because 8000 is taken here.

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
