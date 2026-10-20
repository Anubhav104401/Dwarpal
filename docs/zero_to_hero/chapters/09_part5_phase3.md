## 5.3 Phase 3 — liveness and anti-spoofing

Phase 2 gave the system a real age model. But an age model only answers *how old does this face look?* — never *is this a living person, here, now?* Phase 3 adds that second question, with the layered design of ADR-0007 and the ideas of §2.18: a random challenge chosen by the server, evidence measured from the photos, and a decision that tells an attacker as little as possible.

| Layer (ADR-0007) | What | Status |
| :-- | :-- | :-- |
| L1 | Capture quality gate | ✅ since Phase 1 |
| L2 | **Passive PAD** — MiniFASNet, two networks that spot faces shown on paper or screens | ✅ decides (§5.3.3, §5.3.7) |
| L3 | **Random head-pose challenge**, checked on the server with a 478-point face mesh | ✅ turns decide; look-up and mid-turn photos are recorded |
| L4 | **Screen-light challenge** — colours reflected on the skin | ✅ measured and recorded; too variable to decide |
| L5 | **Injection signs** — automation, virtual cameras, hidden page, frozen frames; hands beside the face | ✅ hands recorded only |
| — | Decision, vague outward reasons, per-session and per-device attempt limits | ✅ §5.3.4 |

**The journey of one attempt, with liveness:**

```
verify page ── POST …/challenge ──► API: new_challenge() → random poses + colours, stored in Valkey (one use)
     │  ◄── { challenge_id, poses: [turn_right, look_up, turn_left, turn_right], colours: [4 × #rrggbb], step_ms: 600 }
     │
     │  MediaPipe guidance: "Move a little closer" … "That's good. Press Start"
     │  Start ► the screen glows in 4 colours, one baseline photo each   (none in calm mode)
     │        ► "Turn your head to your right, eyes on the screen"  [████░░░░░░] photo … [██████████] 2 photos (≤ 6 s)
     │        ► "Lift your chin up, eyes on the screen" … ► "Turn your head to your left, …" … ► …
     │
     └─ POST …/face-attempts  (up to 16 labelled photos + timings + browser signals)
            │
            ▼
API: take_challenge() — the server's own copy replaces whatever the page claimed
            │
            ▼
inference service: per photo — quality and people, face-mesh angles, hands, MiniFASNet real-face chance, screen pattern
            pose_check: frontal start? poses in order? each turn really shown, from the person's own frontal angles?
            light_check: did the cheeks follow the screen's colours?          (recorded only)
            injection_signs: automation, virtual camera, hidden page, frozen frames, hands (recorded only)
            │
            ▼
API: decide() — quality, then liveness, then age
            pose failed      → retry "liveness_check_failed"; the second time → reject "verification_failed"
            injection signs, or a real-face chance below 0.5 → step up "liveness_uncertain"
            otherwise        → the age decision of Phase 1–2
```

### 5.3.1 The challenge — chosen and kept by the server

Every attempt gets a fresh challenge: three or four head poses, never the same twice in a row and at most one look-up (24 possible orders), and four screen colours from a calm palette. It is drawn with the operating system's unpredictable random numbers, stored once, and destroyed when used. The page receives it so it can show the prompts — knowing the order a moment in advance doesn't help a prepared recording.

!walk services/api/src/dwarpal_api/domain/challenges.py

The rest of the server side changed in existing files, each explained in its own walkthrough: the contracts gained `Challenge`, `ClientSignals` and `Liveness` (`libs/contracts/src/dwarpal_contracts/face.py`); the store saves the challenge and hands it back (`adapters/store.py`); and `app/verification.py` puts the **server's** copy into the request before the inference service sees it.

### 5.3.2 The verify page plays it

The page does three things. **It guides**: MediaPipe's face landmarker, running inside the browser, turns what it sees into plain instructions before the check begins. **It plays the challenge**: the colours, on a fixed timetable so the server can tell which colour lit which photo, then each pose, with a **meter** that fills as the head turns, taking one photo on the way and two once the head has held it for three readings — or after six seconds anyway. Every photo is only copied while the challenge runs; encoding them to JPEG waits until the end, so nothing slow can shift the colours' timetable. **It reports**: the browser's own signals, which can only make the check stricter.

The guidance never decides anything. After 8 seconds Start can be pressed regardless, and if MediaPipe can't run at all the page simply works without it: a person whose face the landmarker reads badly must never be locked out by the page.

!walk apps/web/lib/challenge.ts

!walk apps/web/lib/challenge.test.ts

!walk apps/web/lib/landmarker.ts

!walk apps/web/scripts/mediapipe.mjs

The page also keeps a random **device ID** for the API's per-device budgets (§5.3.4) — a random number, not a fingerprint:

!walk apps/web/lib/device.ts

!walk apps/web/lib/device.test.ts

The camera code was rewritten around the challenge (`apps/web/lib/camera.ts`), and so was the camera screen (`apps/web/app/v/[sessionId]/camera-view.tsx`), with the full-screen colour layer, the guidance and the signals. Smaller changes: the flow client sends the labels and signals (`lib/flow-api.ts`), the page's security policy allows WebAssembly (`next.config.ts`), and `package.json` runs `mediapipe.mjs` before every start and build. The MediaPipe face model is pinned, like every other model, in `models/third_party.json`.

### 5.3.3 The evidence — measured from the photos

The inference service measures every photo: the sideways turn (**yaw**) it already measured, and now the up-down tilt (**pitch**, `libs/vision/src/dwarpal_vision/quality.py`). Each pose is judged against the person's **own** frontal angles, taken from their opening photos. The quality check also learned to count **people** rather than detections: a second box inside the same face, or a small face-like shape in the background, is no longer a second person (§5.3.6). From those numbers, the colours and the browser's signals, `liveness.py` gathers the three kinds of evidence. It decides nothing itself.

!walk services/inference/src/dwarpal_inference/liveness.py

!walk services/inference/tests/test_liveness.py

After the owner's tests (§5.3.6–5.3.7) the service measures far more in each photo, with three components added to the vision library — all run by OpenCV from pinned files, no new libraries:

- the **face mesh**, MediaPipe's 478 points, which measure the head's angles much better than YuNet's five, above all a lifted chin;
- the **hand detector**, MediaPipe's palm detector, looking for a hand held next to the face (recorded only: in the tests it didn't work well enough to trust);
- the **anti-spoofing networks**, MiniFASNet, filling layer L2, with a hand-made **screen-pattern** measure beside them.

!walk libs/vision/src/dwarpal_vision/mesh.py

!walk libs/vision/src/dwarpal_vision/hands.py

!walk libs/vision/src/dwarpal_vision/antispoof.py

MiniFASNet was published as PyTorch weights. One script turns them into the ONNX files the service runs, proving on the way that nothing changed:

!walk ml/src/dwarpal_ml/antispoof.py

!walk ml/tests/test_antispoof.py

`pipeline.py` collects what was seen in each photo and runs the checks; `main.py` and `settings.py` load the new models and add the labels test mode (§5.3.5).

### 5.3.4 The decision, and the red team

The decision engine (`services/api/src/dwarpal_api/domain/decision.py`) now checks liveness **after** quality and **before** age: a dark photo should be told to find light, not be counted as a liveness failure. A failed pose challenge gets one retry, then the session is rejected; signs of injection — or an anti-spoofing verdict below 0.5 — send even a clear adult to a stronger check. Outward reasons never say which check fired (the domain tests prove it). The detail is stored with the attempt, for the operator, and `liveness-report` summarises it (`cli.py`).

**Per-device budgets** stop endless trial and error. Each session already had a budget of challenges; a person testing photo after photo could simply start new sessions. Now each device (the page's random ID) may take 30 challenges per project an hour, and each network address 120, counted in Valkey whatever the session (`app/verification.py`, `adapters/store.py`). Past that, the page asks the person to wait a while.

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

    It prints the outcomes, how many pose challenges passed — and so the false-reject rate, if every attempt was genuine — the most common problems, which measurement judged the poses, how far each pose got (median and lowest), the injection signs, the presentation evidence (real-face chance, screen pattern, poses caught mid-turn), and the light correlations.

### 5.3.7 The red team — the owner attacks their own system

With the genuine false-reject rate under control, the owner turned attacker, and a server-side face mesh had made looking up measurable (genuine chins now measured 0.11–0.38). Two findings came first, both about the page:

- **Photos darkened by the screen's blue were set aside** by the quality check, leaving the light check with nothing to measure. Liveness now looks at every photo of one person; only the age needs flawless ones.
- **Encoding a photo took about a second** on a busy laptop, and the page stamped each photo's time *after* encoding: photos landed in the wrong colours, and later colours slid out of their timetable. Photos are now copied instantly, stamped at that moment, and encoded after the challenge.

Then the attacks. The owner held their phone up to the webcam, showing **selfies of themselves posed in each direction**, swiping to whichever one the prompt asked for — and later **a video of themselves turning**, paused and skipped to match the prompts:

| Defences in place | Genuine attempts | Attacks that reached the cellar | What the numbers showed |
| :-- | :-- | :-- | :-- |
| Poses, light recorded | passed | **posed selfies: 5 of 10 attempts** | A photo of a turned head *is* a turned head: the pose check alone can't tell |
| + light decides (≥ 0.5), a large or central second face counts, hands decide | **0 of 3** passed | 0 of 5 | Light stopped 3 attacks but also 2 genuine attempts (r 0.34, 0.38); the owner peeking from behind the phone was caught as a second face; the hand detector missed the holding hands and once saw a hand that wasn't there |
| + **MiniFASNet decides (≥ 0.5)**, light and hands record only | 5 of 6 (one stepped up by light, before it was demoted) | **0 of 7** (3 selfie, 4 video) | Real faces 0.94–0.995; phone photos and videos 0.006–0.195 |

The anti-spoofing networks are the layer that finally separated the two — by a margin wide enough to trust, where light (real faces −0.25 to 0.99) never could. Two more measures point the same way and are recorded for later: the **screen pattern** (real faces 0.99–1.14, phone 1.16–1.31) and whether each pose was caught **mid-turn** (real heads 19 of 19, attacks 5 of 23).

!!! honest "Honest limitation"
    Phase 3 is not finished against its exit criteria. Every number here comes from **one person**, one laptop camera and one room, over a few dozen attempts: the false-reject rate and the anti-spoofing margin need more people, cameras, rooms and attack media before they can be trusted. MiniFASNet was trained by someone else on data we haven't seen, so its behaviour on other faces and skin tones is unmeasured — the fairness questions of §2.16 apply to it too. The light, the screen pattern, the mid-turn photos, the hand detector and looking up are **recorded but not used**. An attacker who drives a fake camera directly (no phone, no screen in the picture) or uses a convincing real-time deepfake was not tested. And the design can't stop an adult who does the check for a child.
