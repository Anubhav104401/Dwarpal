---
fingerprint: 19bbf6b2ca000c09
---
**The frame-count check** (Phase 7, decision P1, §5.7.4): before the age model was allowed to see only 3 of an attempt's frames, this measured whether doing so changes its decisions. It simulates webcam bursts from exact-age photos and decides from the clean photo, the sharpest frame, the 3 sharpest and all 8, against the certified safety lines.

@@ 1-13
What it asks, how to run it, and why: the lines were certified on one clean photo per person, the service mixes several webcam frames, and using fewer must not weaken them. It compares choices on the **calibration split** and changes no threshold; the test split, opened once, stays closed.

@@ 15
Newer type-hint syntax on older Pythons.

@@ 17-23
Standard tools: the command line, JSON, the program's exit, reading the zip archive of faces, small data classes, paths and loose types.

@@ 25-30
OpenCV (sharpness and image work), NumPy, PyTorch, NumPy's array type, the safe weights reader, and PyTorch's batch loader.

@@ 32-38
From the ML package, reused rather than rewritten: the decision measurements of calibration (§5.2.6), the training augmentations, the image converter and the dataset rows, the evaluation's prediction and softmax, the row type, the model, and where the prepared faces live; and the vision library's safe image decoder.

@@ 40-42
8 frames per burst, as the verify page sends; the choices to compare — 1, 3 and all 8; and a fixed starting number for the random changes, so the run can be repeated exactly.

@@ 45-49
**`weight`** — a frame's weight, as the inference pipeline computes it: the face's sharpness (the variance of its *Laplacian*, which is large when edges are crisp) at 112 × 112, divided by 200 and capped at 1. Most good frames reach the cap, so among sharp frames the choice is effectively the first ones — as in the service itself.

@@ 52-59
**`Bursts`** — the people of a split, as a dataset that hands out each person's burst. It keeps the rows and the archive's path; the open archive itself is left out of copies (`repr=False`)…

@@ 61-62
…and of what is sent to worker processes (`__getstate__`): an open file can't be sent; each process opens its own.

@@ 64-65
How many people.

@@ 67-70
**One burst.** In each process, the first time: one OpenCV thread (processes run side by side already) and the archive opened.

@@ 71-73
Read the person's photo and make 8 frames from it with the training augmentations, seeded by the person's position, so every run makes the very same frames.

@@ 74-75
Each frame's weight, and the 8 frames as one stack of tensors.

@@ 78-81
**`burst_probabilities`** — every frame's 101 age probabilities, and the weights.

@@ 82-86
Load the trained model from its run folder, on the graphics card if there is one, ready to predict (`eval`).

@@ 87-89
Feed the bursts, 16 people at a time, with no gradients (nothing is being trained).

@@ 90-92
Each batch is people × 8 frames: flatten that into one long batch of faces for the model, in 16-bit precision on the graphics card, and bring the scores back.

@@ 93-94
Turn scores into probabilities with the calibration's temperature (§2.13), and fold them back into people × frames × ages; keep the weights.

@@ 95-96
Every 50 batches, say how far it has got: the full run takes about 25 minutes.

@@ 97
All the batches joined.

@@ 100-101
**`sharpest`** — for each person, mix their `count` best-weighted frames' probabilities, as the pipeline does.

@@ 102-104
`argsort` of the negated weights lists each person's frames best first (stably, keeping ties in order); keep the first `count`, and pick out those frames' probabilities and weights.

@@ 105-107
Turn the weights into shares that add up to 1 (equal shares if all were 0), and mix.

@@ 110-114
**`summary`** — a table per age line: its risk budget, then one row per choice.

@@ 115-123
Each row: the share of minors passed, with its upper bound (the one the risk budget is about), and the share of adults three or more years over the line who were asked to step up.

@@ 124
The table as text.

@@ 127-135
**`main`** — read the command line: the run, the dataset, the split (calibration by default), and how many worker processes make the bursts — none by default, because on Windows each worker's start-up cost more than it saved.

@@ 136-138
**Refuse the test split**, which was opened once in Phase 2 and must not help choose anything.

@@ 139-141
The calibration's temperature and thresholds, and the split's rows.

@@ 142-144
The clean photos' predictions (cached by the evaluation), checked to be for the very same faces in the same order.

@@ 145-147
The bursts' predictions and weights.

@@ 148-149
The four choices: the clean photo, and the best 1, 3 and 8 frames.

@@ 150-161
For each age line with certified thresholds, measure each choice's decisions with calibration's own `decisions_view`.

@@ 162-164
Save the results beside the run, and print the table.

@@ 167-168
Run `main` when started as a program.
