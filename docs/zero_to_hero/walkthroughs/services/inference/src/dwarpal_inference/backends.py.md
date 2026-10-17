---
fingerprint: ade0560713d52e07
---
**Age models**, behind one small interface. Phase 1 ships a **stand-in** (a "stub") that gives every face the same, chosen age distribution. The whole system — API, decisions, tokens, websites — can therefore be built and tested end to end before the real model exists (the walking skeleton, §3.9). Phase 2 adds the real ONNX model behind the same interface.

@@ 1
The docstring: a stand-in age model, used to build and test the whole system before a real one existed, and trained models exported to ONNX, added in Phase 2.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`hashlib` (to check the model file's fingerprint), `json` (to read its manifest) and `Path` (added with the ONNX backend).

@@ 8
`Protocol` — a way to describe an *interface*: "anything with these attributes and methods counts". The stub and the future real model don't have to share a parent class; they only need the same shape.

@@ 10-12
NumPy and its array type, and **ONNX Runtime**: Microsoft's engine for running ONNX models fast on ordinary processors (MIT licence). The service runs the model with it, without needing PyTorch at all.

@@ 14
Our picture type, and the conversion from aligned faces to the model's input (`to_model_input`) — the very function training's checks use (§5.2.7).

@@ 16
`AGES` — the numbers 0, 1, 2, …, 100. A model's output is one probability for each of these ages (ADR-0005).

@@ 19-22
**`AgeBackend` — the interface.** Every age model has a `version` (recorded with every decision) and a `predict` method. `predict` takes aligned face pictures and returns one row of 101 probabilities per face. The `...` body means "no code here; this only describes the shape".

@@ 25
**`StubAgeBackend` — the stand-in.**

@@ 26-27
Build a **bell curve** (a Gaussian) centred on the chosen age: ages near `age` get high weights, which fall off smoothly with distance. `spread` controls how wide the bell is.

@@ 28
Divide by the total, so the 101 probabilities add up to exactly 1, as a probability distribution must.

@@ 29
The version names the stand-in and its age, for example `stub-age-30` (`:g` prints 30.0 as `30`). Every analysis therefore says plainly that it came from a stand-in.

@@ 31-32
`predict` ignores the faces' pixels and returns the same row once per face. `np.tile` repeats the row `len(faces)` times. The real model will actually look at the pictures.

@@ 35-36
**`ModelFileError`** — the model file is missing, or isn't the file its manifest pins.

@@ 39-40
**`OnnxAgeBackend`** — a trained model exported to ONNX, loaded from its folder in the model registry (`models/registry/age/<version>/`).

@@ 42-44
Read the folder's `manifest.json`, and find the model file it names.

@@ 45-48
**Fail closed on the wrong file.** If the file is missing, or its SHA-256 fingerprint differs from the manifest's, refuse to start. A corrupted, replaced or half-copied model must never quietly judge anyone's age; the service not starting is the safe failure.

@@ 49-51
Start an ONNX Runtime **session** — the loaded, ready-to-run model — on the processor, with a chosen number of threads. One thread per request is the default: the service already runs several requests side by side (`workers` in the settings), and each using every core would make them fight.

@@ 52
The model's version, from its manifest. The service reports it with every analysis, and the API checks it against the manifest *it* was given (§5.1.3), so the two can never silently disagree about which model is deciding.

@@ 54-56
**`predict`** — turn the aligned faces into the model's input, run the model, and return its 101 probabilities per face. The temperature correction and the softmax are inside the exported model, so these are final, calibrated probabilities.
