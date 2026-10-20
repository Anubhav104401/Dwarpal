---
fingerprint: f1161043f96e4444
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

@@ 26-28
**`report`** — a frame report with chosen head angles, number of faces, and optionally face-mesh angles. By default: one face, straight ahead (yaw 0, pitch 0.55), no mesh reading.

@@ 29-41
Everything else is fixed at ordinary, good values, with no quality flags; the mesh angles are filled in only when given.

@@ 44-52
**`frame`** — one `Seen` frame: its number, its phase label (baseline unless given), its time, its aligned face (none unless given), its head angles, and optionally its mesh angles.

@@ 53
Its description. Unless a time is given, frames are 200 ms apart (`200.0 * index`).

@@ 54
Put it together, with a matching report.

@@ 57-65
**`genuine`** — what an honest attempt at `CHALLENGE` looks like: three frontal baseline frames, then a frame turned clearly left (yaw 0.5), one looking up (pitch 0.25) and one turned clearly right (−0.5).

@@ 68-69
**Each pose is measured from the person's own frontal angles.** Here those are straight ahead: yaw 0, pitch 0.55.

@@ 70-75
Exactly the turn limit to the left counts as turned left; the same amount the other way doesn't. A strong right turn counts as right. A pitch twice the limit below the frontal one is looking up; the frontal pitch itself isn't. And a strong left turn with **two people** in the picture counts for nothing.

@@ 76-78
Why measure from the person's own angles: with a camera below the face, the frontal pitch might be 0.7. Lifting the chin to 0.6 is then a real look-up — though from a frontal 0.55, the same 0.6 would be a head tilted *down*.

@@ 81-82
**The poses asked for, in the order asked, pass.**

@@ 85-88
**The check records how far each pose got.** For the genuine attempt: frontal angles 0 and 0.55, and each pose's reach, in order — turns of 0.5, a look-up of 0.3.

@@ 91-99
**The face mesh measures the poses when it saw every frontal frame.** Six frames, all with mesh readings: three frontal ones around pitch 0.75 (the mesh's frontal range differs from the five points'), then the three poses.

@@ 100-103
The check passes, says it used the mesh, and records the look-up as a 0.15 rise from the frontal median (0.75 → 0.6).

@@ 106-111
**Without the mesh on every frontal frame, the five points measure everything.** Only the first frame has a mesh reading, so the check uses the five points throughout — never a mixture of two measurements with different scales.

@@ 114-117
**Poses in another order fail.** Swap the first and last poses: the frames still show their labels' poses perfectly, but not in the challenge's order. The only problem is `wrong_order`. `a, b = x, y` assigns two things at once.

@@ 120-123
**A pose that is named but not shown fails.** The frame is labelled `turn_left`, but the head is turned only 0.05 — barely at all. The labels can say what they like: the measurement decides.

@@ 126-129
**A photo that never turns fails every turn.** All six frames look straight ahead — a still photo, labelled to follow the challenge exactly. Both turns are reported as not shown; the look-up is recorded, but never decides.

@@ 132-137
**Looking up is recorded but doesn't decide.** In an otherwise genuine attempt, the look-up frame's pitch barely moves (0.56, from 0.55). The check still passes on its turns, and records the look-up's reach: −0.01, a hair the wrong way.

@@ 140-143
**The baseline must come first, be frontal and be long enough.** First: one baseline frame turned past the frontal limit.

@@ 144
Then: only one baseline frame (the list from position 2 on).

@@ 145-146
Then: the poses first, and the three baseline frames afterwards (at 2 to 2.4 seconds). `[*a, b, c]` makes a list of `a`'s items followed by `b` and `c`.

@@ 149-152
**Frames whose clock runs backwards fail.** Frame 1 claims to be taken at 900 ms — after frames 2, 3 and 4. Sorting by time then puts the numbers out of order: `timing`.

@@ 155
**`face_lit_by`** — a synthetic 224 × 224 "face" lit by a screen colour. `strength` says how much the screen's colour mixes into the skin's: 0 means not at all.

@@ 156
Read the colour's red, green and blue, in OpenCV's blue-green-red order (characters 5–6 first).

@@ 157
Mix an ordinary skin tone (in blue-green-red: 110, 140, 190) with the screen's colour, in the given proportion.

@@ 158
Fill the picture with that colour, plus a little random noise, like a real camera's (`rng.normal(0, 2, …)`: random values around 0, typically within ±2). Keep values in 0–255 and store them as image bytes.

@@ 161-163
**`lit_frames`** — three baseline frames, one under each of the challenge's colours: each taken 100 ms into its colour's 600 ms. `default_rng(0)` makes the noise the same every run.

@@ 166-170
**Skin that follows the screen correlates strongly** — at 20 % strength, above 0.9.

@@ 173-177
**Skin that ignores the screen doesn't** — at 0 %, only the noise changes, and the correlation stays below 0.9.

@@ 180-185
**Without the screen colours there is no light evidence**: no start time; colours not shown (calm mode), recorded as `shown: false`; or only two frames, shown but too few to measure — each time, not usable.

@@ 188-190
**A colour is read as its share of red and blue.** Pure red is all red and no blue. Near-white is a third of each. `pytest.approx` compares decimals with a tiny tolerance.

@@ 193-195
**Browser reports and frozen frames are signs of injection.** A random 224 × 224 picture as the "face".

@@ 196
`frozen` — three frames that are the very same picture.

@@ 197
`alive` — three frames of that picture, each with its own small noise: like a live camera filming something perfectly still.

@@ 198
Signals with every warning on.

@@ 199
The frozen frames with those signals give all four signs, in order.

@@ 200
The live frames with normal signals give none.

@@ 203-209
**A hand beside the face in more than one photo is a sign of a held phone.** A helper builds frames whose reports say how many hands were next to the face (`model_copy(update=…)` copies a report with one field changed), and returns the injection signs.

@@ 211-212
Hands in two photos give the sign `hand_near_face`; in one photo alone, nothing — that could be a passing gesture, or a false find.

@@ 215-219
**A photo on the way into a pose shows the movement was gradual.** Add a frame to the genuine attempt, labelled `turn_left`, turned 0.2 — partway to the full 0.5. That pose is recorded as gradual; the others, with a single photo each at their full angle, aren't.
