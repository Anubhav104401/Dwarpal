---
fingerprint: d14b4467558edf67
---
The **liveness checks** (§5.3, ADR-0007): evidence that a real, present person stood in front of the camera — not a photo, a screen replaying a video, or a fake camera feeding in pictures. There are three:

1. **The pose check** — did the head turn as the challenge asked, in the right order? A printed photo can't turn its head when asked; a pre-recorded video doesn't know which way it will be asked to turn.
2. **The light check** — while the screen showed its colours, did the skin pick up their glow? Real skin a hand's width from a bright screen reflects its colour. This one is only **recorded** for now: on its own it is weak (in a bright room the glow is faint), and its limits must first be measured on genuine attempts.
3. **Injection signs** — anything suggesting the pictures didn't come from a live camera: the browser's own warnings, and frames that are *too* identical.

As the docstring says, this file only gathers **evidence**. The decision — retry, reject, step up — belongs to the API's decision engine (`decision.py`).

@@ 1-2
The module docstring: the three questions, and the rule that this is evidence only.

@@ 4
`from __future__ import annotations` — the project-wide type-hint setting.

@@ 6
`itertools` — for `pairwise`, which gives each pair of neighbours in a list.

@@ 7
`dataclass` — for the small `Seen` record below.

@@ 8
`Literal` — for the type that names the two measurements, `"mesh"` and `"five_points"`.

@@ 10-12
OpenCV (`cv2`, for converting to greyscale), NumPy, and NumPy's array type for annotations.

@@ 14
The contracts this file reads and produces.

@@ 15
`Image` — the project's type for a picture: a NumPy array of pixels.

@@ 17-22
The comment explains the limits below, which were **set from the owner's genuine attempts** (§5.3.6), and how the head is measured: a turned head moves the nose sideways against the eyes; a raised one moves it towards the eyes. Each pose is measured against the person's **own** frontal angles, so camera height and face shape cancel out.

The measurements behind the numbers: from YuNet's five points, genuine turns moved the nose 0.23–0.69 eye-widths, but lifted chins anywhere from −0.03 to 0.12 — five points can't measure looking up. The 478-point face mesh does far better: turns 0.42–0.70, lifted chins 0.11–0.38. Turns carry the proof; looking up is recorded but doesn't decide. A flat photo, turned or tilted, moves neither.

@@ 23
`FRONTAL_YAW = 0.2` — a baseline frame must be facing the camera: sideways turn no more than 0.2 either way (five-point measure).

@@ 24-25
The five-point limits: a turn counts from a shift of 0.18 eye-widths (about 18 degrees); a look-up from 0.03, though it is only recorded.

@@ 26-27
The face mesh's limits: 0.18 for a turn, 0.08 for a look-up — below every genuine attempt measured (0.42 and 0.11 at the lowest).

@@ 28
`DECIDING` — the poses whose failure fails the check: the two turns. A **frozenset** is a set that can't be changed; the annotation `frozenset[Pose]` says it holds poses.

@@ 29
`MIN_BASELINE = 3` — at least three frontal frames are needed.

@@ 30-31
`STILL_FRAMES = 0.75` — as the comment says, two frames from a live camera are never quite the same: even with a perfectly still person, the sensor adds a little **noise**. If every pair of frames differs by less than 0.75 grey levels on average (out of 255), they were probably copies of one picture.

@@ 32
`HAND_FRAMES = 2` — a hand next to the face must show in at least two photos to count as a sign.

@@ 33-36
Where to sample on the 224 × 224 aligned face (`align_face` puts every face in the same place). Each `slice(a, b)` is a range of rows or columns.

- `SKIN` — three small patches: the right cheek, the left cheek and the forehead;
- `BACKGROUND` — the two top corners, which are beyond the head and hair.

@@ 39-45
**`Seen`** — one frame as the checks see it: its description from the browser (`meta`, with its phase label and time), the inference service's report on it (`report`), and its aligned face, or `None` if the frame had a quality problem. `frozen=True` — it can't be changed after it's made.

@@ 48
`Angles` — a name for a pair of numbers: yaw, then pitch.

@@ 49
`Source` — which measurement the angles come from: the face mesh, or the detector's five points.

@@ 50
`LIMITS` — each measurement's (turn, look-up) limits, so the code below can look them up by source.

@@ 53-54
**`head`** — a frame's yaw and pitch from the chosen measurement, as the docstring says.

@@ 55-56
From the five points: always there.

@@ 57-59
From the mesh: `None` if the mesh didn't measure this frame, otherwise its two angles.

@@ 62-63
**`source_for`** — which measurement to use for a whole attempt: the mesh when it measured every frontal frame of one person, otherwise the five points — never a mixture, because the two use different scales.

@@ 64-65
The baseline frames of one person, and the choice. `all(…)` is true only if every one of them has mesh angles.

@@ 68-69
**`frontal_angles`** — the person's own angles when facing the camera, from the chosen measurement. The docstring: the **median** over the baseline frames with exactly one face. The median — the middle value — isn't dragged away by one odd frame.

@@ 70
The readings: for each one-person baseline frame, its angles, skipping frames the chosen measurement didn't measure. `(a := …)` stores the angles in `a` and tests them in one step.

@@ 71-72
No readings: there is nothing to measure from.

@@ 73
The median yaw and the median pitch, as a pair.

@@ 76-77
**`shift`** — how far a frame's angles have moved from the frontal angles **in the pose's direction**, as the docstring says. A negative answer means it moved the other way.

@@ 78-79
Turning to the left raises the sideways ratio (in an unmirrored picture, the nose moves towards the right of the picture): the shift is how much it rose.

@@ 80-81
Turning to the right lowers it: the shift is how much it fell.

@@ 82
Otherwise the pose is `look_up`, which lowers the up-down ratio: the shift is how much it fell.

@@ 85
**`shows`** — does this frame show the pose, by the chosen measurement (the five points unless told otherwise)?

@@ 86-88
Only with exactly one person in the picture, and only if the measurement has angles for this frame.

@@ 89-90
Then: has it moved at least the measurement's limit — the look-up limit for looking up, the turn limit for a turn?

@@ 93
**`segments`** — split the frames, in time order, into **runs** of the same phase. Labels baseline, baseline, turn_left, look_up give three runs: two baseline frames, one turn_left, one look_up.

@@ 94
The runs so far: each a pair of (phase, its frames).

@@ 95-97
For each frame: if it has the same phase as the last run, add it to that run …

@@ 98-99
… otherwise start a new run.

@@ 100
Return the runs.

@@ 103
**`pose_check`** — check the frames against the challenge. With `trust_labels` (the test mode), the labels are believed, and the head measurements are skipped.

@@ 104
Put the frames in time order, by `t_ms`.

@@ 105
The problems found, as short names. An empty list at the end means it passed.

@@ 106-107
**`timing`** — the frames' numbers must run in the same order as their times. Frame 3 can't have been taken before frame 2: if it was, the description was tampered with.

@@ 108-109
Split into runs, and collect every baseline frame. (The double `for` reads left to right: for each run that is a baseline run, for each of its frames.)

@@ 110-111
**`baseline_missing`** — fewer than three baseline frames.

@@ 112-115
**`baseline_not_frontal`** — measured from the images (not in the test mode): every baseline frame must show exactly one face, facing the camera. A frontal start is what makes the turns that follow meaningful; it also stops an attacker from sending only turned pictures.

@@ 116-117
**`baseline_not_first`** — the attempt must *start* with the baseline.

@@ 118-119
Choose the measurement for this attempt, and the person's frontal angles by it — or `None`.

@@ 120-121
`reached` and `gradual` — the per-pose records, filled below.

@@ 122
The pose runs: every run that isn't baseline, in order.

@@ 123-124
**`wrong_order`** — the pose runs' labels must be exactly the challenge's poses, in its order, with nothing extra. `list(…)` because the challenge's poses and the labels must be compared as lists of the same kind.

@@ 125-126
If the order is right — and not in the test mode — go through the challenge's poses together with their runs. `zip(…, strict=True)` pairs them, and would fail loudly if the two lists had different lengths — which the order check has just ruled out.

@@ 127-128
The run's frames with exactly one person, and their angles by the chosen measurement.

@@ 129-130
The **furthest** any of them moved in the pose's direction (`max`), or `None` when there is no frontal reference or no measured frame — and record it, rounded to three decimals.

@@ 131-134
**Was the movement gradual?** True if some photo caught the head partway — between 15 % and 75 % of the way to its furthest point. The page takes one photo on the way into each pose; a real head passes through the angles between, while swiping from one photo to the next jumps.

@@ 135
Did the pose go unseen — no reference, or no frame that shows it?

@@ 136-137
Only a **turn** that went unseen is a problem: `not_shown:` and the pose's name, such as `not_shown:turn_left`. A look-up that went unseen is only recorded, in `reached`.

@@ 138-146
The result: passed if there were no problems, with the list either way, the frontal angles (rounded), how far each pose got, which measurement was used, and which poses were reached gradually.

@@ 149
**`chromaticity`** — the colour of some patches of a picture, **without its brightness**. Brightness changes for many reasons (the person moves, the camera adjusts itself); the *balance* of red, green and blue is what the screen's colour changes.

@@ 150
Take every patch's pixels, lay them out as one long list of (blue, green, red) values (`reshape(-1, 3)`: −1 means "as many rows as needed"), join the patches together, and switch to decimals.

@@ 151
The average of each colour. OpenCV stores pixels as **B**lue, **G**reen, **R**ed — in that order.

@@ 152-153
Divide by the total, so only the balance remains: the share of red and the share of blue. (The share of green is whatever is left, so it adds nothing.) `max(…, 1.0)` avoids dividing by zero on a black patch.

@@ 156
**`emitted`** — the same two shares for a colour the screen showed, from its web code.

@@ 157
Read the code's three pairs of hexadecimal digits — characters 1–2, 3–4 and 5–6 of `#3c78ff` — as numbers from 0 to 255. `int(…, 16)` reads a number written in base 16.

@@ 158-159
The shares of red and blue, as for the skin.

@@ 162
**`correlation`** — how closely the measured colours followed the shown ones, from −1 to +1. This is **Pearson's correlation**: +1 means they rose and fell exactly together, 0 means no relation.

@@ 163-164
Subtract each list's average, so only the *changes* remain.

@@ 165
The size of each list of changes — `np.linalg.norm` is the length of the whole list taken as one long arrow — multiplied together.

@@ 166
Correlation is the sum of the changes multiplied together, divided by that product. If either list never changed at all (`spread` is 0), there is nothing to compare: `None`. `np.clip` guards against rounding taking it a hair past ±1.

@@ 169-171
**`light_check`** — did the skin follow the screen's colours? It needs the frames, the challenge (for its colours and timing), when the colours started, and the browser's signals.

@@ 172-173
No colours were shown — calm mode, or an older page: nothing to measure, and the result says so (`shown=False`). This never counts against anyone.

@@ 174
Three lists: the skin's colour in each frame, the background's, and what the screen showed.

@@ 175-176
For each frame, work out **which colour was on screen** when it was taken: the time since the colours started, divided by the step length, rounded down (`//`).

@@ 177-178
Skip frames that aren't baseline frames, that have no usable face, or that fall outside the colours' time.

@@ 179-181
Measure the skin and the background, and note the colour shown.

@@ 182-183
At least three measured frames are needed, under at least two *different* colours (`{…}` makes a set, which keeps each colour once). Otherwise: not usable.

@@ 184
The result: how well the skin followed the screen, and how well the background did. A real face close to the screen should follow it clearly; the background, further away, much less. A photo or a screen held up to the camera tends to behave differently — but how differently, in real rooms, is what the owner's tests will measure.

@@ 187
**`injection_signs`** — signs that the pictures didn't come from a live camera.

@@ 188
The signs found.

@@ 189-194
The browser's own reports: a program driving the browser (`automation`), a virtual camera (`virtual_camera`), and the page being hidden during the check (`page_hidden`). These come from the browser and can be faked — but only an honest browser reports them, and then they are worth knowing.

@@ 195
The usable faces, in time order.

@@ 196
Each converted to greyscale, as decimals.

@@ 197
How much each frame differs from the next: the average difference between their pixels.

@@ 198-199
**`identical_frames`** — if there are at least two such differences and even the largest is below 0.75 grey levels, the frames are near-copies: one picture sent several times, as a fake camera might. Not in the test mode, where the frames are copies of one test photo on purpose.

@@ 200-203
**`hand_near_face`** — a hand next to the face in at least two photos: someone may be holding a phone or a photo up to the camera. As the comment says, one photo alone could be a passing gesture, or a false find. (The API records this sign but doesn't yet let it decide: in the owner's tests the hand detector missed the holding hands and once saw one that wasn't there.)

@@ 204
Return the signs.
