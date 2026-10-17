---
fingerprint: efcd1434d10be97c
---
Unit tests for `challenge.ts` (Vitest, §4.20): reading head angles, recognising poses, checking the server's challenge, and recognising virtual cameras. They need no browser and no camera — just numbers in and answers out.

@@ 1
Vitest's tools: `describe` (a group of tests), `it` (one test) and `expect` (a check).

@@ 3
The functions under test.

@@ 5-8
**Head angles.** Made-up face points, as fractions of the picture: the person's right eye at the left (`x: 0.4`), the left eye at the right (`0.6`), both at the same height, and the mouth 0.2 below them.

@@ 10-14
A nose exactly between the eyes, 0.11 below them: yaw close to 0 — straight ahead — and pitch 0.11 / 0.2 = 0.55. `toBeCloseTo` allows for tiny rounding errors in decimal arithmetic.

@@ 16-20
Move the nose to the picture's right (`x: 0.6`, a full eye distance) — that is a turn to the *person's* left, as `reached` says, and not to their right.

@@ 22-25
Raise the nose to 0.06 below the eyes (pitch 0.3): a raised head. At the normal 0.11 (pitch 0.55): not raised.

@@ 26
The end of the group.

@@ 28-34
**Reading a challenge.** A well-formed answer from the server, in the API's spelling.

@@ 36-43
It is accepted, and converted to the page's spelling: `challenge_id` becomes `id`, `step_ms` becomes `stepMs`.

@@ 45-50
**Everything odd is refused**: a pose the page doesn't know, colour names instead of colour codes, a step of 50 ms (which would flash far too fast — a safety issue, not just a technical one), and an empty ID. `{ ...answer, poses: [...] }` copies the good answer with one field changed. `expect(() => …).toThrow()` passes only if the function throws an error.

@@ 51
The end of the group.

@@ 53-59
**Virtual cameras**: two common virtual-camera names are recognised, regardless of capital letters; two real built-in cameras are not.

@@ 60
The end of the group.
