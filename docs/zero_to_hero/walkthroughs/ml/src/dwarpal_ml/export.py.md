---
fingerprint: 976ff8dc9e3e4dfa
---
**Export**: turn a trained, calibrated model into the file the service runs, prove that file gives the same answers, and write the model's **manifest** — its passport in the model registry.

```
run folder (.runs/…) ─► model + temperature + softmax ─► ONNX file ─► models/registry/age/<version>/model.onnx
                                                     ─► checks:  parity (PyTorch vs ONNX, same faces)
                                                                 serving path (faces aligned the service's way)
                                                                 CPU speed (one burst of 5 faces)
                                                     ─► models/registry/age/<version>/manifest.json
```

**ONNX** (Open Neural Network Exchange) is an open file format for trained models: the network's layers and all its knobs, written down in a standard way that many engines can run. The service runs it with **ONNX Runtime** (§2.19), which is small, fast on ordinary processors, and doesn't need PyTorch — a 2 GB library the service would otherwise have to carry.

@@ 1-4
The docstring, with the command.

@@ 6
The project-wide type-hint setting.

@@ 8-15
Standard-library tools: `argparse`, `hashlib` (the model file's fingerprint), `json`, `sys`, `time` (for speed), `zipfile`, `Path` and `Any`.

@@ 17-22
NumPy, **ONNX Runtime**, PyTorch, NumPy's array type, `load_file` for the trained weights, and PyTorch's network building blocks.

@@ 24-29
From the ML package: shrinking faces and the usable rows; predictions and the temperature; the model; the detector's location, the prepared faces and the central-face rule; the root and the register. From the vision library: detection, alignment, decoding, and the conversion to the model's input.

@@ 31
`REGISTRY` — the age models' registry: `models/registry/age/`, one folder per version.

@@ 32
`OPSET = 18` — which version of ONNX's set of operations the file uses. Each runtime supports operation sets up to some version; 18 is widely supported and has everything this model needs.

@@ 33
How many validation faces the parity checks use.

@@ 34-35
**`TOLERANCE`** — how far the exported file may differ from PyTorch, in any probability of any face: 0.0001. Two correct implementations of the same arithmetic never agree to the last digit — the order in which numbers are added changes the rounding — but a real mistake shows up as differences thousands of times larger.

@@ 36-37
A burst is 5 faces (the verify page sends 5 frames); the age limit used to compare the two ways of aligning is 18.

@@ 39
`Floats` — an array of decimal numbers.

@@ 42-43
**`Served`** — the model as the service will run it, with its calibration built in: the temperature correction (§2.13) and the softmax become part of the file, so the service receives final probabilities and can't forget either step.

@@ 45-48
It holds the trained model and its temperature.

@@ 50-51
Pixels in; logits divided by the temperature; softmax; 101 probabilities out.

@@ 54-58
**`load_served`** — rebuild the trained model from its run folder (the backbone named in `run.json`, the weights from `model.safetensors`), wrap it with the temperature, and switch it to evaluation behaviour.

@@ 61
**`export`** — write the ONNX file.

@@ 62-64
Create the version's folder. An **example input** — 5 blank faces — shows the exporter the input's shape; `Dim("faces", min=1, max=64)` says the first size, the number of faces, may be anything from 1 to 64.

@@ 65-74
**Export.** PyTorch's modern exporter (`dynamo=True`) first records exactly which operations the model performs, as a graph, then writes that graph as ONNX. The input is named `pixels`, the output `probabilities` — the names the service asks for. `verbose=False` keeps it quiet: its progress messages include an emoji that the Windows console's old character set can't print, which crashed the first run.

@@ 75-77
Refuse if nothing came back; otherwise save the file, with all the knobs inside it rather than in a separate file (`external_data=False`), so one file is one model.

@@ 80-83
**`session`** — load an ONNX file into ONNX Runtime, on the processor, with a chosen number of threads (0 means "decide for yourself").

@@ 86-87
**`run_onnx`** — run a batch through it and return the probabilities.

@@ 90-91
**`expected`** — each face's expected age.

@@ 94
**`parity`** — the first check: on the same faces, does the ONNX file give the same probabilities as the PyTorch model?

@@ 95-100
In batches of 64: convert the faces with the shared conversion, run PyTorch and ONNX Runtime on the very same numbers, and keep each face's largest difference across its 101 probabilities.

@@ 101-107
The largest difference over all faces, the tolerance, and whether it passed. On the first model: 0.0000008 — about a hundred times inside the tolerance.

@@ 110
**`serving_path`** — the second check: the training side and the service prepare a face in slightly different ways. Training aligned each face at 256×256 and shrank it to 224 (§5.2.3); the service aligns straight to 224 from the camera frame. Both use the same alignment, so they *should* give nearly the same face — this measures how nearly.

@@ 111-114
The dataset, its first validation faces, the detector, and two lists.

@@ 115-122
For each face: decode the **original** photo, find the face, and prepare it both ways — the training way (the prepared 256×256 face, shrunk) and the service's way (`align_face` straight from the photo, at 224).

@@ 123-128
Run the exported model on both versions.

@@ 129-136
How far apart the two answers are: the expected age (average, and the gap that 95 % of faces stay within) and the probability of being 18 or over. On the first model: 0.16 years on average, 0.45 for 95 % of faces, and 0.003 in probability — training and serving see practically the same face.

@@ 139
**`latency`** — the third check: how long one burst takes on the processor.

@@ 140-141
A burst of 5 faces, run once first, so that one-time start-up work isn't counted.

@@ 142-146
Time 100 runs, in milliseconds (`perf_counter` is Python's most precise clock).

@@ 147-151
The typical time (**p50**, the median: half the runs were faster) and the slow-case time (**p95**: 95 % were faster). Services are judged by their slow cases, because every user waits for their own request, not the average one. On one thread: 668 ms typical, 697 ms at p95, inside the design's budget of 1.5 s for a whole submission on 4 virtual CPUs (NFR-05).

@@ 154-155
**`sha256_of`** — the model file's fingerprint.

@@ 158-160
**`manifest`** — the model's passport, from the run's record, its calibration and the checks.

@@ 161-163
Read the run record and the calibration; look up the training and calibration datasets in the register.

@@ 164-175
The thresholds, for every limit that could be certified: the limit, the budget, both lines, both bounds, and whether they hold per age and group or per age only.

@@ 176-179
The fields the API reads (§5.1.2): the model's name and version, which versions it serves (exactly this one)…

@@ 180
…and **`calibrated: False`**. The thresholds *are* risk-controlled, but not to the release standard. The API refuses live sessions with an uncalibrated model, so this model can only decide test-mode sessions — which is exactly right until better data allows the real standard.

@@ 181-185
The note that says why, in plain words, for anyone reading the manifest.

@@ 186
**`permitted_use`** — the strictest terms among the model's ingredients: the calibration data, UTKFace, allows non-commercial research only, and the thresholds are derived from it.

@@ 187-195
The model file: its name, fingerprint and size; the operation set; what goes in and what comes out; and the temperature already built in.

@@ 196-202
Where it came from: the training run, the backbone, the pretrained weights (name, fingerprint, licence), the training dataset with its licence and the source of its ages, and the code version.

@@ 203-208
How it was calibrated: the dataset, its licence, the source of its ages, and how many faces.

@@ 209-211
The thresholds, and the three checks.

@@ 214-219
**`main`** — the run, the calibration dataset, and the version name to register it under.

@@ 220-223
Rebuild the temperature on validation (the same one calibration used) and the served model.

@@ 224-226
Export it into the registry, and load the result back into ONNX Runtime.

@@ 227-230
The first validation faces, prepared the training way.

@@ 231-235
Run the three checks.

@@ 236-239
Write the manifest next to the model, print the checks, and exit with `1` if parity failed — an exported file that doesn't give the model's answers must never be used.

@@ 242-243
Run `main` when the module is started as a program.
