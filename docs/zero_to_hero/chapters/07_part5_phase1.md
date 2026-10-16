## 5.1 Phase 1 — the walking skeleton

Phase 1 builds the "skateboard" of §3.9: a thin version of the **whole** system, working end to end before any part is made fancy.

1. A shop creates a verification session.
2. The visitor's camera captures a few frames.
3. The API asks the inference service to analyse them.
4. The decision engine decides.
5. A signed token goes back to the shop, which checks the seal.

Only the age model is a stand-in. Everything around it is real.

Phase 1 is built in this order, and this chapter grows in the same order:

| Step | What | Section |
| :-: | :-- | :-- |
| 1 | The face side: shared contracts, the vision library, the inference service | §5.1.1 ✅ |
| 2 | The API core: database, identifiers, signed tokens, the decision engine | §5.1.2 ✅ |
| 3 | The API's endpoints: sessions and the capture flow | §5.1.3 ✅ |
| 4 | The front end: the Node SDK, the verify page, the demo shop | §5.1.4 ✅ |
| 5 | The end-to-end test with a fake camera | §5.1.5 ✅ |

### 5.1.1 The face side — contracts, vision and inference

**The journey of one burst of frames through the code built in this step:**

```
browser ──(JPEG frames + meta)──► API ──(same frames)──► inference service  /internal/v1/analyze/face
                                                            │  main.py: limits, multipart parsing, worker thread
                                                            ▼
                                                         pipeline.py, for each frame:
                                                            decode.py   header check, then decode
                                                            detect.py   YuNet: box, 5 landmarks, score
                                                            quality.py  light, sharpness, size, pose → flags
                                                            align.py    straighten + crop to 224×224
                                                         then for all good frames together:
                                                            backends.py age model → 101 probabilities each
                                                            pipeline.py weighted mixture → mean, spread, P(age ≥ N)
                                                            ▼
                                         ◄──── FaceAnalysis (face.py): numbers and flags only, never an image
```

The packages created as skeletons in Phase 0 gained real dependencies in this step. Their updated `pyproject.toml` and `__init__.py` walkthroughs are in §5.0.2, where those files first appear. CI also gained a step that downloads the model files (§5.0.6).

#### The shared contracts

!walk libs/contracts/src/dwarpal_contracts/face.py

#### The vision library

The four modules are walked through in the order a frame passes through them.

!walk libs/vision/src/dwarpal_vision/decode.py

!walk libs/vision/src/dwarpal_vision/detect.py

!walk libs/vision/src/dwarpal_vision/quality.py

!walk libs/vision/src/dwarpal_vision/align.py

!walk libs/vision/tests/test_vision.py

#### The model register and the fetch script

!walk models/third_party.json

!walk infra/scripts/fetch_models.py

#### The inference service

!walk services/inference/src/dwarpal_inference/settings.py

!walk services/inference/src/dwarpal_inference/backends.py

!walk services/inference/src/dwarpal_inference/pipeline.py

!walk services/inference/src/dwarpal_inference/main.py

!walk services/inference/tests/test_inference.py

!!! real "Real world — what this step measured"
    All 20 tests pass.

    **Speed.** The full face pipeline (decode, detect, check, align, estimate) was timed 20 times on this laptop's CPU (Intel i9-14900HX), using the 512 × 512 test portrait:

    - 3 frames: median **38 ms**;
    - 8 frames: median **103 ms** (slowest run 113 ms).

    That is far inside the 1.5-second budget (NFR-05). The stand-in age model costs almost nothing, so Phase 2 re-measures with the real model.

    **Typing.** The strict type checker found three places where OpenCV's own type descriptions were less precise than our code needed. Each was fixed with an explicit conversion, not by switching the checks off.

### 5.1.2 The API core — rules, memory and keys

The API is the system's brain. Websites talk to it, the verify page talks to it, and it is the only part that decides anything. This step builds everything the brain needs *except* its front doors: the rules, the database, the short-term memory, the signing keys, and the connection to the AI.

The code is organised in four **layers** — explained with the package's `__init__.py` in §5.0.2 — and this step builds the bottom two:

```
http/       problems · limits · deps · rp · flow · wellknown · health     §5.1.3
app/        verification — the steps of a check                           §5.1.3
adapters/   db · tables · migrations · store · signing · inference        this section
domain/     ids · keys · policy · decision · sessions                     this section
```

Each layer may only use the layers *below* it. The domain, at the bottom, uses nothing at all — no database, no network, no clock — which is why its rules can be tested exhaustively in seconds.

#### Settings and logs

!walk services/api/src/dwarpal_api/settings.py

!walk services/api/src/dwarpal_api/logs.py

!walk services/api/logging.json

#### The domain: the rules, as pure Python

The files are walked through from the simplest to the most important: identifiers, secrets, policies and their thresholds, then the decision engine and the life of a session.

!walk services/api/src/dwarpal_api/domain/__init__.py

!walk services/api/src/dwarpal_api/domain/ids.py

!walk services/api/src/dwarpal_api/domain/keys.py

!walk services/api/src/dwarpal_api/domain/policy.py

!walk models/registry/age/stub/manifest.json

!walk services/api/src/dwarpal_api/domain/decision.py

!walk services/api/src/dwarpal_api/domain/sessions.py

#### One kind of refusal

!walk services/api/src/dwarpal_api/errors.py

#### The adapters: the database

!walk services/api/src/dwarpal_api/adapters/__init__.py

!walk services/api/src/dwarpal_api/adapters/db.py

!walk services/api/src/dwarpal_api/adapters/tables.py

#### Migrations: building the tables

!walk services/api/src/dwarpal_api/migrations/env.py

!walk services/api/src/dwarpal_api/migrations/script.py.mako

!walk services/api/src/dwarpal_api/migrations/versions/v0001_initial.py

#### The adapters: Valkey, the signing keys and the AI

!walk services/api/src/dwarpal_api/adapters/store.py

!walk services/api/src/dwarpal_api/adapters/signing.py

!walk services/api/src/dwarpal_api/adapters/inference.py

#### Tests for the rules

!walk services/api/tests/test_domain.py

### 5.1.3 The API's endpoints — the journey of one check

This step adds the front doors. Here is one complete check, as the API sees it:

```
 website's server                     API                                  verify page (browser)
 ────────────────                     ───                                  ─────────────────────
 POST /v1/verification-sessions ───►  create_session
   (API key)                          ◄─── id, link …/v/vs_…#cs=secret
 sends the person to the link ───────────────────────────────────────────► opens the link
                                      start_flow  ◄─── POST …/start (client secret)
                                      ───► flow token, project name, minimum age
                                      issue_challenge  ◄─── POST …/challenge (flow token)
                                      submit_face_attempt ◄─ POST …/face-attempts (frames)
                                        → inference service → decide → record
                                      ───► pass / fail / step up / retry
                                      finish  ◄─── POST …/finish
                                      ───► back to the shop with ?session_id=vs_…
 GET /v1/verification-sessions/vs_… ► result_view + mint_token
   (API key)                          ◄─── outcome + signed age token
 checks the token's signature with the public keys from /.well-known/jwks.json
```

Notice what travels through the browser: only the session's ID and a one-time secret. The *answer* goes straight from the API to the website's server, which must use its own key to fetch it. A person can't fake a "pass" by editing a web address.

#### The use cases

!walk services/api/src/dwarpal_api/app/__init__.py

!walk services/api/src/dwarpal_api/app/verification.py

#### The HTTP layer

The shared machinery first — errors, size limits, credentials — then the endpoints.

!walk services/api/src/dwarpal_api/http/__init__.py

!walk services/api/src/dwarpal_api/http/problems.py

!walk services/api/src/dwarpal_api/http/limits.py

!walk services/api/src/dwarpal_api/http/deps.py

!walk services/api/src/dwarpal_api/http/rp.py

!walk services/api/src/dwarpal_api/http/flow.py

!walk services/api/src/dwarpal_api/http/wellknown.py

!walk services/api/src/dwarpal_api/http/health.py

#### Assembling and running the API

!walk services/api/src/dwarpal_api/main.py

!walk services/api/src/dwarpal_api/cli.py

!!! try "Try it yourself — run the API on your own computer"
    You need Docker running and the model files downloaded (`uv run infra/scripts/fetch_models.py`). Then, in four terminals from the project folder:

    1. `docker compose -f infra/compose/compose.yaml up -d --wait` — start PostgreSQL and Valkey;
    2. `uv run --package dwarpal-api python -m dwarpal_api.cli migrate`, then `uv run --package dwarpal-api python -m dwarpal_api.cli seed-dev` — create the tables and a test key (copy it);
    3. `uv run --package dwarpal-inference uvicorn dwarpal_inference.main:create_app --factory --port 8001` — the inference service;
    4. `uv run --package dwarpal-api uvicorn dwarpal_api.main:create_app --factory --port 8000 --log-config services/api/logging.json` — the API.

    Open `http://localhost:8000/docs` for FastAPI's automatic, clickable documentation, or `http://localhost:8000/.well-known/dwarpal-configuration` to see the discovery document. Each request you make prints one JSON log line in the API's terminal.

#### The integration tests

!walk services/api/tests/test_api.py

!!! real "Real world — what a careful review found"
    Before the walkthroughs above were written, every line of the API was read again, as a reviewer would. Writing an explanation for a beginner is a strict review in itself: a line that is hard to explain is often a line that is wrong. The review found five real problems, each now fixed and covered by a test:

    1. **A token that could be misread.** A token for a *failed* check said `"outcome": "fail"` — but also `"age_over": 18`. A website reading only the second claim would have let a child in. The claim is now `"age_over_18": false` (ADR-0020).
    2. **Unlimited challenges.** One session could ask for endless challenges, and so make the AI analyse endless pictures. Each session now gets twice its attempts.
    3. **No size limit on uploads.** The API would have read a body of any size before checking it. Bodies are now measured from their headers first (`limits.py`).
    4. **A dead end after reloading.** A person who reloaded the verify page after finishing got an error, with no way back to the shop. Finished sessions can now be reopened to see the result.
    5. **Unsafe production settings were possible.** Plain `http://` addresses are now refused in production, like the development master key.

    The same review moved the error documentation links from a web domain this project doesn't own to the API's own address, and fixed two bugs in the book builder itself (§X.6).

!!! real "Real world — what this step measured"
    **Tests.** The API has 42 tests: 30 fast ones for the rules (about 2 seconds) and 12 integration tests against real databases (about 10 seconds, most of it starting the containers). Every one passes, along with the strict linter and type checker across all 51 Python files.

    **Speed.** Thirty complete checks were timed through the real API, with PostgreSQL and Valkey in Docker on this laptop (median, then the slowest 10 %):

    | Request | Median | 90th percentile |
    | :-- | --: | --: |
    | create a session | 11.9 ms | 13.2 ms |
    | start the flow | 10.3 ms | 11.3 ms |
    | get a challenge | 10.8 ms | 12.2 ms |
    | a face attempt with 4 frames, including the AI | 68.6 ms | 82.1 ms |
    | read the result and sign a token | 13.6 ms | 14.4 ms |

    Where does the time go? Mostly into **round trips** to the databases. A typical request makes eight to ten of them — borrowing a connection, starting and ending transactions, the queries themselves — and on this laptop, through Docker Desktop's virtual network, one PostgreSQL round trip takes about 1.2 ms (Valkey: 0.6 ms). That is a property of the development machine, not of the code: on a Linux server, the same round trips are usually several times faster. Either way, the whole journey stays far inside the 1.5-second budget for an answer (NFR-05).

### 5.1.4 The front end — the SDK, the verify page and the demo shop

This step builds the three things people and websites actually touch:

```
 Amber Cellars (demo shop, port 3100)          Dwarpal verify page (port 3000)            Dwarpal API (port 8000)
 ───────────────────────────────────           ───────────────────────────────            ───────────────────────
 "Verify my age" ─ server action ─ SDK ──────────────────────────────────────────────────► create session
   remembers the session in a cookie ◄──────────────────────────────────────────────────── link with #cs=secret
 redirect ───────────────────────────────────► reads the secret, wipes it from the address
                                               start ─────────────────────────────────────► flow token
                                               camera: 5 photos ── challenge + upload ────► decide
                                               "You're all set" ── finish ────────────────► return address
 /age-check/complete ◄─────────────────────── redirect with ?session_id=
   checks the cookie · SDK: result + token ──────────────────────────────────────────────► result + signed token
   SDK: verify signature (JWKS) · age_over_18 === true
   signed pass cookie ─► /cellar
```

Three parts, in the order they are walked through:

- **`@dwarpal/node`**, the SDK — what every website needs: create sessions, read results, and above all *verify* tokens;
- **the verify page** — where a person takes the check;
- **the demo shop** — a pretend customer, built exactly the way a real one should be.

#### The SDK: `@dwarpal/node`

!walk packages/sdk-node/package.json

!walk packages/sdk-node/tsconfig.json

!walk packages/sdk-node/tsconfig.build.json

!walk packages/sdk-node/src/errors.ts

!walk packages/sdk-node/src/client.ts

!walk packages/sdk-node/src/token.ts

!walk packages/sdk-node/src/index.ts

!walk packages/sdk-node/test/client.test.ts

!walk packages/sdk-node/test/token.test.ts

#### The verify page: settings and look

!walk apps/web/package.json

!walk apps/web/tsconfig.json

!walk apps/web/postcss.config.mjs

!walk apps/web/next.config.ts

!walk apps/web/app/globals.css

!walk apps/web/app/layout.tsx

!walk apps/web/components/shell.tsx

!walk apps/web/app/page.tsx

#### The verify page: talking to the API, and to the camera

!walk apps/web/lib/flow-api.ts

!walk apps/web/lib/flow-api.test.ts

!walk apps/web/lib/camera.ts

!walk apps/web/lib/advice.ts

!walk apps/web/lib/advice.test.ts

#### The verify page: the screens

!walk apps/web/app/v/[sessionId]/page.tsx

!walk apps/web/app/v/[sessionId]/camera-view.tsx

!walk apps/web/app/v/[sessionId]/verify-flow.tsx

#### The demo shop: settings and secrets

!walk apps/demo-shop/package.json

!walk apps/demo-shop/tsconfig.json

!walk apps/demo-shop/postcss.config.mjs

!walk apps/demo-shop/next.config.ts

!walk apps/demo-shop/.env.example

!walk apps/demo-shop/lib/config.ts

!walk apps/demo-shop/lib/pass.ts

!walk apps/demo-shop/lib/pass.test.ts

#### The demo shop: the age check, from start to finish

!walk apps/demo-shop/app/actions.ts

!walk apps/demo-shop/app/age-check/complete/route.ts

#### The demo shop: its pages

!walk apps/demo-shop/app/globals.css

!walk apps/demo-shop/app/layout.tsx

!walk apps/demo-shop/components/ui.tsx

!walk apps/demo-shop/app/page.tsx

!walk apps/demo-shop/app/cellar/page.tsx

!walk apps/demo-shop/app/refused/page.tsx

!walk apps/demo-shop/app/error.tsx

!!! real "Real world — what building the front end taught us"
    - **TypeScript 7 and Next.js.** The plan kept TypeScript 6 in reserve, in case the brand-new TypeScript 7 didn't work with Next.js. It did — including Next.js's own type-checking step — so no fallback was needed. Testing a risky choice early, on real code, beats guessing.
    - **A cooldown for new releases.** Brand-new package versions are where supply-chain attacks and bugs show up first, so the workspace now refuses any version less than seven days old (`pnpm-workspace.yaml`). Its first check caught a tool pinned in Phase 0 only two days after release.
    - **A return link that worked anywhere.** A review of the shop found that its return link worked in *any* browser: an adult could pass a check and send the link to a child. The shop now remembers which check each browser started (`actions.ts`), and an end-to-end test proves that a link opened elsewhere is refused.
    - **A placeholder that would have worked.** The first example settings file had a long placeholder secret — long enough to be accepted. Placeholders are now chosen so they fail loudly instead (`.env.example`).

### 5.1.5 The end-to-end test — a real browser, a fake camera

The last step proves that everything built in Phase 1 works *together*, the way a person would use it: a real Chromium browser, driven by **Playwright** (§4.20), with the test portrait playing as its webcam.

#### The fake camera

!walk infra/scripts/make_fake_camera.py

#### The test

!walk e2e/package.json

!walk e2e/tsconfig.json

!walk e2e/playwright.config.ts

!walk e2e/tests/age-check.spec.ts

!!! try "Try it yourself"
    With Docker running and the models downloaded (`uv run infra/scripts/fetch_models.py`), install the browser once — `pnpm --filter @dwarpal/e2e exec playwright install chromium` — then run:

    `pnpm e2e`

    Turborepo builds the SDK and both apps; Playwright starts the databases and all four services, and acts out the four stories. Afterwards, the screenshots of the main story are in `e2e/test-results/`. (If `uv` isn't on your `PATH`, set the `UV` variable to its full path first.)

!!! real "Real world — what this step measured"
    All four end-to-end stories pass, in about **15 seconds** in total on this laptop — most of it starting the services. The main story, from the shop's button to the cellar, takes about **4 seconds**, including starting the camera, the 0.6-second burst, the analysis, and both redirects.

    Around it: 20 JavaScript unit tests (11 for the SDK, 6 for the verify page, 3 for the shop), and a clean lint, type check and production build of every package. The screenshots of every screen were also checked by eye: tests prove that the right things happen, but only a person can judge whether they look right.

The walking skeleton is complete: every layer of the system exists, connected end to end, with a stand-in where the real age model will go. Phase 2 replaces that stand-in with a trained, calibrated model.
