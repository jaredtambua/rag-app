# Verification and release parts (5.x, 6.1)

### 5.1 Automated checks
- Status: done (workflow exists; first CI run happens after the push)
- Does: gathers the backend tests (from parts 2.x), runs them with front end lint and build, and adds a GitHub Actions workflow that runs the front end lint and build and the backend tests on each push.
- Does not: no browser tests, no real OpenAI calls.
- Needs: 2.4, 3.4, 4.2
- Inputs and outputs: `backend/tests/`, `.github/workflows/ci.yml`; a status badge line for the README.
- Design: tests use stubs only; CI must not need any secret. Keep the workflow short. CI installs both `requirements.txt` and `requirements-dev.txt` using the same Python version recorded in the README.
- Build steps: run everything locally; write the workflow; add the badge to the README.
- Checks: plain: `pytest backend/tests`, `npm run lint`, `npm run build` all pass locally; the workflow file is valid YAML and mirrors those commands. Pass: all green. Note in the report that the first CI run happens after the push.
- Done when: all local checks pass and the workflow exists.
- If it goes wrong: a failing test is fixed in the code, never weakened.

### 5.2 Security testing
- Status: not started
- Does: runs the installed `security-testing` skill (`C:\Users\dcruz\.claude\skills\security-testing\SKILL.md`) once against the LOCAL running app with `FAKE_OPENAI=1` (the stub from 2.4), covering the upload route, per-visitor privacy, the delete route, rate limits and CORS.
- Does not: no attacks on the live Render site, no real OpenAI calls.
- Needs: 5.1
- Inputs and outputs: local backend and front end; findings list.
- Design: scope is exactly the changes in this plan. Run the local backend on port 8010 with `DATA_DIR` pointing to a temp folder so no leftover data is picked up (the dev front end uses `VITE_API_URL=http://localhost:8010`; `http://localhost:5173` is already an allowed origin). Include a CORS check: the live front-end origin is allowed and an unlisted origin is not. Route confirmed findings back to the coder, fix, then recheck each fix.
- Build steps: start local servers on a spare port with the stubbed model; run the skill; fix confirmed issues; retest.
- Checks: agent review by the security-testing skill. Pass: no confirmed high or medium finding left unfixed; anything not fixed is listed in the handover.
- Done when: the audit has run and every confirmed issue is fixed or listed.
- If it goes wrong: if the app cannot be run safely, report the gap; do not claim the test happened.

### 5.3 Browser walk-through (QA)
- Status: not started
- Does: starts the local app with `FAKE_OPENAI=1` and `UPLOAD_TTL_SECONDS` set low for the expiry step, then follows the `qa` skill (`C:\Users\dcruz\.claude\skills\qa\SKILL.md`) through the whole visitor journey on the local app: land on the page, Try the Demo, upload, wait, ask, read the answer and sources, delete, hit each limit, let a file expire (shorten the lifetime with a setting for the test), refresh, use the keyboard only, view at 390 and 1440 widths.
- Does not: no real OpenAI calls (stub), no testing of the live site.
- Needs: 5.2
- Inputs and outputs: screenshots in the scratchpad; a short list of defects.
- Design: look at each screenshot closely. Fix clear defects only; max three fix rounds as in the design skill.
- Build steps: run the journey; fix; re-run.
- Checks: manual or visual per the qa skill. Pass: every step works and nothing overlaps, clips or scrolls sideways; defects left are listed.
- Done when: the whole journey passes or remaining defects are listed.
- If it goes wrong: report what could not be verified.

### 5.4 Independent review and repairs
- Status: not started
- Does: a fresh reviewer (reviewer skill) checks the whole change against this plan's decisions: privacy between visitors, limits, expiry, copy truthfulness, no regressions to ask, upload and delete. Confirmed findings are repaired and rechecked once.
- Does not: no review of unchanged landing animation code.
- Needs: 5.3
- Inputs and outputs: the plan, the diff since the start of this plan, test results.
- Design: give the reviewer requirements and diff only, not the builder's conversation.
- Build steps: spawn reviewer; repair confirmed findings; focused recheck.
- Checks: agent review. Pass: no unresolved confirmed finding.
- Done when: the reviewer reports no confirmed issues, or the rest are listed.
- If it goes wrong: after two rounds list what is unresolved.

### 6.1 Final check, push and report
- Status: not started
- Does: runs every check once more, commits any remaining changes, pushes `master` once, then reads the live site and API (plain GET requests) to confirm they respond after Render redeploys.
- Does not: no force-push, no Render settings changes.
- Needs: 5.4
- Inputs and outputs: pushed commit; a plain-English report to the user.
- Design: the report lists what changed, checks run and results, what could not be verified (LinkedIn preview, real OpenAI behaviour, live deploy timing), and the user's own to-dos: set an OpenAI monthly spend cap, test the link in LinkedIn Post Inspector, try the live demo with a real PDF.
- Build steps: run tests, lint, build; commit; push; poll the live URLs for up to 10 minutes.
- Checks: plain: all local checks pass; `git status` clean and `git log origin/master..HEAD` empty after the push; the live front end returns the page and the API answers a plain GET. Pass: all true or, if Render has not finished, reported honestly.
- Done when: pushed, and the live site is confirmed or the gap is reported.
- If it goes wrong: if the push is rejected, report it; do not force.
