---
fingerprint: 44de14d0f451a32d
---
The vision package's **front door**: it re-exports the useful names from its four modules, so other code can simply write `from dwarpal_vision import FaceDetector, assess`.

@@ 1
The docstring: everything this library does with pictures of faces and hands — decoding, detection, alignment, quality checks, head angles and the model's input — shared by training and serving. Sharing them prevents *train/serve skew* (see `libs/vision/pyproject.toml`).

@@ 3
From `align.py`: `align_face`, which straightens and crops a face.

@@ 4
The anti-spoofing pieces (`antispoof.py`): the detector, its model description, and the screen-pattern measure.

@@ 5
`to_model_input` — aligned faces in, the age model's input out (added in Phase 2).

@@ 6
From `decode.py`:

- `DecodeError` — the error raised for unacceptable bytes;
- `Image` — the type name for a picture array;
- `decode_image` — bytes to picture;
- `image_size` — read the size from the header only.

@@ 7
From `detect.py`: `Face` (one detected face) and `FaceDetector` (the YuNet wrapper).

@@ 8
The hand detector (`hands.py`).

@@ 9
The face mesh and its head-angle result (`mesh.py`).

@@ 10
From `quality.py`: the default rules, the `Quality` result, the `QualityRules` settings, and `assess`, which checks a frame.

@@ 13-33
`__all__` — the public interface, one name per line, in alphabetical order (capitals first, as Ruff's sorter arranges them).

@@ 11
The render detector's wrapper (§5.9.4).
