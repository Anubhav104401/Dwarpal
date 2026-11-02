---
fingerprint: 9f5aa14882ad591c
---
**The render detector in the inference service** (§5.9.4).

@@ 1-3
The module's docstring: the render detector as the inference service runs it — our own network, exported by `dwarpal_ml.render_detector`, run by OpenCV like MiniFASNet, on the same crop.

@@ 5
The project-wide type-hint setting.

@@ 7-15
A lock, paths, OpenCV, NumPy; MiniFASNet's crop, and the picture and face types.

@@ 17-19
The crop size it was trained on (2.7 face-sizes), and which of its two answers is *rendered*.

@@ 22-27
**`RenderDetector`**: the file is loaded once. A missing file stops with a message naming the command that makes one. One OpenCV network isn't safe to use from two threads at once, so a lock guards it.

@@ 29-31
**`rendered`**: the face's crop…

@@ 32-33
…as the network was trained to see it: blue-green-red, 0–255, colours first, one face.

@@ 34-36
Through the network, one request at a time; the *rendered* chance comes back.
