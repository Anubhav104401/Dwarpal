---
fingerprint: 961f01090aff43aa
---
Unit tests for the liveness checks (`liveness.py`). They build frames by hand — a report with chosen head angles, or a synthetic "face" lit by a chosen colour — so each check can be tested on exactly the situation it is meant for, with no camera and no detector.

The real images are tested elsewhere: the red-team tests in `services/api/tests/test_api.py` send a real portrait through the whole system.

@@ 1
The module docstring: the three kinds of evidence under test.

@@ 3
`from __future__ import annotations` — the project-wide type-hint setting.

@@ 5-6
NumPy for building pictures, and pytest for `pytest.approx`.

@@ 8
The contracts used to build test frames.

@@ 9-18
The code under test, including two of its limits, so the tests follow them if they change.

@@ 20-22
`CHALLENGE` — one fixed challenge for every test: turn left, look up, turn right; three colours, 600 ms each.

@@ 25
**`report`** — a frame report with chosen head angles and number of faces. By default: one face, straight ahead (yaw 0, pitch 0.55).

@@ 26-36
Everything else is fixed at ordinary, good values, with no quality flags.

@@ 39-46
**`frame`** — one `Seen` frame: its number, its phase label (baseline unless given), its time, its aligned face (none unless given) and its head angles.

@@ 47
Its description. Unless a time is given, frames are 200 ms apart (`200.0 * index`).

@@ 48
Put it together, with a matching report.

@@ 51-59
**`genuine`** — what an honest attempt at `CHALLENGE` looks like: three frontal baseline frames, then a frame turned clearly left (yaw 0.5), one looking up (pitch 0.25) and one turned clearly right (−0.5).

@@ 62-68
**Each pose is recognised by its landmarks.** Exactly at the turn limit counts as turned left; the same amount the other way doesn't. A strong right turn counts as right. A pitch of 0.3 is looking up; the normal 0.55 isn't. And a strong left turn with **two faces** in the picture counts for nothing.

@@ 71-72
**The poses asked for, in the order asked, pass.**

@@ 75-78
**Poses in another order fail.** Swap the first and last poses: the frames still show their labels' poses perfectly, but not in the challenge's order. The only problem is `wrong_order`. `a, b = x, y` assigns two things at once.

@@ 81-84
**A pose that is named but not shown fails.** The frame is labelled `turn_left`, but the head is turned only 0.05 — barely at all. The labels can say what they like: the measurement decides.

@@ 87-90
**A photo that never turns fails every pose.** All six frames look straight ahead — a still photo, labelled to follow the challenge exactly. Every pose is reported as not shown.

@@ 93-96
**The baseline must come first, be frontal and be long enough.** First: one baseline frame turned past the frontal limit.

@@ 97
Then: only one baseline frame (the list from position 2 on).

@@ 98-99
Then: the poses first, and the three baseline frames afterwards (at 2 to 2.4 seconds). `[*a, b, c]` makes a list of `a`'s items followed by `b` and `c`.

@@ 102-105
**Frames whose clock runs backwards fail.** Frame 1 claims to be taken at 900 ms — after frames 2, 3 and 4. Sorting by time then puts the numbers out of order: `timing`.

@@ 108
**`face_lit_by`** — a synthetic 224 × 224 "face" lit by a screen colour. `strength` says how much the screen's colour mixes into the skin's: 0 means not at all.

@@ 109
Read the colour's red, green and blue, in OpenCV's blue-green-red order (characters 5–6 first).

@@ 110
Mix an ordinary skin tone (in blue-green-red: 110, 140, 190) with the screen's colour, in the given proportion.

@@ 111
Fill the picture with that colour, plus a little random noise, like a real camera's (`rng.normal(0, 2, …)`: random values around 0, typically within ±2). Keep values in 0–255 and store them as image bytes.

@@ 114-116
**`lit_frames`** — three baseline frames, one under each of the challenge's colours: each taken 100 ms into its colour's 600 ms. `default_rng(0)` makes the noise the same every run.

@@ 119-123
**Skin that follows the screen correlates strongly** — at 20 % strength, above 0.9.

@@ 126-130
**Skin that ignores the screen doesn't** — at 0 %, only the noise changes, and the correlation stays below 0.9.

@@ 133-136
**Without the screen colours there is no light evidence**: no start time, colours not shown (calm mode), or only two frames — each time, not usable.

@@ 139-141
**A colour is read as its share of red and blue.** Pure red is all red and no blue. Near-white is a third of each. `pytest.approx` compares decimals with a tiny tolerance.

@@ 144-146
**Browser reports and frozen frames are signs of injection.** A random 224 × 224 picture as the "face".

@@ 147
`frozen` — three frames that are the very same picture.

@@ 148
`alive` — three frames of that picture, each with its own small noise: like a live camera filming something perfectly still.

@@ 149
Signals with every warning on.

@@ 150
The frozen frames with those signals give all four signs, in order.

@@ 151
The live frames with normal signals give none.
