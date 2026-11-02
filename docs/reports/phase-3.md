# Phase 3 report — liveness and anti-spoofing

**Dates:** 17–20 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Decision record:** [ADR-0007](../adr/0007-layered-liveness.md) · **Status:** 🟡 built, tested locally and red-teamed by the owner. Every attack the owner tried is now blocked and genuine attempts pass, but on **one person, one camera, one room**: the exit criteria need broader measurement before they can be called met.

**Goal (from the roadmap):** fuse independent liveness layers so that a photo, a replayed video or an injected feed can't pass the age check. **Exit:** every red-team case is blocked; the genuine-attempt false-reject rate is measured and documented.

## What is built

| Layer / area | Delivered | Decides? |
| :-- | :-- | :-- |
| L1 quality | Unchanged gate; now counts **people**, not detections: a second detection counts only if confident and outside the main face's box and ≥ ½ its size — ≥ ¼ in the picture's middle — or larger than the main face at any score (`dwarpal_vision.quality.people`) | yes |
| **L2 passive PAD** | **MiniFASNet** V2 (crop 2.7×) + V1SE (crop 4×), Apache-2.0, pinned at commit `b6d5f04`; PyTorch weights read with `weights_only`, rebuilt from their shapes (strict load), converted to ONNX by `python -m dwarpal_ml.antispoof` (parity 5.5 × 10⁻⁷); run by OpenCV; median "real-face" chance per attempt | **yes**: < 0.5 → step up |
| L3 pose challenge | Server-issued, 3–4 poses, ≤ 1 look-up (24 orders); measured against the person's own frontal angles by MediaPipe's **478-point face mesh**, run by OpenCV from the pinned bundle (five-point fallback); turns decide (shift ≥ 0.18); look-up and "caught mid-turn" recorded | turns: yes (retry, then reject) |
| L4 screen light | Colours on a fixed timetable; photos copied instantly, encoded after the challenge; chromaticity correlation of skin vs. emitted colour | recorded only |
| L5 injection | Automation, virtual camera, hidden page, identical frames; **hand beside the face** (MediaPipe palm detector) | hand sign recorded only; others step up |
| Screen pattern | Fine-detail spectrum peak in the face (moiré / pixel grid) | recorded only |
| Attempt budgets | Per session (Phase 1) + **per device** (30 challenges/hour, the page's random device ID, not a fingerprint) and **per network address** (120/hour), per project, in Valkey; `429 too_many_attempts` | yes |
| Verify page | MediaPipe guidance; live pose meter; 2 held photos + 1 on the way into each pose; calm mode for reduced motion | — |
| Operations | `liveness-report --since …`: outcomes, false-reject rate, pose reach, measurement used, injection signs, presentation (real-face chance, screen pattern, mid-turn), light | — |
| Supply chain | `models/third_party.json`: MediaPipe face landmarker (now `use: serving`), MediaPipe hand landmarker (7,819,105 B), two MiniFASNet weight files (`use: training`); all SHA-256-pinned, MD5 checked against Google's where published | — |
| Book | §2.18 updated; §5.3 extended to §5.3.7 (the red team); 7 new walkthroughs; every changed file re-explained; strict build 160 files, 10,176/10,176 lines | — |

## What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (80 files) |
| Python tests | **173 passed**, in two processes (112 + 61 ML) (incl. mesh, hands, anti-spoofing, screen pattern, people rule, device budgets, converter) |
| JS lint, typecheck, unit tests | clean; **30 passed** (web 16, SDK 11, shop 3) |
| End-to-end | **4 passed**; the main story (colours, 3–4 poses, pass, leave the cellar) ~42 s |
| Book | strict: **160 files, 10,199/10,199 lines** |

### Genuine attempts (the owner, laptop webcam)

| Rounds | Design | Passed | Key numbers |
| :-- | :-- | :-- | :-- |
| 1–6 (17 Oct) | absolute limits → own-frontal shifts → meter → people rule → turns decide | 0/11 → 8/12 → (final rule) | turns 0.23–0.69 (five points); look-up unmeasurable |
| A–B (19 Oct) | face mesh; colours shown | 6/6 | mesh turns 0.42–0.70, look-up 0.11–0.38 |
| PAD rounds (20 Oct) | MiniFASNet decides | 5/6 (1 stepped up by light, since demoted) | real-face chance **0.944–0.995** |

### Red team (the owner attacking their own system)

| Attack | Before L2 | With L2 (MiniFASNet) | Measures |
| :-- | :-- | :-- | :-- |
| Phone showing posed selfies (front / left / right / chin up), swiped to match prompts | **5 of 10 attempts got into the cellar** | **0 of 3** | real-face chance 0.02–0.12 |
| Same, peeking from behind the phone | — | caught as a second face | peeking face larger than the phone face, at the edge |
| Phone replaying a video of the owner turning, paused/skipped to match | — | **0 of 4** | real-face chance 0.006–0.195 |
| Printed / still photo (API test) | blocked (no turn) | blocked | — |
| Wrong pose order; claimed challenge; reused challenge; automation; virtual camera (API tests) | blocked | blocked | — |

Secondary measures, recorded only: screen pattern real 0.99–1.14 vs. phone 1.16–1.31; poses caught mid-turn real 19/19 vs. attacks 5/23; light real −0.25–0.99 vs. phone −0.64–0.85 (no usable separation).

## Findings

- **A photo of a turned head is a turned head.** The pose challenge alone can't stop a carousel of posed selfies (5 of 10 got in). Passive PAD is the layer that separates real from presented faces, by a wide margin (0.94 vs. ≤ 0.2).
- **The screen-light signal is too variable to decide**: genuine faces measured −0.25 to 0.99 depending on room light; deciding on it stepped up 3 genuine attempts.
- **Two page bugs hid the light signal**: dark-coloured photos were set aside by quality flags, and JPEG encoding (~1 s on a busy laptop) shifted photos out of their colours. Fixed (liveness uses every one-person photo; photos copied instantly, encoded after).
- **Five landmarks can't measure looking up** (−0.03 to 0.12); the face mesh can (0.11–0.38). Look-up stays record-only by the owner's decision.
- **The hand detector didn't work**: it missed every hand holding a phone and raised one false alarm. Recorded only.
- **Detectors see faces where people don't** (a face-like object in the owner's room), and an attacker's own face can show behind a held phone. The people rule handles both cases seen.
- **OpenCV 5 quirks**: its new DNN engine returns only a model's last output, and the classic engine is honoured only when loading from a file.
- **One intermittent crash**: in 1 of 5 full local test runs, Python crashed (access violation) while importing `timm` during test collection — a native-library fault, not a failing test; 4 runs and 3 direct pytest runs passed. To watch in CI.

## Open items

1. **Broader measurement (exit criterion).** More people (ages, skin tones, glasses), cameras, rooms and attack media: the false-reject rate and the PAD margin come from one person. MiniFASNet's fairness across groups is unmeasured (§2.16).
2. **Untested attacks:** a virtual camera feeding images directly (no screen in the picture), real-time deepfakes, masks.
3. **Recorded-only signals** (light, screen pattern, mid-turn, hands, look-up) could become deciding once broader data supports limits.
4. ~~The anti-spoofing ONNX files~~ — **resolved 24 Oct**: a live session is never decided without the anti-spoofing verdict (`liveness_unavailable`), and the inference service's `/readyz` reports `antispoof: loaded | missing`. Publishing the ONNX files through the model registry, so production doesn't need PyTorch to make them, remains a nice-to-have.
5. ~~The intermittent test-collection crash~~ — **mitigated 24 Oct**: `tasks.py test` runs the ML tests (PyTorch) in a separate process from the services and libraries (OpenCV, ONNX Runtime). 112 + 61 tests pass.
6. ~~Remote CI~~ — **done**: CI green on GitHub since 2 Nov (`03f3f5b`).
