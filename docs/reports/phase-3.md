# Phase 3 report — liveness and anti-spoofing

**Dates:** 17 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Decision record:** [ADR-0007](../adr/0007-layered-liveness.md) · **Status:** 🟡 built, tested locally, and measured on one genuine user. The exit criteria are **not fully met**: the false-reject rate comes from one person and the final rule wasn't re-tested live, the PAD slot is empty, and the moving-media red-team cases are open.

**Goal (from the roadmap):** fuse independent liveness layers so that a photo, a replayed video or an injected feed can't pass the age check. **Exit:** every red-team case is blocked; the genuine-attempt false-reject rate is measured and documented.

## What is built

| Area | Delivered |
| :-- | :-- |
| Contracts | `Pose`, `POSES`, `Phase`, `Colour`; `FrameMeta.phase`; `Challenge` (1–4 poses, 2–8 colours, 400–2000 ms steps); `ClientSignals` (automation, virtual camera, hidden ms, light shown); `FaceRequestMeta.light_started_ms / signals / challenge`; `FrameReport.pitch_ratio`; `PoseCheck` (with `baseline_yaw`, `baseline_pitch`, `reached`), `LightCheck`, `Liveness` (with `evidence: images \| labels`) on `FaceAnalysis` |
| Challenge (L3/L4) | `domain/challenges.py`: **3 or 4 poses** from turn_left / turn_right / look_up, never repeating the previous step, **at most one look-up** (24 orders; every challenge has ≥ 2 turns); 4 colours from a 5-colour calm palette (no saturated red), 600 ms each (< 2 changes/s, WCAG 2.3.1); drawn with `secrets.SystemRandom`; stored once in Valkey, destroyed on use. The API replaces any challenge the browser sends with the stored one |
| Verify page | MediaPipe Face Landmarker 1.1.0 (Apache-2.0), self-hosted from `public/mediapipe/` (copied by `scripts/mediapipe.mjs`; CSP gains only `'wasm-unsafe-eval'`); GPU → CPU → none fallback. Live guidance, advisory only: Start unlocks after 8 s regardless. Challenge runner: full-screen colour layer on a fixed clock timetable (portal to `<body>`), one baseline photo per colour; per-pose cue ("…, eyes on the screen") with a **live meter** measured from the person's own frontal angles (targets: turn 0.25, chin 0.12); **3 photos per pose** once held for 3 readings, or after 6 s; calm mode for `prefers-reduced-motion`. Signals: `navigator.webdriver`, virtual-camera label match, hidden time |
| Evidence (inference) | `liveness.py`: **pose check** — timing order, ≥ 3 frontal baseline frames first, poses in the challenge's order; each pose measured as a **shift from the person's own frontal angles** (median of baseline frames); **turns decide** (shift ≥ 0.18), **look-up is recorded only** (limit 0.03, never fails the check); the furthest shift per pose is recorded. **Light check** (red/blue chromaticity, Pearson r; recorded only). **Injection signs** (automation, virtual_camera, page_hidden, identical_frames). Vision library: `pitch_ratio`; `people()` counts a second detection only if confident (≥ 0.8), outside the main face's box and ≥ half its size |
| Decision | Liveness after quality, before age. No liveness / no pose check / labels evidence in a live session → retry `liveness_unavailable`; pose failed → retry, then **reject** on the second failure in the session; injection signs → **step up** `liveness_uncertain`. Outward reasons never name the check; full detail stored in the attempt's scores |
| Test mode | `DWARPAL_INFERENCE_LIVENESS=labels` for the e2e fake camera. Three locks: refused at start-up unless the stub age model is used; every result carries `evidence`; the API refuses labels evidence in live sessions |
| Operations | `liveness-report --since …`: outcomes, pose pass rate and false-reject rate (if all genuine), pose problems, **pose reach from frontal (median / lowest per pose)**, injection signs, light correlations. Demo shop: **Leave the cellar** button (forgets the pass, for repeated testing) |
| Supply chain | `models/third_party.json`: MediaPipe face landmarker pinned (SHA-256 `64184e22…`, 3,758,596 bytes); `.gitignore` ignores `*.task` and `apps/web/public/mediapipe/` |
| Book | Part 2 §2.18 in full; §5.3 with 7 new walkthroughs and the measurement story (§5.3.6); every changed walkthrough reviewed |

## What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (75 files) |
| Python tests | **157 passed** (liveness unit tests 14, red-team API tests 4, liveness domain tests 7, second-person rule 1) |
| JS lint, typecheck, unit tests | clean; **28 passed** (web 14, SDK 11, shop 3) |
| End-to-end | **4 passed**; the full journey — colours, 3–4 pose prompts each waiting out 6 s, pass, leave the cellar — takes about a minute |
| Book | strict build: **153 files, 9,361/9,361 lines** explained |

### Genuine attempts (the owner: one adult, one room, laptop webcam)

| Round | Change | Passed | What the numbers showed |
| :-- | :-- | :-- | :-- |
| 1 | Absolute limits (yaw 0.35, pitch 0.38) | **0 / 11** | Turns ~0.25–0.35; "tilt your head up a little" never reached 0.38 |
| 2 | Shifts from own frontal angles (turn 0.18, look-up 0.06); reach recorded | 1 / 6 | Turns 0.16–0.28; look-up ~0 — one photo per pose, taken at the wrong moment |
| 3 | Page meter + 3 photos per pose | 0 / 6 measurable | A steady face-like shape (score ~0.85, eye distance 13 px vs. 100) in every photo → "two faces" |
| 4 | Count people, not detections | **8 / 12** | Turns 0.23–0.66 every time; all 4 failures were look-up |
| 5 | 3–4 poses, ≤ 1 look-up, look-up limit 0.03 | 5 / 8 | Turns **22 / 22** (lowest 0.29); look-up failed 3 / 8 (−0.03 to 0.02) |
| 6 | Look-up recorded only; turns decide | not re-tested live | On round 5's recorded numbers: **8 / 8** |

Injection signs: none in any genuine attempt. Light: not measurable in any attempt (most likely the device reports reduced motion, so no colours were shown).

### Red-team results (through the real API)

| Attack | Expected | Result |
| :-- | :-- | :-- |
| Printed photo (still portrait, measured from images) | blocked | ✅ retry → **reject** (`verification_failed`) — fails every turn |
| Poses labelled in the wrong order | blocked | ✅ retry `liveness_check_failed` |
| Browser claims an easier challenge | ignored | ✅ judged against the issued challenge → fails |
| Challenge reuse (payload replay) | refused | ✅ `409 challenge_invalid` (since Phase 1) |
| Automation flag; virtual camera | step up | ✅ `liveness_uncertain` |
| Screen replay of a turning head; game-render video | blocked | ⬜ **not tested** — no way yet to produce convincing moving media |

## Findings

- **Absolute pose limits fail real people.** Camera height, face shape and how far people are willing to turn vary; measuring each pose against the person's own frontal angles fixed most of it.
- **Feedback matters more than limits.** Without a meter, people stopped short or the single photo caught the wrong moment. With a meter and three photos per pose, every genuine turn cleared the limit with room to spare.
- **Five landmarks can't measure looking up.** Even with a full meter on the page, YuNet's pitch moved −0.03 to 0.12. Look-up stays in the challenge (it makes the order harder to predict, and is recorded) but no longer decides; turns carry the proof — a flat photo can't turn, and synthetic warps never exceeded a yaw of 0.16.
- **Detectors see faces where people don't.** A small object in the owner's room scored 0.85 as a face in every photo and failed every attempt as "multiple faces". A second detection now counts only if it is confident, outside the main face and at least half its size.
- **The demo shop's pass hid retests.** Its 30-minute pass let the tester straight back in, so later "attempts" never reached the server; the shop gained a Leave the cellar button.
- **The light layer lit only the card** at first (the card's `backdrop-filter` makes it the containing block for `position: fixed`); fixed with a portal to `<body>`.
- **The downloaded `.task` model wasn't ignored** by Git; fixed. An unused helper (`colourAt`) was removed while writing the book.

## Open items

1. **Broader genuine measurement.** More people, cameras, rooms and lighting; re-test the final rule (round 6) live; record the false-reject rate per condition.
2. **Look-up measurement.** A denser landmark model on the server (for example MediaPipe's, already pinned for the page) could make look-up a deciding pose again. It needs a new server dependency (the owner's approval for the download).
3. **Moving-media red team.** Optionally, with consent, recordings *of the owner*: a phone showing a photo, and a phone replaying a video of a head turn.
4. **Passive PAD (L2).** The MiniFASNet weights were not approved; the slot is empty.
5. **Light signal.** Recorded only, and not measured in any genuine attempt yet; needs attempts with colours shown, and replays, before it may affect a decision.
6. **Per-device attempt budgets** (roadmap) are not built; only the per-session challenge budget and the reject-after-two-failures rule exist.
7. **Remote CI** has not run Phase 3 yet (it runs on the next push).
