---
fingerprint: f078dac3c457700b
---
The **contracts** for a face attempt — the exact shape of every message the API and the inference service exchange about it. Both services import these classes, so they cannot disagree about a field's name, type or allowed range. And because the models contain only numbers, flags and short texts, **no image can ever travel inside them** (§1.11).

The classes are **Pydantic models** (§4.8). You declare fields with types and limits, and Pydantic **checks every value** when a model is created, or when it is read from JSON. Wrong or missing data is rejected with a precise error message, before any of our own code sees it.

@@ 1-4
The module docstring. Its second paragraph states the privacy property of this file as a rule.

@@ 6
`from __future__ import annotations` — the project-wide type-hint setting.

@@ 8
`Annotated` lets a type carry extra information. `Annotated[float, Field(ge=0.0)]` means "a float, *and* it must be ≥ 0". Python ignores the extra part; Pydantic reads it and enforces it. `Literal` (added in Phase 3) names the exact values allowed: `Literal["a", "b"]` accepts the text `"a"` or `"b"` and nothing else.

@@ 10
The three Pydantic tools used here:

- `BaseModel` — the base class of every model;
- `ConfigDict` — model-wide settings;
- `Field` — limits for one field.

@@ 12
`Probability` — a reusable **type alias**: a float between 0 and 1 inclusive (`ge` = greater-or-equal, `le` = less-or-equal). Every probability field uses it, so the rule is written once.

@@ 13
`POLICY_AGES = (13, 16, 18, 21, 25)` — the ages for which the system reports "probability the person is at least this old":

- 13, 16, 18 and 21 are the legal limits of §1.2;
- 25 is the classic Challenge-25 buffer (§1.8), kept for comparison and analytics.

It is a **tuple** (round brackets), so nobody can change it while the program runs.

@@ 14-15
The two **size limits** for one face attempt, added in Phase 1:

- `MAX_FRAMES = 16` — at most 16 pictures in one burst;
- `MAX_FRAME_BYTES = 512 * 1024` — at most 512 **KiB** per picture (1 KiB = 1,024 bytes). A 640 × 480 camera frame saved as a JPEG is usually 30–80 KiB, so the limit leaves plenty of room for honest cameras. At the same time, one attempt can never be bigger than 16 × 512 KiB = 8 MiB.

Why do these live in the *contracts* package? Two programs must enforce them: the API, which receives frames from the browser, and the inference service, which receives them from the API. If each program kept its own copy, one day someone would change one copy and forget the other. Keeping a single shared value is called a **single source of truth**.

@@ 16-17
The head poses the liveness challenge can ask for (Phase 3): turn left, turn right, look up.

- `type Pose = Literal[…]` — a **type alias**: a new name for "one of these three texts". (`type X = …` is Python 3.12's way of writing an alias.)
- `POSES` — the same three as a tuple, for code that needs to pick from them, such as the server choosing a random challenge. The type annotation `tuple[Pose, ...]` ("a tuple of any length, of `Pose` values") lets the type checker confirm the two lists agree.

@@ 18
`Phase` — which part of the capture a frame belongs to: the opening **baseline** (looking straight at the camera), or one of the three poses.

@@ 19
`Colour` — a screen colour as the web writes it: `#` followed by exactly six hexadecimal digits (`0`–`9`, `a`–`f`), such as `#3c78ff`. The `pattern` is a **regular expression**: `^` and `$` pin it to the whole text, `[0-9a-f]` is one digit, `{6}` means six of them. Anything else — a colour name, or a long piece of text — is refused.

@@ 22-23
**`Contract`** — a shared base class with two strict settings that every model below inherits:

- `extra="forbid"` — an unknown field (for example, a misspelled `usable_frame`) is an **error**, not silently ignored. A sender's typo is caught at the boundary instead of turning into a mysterious missing value.
- `frozen=True` — once created, a model can't be changed. A message is a fact that was received, and nobody should quietly edit it later.

@@ 26-29
**`FrameMeta` — facts about one captured frame:**

- `index` — the frame's position in the burst, from 0 to 31;
- `t_ms` — when it was captured, in milliseconds since the capture started (never negative);
- `phase` — which part of the capture it belongs to, `"baseline"` unless said otherwise. Because its type is `Phase`, only the four known names are accepted.

@@ 32-37
**`Challenge` — what the server asked the person to do** (Phase 3). It is created by the API at random, stored, and handed to the inference service with the frames, so the frames can be checked against it:

- `poses` — 1 to 4 head poses, in order;
- `colours` — 2 to 8 screen colours, shown one after another;
- `step_ms` — how long each colour stays on screen: between 0.4 and 2 seconds.

@@ 40-46
**`ClientSignals` — what the browser says about itself** (Phase 3). Each field has a default, so an older page that sends none still works:

- `automation` — the browser reports that it is being driven by a program (`navigator.webdriver`);
- `virtual_camera` — the camera's name looks like virtual-camera software;
- `hidden_ms` — how long the page was hidden (another tab in front) during the capture;
- `light_shown` — whether the screen colours were actually shown (a person can ask for a calmer check without flashing).

As the docstring says, a browser controlled by an attacker can lie about all of these. They are hints that can only make a check *stricter*, never easier.

@@ 49-53
**`FaceRequestMeta`** — the description that travels *alongside* the frames: a list of 1 to `MAX_FRAMES` (16) `FrameMeta`. The limits are part of the type, so an empty burst — or a flood of frames — is rejected before any work is done.

Phase 3 added three optional fields:

- `light_started_ms` — when the colour sequence began, on the same clock as the frames' `t_ms`, so each frame can be matched to the colour on screen at that moment;
- `signals` — the browser's `ClientSignals`;
- `challenge` — the `Challenge`. The browser *cannot* set this one usefully: the API replaces it with the challenge it stored, so a page claiming an easier challenge achieves nothing.

@@ 56-74
**`FrameReport` — what the inference service found in one frame:**

- `faces` — how many people it found (a second detection counts only if it looks like a separate person; see `quality.py`);
- `detector_score` — how confident the face detector was;
- `brightness` (0–1), `sharpness` and `eye_distance_px` — the quality measurements (see `quality.py`);
- `yaw_ratio` and `pitch_ratio` — how far the head is turned sideways and tilted, from the detector's five points;
- `mesh_yaw` and `mesh_pitch` — the same two angles from the 478-point face mesh, which measures looking up far better (empty when not measured);
- `hands_near_face` — hands found next to the face, as someone holding up a phone might show;
- `real_score` — the anti-spoofing networks' chance that this is a real face rather than a photo or a screen;
- `screen_pattern` — how strongly a screen's regular pixel pattern stands out in the face;
- `flags` — the names of every problem found, such as `too_dark`. An empty list means a good frame.

@@ 76-78
`usable` — a convenience: a frame is usable exactly when it has no flags. It is a `@property`, so it is computed from `flags` and can never disagree with them.

@@ 81-85
**`AgeEstimate` — the combined age result for the whole burst:**

- `mean` — the expected age (0–100);
- `std` — the **standard deviation**: how spread out the estimate is. Small means confident; large means unsure;
- `p_over` — for each age in `POLICY_AGES`, the probability that the person is at least that old. In JSON, keys are always text (`"18"`), and Pydantic converts them back to numbers on arrival;
- `frame_means` — each frame's own expected age, so the API can check whether the frames agree.

@@ 88-90
**`PoseCheck`** (Phase 3) — the result of the head-pose challenge: whether it `passed`, and the names of the `problems` found, such as `wrong_order` (see `liveness.py`).

@@ 91-92
The comment explains the three fields that follow: **measurements**, kept so that the limits can be set from genuine attempts rather than guessed.

@@ 93-94
`baseline_yaw` and `baseline_pitch` — the person's own frontal angles, from their opening photos, or `None` if no face could be measured.

@@ 95
`reached` — for each pose asked for, in order, a pair: the pose's name and how far its best photo moved from the frontal angles in the asked direction (`None`: no face to measure). `tuple[Pose, float | None]` is a pair of a pose and a number-or-nothing; in JSON it becomes a two-item list. The default `[]` keeps older results valid.

@@ 96
`measured_by` — which measurement the pose check used: the face mesh, or the detector's five points.

@@ 97-98
`gradual` — for each pose, whether a photo caught the head *on its way* there. A real head passes through the angles in between; swiping from one photo to the next jumps straight from pose to pose.

@@ 101-106
**`LightCheck`** (Phase 3) — the result of the screen-colour check:

- `usable` — whether there was enough to measure;
- `shown` — whether the page showed the colours at all (not when the person's device asks for reduced motion);
- `r_skin` and `r_background` — how closely the colour changes seen on the face, and on the background, followed the colours shown on screen. They are **correlations**, from −1 to +1: +1 means "rose and fell exactly together", 0 means "unrelated". Each can be `None` when it couldn't be measured. In the owner's tests genuine faces ranged from −0.25 to 0.99, so the light is recorded but doesn't decide.

@@ 109-112
**`Liveness`** (Phase 3) — everything the liveness checks found, kept together:

- `pose` and `light` — the two checks above, each `None` if it couldn't run;
- `injection` — the names of any signs that the camera feed was faked or the page automated. Empty means none.

@@ 113-115
Two more pieces of evidence, each the **median** over the photos of one person: `presentation`, the anti-spoofing networks' real-face chance, and `screen_pattern`. Both empty when not measured — for example in the labels test mode.

@@ 116-118
`evidence` — where the pose result came from. `"images"` is the real thing, measured from the faces in the frames. `"labels"` is a **test mode**: the frames' own phase labels were believed. It exists because the end-to-end tests use a fake camera playing a still portrait, which can't turn its head. The comment states its two limits, which the code enforces: it needs the stand-in age model, and a live session refuses it.

@@ 121-127
**`FaceAnalysis` — the inference service's complete answer:**

- `model_version` — which age model produced it. It is recorded with the decision (auditability, Stage 4 §8);
- `frames` — one report per frame;
- `usable_frames` — how many passed every quality check;
- `age` — an `AgeEstimate`, or `None` when no frame was usable. `X | None` is how Python writes "X or nothing";
- `duration_ms` — how long the analysis took, for performance monitoring;
- `liveness` — the liveness results (Phase 3), or `None` from a service that doesn't produce them.
