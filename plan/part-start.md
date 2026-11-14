# Starting and polish parts (1.1, 4.x)

### 1.1 Save the current UI work as a commit
- Status: not started
- Does: commits the uncommitted front-end work (demo layout redesign, ask bar fixes, headline wording) on `master`. No push.
- Does not: no push, no new changes.
- Needs: nothing
- Inputs and outputs: working tree in, one commit out. `plan/` is committed with the code unless the user says otherwise.
- Design: check `git status` first and stage only the files that belong to this work; `design/` and `.env` stay ignored. End the message with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Build steps: `git status`; `npm run lint` and `npm run build` in `frontend`; commit.
- Checks: plain: lint and build pass before committing; `git status` is clean afterwards. Pass: both.
- Done when: the working tree is clean and the commit exists locally.
- If it goes wrong: if lint or build fails, fix the failure first (it is front-end code only).

### 4.1 README, licence, example settings
- Status: not started
- Does: a root `README.md`, an MIT `LICENSE`, `backend/.env.example`, `frontend/.env.example`; replaces `frontend/README.md` (Vite template) with a short pointer to the root README.
- Does not: no footer or profile links; no claims beyond what is built.
- Needs: 2.4, 3.3, 3.4
- Inputs and outputs: README sections: one-line pitch; live demo link; screenshots (landing, demo first run, an answer with sources; captured with Playwright into `docs/screenshots/`, optimised); how it works (PDF to page text to chunks to embeddings to Chroma to retrieval with neighbour expansion to answer with page citations); stack; local setup (backend and frontend, env vars, port 5173); demo limits and the 30-minute temporary uploads; honest known limits; a short roadmap (persistent personal knowledge base, accounts, hybrid search and reranking, answer checking).
- Design: plain English, short, scannable. Licence holder: use the git user name from `git config user.name`. Example files hold names only, never values; mention that an OpenAI key is needed.
- Build steps: capture screenshots from the running app (local backend with `FAKE_OPENAI=1`); write files; check every command in the README by actually running it where possible. Setup is verified up to starting both servers and loading the demo; no real upload or ask against OpenAI. Mention the Python version, `VITE_API_URL` (build-time) and `ALLOWED_ORIGINS`.
- Checks: manual: follow the README's setup from a clean checkout (the commands must work, including starting both servers); links and image paths resolve. Pass: setup works exactly as written.
- Done when: a stranger could run the project from the README alone.
- If it goes wrong: if a command cannot be verified, say so in the README's known limits or fix it.

### 4.2 Repo tidy
- Status: not started
- Does: removes duplicate lines in `.gitignore`; moves the manual command-line scripts (`app.py`, `reindex.py`, `display.py`) into `backend/scripts/` or removes them if the new design makes them dead; confirms nothing runtime (vector store, documents, `__pycache__`, `.env`) is tracked.
- Does not: no history rewrite, no deletion of anything still used.
- Needs: 2.4
- Inputs and outputs: `git ls-files` list before and after.
- Design: before deleting or moving a file, grep for imports and references; list what you will touch first.
- Build steps: tidy; run the backend tests and a backend start to prove nothing broke.
- Checks: plain: `git ls-files` contains no `.env`, vector store or cache; backend tests pass; the app imports and starts. Pass: all true.
- Done when: the repo contains only what the project needs.
- If it goes wrong: restore any file whose removal breaks a test or the app.
