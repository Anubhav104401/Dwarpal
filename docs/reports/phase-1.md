# Phase 1 report — Walking skeleton

**Dates:** 15–16 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** ✅ complete; CI green on GitHub since 2 Nov (`03f3f5b`)

**Goal (from the roadmap):** demo shop → hosted flow → API → inference (stub) → decision → signed token → demo shop verifies it. **Met:** a Playwright test drives exactly that journey in Chromium with a fake camera, and passes.

## What was built

| Area | Delivered |
| :-- | :-- |
| Contracts | `dwarpal_contracts`: `FrameMeta`, `FaceRequestMeta`, `FrameReport`, `AgeEstimate`, `FaceAnalysis`; shared limits `MAX_FRAMES` (16) and `MAX_FRAME_BYTES` (512 KiB) |
| Vision library | `dwarpal_vision`: header-checked decoding (decompression-bomb guard), YuNet face detection, ArcFace-template alignment, quality gates with named flags |
| Inference service | FastAPI app: multipart parsing with limits, worker-thread pipeline with back-pressure (`503` + `Retry-After`), `StubAgeBackend` (101-bin age distribution), quality-weighted multi-frame mixture |
| API — domain | UUIDv7 IDs with Crockford prefixes; API keys and client secrets stored as digests; preset policies; model manifest; **decision engine** (fail-closed, retry hardening, property-tested); session state machine |
| API — adapters | SQLAlchemy 2 async tables; Alembic migration `0001`; Valkey flow tokens, one-time challenges and a per-session challenge budget; AES-256-GCM-sealed Ed25519 signing keys with an advisory-locked first-start; fail-safe inference client |
| API — HTTP | `POST/GET /v1/verification-sessions`; `/v1/flow/sessions/{id}/start · challenge · face-attempts · finish`; JWKS and discovery documents; `/livez`, `/readyz`; RFC 9457 problem details; request IDs; structured JSON request logs; header-level body limits (`411`/`413`) |
| Node SDK | `@dwarpal/node`: `DwarpalClient` (typed, validated answers) and `verifyAgeToken` (Ed25519-only, `typ`, `iss`, `aud`, `exp`, `sid`, exact `age_over_N`) |
| Verify page | `apps/web` (Next.js 16.4, React 19.3, Tailwind 4.3, TypeScript 7): secret read from the link's fragment and wiped from history; camera burst of 5 frames; retry tips; reload-safe; strict security headers |
| Demo shop | `apps/demo-shop` ("Amber Cellars"): server action + SDK to start a check; browser-bound return; token verified with JWKS; HMAC-signed pass cookie |
| End-to-end | `e2e/`: Playwright 1.64 with a fake camera made from the test portrait; starts databases, seeds a project, launches all four services; 4 stories |
| CI | JavaScript job now builds everything; new end-to-end job (uploads traces on failure) |
| Decisions | ADR-0019 (fully-specified `Ed25519` JWS algorithm, RFC 9864); ADR-0020 (boolean `age_over_N` claims) |
| Book | Part 4 §4.8–4.20; Part 5.1 (§5.1.1–5.1.5) with every new file walked through; builder improvements (below) |

## What was measured

| Check | Result |
| :-- | :-- |
| `uv run tasks.py check` | lint ✅ · format ✅ · mypy strict ✅ (52 files, tests included) · pytest ✅ **67 passed** · book strict ✅ |
| JavaScript | Biome ✅ (53 files) · `tsc` ✅ (7 packages) · Vitest ✅ **20 passed** · production builds ✅ |
| End to end | **4 passed in ~15 s**; the full shop-to-cellar journey takes ~4 s |
| Face pipeline (CPU, i9-14900HX) | median **38 ms** for 3 frames, **103 ms** for 8 frames |
| API through real databases (30 journeys) | create 11.9 ms · start 10.3 ms · challenge 10.8 ms · **face attempt (4 frames, with AI) 68.6 ms** · result + token 13.6 ms (medians); a PostgreSQL round trip costs ~1.2 ms through Docker Desktop on Windows |
| Book coverage | **123 files, 5,523/5,523 non-blank lines explained (100 %)**; 144,007 words |

## What changed from the plan, and why

1. **Layers instead of `modules/`.** Stage 3 §3.1 sketched feature folders; the API is organised as `domain` / `adapters` / `app` / `http`, which made the pure decision rules trivially testable.
2. **Token algorithm named `Ed25519`, not `EdDSA`** (ADR-0019): joserfc flagged `EdDSA` as deprecated by RFC 9864.
3. **The age claim became `age_over_18: true|false`** (ADR-0020): a review found that `"age_over": 18` next to `"outcome": "fail"` could be misread as a pass.
4. **A code review before the walkthroughs found and fixed seven more problems:** unlimited challenges per session (now a budget of 2 × attempts); no request-size limit (now enforced from headers); a dead end after reloading a finished check; plain-`http` addresses accepted in production; error-type links on a domain the project doesn't own (now relative `/errors/<code>`); in the shop, a return link that worked in any browser (now bound with a cookie, and tested end to end); and an example settings file whose placeholder secret would have been accepted (now empty, so the shop refuses to start).
5. **Logging lives in configuration** (`services/api/logging.json`) rather than in code, and uvicorn's own access log (client addresses, query strings) is switched off.
6. **A 7-day release cooldown** (`minimumReleaseAge`) now guards the JavaScript supply chain. It immediately rejected `turbo` 2.11.8 (pinned in Phase 0 two days after its release; now 2.11.7), and chose Next.js 16.4.0 over the day-old 16.4.2.
7. **TypeScript 7 confirmed.** The Phase 0 question is answered: Next.js 16.4 builds and type-checks with TypeScript 7.0.2, so the TypeScript 6 fallback wasn't needed.
8. **No separate `@dwarpal/js` package yet.** The hosted verify page talks to the flow API through its own small client (`apps/web/lib/flow-api.ts`). A browser SDK for embedding arrives with the front-end phase (Phase 5).
9. **No `ChallengeSpec` contract yet.** Challenges carry empty `poses` and `colours` lists; the typed contract arrives with liveness (Phase 3).
10. **The book builder grew up:** re-anchoring now follows difflib's edit operations (an in-place edit keeps every note in place); `--reanchor` moves the snapshot forward, so running it twice is safe (a real bug, found in use); and the strict check now fails if a walkthrough exists but no chapter shows it. 14 builder tests.

## Known limitations

- **The age model is a stand-in.** Its manifest says `calibrated: false`, so the API refuses **live** sessions; test sessions work. Phase 2 trains and calibrates the real model.
- **No liveness yet.** The `reject` outcome exists everywhere but nothing produces it until Phase 3.
- **The verify page's CSP allows inline scripts** (`'unsafe-inline'`), which Next.js needs without nonces. Nonce-based CSP is scheduled for Phase 7.
- **Rate limiting** is limited to the per-session challenge budget; per-key limits arrive in Phase 4.
- **A fresh token is minted on every result read**, and each is recorded in `issued_tokens`. Token introspection and one-time use arrive in Phase 4.
- **One active signing key**; automated rotation (ADR-0008: every 30 days) is not built yet.
- **CI has never run remotely**: the repository isn't on GitHub yet. Every command in the workflow passes locally.
- **uv is still not on `PATH`** on the development machine; the end-to-end test reads its location from the `UV` variable.
- **OpenCV 5.0 prints a harmless warning** at start-up ("Targets are not supported by the new graph engine") from inside its new DNN engine.
- **No licence chosen yet**; the SDK is marked `private` until the owner decides.
- Housekeeping: Docker Desktop's broken socket folder from the earlier crash was renamed, not deleted: `%LOCALAPPDATA%\Docker\run-stale-20261016-061906` can be removed.

## Next: Phase 2 — ML core

Datasets and their licences, training the distributional age model, evaluation by age band and group, risk-controlled thresholds (ADR-0006), and a calibrated manifest that lets live sessions run.
