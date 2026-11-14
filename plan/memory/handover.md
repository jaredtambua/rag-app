# Handover (conversation memory)

- **Last updated:** 2026-11-15, plan written, nothing built yet.
- **Done so far:** 1.1 (history field and validation; 154 tests green). Test helpers moved to conftest. Tests for 1.2/1.3 live in `backend/tests/test_history_followup.py` (split from test_history.py so each part commits green). Branch: feature/landing-redesign-and-memory, one local commit per part, never push.
- **Next up:** 1.2 Fakes.
- **Blocked or broken:** nothing.
- **Changes proposed to the plan:** none.
- **How to run the checks:** from the repo root `.venv\Scripts\python.exe -m pytest` (132 tests exist before this work, all with fake OpenAI); `cd frontend; npm run lint; npm run build`; the browser check is the 3.1 script (Playwright outside the repo).
- **Owner's manual quality script (after the owner pushes and deploys):** with your own PDF on the live site: (1) "List the main sections of this document." then "What does the second one say?"; (2) "Who is responsible for payment?" then "And who signs it?"; (3) an off-topic question then "And tomorrow?", which must still say it cannot find it; then Clear history and "What about the second one?" must not guess. Real follow-up quality cannot be proven without real OpenAI.
- **Owner's own to-dos (carried over from launch):** set an OpenAI monthly spend cap; confirm Render's Python version matches 3.14.3; push when you approve.
- **Notes for the builder:** the launch plan in `plan/` is finished; do not edit it. Uncommitted launch follow-up work (landing and demo changes) may be in the working tree; leave unrelated changes alone.
