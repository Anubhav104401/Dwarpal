---
fingerprint: e094acb96f82ccd2
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

@@ 16-17
The comment is honest about the limits below: **provisional**, to be set from genuine attempts. It also recalls how the head is measured, from the detector's five landmarks (`quality.py`): a turned head moves the nose sideways against the eyes; a raised one moves the nose towards the eyes.

@@ 18
`FRONTAL_YAW = 0.2` — a baseline frame must be facing the camera: sideways turn no more than 0.2 either way.

@@ 19
`TURNED_YAW = 0.35` — a turn counts from 0.35 on. A genuine turn of the head easily goes past 0.5.

@@ 20
`RAISED_PITCH = 0.38` — a raised head: the nose's position between eyes and mouth falls to 0.38 or less, from about 0.5 looking straight ahead.

@@ 21
`MIN_BASELINE = 3` — at least three frontal frames are needed.

@@ 22-23
`STILL_FRAMES = 0.75` — as the comment says, two frames from a live camera are never quite the same: even with a perfectly still person, the sensor adds a little **noise**. If every pair of frames differs by less than 0.75 grey levels on average (out of 255), they were probably copies of one picture.

@@ 24-27
Where to sample on the 224 × 224 aligned face (`align_face` puts every face in the same place). Each `slice(a, b)` is a range of rows or columns.

- `SKIN` — three small patches: the right cheek, the left cheek and the forehead;
- `BACKGROUND` — the two top corners, which are beyond the head and hair.

@@ 30-36
**`Seen`** — one frame as the checks see it: its description from the browser (`meta`, with its phase label and time), the inference service's report on it (`report`), and its aligned face, or `None` if the frame had a quality problem. `frozen=True` — it can't be changed after it's made.

@@ 39
**`shows`** — does this frame's report show the head in the given pose?

@@ 40-41
Only with exactly one face. No face, or two, shows nothing.

@@ 42-43
Turned to the left: sideways ratio at least 0.35. (In an unmirrored picture, a person turning to their left moves their nose towards the right of the picture: a positive ratio.)

@@ 44-45
Turned to the right: at most −0.35.

@@ 46
Otherwise the pose is `look_up`: the up-down ratio at most 0.38.

@@ 49
**`segments`** — split the frames, in time order, into **runs** of the same phase. Labels baseline, baseline, turn_left, look_up give three runs: two baseline frames, one turn_left, one look_up.

@@ 50
The runs so far: each a pair of (phase, its frames).

@@ 51-53
For each frame: if it has the same phase as the last run, add it to that run …

@@ 54-55
… otherwise start a new run.

@@ 56
Return the runs.

@@ 59
**`pose_check`** — check the frames against the challenge. With `trust_labels` (the test mode), the labels are believed, and the head measurements are skipped.

@@ 60
Put the frames in time order, by `t_ms`.

@@ 61
The problems found, as short names. An empty list at the end means it passed.

@@ 62-63
**`timing`** — the frames' numbers must run in the same order as their times. Frame 3 can't have been taken before frame 2: if it was, the description was tampered with.

@@ 64-65
Split into runs, and collect every baseline frame. (The double `for` reads left to right: for each run that is a baseline run, for each of its frames.)

@@ 66-67
**`baseline_missing`** — fewer than three baseline frames.

@@ 68-71
**`baseline_not_frontal`** — measured from the images (not in the test mode): every baseline frame must show exactly one face, facing the camera. A frontal start is what makes the turns that follow meaningful; it also stops an attacker from sending only turned pictures.

@@ 72-73
**`baseline_not_first`** — the attempt must *start* with the baseline.

@@ 74
The pose runs: every run that isn't baseline, in order.

@@ 75-76
**`wrong_order`** — the pose runs' labels must be exactly the challenge's poses, in its order, with nothing extra. `list(…)` because the challenge's poses and the labels must be compared as lists of the same kind.

@@ 77-80
If the order is right — and not in the test mode — check each pose run against its pose: at least one of its frames must really **show** the pose (`any`). Otherwise the problem is `not_shown:` and the pose's name, such as `not_shown:turn_left`. `zip(…, strict=True)` pairs each pose with its run, and would fail loudly if the two lists had different lengths — which the order check has just ruled out.

@@ 81
The result: passed if there were no problems, with the list either way.

@@ 84
**`chromaticity`** — the colour of some patches of a picture, **without its brightness**. Brightness changes for many reasons (the person moves, the camera adjusts itself); the *balance* of red, green and blue is what the screen's colour changes.

@@ 85
Take every patch's pixels, lay them out as one long list of (blue, green, red) values (`reshape(-1, 3)`: −1 means "as many rows as needed"), join the patches together, and switch to decimals.

@@ 86
The average of each colour. OpenCV stores pixels as **B**lue, **G**reen, **R**ed — in that order.

@@ 87-88
Divide by the total, so only the balance remains: the share of red and the share of blue. (The share of green is whatever is left, so it adds nothing.) `max(…, 1.0)` avoids dividing by zero on a black patch.

@@ 91
**`emitted`** — the same two shares for a colour the screen showed, from its web code.

@@ 92
Read the code's three pairs of hexadecimal digits — characters 1–2, 3–4 and 5–6 of `#3c78ff` — as numbers from 0 to 255. `int(…, 16)` reads a number written in base 16.

@@ 93-94
The shares of red and blue, as for the skin.

@@ 97
**`correlation`** — how closely the measured colours followed the shown ones, from −1 to +1. This is **Pearson's correlation**: +1 means they rose and fell exactly together, 0 means no relation.

@@ 98-99
Subtract each list's average, so only the *changes* remain.

@@ 100
The size of each list of changes — `np.linalg.norm` is the length of the whole list taken as one long arrow — multiplied together.

@@ 101
Correlation is the sum of the changes multiplied together, divided by that product. If either list never changed at all (`spread` is 0), there is nothing to compare: `None`. `np.clip` guards against rounding taking it a hair past ±1.

@@ 104-106
**`light_check`** — did the skin follow the screen's colours? It needs the frames, the challenge (for its colours and timing), when the colours started, and the browser's signals.

@@ 107-108
No colours were shown — calm mode, or an older page: nothing to measure. `usable=False`, which never counts against anyone.

@@ 109
Three lists: the skin's colour in each frame, the background's, and what the screen showed.

@@ 110-111
For each frame, work out **which colour was on screen** when it was taken: the time since the colours started, divided by the step length, rounded down (`//`).

@@ 112-113
Skip frames that aren't baseline frames, that have no usable face, or that fall outside the colours' time.

@@ 114-116
Measure the skin and the background, and note the colour shown.

@@ 117-118
At least three measured frames are needed, under at least two *different* colours (`{…}` makes a set, which keeps each colour once). Otherwise: not usable.

@@ 119
The result: how well the skin followed the screen, and how well the background did. A real face close to the screen should follow it clearly; the background, further away, much less. A photo or a screen held up to the camera tends to behave differently — but how differently, in real rooms, is what the owner's tests will measure.

@@ 122
**`injection_signs`** — signs that the pictures didn't come from a live camera.

@@ 123
The signs found.

@@ 124-129
The browser's own reports: a program driving the browser (`automation`), a virtual camera (`virtual_camera`), and the page being hidden during the check (`page_hidden`). These come from the browser and can be faked — but only an honest browser reports them, and then they are worth knowing.

@@ 130
The usable faces, in time order.

@@ 131
Each converted to greyscale, as decimals.

@@ 132
How much each frame differs from the next: the average difference between their pixels.

@@ 133-134
**`identical_frames`** — if there are at least two such differences and even the largest is below 0.75 grey levels, the frames are near-copies: one picture sent several times, as a fake camera might. Not in the test mode, where the frames are copies of one test photo on purpose.

@@ 135
Return the signs.
