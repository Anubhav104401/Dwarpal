---
fingerprint: 68d85787795f10eb
---
Tests for the vision library. They use one real face: the public-domain NASA portrait of astronaut Eileen Collins described in `fixtures/README.md`. Its faces and pixels are known, so every check can be compared against a known right answer.

!!! why "Why test with a real face instead of a drawing?"
    The detector is a neural network trained on photographs. A cartoon or a solid-colour square would only test that "nothing is found". A real, clear portrait lets the tests check the things that matter: exactly one face is found, the alignment lands the eyes in the right places, and the quality checks accept a good frame but name the problem in a bad one.

@@ 1
The module docstring, pointing to where the test picture comes from.

@@ 3
The project-wide type-hint setting.

@@ 5
`dataclasses` — for `dataclasses.replace`, which copies a frozen record with some fields changed.

@@ 6-7
`struct` builds fake image headers (line 20); `Path` locates the fixture and model files.

@@ 9-11
OpenCV (to blur a picture on purpose), NumPy (to darken one) and pytest.

@@ 13-14
The functions under test — including `to_model_input`, added in Phase 2 — plus the alignment `template` used to check where the eyes end up.

@@ 15
`people` — the count of different people among the detections (`quality.py`).

@@ 17
The test picture's location: the `fixtures` folder next to this file.

@@ 18
The YuNet model file. From this file, `parents[3]` climbs `tests → vision → libs → repository root`. The model must have been downloaded by `infra/scripts/fetch_models.py`, as CI does before running tests.

@@ 21-22
**`png_header`** — builds the first bytes of a PNG file claiming any width and height, with no picture data behind them. It lets the tests try "huge" images without creating any. The bytes are:

- the 8-byte PNG signature;
- the IHDR chunk's length (13) and its name;
- the width and height as two big-endian 4-byte numbers;
- the remaining header fields (bit depth 8, colour type 2 = RGB, and three zero settings).

@@ 25-27
A **fixture** — a ready-made value that pytest hands to any test that names it as a parameter. Here it is a `FaceDetector`. `scope="module"` creates it **once** for all the tests in this file, instead of reloading the model for every test.

@@ 30-32
Another module-wide fixture: the test picture's bytes, read once.

@@ 35-37
**Sizes come from headers.** The real JPEG reports 512 × 512, and a fabricated PNG header reports exactly what it claims. No pixel is decoded in either case.

@@ 40-46
**Unwelcome inputs are refused, with the right message.**

- A GIF (its magic number starts `GIF89a`) is refused because only JPEG and PNG are allowed.
- A PNG header claiming 50,000 × 50,000 pixels — a decompression bomb — is refused *before* decoding, and the message names the dimensions.
- 101 bytes with a limit of 100 are refused before anything else is looked at. `bytes(101)` makes 101 zero bytes: their content doesn't matter, because the size check comes first. This proves that a caller's own `max_bytes` is really used.

`pytest.raises(…, match=…)` passes only if that exact kind of error is raised **and** its message contains the given text.

@@ 49-53
**Detection.** The portrait contains exactly one face, the detector is confident about it (score above 0.8), and it is large enough (eyes more than 40 pixels apart).

@@ 56-63
**Alignment lands the eyes where the template says.**

1. Align the face into a 224 × 224 crop.
2. Run the detector *again* on that crop.
3. Check that the eyes it finds there are within 8 pixels of the template positions.

This tests the whole chain — detection, transform, warping — against its purpose, not against its internals. The message after the comma in `assert again, "…"` is shown if the check fails, explaining what went wrong.

@@ 66-68
The test's name says exactly what it proves. The formatter split the signature over three lines because it is long.

@@ 69-71
**A good frame has no flags.**

@@ 72-73
**Too dark.** Multiplying every pixel by 0.12 makes the picture about eight times darker. `astype(np.uint8)` turns the results back into whole numbers from 0 to 255. The same face boxes are reused, so only the lighting changed. The `too_dark` flag must appear.

@@ 74-75
**Too blurry.** A strong Gaussian blur (spread 6 pixels) wipes out fine detail, so the `too_blurry` flag must appear.

OpenCV's blur function is described to mypy as returning "an array of some kind of number", which is vaguer than the "array of bytes 0–255" that `assess` asks for. `np.asarray(..., dtype=np.uint8)` states the exact type. The pixels are already bytes, so NumPy makes no copy; the call only tells the type checker what is true (§4.9).

@@ 76
**No face.** With an empty list of faces, the only flag is `no_face`.

@@ 79-81
**Only a separate, similar-sized face counts as a second person.** Start from the real face the detector finds in the test portrait, and its box.

@@ 82
`shifted` — a copy moved two face-widths to the right: a second person beside the first.

@@ 83
`inside` — a smaller box within the main face's box: the kind of second detection the detector makes of part of the same face.

@@ 84
`faint` — the shifted face, but with a score of 0.7: below the 0.8 the quality rules require.

@@ 85
`small` — the shifted face with its landmarks shrunk to 30 %, so its eyes are much closer together: a face far in the background.

@@ 86-90
Only `shifted` counts as a second person; the others don't, and an empty list counts nobody.

@@ 93-95
**Faces become one batch.** Align the portrait's face, and make a mirrored copy, to have two different faces.

@@ 96-99
The batch has the model's shape — 2 faces, 3 colours, 224 × 224 — in 32-bit decimals, laid out in one unbroken block of memory (`C_CONTIGUOUS`), which ONNX Runtime needs.

@@ 100-101
**The pixels are unchanged, only reordered**: the batch's first colour plane (red) is exactly the face's third OpenCV channel, and its third (blue) is the first. Getting this order wrong is the classic colour bug: a model trained on red-green-blue that is fed blue-green-red sees people with blue skin, and quietly gets worse.
