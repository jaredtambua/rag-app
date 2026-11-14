# Front end parts (3.x)

Files in `frontend/src/` (`demo/`, `landing/`, `routing.js`, `index.css`) and `frontend/index.html`. Keep the Tessel look, existing layout and behaviour. Design reference: `C:\Users\dcruz\.claude\skills\design` (checks.md) for screenshot checks.

### 3.1 Front end: visitor ID, limits, expiry countdown, new messages
- Status: done (1 screenshot round)
- Does: the browser makes and remembers a visitor ID and sends it as `X-Visitor-Id` on every request. The documents list shows how long each file has left. The upload area states the limits (5 MB, 30 pages, 3 files) and a plain warning that uploads are removed after 30 minutes. Backend refusals (too big, limit reached, rate limit with retry time) are shown with the backend's message. When a file expires it disappears from the list without an error. The first-run screen invites the visitor to upload a document they know well.
- Does not: no sample documents, no accounts, no change to the look.
- Needs: 2.1, 2.2, 2.3
- Inputs and outputs: ID is a UUID in local storage (fallback to in-memory if storage is blocked). The list is now objects `{id, name, uploaded_at, seconds_left}` (was plain strings): update the list, delete (by id) and ask code to match. Show the backend `detail` text for any 4xx.
- Design: all request code stays in `demo/useRagDemo.js`. Pre-check size, PDF type and the 3-file limit in the browser so most refusals need no round trip; the server stays the authority. Countdown updates once a minute and refreshes the list when a file expires.
- Build steps: add ID helper; add header to all calls; show limits and warning; show countdown; map 400/413/429 to friendly messages; update first-run copy.
- Checks: manual or visual (screenshots at 1440 and 390, backend mocked by request interception): first run shows the warning and limits; 3 files with countdowns; a 429 shows the retry message; an expired file disappears. Plain check: lint and build pass. Pass: all visible as described.
- Done when: the demo works end to end against a local backend with the stubbed model and shows limits, warning and countdowns.
- If it goes wrong: if the ID cannot be stored, the visitor still works for the page session.

### 3.2 Front end: server waking-up message
- Status: done (1 screenshot round)
- Does: if the server has not answered within 4 seconds of loading the demo, show "The demo server is waking up, this can take up to a minute." and keep retrying quietly; hide the message once it answers. Also ping the server's `/health` endpoint when the landing page loads (never `/documents`, which now needs a visitor ID) so it is warm by the time the visitor clicks "Try the Demo".
- Does not: no uptime pinger service.
- Needs: 3.1
- Inputs and outputs: uses only `GET /health`; no new backend work. Timings: show the waking message after 4 seconds without an answer, retry every 5 seconds, and after 90 seconds show the plain error with a "Try again" action.
- Design: the demo already has a "server may be waking" hint; extend it to retries and to the landing warm-up. Warm-up failures are silent.
- Build steps: add warm-up call on the landing page; add timed message and retry in the demo.
- Checks: manual: simulate a slow response (delay interception 6 s) and see the message appear then clear; a failed warm-up shows nothing. Pass: as described; lint and build pass.
- Done when: a slow server produces the waking message and recovers automatically.
- If it goes wrong: after 90 seconds of failures show the existing plain error with a "Try again" action.

### 3.3 Front end: honest landing and demo copy
- Status: done (1 screenshot round)
- Does: landing and demo copy match the final design: no sample documents; uploads private and removed after 30 minutes; limits stated; and a clear line that the real product keeps a persistent, personalised knowledge base ("This is a demo. Tessel as a product would keep your knowledge base, built from your own documents.") Keep the landing scenes and animation as they are.
- Does not: no new scenes, no claims about features that do not exist (no accounts, no sync), no promises the app cannot keep.
- Needs: 3.1
- Inputs and outputs: copy edits in `landing/Landing.jsx` and `demo/*` only.
- Design: privacy scene says uploads are private to the visitor's browser, are processed by an AI service to build the search index and answers, and are deleted after 30 minutes. Remove "demo shares one document store" wording (no longer true). Keep wording plain English.
- Build steps: edit copy; read every sentence against what the app does.
- Checks: manual: read the landing page and demo top to bottom; every claim is true of the built app. Pass: no claim that is false or unsupported; lint and build pass.
- Done when: all copy matches the real behaviour.
- If it goes wrong: n/a

### 3.4 Share preview, favicon, dev port, unused files
- Status: done
- Does: LinkedIn and other link previews show a title, description and a 1200x630 image; a PNG favicon exists beside the SVG; the dev server is fixed to port 5173; unused template files are removed.
- Does not: no custom domain work.
- Needs: nothing
- Inputs and outputs: `og:title`, `og:description`, `og:image` (absolute URL on the live front-end domain), `og:url`, `og:type`, `twitter:card=summary_large_image` in `frontend/index.html`. Image file in `frontend/public/` made from the landing page (screenshot with a clean crop, plus the product name and tagline), under 300 KB.
- Design: the Vite config sets `server.port: 5173` with `strictPort: true`. Remove `src/assets/hero.png`, `react.svg`, `vite.svg` and `public/icons.svg` only after confirming nothing references them.
- Build steps: capture the image with Playwright; add tags; add favicon PNG; set the port; delete unused files; build.
- Checks: plain: build passes and `dist/` contains the image and tags (`grep`); dev server fails loudly if 5173 is busy; no references to deleted files. Manual: open the image and look at it (readable text, correct crop). Pass: all as described. Note for the final report: validate the link with LinkedIn's Post Inspector after deploy (the agent cannot).
- Done when: the tags and image exist, the build is clean and the port is fixed.
- If it goes wrong: if the screenshot looks poor, build the image as a simple designed graphic (black background, logo, tagline).
