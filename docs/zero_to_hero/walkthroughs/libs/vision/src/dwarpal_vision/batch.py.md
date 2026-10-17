---
fingerprint: 760a50c82288255d
---
**Faces in, the age model's input out.** It is three lines of code, and it lives in the shared vision library because it is exactly the kind of step that drifts apart when written twice: the inference service uses it before every prediction, and the export checks use it to prove the exported model matches (`ml/src/dwarpal_ml/export.py`). If training's checks and serving ever prepared the numbers differently — another colour order, another layout — the model would quietly be fed the wrong numbers.

@@ 1
The docstring: what it does, and why it is shared.

@@ 3
The project-wide type-hint setting.

@@ 5
`Sequence` — "any ordered collection", such as a list of faces.

@@ 7-9
OpenCV, NumPy and NumPy's array type.

@@ 11
The library's `Image` type.

@@ 14-16
**`to_model_input`**, and its contract: OpenCV's blue-green-red faces, each *height × width × 3*, become one red-green-blue batch shaped *(faces, 3, height, width)*, with pixel values still 0–255, because the model scales them itself (`ml/src/dwarpal_ml/model.py`).

@@ 17
Turn each face from blue-green-red to red-green-blue, stack them into one array (`np.stack`), and convert to 32-bit decimals, the type the model expects.

@@ 18
Rearrange from *(faces, height, width, colour)* to *(faces, colour, height, width)* — the order PyTorch and ONNX models use — and lay the result out as one unbroken block of memory (`ascontiguousarray`), which ONNX Runtime needs.
