---
fingerprint: ab4f0a1a1362771a
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

@@ 21-34
Everything from the shared vision package — now including the face mesh, the hand detector, the anti-spoofing detector and the screen-pattern measure. The same code is used in training (ADR on train/serve skew, §5.0.2).

@@ 35
`near_face` — how many hands are next to the face.

@@ 38-40
**`sharpest`** (Phase 7, decision P1, §5.7.4) — the positions of the `count` frames with the highest weights, best first. `sorted(range(n), key=…)` sorts the positions by their weight, highest first (`-weights[i]`); Python's sort is *stable*, so frames with equal weights keep their order.

@@ 43-45
**`median_of`** — the median of some measurements, skipping the missing ones (`None`), or `None` if none were measured. Used for the attempt's presentation evidence below.

@@ 48-62
**`FacePipeline`** keeps its parts: the detector, the age model, the quality rules, and — since the owner's tests — the face mesh, the hand detector and the anti-spoofing detector, each optional. They are *given* to it rather than created inside it. That way tests can hand it a stand-in model, or leave a part out, without changing this code. This style is called **dependency injection**.

`trust_labels` (Phase 3) switches on the test mode in which liveness believes the frames' phase labels. It is off unless the service's settings turn it on — and they refuse to without the stand-in age model.

`age_frames` (Phase 7) — how many flawless frames the age model sees: 3 unless the settings say otherwise.

@@ 63-65
Keep the three optional measuring parts.

@@ 66
Keep the `trust_labels` choice.

@@ 67
And how many frames the age model sees.

@@ 69
**`analyze`** — one burst in, one analysis out.

@@ 70
Start the stopwatch. `perf_counter` is Python's most precise clock for measuring durations.

@@ 71-73
Three lists to fill: one report per frame, the aligned good faces, and a weight for each good face.

@@ 74
`seen` (Phase 3) — one `Seen` record per frame, collected for the liveness checks: the frame's description, its report, and its aligned face (if any).

@@ 75
Walk through the frames and their bytes together. `strict=True` raises an error if the two lists differ in length, so a missing frame can never silently shift the others out of line.

@@ 76-92
**A frame that can't be decoded doesn't stop the others.** The decoder is given the contract's size limit (`max_bytes=MAX_FRAME_BYTES`), so the limit is defined in exactly one place. Its report carries the single flag `undecodable` and zeros everywhere else. It is also recorded in `seen`, with no face (`reports[-1]` is the report just added: index −1 means "the last one"). `continue` moves on to the next frame.

@@ 93-94
Find the faces, then check the frame's quality.

@@ 95
The head's angles from the face mesh, for the main face — when there is a mesh and a face.

@@ 96
How many hands are next to the main face — when there is a hand detector and a face.

@@ 97-99
For a photo of exactly one person: the anti-spoofing networks' real-face chance (when they are loaded) and the screen-pattern measure. With nobody or several people, these would describe the wrong face, so they are left empty.

@@ 100-117
Record the frame's report, copying every measurement into the contract: the quality measurements, the head's angles from the five points and from the mesh, the hands, and the presentation evidence.

@@ 118-124
The comment explains a change made during the owner's tests. Liveness now looks at **every** photo of exactly one person: a turned head, or a face darkened by the screen's blue, is exactly what its checks expect — it was these photos, set aside for their quality flags, that left the light check with nothing to measure. The **age** is still estimated from flawless photos only: align the face and weight it by the detector's confidence times sharpness (capped at 1 from a sharpness of 200 upwards).

@@ 125-128
**Estimate the age** — from the 3 sharpest flawless frames only. The age model takes about half a second per frame on one CPU core, nearly all of an attempt's time, so 8 frames took 4.5 seconds (§5.7.3). Every flawless frame still counts as *usable* (the decision needs enough of them), and liveness has already seen every frame. With no good frame at all, there is no estimate (`None`), and the decision engine turns that into a *retry*, never a guess.

@@ 129-130
Short names for the challenge the frames are checked against (the server's stored copy; see `verification.py`) and for the test-mode switch.

@@ 131-132
**Build the liveness result.** The pose check runs if there is a challenge to check against; otherwise `None`.

@@ 133-135
The light check runs only with a challenge **and** with real images: in the labels test mode the frames come from a still portrait, so measuring the light would mean nothing. The `… if … else None` here spans three lines; the brackets of the call allow that.

@@ 136
The injection signs are always looked for.

@@ 137-138
The attempt's presentation evidence: the median real-face chance and the median screen pattern over its photos — empty in the labels test mode, whose still portrait would make them meaningless.

@@ 139-140
Say where the pose result came from: `labels` in the test mode, `images` otherwise. The API refuses `labels` for a live session.

@@ 141
Stop the stopwatch, in milliseconds.

@@ 142-149
Assemble the answer: the model version, the frame reports, the count of good frames, the age estimate, the duration — and the liveness result (Phase 3).

@@ 151
**`estimate`** — combine the good faces into one age estimate.

@@ 152
Ask the model for one 101-probability row per face, all in one batch, which is faster than one at a time.

@@ 153-154
Turn the weights into **shares** that add up to 1. If every weight were zero, fall back to equal shares instead of dividing by zero.

@@ 155
**The mixture**: a weighted average of the rows. `share[:, None]` turns the shares into a column, so each row is multiplied by its own share; then the rows are added up. The result is still a proper distribution over ages 0–100.

@@ 156
The **expected age**: each age times its probability, added up.

@@ 157
The **standard deviation**: how spread out the distribution is around that expected age.

@@ 158
For each policy age N, **P(age ≥ N)** is the sum of the probabilities from age N upwards (`mixture[age:]`). It is clipped into 0–1 to absorb tiny rounding errors, because the contract insists on that range.

@@ 159
Each frame's own expected age, so the API can check that the frames agree with each other.

@@ 160
Return the combined estimate.
