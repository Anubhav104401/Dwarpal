---
fingerprint: dc8c2fc64739c88e
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

@@ 9-11
OpenCV (`cv2`, for converting to greyscale), NumPy, and NumPy's array type for annotations.

@@ 13
The contracts this file reads and produces.

@@ 14
`Image` — the project's type for a picture: a NumPy array of pixels.

@@ 16-21
The comment explains the limits below, which were **set from the owner's genuine attempts** (§5.3.6), and how the head is measured: from the detector's five landmarks (`quality.py`), a turned head moves the nose sideways against the eyes; a raised one moves the nose towards the eyes. Each pose is measured against the person's **own** frontal angles, so camera height and face shape cancel out.

The measurements behind the numbers: every genuine turn moved the nose 0.23–0.69 eye-widths. A chin lifted until the page's meter was full moved it anywhere from −0.03 to 0.12 — five landmarks can't measure looking up reliably. So looking up is recorded, but never decides, and the turns carry the proof. A flat photo, turned or tilted, moves neither.

@@ 22
`FRONTAL_YAW = 0.2` — a baseline frame must be facing the camera: sideways turn no more than 0.2 either way.

@@ 23
`TURN_SHIFT = 0.18` — a turn counts once the nose has moved 0.18 eye-widths sideways from where it was facing the camera: about 18 degrees. The lowest genuine turn measured was 0.23.

@@ 24
`RAISE_SHIFT = 0.03` — the look-up limit, kept so that the report can say how often it was reached.

@@ 25
`DECIDING` — the poses whose failure fails the check: the two turns. A **frozenset** is a set that can't be changed; the annotation `frozenset[Pose]` says it holds poses.

@@ 26
`MIN_BASELINE = 3` — at least three frontal frames are needed.

@@ 27-28
`STILL_FRAMES = 0.75` — as the comment says, two frames from a live camera are never quite the same: even with a perfectly still person, the sensor adds a little **noise**. If every pair of frames differs by less than 0.75 grey levels on average (out of 255), they were probably copies of one picture.

@@ 29-32
Where to sample on the 224 × 224 aligned face (`align_face` puts every face in the same place). Each `slice(a, b)` is a range of rows or columns.

- `SKIN` — three small patches: the right cheek, the left cheek and the forehead;
- `BACKGROUND` — the two top corners, which are beyond the head and hair.

@@ 35-41
**`Seen`** — one frame as the checks see it: its description from the browser (`meta`, with its phase label and time), the inference service's report on it (`report`), and its aligned face, or `None` if the frame had a quality problem. `frozen=True` — it can't be changed after it's made.

@@ 44
`Angles` — a name for a pair of numbers: yaw, then pitch.

@@ 47
**`frontal_angles`** — the person's own angles when facing the camera, from the baseline frames.

@@ 48
The docstring: the **median** over the baseline frames with exactly one face. The median — the middle value — isn't dragged away by one odd frame.

@@ 49
The reports of the baseline frames that show one face.

@@ 50-51
None: there is nothing to measure from.

@@ 52
The median sideways ratio and the median up-down ratio, as a pair.

@@ 55-56
**`shift`** — how far a frame has moved from the frontal angles **in the pose's direction**, as the docstring says. A negative answer means it moved the other way.

@@ 57
Unpack the frontal yaw and pitch.

@@ 58-59
Turning to the left raises the sideways ratio (in an unmirrored picture, the nose moves towards the right of the picture): the shift is how much it rose.

@@ 60-61
Turning to the right lowers it: the shift is how much it fell.

@@ 62
Otherwise the pose is `look_up`, which lowers the up-down ratio: the shift is how much it fell.

@@ 65
**`shows`** — does this frame show the pose?

@@ 66-67
Only with exactly one person in the picture.

@@ 68
Then: has it moved at least the limit — `RAISE_SHIFT` for looking up, `TURN_SHIFT` for a turn?

@@ 71
**`segments`** — split the frames, in time order, into **runs** of the same phase. Labels baseline, baseline, turn_left, look_up give three runs: two baseline frames, one turn_left, one look_up.

@@ 72
The runs so far: each a pair of (phase, its frames).

@@ 73-75
For each frame: if it has the same phase as the last run, add it to that run …

@@ 76-77
… otherwise start a new run.

@@ 78
Return the runs.

@@ 81
**`pose_check`** — check the frames against the challenge. With `trust_labels` (the test mode), the labels are believed, and the head measurements are skipped.

@@ 82
Put the frames in time order, by `t_ms`.

@@ 83
The problems found, as short names. An empty list at the end means it passed.

@@ 84-85
**`timing`** — the frames' numbers must run in the same order as their times. Frame 3 can't have been taken before frame 2: if it was, the description was tampered with.

@@ 86-87
Split into runs, and collect every baseline frame. (The double `for` reads left to right: for each run that is a baseline run, for each of its frames.)

@@ 88-89
**`baseline_missing`** — fewer than three baseline frames.

@@ 90-93
**`baseline_not_frontal`** — measured from the images (not in the test mode): every baseline frame must show exactly one face, facing the camera. A frontal start is what makes the turns that follow meaningful; it also stops an attacker from sending only turned pictures.

@@ 94-95
**`baseline_not_first`** — the attempt must *start* with the baseline.

@@ 96
The person's frontal angles, from the baseline frames — or `None`.

@@ 97
`reached` — the list of (pose, how far it got) pairs, filled below.

@@ 98
The pose runs: every run that isn't baseline, in order.

@@ 99-100
**`wrong_order`** — the pose runs' labels must be exactly the challenge's poses, in its order, with nothing extra. `list(…)` because the challenge's poses and the labels must be compared as lists of the same kind.

@@ 101-102
If the order is right — and not in the test mode — go through the challenge's poses together with their runs. `zip(…, strict=True)` pairs them, and would fail loudly if the two lists had different lengths — which the order check has just ruled out.

@@ 103
The run's frames with exactly one person in them.

@@ 104
The **furthest** any of them moved in the pose's direction (`max`), or `None` when there is no frontal reference or no face. `default=None` is what `max` returns for an empty list.

@@ 105
Record it, rounded to three decimals.

@@ 106
Did the pose go unseen — no reference, or no frame that shows it?

@@ 107-108
Only a **turn** that went unseen is a problem: `not_shown:` and the pose's name, such as `not_shown:turn_left`. A look-up that went unseen is only recorded, in `reached`.

@@ 109-115
The result: passed if there were no problems, with the list either way, the frontal angles (rounded) and how far each pose got.

@@ 118
**`chromaticity`** — the colour of some patches of a picture, **without its brightness**. Brightness changes for many reasons (the person moves, the camera adjusts itself); the *balance* of red, green and blue is what the screen's colour changes.

@@ 119
Take every patch's pixels, lay them out as one long list of (blue, green, red) values (`reshape(-1, 3)`: −1 means "as many rows as needed"), join the patches together, and switch to decimals.

@@ 120
The average of each colour. OpenCV stores pixels as **B**lue, **G**reen, **R**ed — in that order.

@@ 121-122
Divide by the total, so only the balance remains: the share of red and the share of blue. (The share of green is whatever is left, so it adds nothing.) `max(…, 1.0)` avoids dividing by zero on a black patch.

@@ 125
**`emitted`** — the same two shares for a colour the screen showed, from its web code.

@@ 126
Read the code's three pairs of hexadecimal digits — characters 1–2, 3–4 and 5–6 of `#3c78ff` — as numbers from 0 to 255. `int(…, 16)` reads a number written in base 16.

@@ 127-128
The shares of red and blue, as for the skin.

@@ 131
**`correlation`** — how closely the measured colours followed the shown ones, from −1 to +1. This is **Pearson's correlation**: +1 means they rose and fell exactly together, 0 means no relation.

@@ 132-133
Subtract each list's average, so only the *changes* remain.

@@ 134
The size of each list of changes — `np.linalg.norm` is the length of the whole list taken as one long arrow — multiplied together.

@@ 135
Correlation is the sum of the changes multiplied together, divided by that product. If either list never changed at all (`spread` is 0), there is nothing to compare: `None`. `np.clip` guards against rounding taking it a hair past ±1.

@@ 138-140
**`light_check`** — did the skin follow the screen's colours? It needs the frames, the challenge (for its colours and timing), when the colours started, and the browser's signals.

@@ 141-142
No colours were shown — calm mode, or an older page: nothing to measure. `usable=False`, which never counts against anyone.

@@ 143
Three lists: the skin's colour in each frame, the background's, and what the screen showed.

@@ 144-145
For each frame, work out **which colour was on screen** when it was taken: the time since the colours started, divided by the step length, rounded down (`//`).

@@ 146-147
Skip frames that aren't baseline frames, that have no usable face, or that fall outside the colours' time.

@@ 148-150
Measure the skin and the background, and note the colour shown.

@@ 151-152
At least three measured frames are needed, under at least two *different* colours (`{…}` makes a set, which keeps each colour once). Otherwise: not usable.

@@ 153
The result: how well the skin followed the screen, and how well the background did. A real face close to the screen should follow it clearly; the background, further away, much less. A photo or a screen held up to the camera tends to behave differently — but how differently, in real rooms, is what the owner's tests will measure.

@@ 156
**`injection_signs`** — signs that the pictures didn't come from a live camera.

@@ 157
The signs found.

@@ 158-163
The browser's own reports: a program driving the browser (`automation`), a virtual camera (`virtual_camera`), and the page being hidden during the check (`page_hidden`). These come from the browser and can be faked — but only an honest browser reports them, and then they are worth knowing.

@@ 164
The usable faces, in time order.

@@ 165
Each converted to greyscale, as decimals.

@@ 166
How much each frame differs from the next: the average difference between their pixels.

@@ 167-168
**`identical_frames`** — if there are at least two such differences and even the largest is below 0.75 grey levels, the frames are near-copies: one picture sent several times, as a fake camera might. Not in the test mode, where the frames are copies of one test photo on purpose.

@@ 169
Return the signs.
