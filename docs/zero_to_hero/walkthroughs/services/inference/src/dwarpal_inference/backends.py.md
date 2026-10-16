---
fingerprint: cf679c08e18bf035
---
**Age models**, behind one small interface. Phase 1 ships a **stand-in** (a "stub") that gives every face the same, chosen age distribution. The whole system — API, decisions, tokens, websites — can therefore be built and tested end to end before the real model exists (the walking skeleton, §3.9). Phase 2 adds the real ONNX model behind the same interface.

@@ 1
The docstring explains why a stand-in exists.

@@ 3
The project-wide type-hint setting.

@@ 5
`Protocol` — a way to describe an *interface*: "anything with these attributes and methods counts". The stub and the future real model don't have to share a parent class; they only need the same shape.

@@ 7-8
NumPy and its array type.

@@ 10
Our picture type.

@@ 12
`AGES` — the numbers 0, 1, 2, …, 100. A model's output is one probability for each of these ages (ADR-0005).

@@ 15-18
**`AgeBackend` — the interface.** Every age model has a `version` (recorded with every decision) and a `predict` method. `predict` takes aligned face pictures and returns one row of 101 probabilities per face. The `...` body means "no code here; this only describes the shape".

@@ 21
**`StubAgeBackend` — the stand-in.**

@@ 22-23
Build a **bell curve** (a Gaussian) centred on the chosen age: ages near `age` get high weights, which fall off smoothly with distance. `spread` controls how wide the bell is.

@@ 24
Divide by the total, so the 101 probabilities add up to exactly 1, as a probability distribution must.

@@ 25
The version names the stand-in and its age, for example `stub-age-30` (`:g` prints 30.0 as `30`). Every analysis therefore says plainly that it came from a stand-in.

@@ 27-28
`predict` ignores the faces' pixels and returns the same row once per face. `np.tile` repeats the row `len(faces)` times. The real model will actually look at the pictures.
