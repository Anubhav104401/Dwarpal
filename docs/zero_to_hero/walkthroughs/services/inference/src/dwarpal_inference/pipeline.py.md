---
fingerprint: a5bd4edcaa7595cd
---
The **face pipeline**: from a burst of frames to one `FaceAnalysis`. For every frame it:

1. decodes the bytes;
2. finds faces;
3. checks quality;
4. aligns the good faces.

Then it estimates age for all good faces at once and combines them, giving sharper, more confident frames more weight (Stage 3 §5.2).

@@ 1-2
The docstring lists the pipeline's steps in order — Phase 3 adds the last one, gathering the liveness evidence.

@@ 4
The project-wide type-hint setting.

@@ 6
`time`, to measure how long the analysis takes.

@@ 8
NumPy.

@@ 10-18
The contracts this pipeline produces — including `Liveness` (Phase 3) — plus the shared frame-size limit `MAX_FRAME_BYTES`.

@@ 19
The age-model interface and the 0–100 age scale.

@@ 20
The liveness checks (Phase 3, `liveness.py`): `Seen` — what was seen in one frame — and the three checks that read them.

@@ 21-30
Everything from the shared vision package. The same code is used in training (ADR on train/serve skew, §5.0.2).

@@ 33-39
**`FacePipeline`** keeps its parts: the detector, the age model and the quality rules. They are *given* to it rather than created inside it. That way tests can hand it a stand-in model, or different rules, without changing this code. This style is called **dependency injection**.

The fourth, `trust_labels` (Phase 3), switches on the test mode in which liveness believes the frames' phase labels. It is off unless the service's settings turn it on — and they refuse to without the stand-in age model.

@@ 40
Keep the `trust_labels` choice.

@@ 42
**`analyze`** — one burst in, one analysis out.

@@ 43
Start the stopwatch. `perf_counter` is Python's most precise clock for measuring durations.

@@ 44-46
Three lists to fill: one report per frame, the aligned good faces, and a weight for each good face.

@@ 47
`seen` (Phase 3) — one `Seen` record per frame, collected for the liveness checks: the frame's description, its report, and its aligned face (if any).

@@ 48
Walk through the frames and their bytes together. `strict=True` raises an error if the two lists differ in length, so a missing frame can never silently shift the others out of line.

@@ 49-65
**A frame that can't be decoded doesn't stop the others.** The decoder is given the contract's size limit (`max_bytes=MAX_FRAME_BYTES`), so the limit is defined in exactly one place. Its report carries the single flag `undecodable` and zeros everywhere else. It is also recorded in `seen`, with no face (`reports[-1]` is the report just added: index −1 means "the last one"). `continue` moves on to the next frame.

@@ 66-67
Find the faces, then check the frame's quality.

@@ 68-80
Record the frame's report, copying every quality measurement into the contract — including the head's tilt, `pitch_ratio` (Phase 3).

@@ 81-85
**Only good frames count** for the age. Align the main face — or `None` if the frame had problems — and record what was seen, for liveness. A good frame's face also goes into the age list, with a weight: the detector's confidence times sharpness (capped at 1 from a sharpness of 200 upwards). Clearer frames have more say.

Why does liveness get *every* frame, not only the good ones? A turned head can trip quality flags such as `not_frontal` — which is exactly what a pose frame should do.

@@ 86
Estimate age if at least one frame was good; otherwise there is no estimate (`None`). The decision engine turns that into a *retry*, never a guess.

@@ 87-88
Short names for the challenge the frames are checked against (the server's stored copy; see `verification.py`) and for the test-mode switch.

@@ 89-90
**Build the liveness result.** The pose check runs if there is a challenge to check against; otherwise `None`.

@@ 91-93
The light check runs only with a challenge **and** with real images: in the labels test mode the frames come from a still portrait, so measuring the light would mean nothing. The `… if … else None` here spans three lines; the brackets of the call allow that.

@@ 94
The injection signs are always looked for.

@@ 95-96
Say where the pose result came from: `labels` in the test mode, `images` otherwise. The API refuses `labels` for a live session.

@@ 97
Stop the stopwatch, in milliseconds.

@@ 98-105
Assemble the answer: the model version, the frame reports, the count of good frames, the age estimate, the duration — and the liveness result (Phase 3).

@@ 107
**`estimate`** — combine the good faces into one age estimate.

@@ 108
Ask the model for one 101-probability row per face, all in one batch, which is faster than one at a time.

@@ 109-110
Turn the weights into **shares** that add up to 1. If every weight were zero, fall back to equal shares instead of dividing by zero.

@@ 111
**The mixture**: a weighted average of the rows. `share[:, None]` turns the shares into a column, so each row is multiplied by its own share; then the rows are added up. The result is still a proper distribution over ages 0–100.

@@ 112
The **expected age**: each age times its probability, added up.

@@ 113
The **standard deviation**: how spread out the distribution is around that expected age.

@@ 114
For each policy age N, **P(age ≥ N)** is the sum of the probabilities from age N upwards (`mixture[age:]`). It is clipped into 0–1 to absorb tiny rounding errors, because the contract insists on that range.

@@ 115
Each frame's own expected age, so the API can check that the frames agree with each other.

@@ 116
Return the combined estimate.
