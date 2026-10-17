# Phase 3 report — liveness and anti-spoofing

**Dates:** 17 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Decision record:** [ADR-0007](../adr/0007-layered-liveness.md) · **Status:** 🟡 built and tested locally; the exit criteria are **not yet met** (genuine false-reject rate unmeasured, PAD slot empty, moving-media red-team cases open). Not yet committed.

**Goal (from the roadmap):** fuse independent liveness layers so that a photo, a replayed video or an injected feed can't pass the age check. **Exit:** every red-team case is blocked; the genuine-attempt false-reject rate is measured and documented.

## What is built

| Area | Delivered |
| :-- | :-- |
| Contracts | `Pose`, `POSES`, `Phase`, `Colour`; `FrameMeta.phase`; `Challenge` (1–4 poses, 2–8 colours, 400–2000 ms steps); `ClientSignals` (automation, virtual camera, hidden ms, light shown); `FaceRequestMeta.light_started_ms / signals / challenge`; `FrameReport.pitch_ratio`; `PoseCheck`, `LightCheck`, `Liveness` (with `evidence: images \| labels`) on `FaceAnalysis` |
| Challenge (L3/L4) | `domain/challenges.py`: 3 poses from turn_left / turn_right / look_up, never repeating the previous step (12 orders); 4 colours from a 5-colour calm palette (no saturated red), 600 ms each (< 2 changes/s, WCAG 2.3.1); drawn with `secrets.SystemRandom`; stored once in Valkey, destroyed on use, session budget unchanged. The API replaces any challenge the browser sends with the stored one |
| Verify page | MediaPipe Face Landmarker 1.1.0 (Apache-2.0), self-hosted from `public/mediapipe/` (copied by `scripts/mediapipe.mjs`; CSP gains only `'wasm-unsafe-eval'`); GPU → CPU → none fallback. Live guidance (no face / several / too far / off-centre / turned), advisory only: Start unlocks after 8 s regardless. Challenge runner: full-screen colour layer on a fixed clock timetable (portal to `<body>`), one baseline photo per colour; per-pose cue, photo after 3 steady readings or 5 s; calm mode for `prefers-reduced-motion` (4 plain baseline photos, no colours). Signals: `navigator.webdriver`, virtual-camera label match, hidden time |
| Evidence (inference) | `liveness.py`: **pose check** (timing order, ≥ 3 frontal baseline frames first, poses in the challenge's order, each shown: yaw ≥ 0.35 / ≤ −0.35, pitch ≤ 0.38); **light check** (red/blue chromaticity of cheeks + forehead vs. background corners vs. emitted colour, Pearson r; recorded only); **injection signs** (automation, virtual_camera, page_hidden, identical_frames < 0.75 grey levels). Vision library gains `pitch_ratio` |
| Decision | Liveness after quality, before age. No liveness / no pose check / labels evidence in a live session → retry `liveness_unavailable`; pose failed → retry, then **reject** on the second failure in the session; injection signs → **step up** `liveness_uncertain`. Outward reasons never name the check (rejections show only `verification_failed`); full detail stored in the attempt's scores |
| Test mode | `DWARPAL_INFERENCE_LIVENESS=labels`: pose check believes the photo labels (needed because the e2e fake camera plays a still portrait). Three locks: refused at start-up unless the stub age model is used; every result carries `evidence`; the API refuses labels evidence in live sessions |
| Operations | `python -m dwarpal_api.cli liveness-report --since …`: outcomes, pose pass rate and false-reject rate (if all genuine), pose problems, injection signs, light correlations (median, range) |
| Supply chain | `models/third_party.json`: MediaPipe face landmarker pinned (SHA-256 `64184e22…`, 3,758,596 bytes, MD5 matched Google's published hash); `use: "web"`, fetched by default. `.gitignore` ignores `*.task` and `apps/web/public/mediapipe/` |
| Book | Part 2 §2.18 (liveness and anti-spoofing) in full; §5.3 (Phase 3) with 7 new walkthroughs; 28 changed walkthroughs reviewed (camera screen and camera code rewritten in full) |

## What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (75 files) |
| Python tests | **154 passed**: 12 new liveness unit tests; 4 new red-team API tests; 7 new domain tests (liveness decisions, live-mode refusal of labels, challenge randomness over 500 draws covering all 12 orders, liveness report) |
| JS lint, typecheck, unit tests | clean; **26 passed** (web 12, including 6 new for `challenge.ts`) |
| End-to-end | **4 passed**; the full journey (colours, 3 pose prompts each waiting out 5 s, pass) takes 40.4 s |
| Book | strict build: **153 files, 9,163/9,163 lines** explained |

### Red-team results (through the real API)

| Attack | Expected | Result |
| :-- | :-- | :-- |
| Printed photo (still portrait, measured from images) | blocked | ✅ retry → **reject** (`verification_failed`) |
| Poses labelled in the wrong order | blocked | ✅ retry `liveness_check_failed` |
| Browser claims an easier challenge | ignored | ✅ judged against the issued challenge → fails |
| Challenge reuse (payload replay) | refused | ✅ `409 challenge_invalid` (since Phase 1) |
| Automation flag; virtual camera | step up | ✅ `liveness_uncertain` |
| Screen replay of a turning head; game-render video | blocked | ⬜ **not tested** — no way yet to produce convincing moving media (see findings) |

## Findings

- **Synthetic head turns don't fool YuNet.** 2-D and simple 3-D warps of the test portrait never pushed the detector's yaw ratio above 0.16 (a turn needs 0.35). Good for security, but it means the moving-media red-team cases need real recordings, and the e2e test needs the labels mode.
- **The light layer lit only the card** at first: the card's `backdrop-filter` makes it the containing block for `position: fixed`. Fixed by rendering the layer into `<body>` with a portal.
- **Biome rejects CRLF JSON** written by Python on Windows; the exporter now writes manifests with `\n`, and Biome skips registry manifests (it would rewrite `8.3e-07` as `8.3e-7`).
- **The downloaded `.task` model wasn't ignored** by Git (only `.onnx`, `.pt`, `.pth`, `.safetensors` were, the last twice); fixed.
- **An unused helper** (`colourAt`, the page-side colour lookup) was removed while writing the book: the page keeps its own timetable and the server does the lookup.
- **Every liveness threshold is provisional**: the page uses slightly stricter limits than the server (turn 0.4 vs 0.35; raised 0.35 vs 0.38) so a photo the page accepts also passes on the server. Both sets must be set from genuine attempts.

## Open items

1. **Genuine-attempt measurement (exit criterion).** With the owner: run the stack with `DWARPAL_INFERENCE_LIVENESS=images` and the stub age model, make N real attempts in different rooms and light through the demo shop (test key), then `liveness-report --since …`. Nothing but numbers is stored. Use the results to set the pose limits and decide whether the light signal can carry weight.
2. **Moving-media red team.** Optionally, with consent, recordings *of the owner*: a phone showing a photo, and a phone replaying a video of a head turn, played to the camera (or fed via Chromium's fake-camera file). These would close the screen-replay row.
3. **Passive PAD (L2).** The MiniFASNet weights were not approved; the slot is empty. Alternatives need a licence check before any download.
4. **Light-signal weight.** Recorded only. Needs genuine and replay measurements before it may affect a decision.
5. **Per-device attempt budgets** (roadmap) are not built; only the per-session challenge budget and the reject-after-two-failures rule exist.
6. **Remote CI** has not run Phase 3 yet (it runs on the next push).
