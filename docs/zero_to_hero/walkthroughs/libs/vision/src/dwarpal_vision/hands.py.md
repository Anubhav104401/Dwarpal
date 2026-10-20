---
fingerprint: fb564cf510222c43
---
**Hands in a picture**, found by MediaPipe's **palm detector**, run by OpenCV from the pinned hand landmarker bundle (§5.3.6). Its purpose: someone holding a phone or a printed photo up to the camera usually has fingers next to the face — the owner's own idea after their red-team tests.

In those tests, though, it didn't work well enough to trust: it missed the hands that held the phone, and once found a hand that wasn't there. So the sign it produces is **recorded but decides nothing** (`domain/decision.py`, `RECORDED_ONLY`), until it is shown to work.

@@ 1-4
The module docstring: what it finds, and why liveness wants to know.

@@ 6
The project-wide type-hint setting.

@@ 8-11
A temporary folder, a lock, the zip archive, and paths — as for the face mesh.

@@ 13-15
OpenCV, NumPy, and NumPy's array type for annotations.

@@ 17
The library's picture type.

@@ 19
The palm detector's name inside the bundle. (The bundle's second model, which finds the 21 points of a hand, isn't needed: knowing where a hand is is enough.)

@@ 20
The model's input: a 192 × 192 picture.

@@ 21-22
The detector doesn't search freely: it judges a fixed grid of **candidate boxes**, called anchors, as the comment says — 2 for each cell of a 24 × 24 grid, then 6 for each cell of a 12 × 12 grid: 1,152 + 864 = 2,016 in all. For each one it answers a score and how to adjust the box.

@@ 23
`MIN_SCORE = 0.5` — a hand is kept only if the model gives it at least an even chance.

@@ 25
`Box` — a box as (left, top, width, height), in pixels.

@@ 28-36
**`anchors`** — the centres of the 2,016 candidate boxes, as fractions of the picture, in the order the model uses: grid by grid, row by row, cell by cell, and the boxes of a cell one after another. A centre is the middle of its cell: `(x + 0.5) / cells`.

@@ 39
Worked out once, when the module is loaded.

@@ 42-45
**`HandDetector`** — load the palm detector once. A missing bundle is a clear error, with the command that fetches it.

@@ 46-50
As the comment says: unpacked to a temporary folder and loaded with OpenCV's classic engine, exactly like the face mesh.

@@ 51-52
Its output names, and a lock for running it from several attempts at once.

@@ 54-55
**`detect`** — the hands in a picture, as boxes in pixels, most confident first.

@@ 56-57
The picture's size, and its longer side.

@@ 58-59
**Letterbox** it, as the comment says: add black below or to the right until it is square, so hands keep their shape when it is shrunk.

@@ 60-61
Shrink to 192 × 192, change to red-green-blue, and make the model's input: decimals from 0 to 1, channels first, a batch of one.

@@ 62-64
Run the model under the lock, and pair each output with its name in a dict.

@@ 65-66
The two outputs, told apart by shape: one score per candidate box, and 18 numbers per box (its adjustment: centre, size, and seven key points not used here).

@@ 67
Turn the raw scores into chances from 0 to 1 with the **sigmoid** function, 1 / (1 + e^−score). `np.clip` keeps the scores in a range where the arithmetic can't overflow.

@@ 68
The hands found so far.

@@ 69-71
Go through the candidates from the most likely down (`argsort` of the negated chances), stopping at the first below the minimum.

@@ 72-75
Decode the box: the model's numbers are offsets from the candidate's centre and the box's size, in 192-pixel units. Divide by 192, add the anchor's centre, and multiply by the square's side to get pixels; then turn the centre and size into (left, top, width, height).

@@ 76-78
Keep it unless it overlaps a hand already kept by 30 % or more — the same hand found by neighbouring candidates. This is called **non-maximum suppression**. Return the hands.

@@ 81-82
**`near_face`** — how many hands are next to the face: centred within one face-size of the face's centre, on any side.

@@ 83
The face's box.

@@ 84-88
Count the hands whose centre is at most one and a half face-widths from the face's centre across, and one and a half face-heights up or down.

@@ 91-92
**`overlap`** — how much two boxes overlap: the shared area over the area they cover together. 0 means apart; 1 means the same box. This measure is called **intersection over union**.

@@ 93-94
The shared rectangle's edges: the larger of the two left edges and top edges, the smaller of the two right edges and bottom edges.

@@ 95
Its area — 0 if the boxes don't meet (a negative width or height becomes 0).

@@ 96
Divide by the combined area: both boxes' areas, minus the shared part counted twice. `max(…, 1e-6)` avoids dividing by zero.
