---
fingerprint: 1155ea50d88314b8
---
The **contracts** for a face attempt — the exact shape of every message the API and the inference service exchange about it. Both services import these classes, so they cannot disagree about a field's name, type or allowed range. And because the models contain only numbers, flags and short texts, **no image can ever travel inside them** (§1.11).

The classes are **Pydantic models** (§4.8). You declare fields with types and limits, and Pydantic **checks every value** when a model is created, or when it is read from JSON. Wrong or missing data is rejected with a precise error message, before any of our own code sees it.

@@ 1-4
The module docstring. Its second paragraph states the privacy property of this file as a rule.

@@ 6
`from __future__ import annotations` — the project-wide type-hint setting.

@@ 8
`Annotated` lets a type carry extra information. `Annotated[float, Field(ge=0.0)]` means "a float, *and* it must be ≥ 0". Python ignores the extra part; Pydantic reads it and enforces it.

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

@@ 18-19
**`Contract`** — a shared base class with two strict settings that every model below inherits:

- `extra="forbid"` — an unknown field (for example, a misspelled `usable_frame`) is an **error**, not silently ignored. A sender's typo is caught at the boundary instead of turning into a mysterious missing value.
- `frozen=True` — once created, a model can't be changed. A message is a fact that was received, and nobody should quietly edit it later.

@@ 22-25
**`FrameMeta` — facts about one captured frame:**

- `index` — the frame's position in the burst, from 0 to 31;
- `t_ms` — when it was captured, in milliseconds since the capture started (never negative);
- `phase` — which part of the capture it belongs to (`"baseline"` by default; Phase 3 adds pose phases). At most 32 characters, so nobody can smuggle a large blob of data into a text field.

@@ 28-29
**`FaceRequestMeta`** — the description that travels *alongside* the frames: a list of 1 to `MAX_FRAMES` (16) `FrameMeta`. The limits are part of the type, so an empty burst — or a flood of frames — is rejected before any work is done.

@@ 32-40
**`FrameReport` — what the inference service found in one frame:**

- `faces` — how many faces it detected;
- `detector_score` — how confident the face detector was;
- `brightness` (0–1), `sharpness` and `eye_distance_px` — the quality measurements (see `quality.py`);
- `yaw_ratio` — how far the head is turned;
- `flags` — the names of every problem found, such as `too_dark`. An empty list means a good frame.

@@ 42-44
`usable` — a convenience: a frame is usable exactly when it has no flags. It is a `@property`, so it is computed from `flags` and can never disagree with them.

@@ 47-51
**`AgeEstimate` — the combined age result for the whole burst:**

- `mean` — the expected age (0–100);
- `std` — the **standard deviation**: how spread out the estimate is. Small means confident; large means unsure;
- `p_over` — for each age in `POLICY_AGES`, the probability that the person is at least that old. In JSON, keys are always text (`"18"`), and Pydantic converts them back to numbers on arrival;
- `frame_means` — each frame's own expected age, so the API can check whether the frames agree.

@@ 54-59
**`FaceAnalysis` — the inference service's complete answer:**

- `model_version` — which age model produced it. It is recorded with the decision (auditability, Stage 4 §8);
- `frames` — one report per frame;
- `usable_frames` — how many passed every quality check;
- `age` — an `AgeEstimate`, or `None` when no frame was usable. `X | None` is how Python writes "X or nothing";
- `duration_ms` — how long the analysis took, for performance monitoring.
