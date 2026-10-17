## 5.3 Phase 3 — liveness and anti-spoofing

Phase 2 gave the system a real age model. But an age model only answers *how old does this face look?* — never *is this a living person, here, now?* Phase 3 adds that second question, with the layered design of ADR-0007 and the ideas of §2.18: a random challenge chosen by the server, evidence measured from the photos, and a decision that tells an attacker as little as possible.

| Layer (ADR-0007) | What | Status |
| :-- | :-- | :-- |
| L1 | Capture quality gate | ✅ since Phase 1 |
| L2 | Passive PAD (a model that spots paper and screens) | ⬜ slot empty: its weights are not approved |
| L3 | **Random head-pose challenge**, checked on the server from the photos | ✅ §5.3.1–5.3.3; turns decide, look-up is recorded (§5.3.6) |
| L4 | **Screen-light challenge** — colours reflected on the skin | ✅ measured and recorded; decides nothing yet |
| L5 | **Injection signs** — automation, virtual cameras, hidden page, frozen frames | ✅ §5.3.3 |
| — | Decision, vague outward reasons, attempt limits | ✅ §5.3.4 |

**The journey of one attempt, with liveness:**

```
verify page ── POST …/challenge ──► API: new_challenge() → random poses + colours, stored in Valkey (one use)
     │  ◄── { challenge_id, poses: [turn_right, look_up, turn_left, turn_right], colours: [4 × #rrggbb], step_ms: 600 }
     │
     │  MediaPipe guidance: "Move a little closer" … "That's good. Press Start"
     │  Start ► the screen glows in 4 colours, one baseline photo each   (none in calm mode)
     │        ► "Turn your head to your right, eyes on the screen"  [████████░░] … full: 3 photos (or after 6 s)
     │        ► "Lift your chin up, eyes on the screen" … ► "Turn your head to your left, …" … ► …
     │
     └─ POST …/face-attempts  (up to 16 labelled photos + timings + browser signals)
            │
            ▼
API: take_challenge() — the server's own copy replaces whatever the page claimed
            │
            ▼
inference service: quality, pitch and yaw per photo ─► liveness.py
            pose_check: frontal start? poses in order? each turn really shown, from the person's own frontal angles?
            light_check: did the cheeks follow the screen's colours?          (recorded only)
            injection_signs: automation, virtual camera, hidden page, frozen frames
            │
            ▼
API: decide() — quality, then liveness, then age
            pose failed      → retry "liveness_check_failed"; the second time → reject "verification_failed"
            injection signs  → step up "liveness_uncertain"
            otherwise        → the age decision of Phase 1–2
```

### 5.3.1 The challenge — chosen and kept by the server

Every attempt gets a fresh challenge: three or four head poses, never the same twice in a row and at most one look-up (24 possible orders), and four screen colours from a calm palette. It is drawn with the operating system's unpredictable random numbers, stored once, and destroyed when used. The page receives it so it can show the prompts — knowing the order a moment in advance doesn't help a prepared recording.

!walk services/api/src/dwarpal_api/domain/challenges.py

The rest of the server side changed in existing files, each explained in its own walkthrough: the contracts gained `Challenge`, `ClientSignals` and `Liveness` (`libs/contracts/src/dwarpal_contracts/face.py`); the store saves the challenge and hands it back (`adapters/store.py`); and `app/verification.py` puts the **server's** copy into the request before the inference service sees it.

### 5.3.2 The verify page plays it

The page does three things. **It guides**: MediaPipe's face landmarker, running inside the browser, turns what it sees into plain instructions before the check begins. **It plays the challenge**: the colours, on a fixed timetable so the server can tell which colour lit which photo, then each pose, with a **meter** that fills as the head turns, taking three photos once the head has held it for three readings — or after six seconds anyway. **It reports**: the browser's own signals, which can only make the check stricter.

The guidance never decides anything. After 8 seconds Start can be pressed regardless, and if MediaPipe can't run at all the page simply works without it: a person whose face the landmarker reads badly must never be locked out by the page.

!walk apps/web/lib/challenge.ts

!walk apps/web/lib/challenge.test.ts

!walk apps/web/lib/landmarker.ts

!walk apps/web/scripts/mediapipe.mjs

The camera code was rewritten around the challenge (`apps/web/lib/camera.ts`), and so was the camera screen (`apps/web/app/v/[sessionId]/camera-view.tsx`), with the full-screen colour layer, the guidance and the signals. Smaller changes: the flow client sends the labels and signals (`lib/flow-api.ts`), the page's security policy allows WebAssembly (`next.config.ts`), and `package.json` runs `mediapipe.mjs` before every start and build. The MediaPipe face model is pinned, like every other model, in `models/third_party.json`.

### 5.3.3 The evidence — measured from the photos

The inference service measures every photo: the sideways turn (**yaw**) it already measured, and now the up-down tilt (**pitch**, `libs/vision/src/dwarpal_vision/quality.py`). Each pose is judged against the person's **own** frontal angles, taken from their opening photos. The quality check also learned to count **people** rather than detections: a second box inside the same face, or a small face-like shape in the background, is no longer a second person (§5.3.6). From those numbers, the colours and the browser's signals, `liveness.py` gathers the three kinds of evidence. It decides nothing itself.

!walk services/inference/src/dwarpal_inference/liveness.py

!walk services/inference/tests/test_liveness.py

`pipeline.py` collects what was seen in each photo and runs the checks; `main.py` and `settings.py` add the labels test mode (§5.3.5).

### 5.3.4 The decision, and the red team

The decision engine (`services/api/src/dwarpal_api/domain/decision.py`) now checks liveness **after** quality and **before** age: a dark photo should be told to find light, not be counted as a liveness failure. A failed pose challenge gets one retry, then the session is rejected; signs of injection send even a clear adult to a stronger check. Outward reasons never say which check fired (the domain tests prove it). The detail is stored with the attempt, for the operator, and `liveness-report` summarises it (`cli.py`).

The **red-team tests** (`services/api/tests/test_api.py`) attack the running system through its real API:

| Attack | Result |
| :-- | :-- |
| A printed photo (the still test portrait, measured from the images) | retry, then **reject** |
| Poses labelled in the wrong order | retry `liveness_check_failed` |
| A browser claiming an easier challenge of its own | ignored: judged against the issued one |
| A reused challenge (Phase 1) | refused, `409 challenge_invalid` |
| Automation, and a virtual camera | **step up** `liveness_uncertain` |

### 5.3.5 The labels test mode

The end-to-end test's fake camera plays a still portrait (§5.1.5). It can't turn its head — so, measured honestly, it fails every pose challenge, as a photo should. To keep testing the whole journey, the inference service has a **test mode**, `DWARPAL_INFERENCE_LIVENESS=labels`, in which the pose check believes the photos' labels instead of measuring them.

Three locks keep it out of real use: the inference service refuses to start in that mode unless it uses the stand-in age model; every result says where its evidence came from (`evidence: "labels"`); and the API refuses that evidence for any live session. Labels mode still catches a wrong order, a missing baseline and a claimed challenge — the red-team tests above run in it, except the printed photo, which uses real measurement.

!!! real "Real world — what Phase 3 found"
    - **A synthetic head turn doesn't fool the detector.** To test turns without a person, we warped the test portrait in 2-D and in a simple 3-D projection to look turned. YuNet's sideways ratio never rose above 0.16 — far short of the 0.35 a turn needs. Good news for security (a flat picture, bent, doesn't look like a turned head); for testing, it meant the labels mode, and a real person.
    - **The colour layer lit only the card at first.** The card's blurred background made it the frame of reference for the full-screen layer. Drawing the layer straight into the page's body fixed it (see the comment above the portal in `camera-view.tsx`).
    - **The end-to-end journey still passes**, now with the colours, three or four pose prompts that each wait out their 6 seconds (a still portrait never turns), a pass for the 30-year-old stand-in, and leaving the cellar again: about a minute for the whole story.

### 5.3.6 Measuring on genuine attempts

Every liveness check turns away some honest people, so the roadmap's exit asks for that **false-reject rate** to be measured. The project's owner — a 21-year-old adult — made genuine attempts on the local stack with real measurement (`DWARPAL_INFERENCE_LIVENESS=images`) and the stand-in age model, so that only liveness was under test. Nothing was stored but numbers; `liveness-report` summarised each round, and the design changed after each one:

| Round | What the check did | Result | What the numbers showed |
| :-- | :-- | :-- | :-- |
| 1 | Fixed limits: turn yaw 0.35, look-up pitch 0.38 | **0 of 11** passed | Turns reached about 0.25–0.35; the prompt said "a little" |
| 2 | Poses measured from the person's own frontal angles (turn 0.18, look-up 0.06); reach recorded | 1 of 6 | Turns 0.16–0.28; look-up often about 0 — the photo was taken before or after the chin was up |
| 3 | A **meter** on the page and **three photos per pose** | 0 of 6 measurable | Every photo held a "second face": a small, steady face-like shape beside the owner, about a seventh of the real face's size |
| 4 | Count **people**, not detections (`quality.py`) | 8 of 12 | Turns 0.23–0.66, every time; all four failures were look-up |
| 5 | 3 or 4 poses, at most one look-up; look-up limit 0.03 | 5 of 8 | Turns 22 of 22, lowest 0.29; look-up still failed 3 of 8 (−0.03 to 0.02) |
| 6 | **Look-up recorded only; the turns decide** | not re-tested live | On round 5's numbers, all 8 attempts pass |

Two lessons came out of it. First, **a turn is a strong, measurable proof**: genuine turns cleared the limit by a wide margin every time, while a flat photo — turned or tilted — barely moves the nose against the eyes. Looking up is measured poorly by five landmarks, so it stays in the challenge (it makes the order harder to predict, and its reach is recorded for later), but it no longer decides. Second, **a detector sees faces where people don't**: something in the owner's room scored 0.85 as a face in every photo, and every attempt failed until the quality check learned to ignore detections that are small, faint or inside the main face.

For repeated testing, the demo shop gained a **Leave the cellar** button that forgets the pass — otherwise the shop's 30-minute pass lets the tester straight back in, and no new check is made.

!!! try "Try it yourself"
    After a series of attempts, summarise everything since a given time:

    `uv run --package dwarpal-api python -m dwarpal_api.cli liveness-report --since 2026-10-17T12:00`

    It prints the outcomes, how many pose challenges passed — and so the false-reject rate, if every attempt was genuine — the most common problems, how far each pose got from the person's frontal angles (median and lowest), the injection signs, and the light correlations.

!!! honest "Honest limitation"
    Phase 3 is not finished against its exit criteria. The false-reject rate comes from **one person** in one room and a few dozen attempts, and the final rule (round 6) was checked on recorded numbers, not re-tested live; it needs more people, cameras and rooms. The passive PAD layer is **empty** (its weights were not approved); the light signal is **recorded but not used** — and in the owner's tests it could not be measured at all, most likely because the device asked for reduced motion; looking up is **recorded but not used**; and the red-team cases that need a moving fake face — a screen replay, a game render — can't be produced synthetically (see above) and are still open. The design also can't stop an adult who does the check for a child.
