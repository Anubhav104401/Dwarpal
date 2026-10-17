---
fingerprint: c827ebb601c3c819
---
**Liveness challenges** — what the person will be asked to do in their next face attempt (§5.3). Each challenge is a random order of three head poses and a random run of four screen colours, made fresh for every attempt.

Why random? A **replay attack** plays a recording of someone — a video of an adult turning their head — to the camera. If the challenge were always "turn left, then right", one recording would work every time. With 12 possible pose orders and hundreds of colour runs, chosen only when the attempt begins, an attacker can't prepare the right recording in advance.

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
`POSES` (the three head poses) and the `Challenge` contract.

@@ 11-12
The comment explains how the colours were chosen, with **people with photosensitive epilepsy** in mind. Flashing light can trigger seizures; the accessibility standard **WCAG** (rule 2.3.1) says nothing should flash more than three times a second. So: calm colours, no saturated red (the most dangerous colour for this), and each shown for 600 ms — fewer than two changes a second. People who have asked their device for reduced motion see no colours at all (`camera.ts`).

@@ 13
`PALETTE` — the five colours, written as web colours: blue, teal, yellow, violet, and near-white. They are far apart from each other, so the change in the light reflected from a face is as clear as possible.

@@ 14-16
The challenge's size: `POSE_STEPS = 3` poses, `COLOUR_STEPS = 4` colours, and `STEP_MS = 600` milliseconds per colour. The colours take 2.4 seconds in all.

@@ 18
`_unpredictable` — the one secure random generator the module uses by default. `SystemRandom` has the same methods as `random.Random`, but draws on `secrets`' source. The leading `_` marks it as private to this module.

@@ 21
**`sequence`** — pick `length` items from `options`, at random, **never the same item twice in a row**. `[T]` after the name makes it **generic**: it works for any type `T` — poses, colours — and the type checker knows the result is a list of the same type as the options.

@@ 22
The first item: any of the options. `rng.choice` picks one at random.

@@ 23-24
While the list is too short, add a random item from the options *other than* the last one picked (`chosen[-1]`). A repeated step would be a weak one: "turn left" twice in a row can be passed by simply staying turned, and the same colour twice doesn't change the light.

@@ 25
Return the list.

@@ 28
**`new_challenge`** — make one challenge. Normally it uses the secure generator; a test can pass a seeded one to get the same "random" challenges every run.

@@ 29-33
The challenge: three poses, four colours, each colour shown for 600 ms. Pydantic checks it against the contract's limits as it is created.
