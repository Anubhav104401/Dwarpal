---
fingerprint: d559101fe9f960c5
---
**Face detection**: given a picture, find every face — where it is (a box), five key points (eyes, nose tip, mouth corners) and how confident the detector is.

We use **YuNet**, a tiny neural network (about 230 KB) from the OpenCV model zoo, published under the MIT licence (ADR-0018). It finds faces from about 10 pixels wide upwards, runs in a few milliseconds on a CPU, and OpenCV can run it directly. The file is downloaded and fingerprint-checked by `infra/scripts/fetch_models.py`.

!!! alt "Alternatives considered"
    - **RetinaFace / SCRFD** — accurate, but the popular pretrained weights forbid commercial use.
    - **YOLOv8-face** — AGPL licence.
    - **MediaPipe** — great, and used in the browser (Phase 3), but heavier to run on the server.
    - **MTCNN** — older and slower.

@@ 1
The docstring names the model and its licence, so readers don't have to look it up.

@@ 3
The project-wide type-hint setting.

@@ 5
`import threading` — for a **lock** (line 33), explained below.

@@ 6-8
- `dataclass` — for the `Face` record;
- `Path` — for the model file's location;
- `cast` — to correct a wrong type hint in OpenCV (line 39).

@@ 10-12
OpenCV, NumPy, and NumPy's array type for type hints.

@@ 14
The `Image` type from our own `decode` module.

@@ 17-21
**`Face` — one detected face**, an unchangeable (`frozen`) record:

- `box` — (x, y, width, height) of the face's rectangle, in pixels from the top-left corner;
- `landmarks` — a 5 × 2 array: the (x, y) of the right eye, left eye, nose tip, right mouth corner and left mouth corner, in that order. "Right" means the *person's* right, which appears on the left of a non-mirrored photo;
- `score` — the detector's confidence, from 0 to 1.

@@ 23-25
`eye_distance` — the distance in pixels between the two eye points, using Pythagoras' theorem (`np.linalg.norm` gives the length of the difference between the two points).

The eye distance is our measure of **how big the face is in the picture**. It hardly depends on hairstyle or how the box is drawn, which makes it more reliable than the box size.

@@ 28
**`FaceDetector` — wraps the YuNet model.**

@@ 29
The constructor takes the model file's path and a **score threshold**: faces scoring below 0.6 are not reported at all. The stricter "good enough to judge" limit (0.8) is applied later, by `quality.py`. Keeping the two separate lets us still *notice* a second, faint face in the background.

@@ 30-31
**Fail early and clearly.** If the model file is missing, stop immediately with a message saying exactly how to fix it. A missing file discovered at start-up is far better than a confusing error halfway through a user's verification.

@@ 32
Create OpenCV's YuNet detector:

- `""` — no separate configuration file is needed;
- `(320, 320)` — a starting input size, which `detect` changes for each picture;
- the score threshold.

@@ 33
**A lock.** The detector stores the "current input size" inside itself, and the server analyses several requests at the same time on different threads (§4.8). Without a lock, thread A could set the size for its 640×480 picture, then thread B could set 320×240 for its own before A runs — and A's detection would silently go wrong. This bug is called a **race condition**. The lock lets only one thread at a time through the size-then-detect steps.

@@ 35
**`detect` — find faces in one picture.**

@@ 36
`image.shape[:2]` is the picture's (height, width). The third number, the 3 colour channels, is not needed.

@@ 37
`with self._lock:` — wait for the lock, hold it during the indented lines, and release it automatically afterwards, even if an error happens.

@@ 38
Tell YuNet the size of this picture. Note OpenCV's order: width first.

@@ 39
**Run the detector.** It returns two things; `[1]` is the array of faces, one row per face. When it finds **nothing**, OpenCV returns `None` — even though its published type hints claim it always returns an array.

`cast(…)` tells the type checker the truth ("this may be `None`"), so it doesn't wrongly report the next line as unreachable. `cast` changes nothing at run time; it only corrects the label.

@@ 40-41
No faces: return an empty list.

@@ 42
`faces` collects one `Face` per row.

@@ 43
Each row of YuNet's output holds 15 numbers: 4 for the box, 10 for the five landmark points, and 1 score.

@@ 44
The first four numbers are the box. They are converted to plain Python floats (from NumPy's 32-bit floats) and unpacked into four names.

@@ 45
Numbers 4–13 are the ten landmark coordinates. `reshape(5, 2)` arranges them as five (x, y) pairs.

@@ 46
Number 14 is the score. Build the `Face` and add it.

@@ 47
Return the faces **most confident first**, so `faces[0]` is always the main face.
