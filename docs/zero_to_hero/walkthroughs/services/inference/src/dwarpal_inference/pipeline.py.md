---
fingerprint: 58ae8c3efcb8153f
---
The **face pipeline**: from a burst of frames to one `FaceAnalysis`. For every frame it:

1. decodes the bytes;
2. finds faces;
3. checks quality;
4. aligns the good faces.

Then it estimates age for all good faces at once and combines them, giving sharper, more confident frames more weight (Stage 3 §5.2).

@@ 1
The docstring lists the pipeline's steps in order.

@@ 3
The project-wide type-hint setting.

@@ 5
`time`, to measure how long the analysis takes.

@@ 7
NumPy.

@@ 9
The contracts this pipeline produces, plus the shared frame-size limit `MAX_FRAME_BYTES`.

@@ 10
The age-model interface and the 0–100 age scale.

@@ 11-20
Everything from the shared vision package. The same code is used in training (ADR on train/serve skew, §5.0.2).

@@ 23-27
**`FacePipeline`** keeps its three parts: the detector, the age model and the quality rules. They are *given* to it rather than created inside it. That way tests can hand it a stand-in model, or different rules, without changing this code. This style is called **dependency injection**.

@@ 29
**`analyze`** — one burst in, one analysis out.

@@ 30
Start the stopwatch. `perf_counter` is Python's most precise clock for measuring durations.

@@ 31-33
Three lists to fill: one report per frame, the aligned good faces, and a weight for each good face.

@@ 34
Walk through the frames and their bytes together. `strict=True` raises an error if the two lists differ in length, so a missing frame can never silently shift the others out of line.

@@ 35-50
**A frame that can't be decoded doesn't stop the others.** The decoder is given the contract's size limit (`max_bytes=MAX_FRAME_BYTES`), so the limit is defined in exactly one place. Its report carries the single flag `undecodable` and zeros everywhere else. `continue` moves on to the next frame.

@@ 51-52
Find the faces, then check the frame's quality.

@@ 53-64
Record the frame's report, copying every quality measurement into the contract.

@@ 65-67
**Only good frames count.** Align the main face and give it a weight: the detector's confidence times sharpness (capped at 1 from a sharpness of 200 upwards). Clearer frames have more say.

@@ 68
Estimate age if at least one frame was good; otherwise there is no estimate (`None`). The decision engine turns that into a *retry*, never a guess.

@@ 69
Stop the stopwatch, in milliseconds.

@@ 70-72
Assemble the answer: the model version, the frame reports, the count of good frames, the age estimate and the duration.

@@ 74
**`estimate`** — combine the good faces into one age estimate.

@@ 75
Ask the model for one 101-probability row per face, all in one batch, which is faster than one at a time.

@@ 76-77
Turn the weights into **shares** that add up to 1. If every weight were zero, fall back to equal shares instead of dividing by zero.

@@ 78
**The mixture**: a weighted average of the rows. `share[:, None]` turns the shares into a column, so each row is multiplied by its own share; then the rows are added up. The result is still a proper distribution over ages 0–100.

@@ 79
The **expected age**: each age times its probability, added up.

@@ 80
The **standard deviation**: how spread out the distribution is around that expected age.

@@ 81
For each policy age N, **P(age ≥ N)** is the sum of the probabilities from age N upwards (`mixture[age:]`). It is clipped into 0–1 to absorb tiny rounding errors, because the contract insists on that range.

@@ 82
Each frame's own expected age, so the API can check that the frames agree with each other.

@@ 83
Return the combined estimate.
