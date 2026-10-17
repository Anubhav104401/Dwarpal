---
fingerprint: de862ff9968648ad
---
**Live guidance** for the camera screen, using Google's **MediaPipe Face Landmarker** (§5.3). It runs entirely inside the browser: the picture never leaves the device for it. From each picture of the preview it finds the face and **478 points** on it — the eyes' corners, the nose tip, the lips and so on, called a **face mesh** — fast enough to keep up with live video.

From a few of those points the page works out where the face is, how big it is and which way the head points, and turns that into plain instructions ("Move a little closer"). It also tells the challenge when the head has reached each pose, so the photo is taken at the right moment.

As the first line says: **it guides; it decides nothing.** Every decision is made on the server, from the photos, by our own checks. If the landmarker can't run at all, the page still works — just without live guidance.

@@ 1
The doc comment: loaded only when the camera starts — a few megabytes that nobody else needs — and it decides nothing.

@@ 3
Two MediaPipe **types** (only types: nothing is loaded by this line): the landmarker itself, and `NormalizedLandmark` — one point of the mesh, with `x` and `y` as fractions of the picture's width and height (0 to 1).

@@ 5
From `challenge.ts`: `anglesFrom`, which turns face points into head angles, and the `HeadAngles` type.

@@ 7-8
`ASSETS` — the web address of MediaPipe's files: `/mediapipe`, a folder of the verify page's own site, filled before each build (`scripts/mediapipe.mjs`). Serving them ourselves, rather than from Google's servers, means the page talks to nobody else, and the version is exactly the one we pinned.

@@ 10-17
**`Reading`** — what the landmarker saw in one picture:

- `faces` — how many faces;
- `angles` — the head's angles, or `null` with no face;
- `centred` — whether the face is near the middle of the picture;
- `closeEnough` — whether the face is wide enough: at least a fifth of the picture's width.

@@ 19-20
**`MESH`** — which of the 478 points to use, by their numbers in MediaPipe's mesh: both corners of each eye (33 and 133 for the person's right eye, 362 and 263 for the left), the nose tip (1), and the two mouth corners (61 and 291). Averaging two corners gives an eye's centre, matching the five points the server's YuNet detector finds. `as const` tells TypeScript these lists never change.

@@ 22
**`centre`** — the average position of some of the points, chosen by their numbers.

@@ 23
Look up each point. `?? { x: 0, y: 0 }` stands in for a point that is missing — it shouldn't happen, but the type system can't know that.

@@ 24-28
The average: add up the `x` values and divide by how many there are, then the same for `y`. `reduce` walks through a list carrying a running total, starting from `0`.

@@ 30
**`create`** — make a landmarker that runs on the chosen **delegate**: `"GPU"` (the graphics chip, fast) or `"CPU"` (the main processor, slower but available everywhere).

@@ 31
**Load MediaPipe's code now**, not when the page first opens. `await import(…)` is a **dynamic import**: the code is downloaded only when this line runs. People who never reach the camera never download it.

@@ 32
Point MediaPipe at its WebAssembly files, in our own `/mediapipe/wasm` folder.

@@ 33-38
Create the landmarker:

- `modelAssetPath` — the face model, also from our own folder;
- `delegate` — where it runs;
- `runningMode: "VIDEO"` — the pictures come from a video, so it can follow the face from one picture to the next, which is faster and steadier than starting afresh each time;
- `numFaces: 2` — look for up to two faces. One is all we use, but finding a second lets the page say "Make sure only you are in view."

@@ 40-41
**`loadLandmarker`** — the landmarker, on the graphics chip if possible, otherwise the processor, or `null` if it can't run at all.

@@ 42-44
Try `"GPU"` first, then `"CPU"`. The first that works is returned at once.

@@ 45-48
If one fails — an old graphics driver, a browser without WebGL — the `catch` swallows the error, and the loop tries the next. The comment says why it's safe to give up quietly: without guidance the check still works.

@@ 49-50
Neither worked: `null`.

@@ 52
**`read`** — what the landmarker sees in the video's current picture. `nowMs` is the current time, which video mode needs.

@@ 53
Ask it. `faceLandmarks` is a list with one entry per face found, each a list of 478 points.

@@ 54-57
Take the first face. If there is none: a reading with no face.

@@ 58-59
All the points' `x` values, and all their `y` values.

@@ 60
The face's width: from its leftmost point to its rightmost. `Math.max(...xs)` — the `...` spreads the list into separate arguments, as `Math.max` expects.

@@ 61-62
The middle of the face's box, across and down.

@@ 63-68
The head's angles, from the centres of the right eye, the left eye, the nose tip and the mouth.

@@ 69-75
The reading:

- `faces` — how many were found;
- `angles`;
- `centred` — the face's middle is within 0.15 of the picture's middle across, and within 0.2 down (people tend to sit a little lower or higher);
- `closeEnough` — the face spans at least a fifth of the picture's width.
