---
fingerprint: e0fa6ce7c8b429ba
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

@@ 1-5
The docstring, with the two commands: the whole export, and (added in Phase 5) rewriting only the manifest of a model already exported.

@@ 7
The project-wide type-hint setting.

@@ 9-16
Standard-library tools: `argparse`, `hashlib` (the model file's fingerprint), `json`, `sys`, `time` (for speed), `zipfile`, `Path` and `Any`.

@@ 18-23
NumPy, **ONNX Runtime**, PyTorch, NumPy's array type, `load_file` for the trained weights, and PyTorch's network building blocks.

@@ 25-30
From the ML package: shrinking faces and the usable rows; predictions and the temperature; the model; the detector's location, the prepared faces and the central-face rule; the root and the register. From the vision library: detection, alignment, decoding, and the conversion to the model's input.

@@ 32
`REGISTRY` — the age models' registry: `models/registry/age/`, one folder per version.

@@ 33
`OPSET = 18` — which version of ONNX's set of operations the file uses. Each runtime supports operation sets up to some version; 18 is widely supported and has everything this model needs.

@@ 34
How many validation faces the parity checks use.

@@ 35-36
**`TOLERANCE`** — how far the exported file may differ from PyTorch, in any probability of any face: 0.0001. Two correct implementations of the same arithmetic never agree to the last digit — the order in which numbers are added changes the rounding — but a real mistake shows up as differences thousands of times larger.

@@ 37-38
A burst is 5 faces (the verify page sends 5 frames); the age limit used to compare the two ways of aligning is 18.

@@ 40
`Floats` — an array of decimal numbers.

@@ 43-44
**`Served`** — the model as the service will run it, with its calibration built in: the temperature correction (§2.13) and the softmax become part of the file, so the service receives final probabilities and can't forget either step.

@@ 46-49
It holds the trained model and its temperature.

@@ 51-52
Pixels in; logits divided by the temperature; softmax; 101 probabilities out.

@@ 55-59
**`load_served`** — rebuild the trained model from its run folder (the backbone named in `run.json`, the weights from `model.safetensors`), wrap it with the temperature, and switch it to evaluation behaviour.

@@ 62
**`export`** — write the ONNX file.

@@ 63-65
Create the version's folder. An **example input** — 5 blank faces — shows the exporter the input's shape; `Dim("faces", min=1, max=64)` says the first size, the number of faces, may be anything from 1 to 64.

@@ 66-75
**Export.** PyTorch's modern exporter (`dynamo=True`) first records exactly which operations the model performs, as a graph, then writes that graph as ONNX. The input is named `pixels`, the output `probabilities` — the names the service asks for. `verbose=False` keeps it quiet: its progress messages include an emoji that the Windows console's old character set can't print, which crashed the first run.

@@ 76-78
Refuse if nothing came back; otherwise save the file, with all the knobs inside it rather than in a separate file (`external_data=False`), so one file is one model.

@@ 81-84
**`session`** — load an ONNX file into ONNX Runtime, on the processor, with a chosen number of threads (0 means "decide for yourself").

@@ 87-88
**`run_onnx`** — run a batch through it and return the probabilities.

@@ 91-92
**`expected`** — each face's expected age.

@@ 95
**`parity`** — the first check: on the same faces, does the ONNX file give the same probabilities as the PyTorch model?

@@ 96-101
In batches of 64: convert the faces with the shared conversion, run PyTorch and ONNX Runtime on the very same numbers, and keep each face's largest difference across its 101 probabilities.

@@ 102-108
The largest difference over all faces, the tolerance, and whether it passed. On the first model: 0.0000008 — about a hundred times inside the tolerance.

@@ 111
**`serving_path`** — the second check: the training side and the service prepare a face in slightly different ways. Training aligned each face at 256×256 and shrank it to 224 (§5.2.3); the service aligns straight to 224 from the camera frame. Both use the same alignment, so they *should* give nearly the same face — this measures how nearly.

@@ 112-115
The dataset, its first validation faces, the detector, and two lists.

@@ 116-123
For each face: decode the **original** photo, find the face, and prepare it both ways — the training way (the prepared 256×256 face, shrunk) and the service's way (`align_face` straight from the photo, at 224).

@@ 124-129
Run the exported model on both versions.

@@ 130-137
How far apart the two answers are: the expected age (average, and the gap that 95 % of faces stay within) and the probability of being 18 or over. On the first model: 0.16 years on average, 0.45 for 95 % of faces, and 0.003 in probability — training and serving see practically the same face.

@@ 140
**`latency`** — the third check: how long one burst takes on the processor.

@@ 141-142
A burst of 5 faces, run once first, so that one-time start-up work isn't counted.

@@ 143-147
Time 100 runs, in milliseconds (`perf_counter` is Python's most precise clock).

@@ 148-152
The typical time (**p50**, the median: half the runs were faster) and the slow-case time (**p95**: 95 % were faster). Services are judged by their slow cases, because every user waits for their own request, not the average one. On one thread: 668 ms typical, 697 ms at p95, inside the design's budget of 1.5 s for a whole submission on 4 virtual CPUs (NFR-05).

@@ 155-156
**`sha256_of`** — the model file's fingerprint.

@@ 159-162
**`adult_outcomes`** (Phase 5, §5.5.8) — for each age line, how adults in each band above it fared on the exact-age **test split**: passed, sent to a stronger check, or failed. `calibrate` measured them when it set the lines, opening that split once; nothing here measures again or changes a line. The console's policy editor shows them as its projection.

@@ 163-165
The measurements are in the run's `evaluation-<dataset>-test.json`. A run never measured that way has none: an empty answer.

@@ 166
Read the file.

@@ 167-177
For each limit, one entry per adult band: the band's name ("18-20", "30+"), how many faces it held, and the three shares, rounded to four decimal places — finer than anyone needs, and no hint of more precision than 330 faces can give. `**{…}` spreads the three shares into the entry. A limit with no adult bands gets an empty list.

@@ 180-182
**`manifest`** — the model's passport, from the run's record, its calibration and the checks.

@@ 183-185
Read the run record and the calibration; look up the training and calibration datasets in the register.

@@ 186
The adults' outcomes, by limit.

@@ 187-199
The thresholds, for every limit that could be certified: the limit, the budget, both lines, both bounds, whether they hold per age and group or per age only — and the adults' outcomes at that line.

@@ 200-203
The fields the API reads (§5.1.2): the model's name and version, which versions it serves (exactly this one)…

@@ 204
…and **`calibrated: False`**. The thresholds *are* risk-controlled, but not to the release standard. The API refuses live sessions with an uncalibrated model, so this model can only decide test-mode sessions — which is exactly right until better data allows the real standard.

@@ 205-209
The note that says why, in plain words, for anyone reading the manifest.

@@ 210
**`permitted_use`** — the strictest terms among the model's ingredients: the calibration data, UTKFace, allows non-commercial research only, and the thresholds are derived from it.

@@ 211-219
The model file: its name, fingerprint and size; the operation set; what goes in and what comes out; and the temperature already built in.

@@ 220-226
Where it came from: the training run, the backbone, the pretrained weights (name, fingerprint, licence), the training dataset with its licence and the source of its ages, and the code version.

@@ 227-232
How it was calibrated: the dataset, its licence, the source of its ages, and how many faces.

@@ 233-235
The thresholds, and the three checks.

@@ 238-242
**`main`** — the run, the calibration dataset, and the version name to register it under…

@@ 243-244
…and `--manifest-only`, a switch (`store_true`: present or not, no value), to rewrite only the manifest.

@@ 245-246
Where the model and its manifest live in the registry.

@@ 247-252
**Manifest only**: as the comment says, the model and its checks stay as they were — the checks are read back from the existing manifest — and everything read from the run's files is read again. It was added so a model's manifest could gain the adults' outcomes (Phase 5) without exporting it again: the model's fingerprint, its checks and its lines come out exactly as before. Then write the manifest, as below, and stop.

@@ 253
Otherwise, the whole export: read the run's record.

@@ 254-256
Rebuild the temperature on validation (the same one calibration used) and the served model.

@@ 257-258
Export it into the registry, and load the result back into ONNX Runtime.

@@ 259-262
The first validation faces, prepared the training way.

@@ 263-267
Run the three checks.

@@ 268-272
Write the manifest next to the model — with `\n` line endings on every system (`newline="\n"`), as the repository and its JSON formatter expect: on Windows, Python would otherwise write `\r\n` — then print the checks, and exit with `1` if parity failed — an exported file that doesn't give the model's answers must never be used.

@@ 275-276
Run `main` when the module is started as a program.
