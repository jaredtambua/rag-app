# Handover

- **Last updated:** after part 3.2.
- **Done so far:** 1.1 (commit 64c5aa6), 2.1 (per-visitor storage, expiry, sweeper, fake OpenAI module, 16 tests green).
- **Next up:** 3.3 copy.
- **Blocked or broken:** nothing. `app.py`, `reindex.py`, `display.py` are broken on purpose until 4.2 (they import removed functions).
- **Changes proposed to the plan:** none yet.
- **Python version:** the project `.venv` runs Python 3.14.3 (system Python is 3.13.0). Recorded for README and CI.
- **How to run the checks:** from repo root: `.venv\Scripts\python.exe -m pytest` (needs `pytest` installed); `cd frontend; npm run lint; npm run build`.
- **Notes:** `FAKE_OPENAI=1` switch is already in place (config.fake_openai); the RENDER guard comes in 2.4. Upload endpoint is a plain `def` (threadpool). Expiry is read-time plus sweeper every 60 s.
