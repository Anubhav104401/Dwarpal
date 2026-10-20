---
fingerprint: d6bcd1566405101c
---
**Head angles from a face mesh**, on the server (§5.3.6). YuNet's five points — two eyes, the nose tip, two mouth corners — measure a sideways turn well, but in the owner's tests they measured a lifted chin anywhere from −0.03 to 0.12, too unreliable to judge. MediaPipe's **face mesh** places 478 points on the face, and in particular the eye corners, nose tip and mouth corners far more precisely: with it, the same lifted chins measured 0.11–0.38.

The mesh model was already pinned for the verify page (`models/third_party.json`). Here **OpenCV** runs it, from the same bundle — no new download, and no new library. The angles use exactly the page's formulas (`apps/web/lib/challenge.ts`), so the page's meter and the server measure the same thing.

@@ 1-6
The module docstring: what it measures, why the mesh is needed, and that its formulas match the page's.

@@ 8
The project-wide type-hint setting.

@@ 10-14
Standard tools: `tempfile` (a temporary folder for unpacking the model), `threading` (a lock), `zipfile` (the model bundle is a zip archive), `dataclass`, and `Path`.

@@ 16-18
OpenCV, NumPy, and NumPy's array type for annotations.

@@ 20-21
The library's own picture and face types.

@@ 23
The mesh model's name inside the bundle. The bundle also holds a face detector and an expression model, which aren't needed: YuNet has already found the face.

@@ 24
The model's input: a 256 × 256 picture.

@@ 25-26
`MARGIN = 1.5` — as the comment says, the model expects the face in the middle of a square a little larger than the face itself: here one and a half times the face box.

@@ 27
The mesh points used, by their numbers in MediaPipe's mesh — the same as the page's: both corners of each eye (33 and 133, 362 and 263), the nose tip (1) and the mouth corners (61 and 291). `(1,)` is a tuple of one number; the comma makes it a tuple.

@@ 30-33
**`HeadAngles`** — the result: sideways turn (`yaw`) and up-down tilt (`pitch`).

@@ 36-37
**`centre`** — the average position of some mesh points, chosen by number. `points[list(indices), :2]` picks those rows and their first two columns (x and y; the third is depth).

@@ 40-42
**`angles_from`** — the two angles from the 478 points: the centres of the right eye, the left eye, the nose tip and the mouth.

@@ 43
The point between the eyes.

@@ 44
The distance between the eyes — `np.linalg.norm` is the length of the line from one to the other. `max(…, 1e-6)` keeps it from ever being zero, so the division below can't fail.

@@ 45
How far the mouth is below the eyes, also never zero.

@@ 46
**Yaw**: how far the nose is to the side of the eyes' midpoint, in eye distances. **Pitch**: how far down from the eyes the nose sits, as a fraction of the way to the mouth. Lifting the chin moves the nose up towards the eyes, so pitch falls.

@@ 49-52
**`FaceMesh`** — load the mesh model once. A missing bundle is a clear error, with the command that fetches it.

@@ 53-54
The comment explains two OpenCV quirks found while building this. OpenCV 5 has a new engine that returns only a model's *last* output — not the 478 points — so the **classic** engine is chosen; and OpenCV honours that choice only when loading from a file, not from memory.

@@ 55-58
So: unpack the model from the bundle into a temporary folder, and load it from there with the classic engine. The folder and the file are deleted when the `with` block ends; the network stays in memory.

@@ 59
The names of the model's outputs: whether a face is present, the 478 points, and one more not used here.

@@ 60
A lock: the inference service analyses several attempts at once, and one network must not be run by two of them at the same moment.

@@ 62-63
**`angles`** — the head's angles for a face YuNet found, or `None` when the mesh model sees no face in the crop.

@@ 64-67
The square to crop: one and a half times the face box's larger side, centred on the face. `round` gives whole pixels; `max(…, 1)` avoids an empty square.

@@ 68-71
As the comment says: where the square reaches past the picture's edge, add a black border all round, so the face stays centred and unstretched. `pad` is the largest overhang on any side (0 if none).

@@ 72
Cut the square out of the padded picture (shifted by the border's width).

@@ 73
Shrink it to 256 × 256 (`INTER_AREA` is the best method for shrinking) and reorder the colours from OpenCV's blue-green-red to red-green-blue.

@@ 74
The model's input: decimals from 0 to 1, channels first, as a batch of one.

@@ 75-77
Run the model, under the lock, and take its first two outputs: face presence and the points.

@@ 78-79
Face presence is a raw score where above 0 means "a face". At or below 0, there is no face to measure: `None`.

@@ 80
The 478 points as rows of (x, y, depth), and the angles from them.
