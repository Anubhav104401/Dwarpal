---
fingerprint: ddb677a56baa60da
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

@@ 9-19
The code under test, including three of its limits, so the tests follow them if they change.

@@ 21-23
`CHALLENGE` — one fixed challenge for every test: turn left, look up, turn right; three colours, 600 ms each.

@@ 26
**`report`** — a frame report with chosen head angles and number of faces. By default: one face, straight ahead (yaw 0, pitch 0.55).

@@ 27-37
Everything else is fixed at ordinary, good values, with no quality flags.

@@ 40-47
**`frame`** — one `Seen` frame: its number, its phase label (baseline unless given), its time, its aligned face (none unless given) and its head angles.

@@ 48
Its description. Unless a time is given, frames are 200 ms apart (`200.0 * index`).

@@ 49
Put it together, with a matching report.

@@ 52-60
**`genuine`** — what an honest attempt at `CHALLENGE` looks like: three frontal baseline frames, then a frame turned clearly left (yaw 0.5), one looking up (pitch 0.25) and one turned clearly right (−0.5).

@@ 63-64
**Each pose is measured from the person's own frontal angles.** Here those are straight ahead: yaw 0, pitch 0.55.

@@ 65-70
Exactly the turn limit to the left counts as turned left; the same amount the other way doesn't. A strong right turn counts as right. A pitch twice the limit below the frontal one is looking up; the frontal pitch itself isn't. And a strong left turn with **two people** in the picture counts for nothing.

@@ 71-73
Why measure from the person's own angles: with a camera below the face, the frontal pitch might be 0.7. Lifting the chin to 0.6 is then a real look-up — though from a frontal 0.55, the same 0.6 would be a head tilted *down*.

@@ 76-77
**The poses asked for, in the order asked, pass.**

@@ 80-83
**The check records how far each pose got.** For the genuine attempt: frontal angles 0 and 0.55, and each pose's reach, in order — turns of 0.5, a look-up of 0.3.

@@ 86-89
**Poses in another order fail.** Swap the first and last poses: the frames still show their labels' poses perfectly, but not in the challenge's order. The only problem is `wrong_order`. `a, b = x, y` assigns two things at once.

@@ 92-95
**A pose that is named but not shown fails.** The frame is labelled `turn_left`, but the head is turned only 0.05 — barely at all. The labels can say what they like: the measurement decides.

@@ 98-101
**A photo that never turns fails every turn.** All six frames look straight ahead — a still photo, labelled to follow the challenge exactly. Both turns are reported as not shown; the look-up is recorded, but never decides.

@@ 104-109
**Looking up is recorded but doesn't decide.** In an otherwise genuine attempt, the look-up frame's pitch barely moves (0.56, from 0.55). The check still passes on its turns, and records the look-up's reach: −0.01, a hair the wrong way.

@@ 112-115
**The baseline must come first, be frontal and be long enough.** First: one baseline frame turned past the frontal limit.

@@ 116
Then: only one baseline frame (the list from position 2 on).

@@ 117-118
Then: the poses first, and the three baseline frames afterwards (at 2 to 2.4 seconds). `[*a, b, c]` makes a list of `a`'s items followed by `b` and `c`.

@@ 121-124
**Frames whose clock runs backwards fail.** Frame 1 claims to be taken at 900 ms — after frames 2, 3 and 4. Sorting by time then puts the numbers out of order: `timing`.

@@ 127
**`face_lit_by`** — a synthetic 224 × 224 "face" lit by a screen colour. `strength` says how much the screen's colour mixes into the skin's: 0 means not at all.

@@ 128
Read the colour's red, green and blue, in OpenCV's blue-green-red order (characters 5–6 first).

@@ 129
Mix an ordinary skin tone (in blue-green-red: 110, 140, 190) with the screen's colour, in the given proportion.

@@ 130
Fill the picture with that colour, plus a little random noise, like a real camera's (`rng.normal(0, 2, …)`: random values around 0, typically within ±2). Keep values in 0–255 and store them as image bytes.

@@ 133-135
**`lit_frames`** — three baseline frames, one under each of the challenge's colours: each taken 100 ms into its colour's 600 ms. `default_rng(0)` makes the noise the same every run.

@@ 138-142
**Skin that follows the screen correlates strongly** — at 20 % strength, above 0.9.

@@ 145-149
**Skin that ignores the screen doesn't** — at 0 %, only the noise changes, and the correlation stays below 0.9.

@@ 152-155
**Without the screen colours there is no light evidence**: no start time, colours not shown (calm mode), or only two frames — each time, not usable.

@@ 158-160
**A colour is read as its share of red and blue.** Pure red is all red and no blue. Near-white is a third of each. `pytest.approx` compares decimals with a tiny tolerance.

@@ 163-165
**Browser reports and frozen frames are signs of injection.** A random 224 × 224 picture as the "face".

@@ 166
`frozen` — three frames that are the very same picture.

@@ 167
`alive` — three frames of that picture, each with its own small noise: like a live camera filming something perfectly still.

@@ 168
Signals with every warning on.

@@ 169
The frozen frames with those signals give all four signs, in order.

@@ 170
The live frames with normal signals give none.
