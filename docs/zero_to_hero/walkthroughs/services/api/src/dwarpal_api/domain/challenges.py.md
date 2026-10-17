---
fingerprint: fb5e43a07ecec780
---
**Liveness challenges** — what the person will be asked to do in their next face attempt (§5.3). Each challenge is a random order of three or four head poses and a random run of four screen colours, made fresh for every attempt.

Why random? A **replay attack** plays a recording of someone — a video of an adult turning their head — to the camera. If the challenge were always "turn left, then right", one recording would work every time. With 24 possible pose orders and hundreds of colour runs, chosen only when the attempt begins, an attacker can't prepare the right recording in advance.

@@ 1
The module docstring: a random order of poses and a random run of colours, new for every attempt.

@@ 3
`from __future__ import annotations` — the project-wide type-hint setting.

@@ 5
`random` — Python's random-number tools. Only its type `random.Random` is used here, so a test can pass in a generator of its own.

@@ 6
`secrets` — random numbers that are safe for security: they come from the operating system and **can't be predicted** from earlier ones. The plain `random` module is fast but predictable — someone who sees enough of its output can work out what comes next.

@@ 7
`Sequence` — the type for "anything that can be indexed and counted", such as a tuple or a list.

@@ 9
`POSES` (the three head poses), the `Challenge` contract, and the `Pose` type.

@@ 11-12
The comment explains how the colours were chosen, with **people with photosensitive epilepsy** in mind. Flashing light can trigger seizures; the accessibility standard **WCAG** (rule 2.3.1) says nothing should flash more than three times a second. So: calm colours, no saturated red (the most dangerous colour for this), and each shown for 600 ms — fewer than two changes a second. People who have asked their device for reduced motion see no colours at all (`camera.ts`).

@@ 13
`PALETTE` — the five colours, written as web colours: blue, teal, yellow, violet, and near-white. They are far apart from each other, so the change in the light reflected from a face is as clear as possible.

@@ 14-15
The comment explains the pose rules, which came out of the owner's genuine tests (§5.3.6). A **turn** is the strong proof: a flat picture can't turn its head, and every genuine turn was measured clearly. **Looking up** is hard to measure from five landmarks, so it appears at most once — and every challenge still holds at least two turns.

@@ 16-19
The challenge's size: **3 or 4 poses** (`POSE_STEPS = (3, 4)`, a tuple to choose from), at most `MAX_LOOK_UPS = 1` look-up, `COLOUR_STEPS = 4` colours, and `STEP_MS = 600` milliseconds per colour. The colours take 2.4 seconds in all.

@@ 21
`_unpredictable` — the one secure random generator the module uses by default. `SystemRandom` has the same methods as `random.Random`, but draws on `secrets`' source. The leading `_` marks it as private to this module.

@@ 24
**`sequence`** — pick `length` items from `options`, at random, **never the same item twice in a row**. Used for the colours. `[T]` after the name makes it **generic**: it works for any type `T`, and the type checker knows the result is a list of the same type as the options.

@@ 25
The first item: any of the options. `rng.choice` picks one at random.

@@ 26-27
While the list is too short, add a random item from the options *other than* the last one picked (`chosen[-1]`). A repeated step would be a weak one: "turn left" twice in a row can be passed by simply staying turned, and the same colour twice doesn't change the light.

@@ 28
Return the list.

@@ 31
**`pose_sequence`** — pick `length` poses at random, with two rules: never the same pose twice in a row, and at most one look-up.

@@ 32
The poses chosen so far: none yet.

@@ 33
Until there are enough:

@@ 34-38
List the poses **allowed** next. A pose is allowed if it is not the one just chosen (or nothing is chosen yet), **and** it is not a look-up — or not enough look-ups have been chosen yet. `chosen.count("look_up")` counts them.

@@ 39-40
Pick one of the allowed poses at random, add it, and finally return the list.

@@ 43
**`new_challenge`** — make one challenge. Normally it uses the secure generator; a test can pass a seeded one to get the same "random" challenges every run.

@@ 44-48
The challenge: 3 or 4 poses (`rng.choice(POSE_STEPS)` picks the number), four colours, each colour shown for 600 ms. Pydantic checks it against the contract's limits as it is created.
