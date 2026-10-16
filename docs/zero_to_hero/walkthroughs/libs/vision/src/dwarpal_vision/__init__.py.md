---
fingerprint: 3b545aa34b5e0c8e
---
The vision package's **front door**: it re-exports the useful names from its four modules, so other code can simply write `from dwarpal_vision import FaceDetector, assess`.

@@ 1
The docstring: decoding, detection, alignment and quality checks, shared by training and serving. Sharing them prevents *train/serve skew* (see `libs/vision/pyproject.toml`).

@@ 3
From `align.py`: `align_face`, which straightens and crops a face.

@@ 4
From `decode.py`:

- `DecodeError` — the error raised for unacceptable bytes;
- `Image` — the type name for a picture array;
- `decode_image` — bytes to picture;
- `image_size` — read the size from the header only.

@@ 5
From `detect.py`: `Face` (one detected face) and `FaceDetector` (the YuNet wrapper).

@@ 6
From `quality.py`: the default rules, the `Quality` result, the `QualityRules` settings, and `assess`, which checks a frame.

@@ 8-20
`__all__` — the public interface, one name per line, in alphabetical order (capitals first, as Ruff's sorter arranges them).
