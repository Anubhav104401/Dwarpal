---
fingerprint: 1a0e9794503caa5f
---
The **3D hero's face** (Phase 5, decision D1): 478 points in the shape of a face, made from a few smooth rules. Pure arithmetic — no browser, no graphics — so it is tested like any other function.

@@ 1-3
The module's comment, with its one rule: the face is **no one's**. A real person's face shape — even a public-domain portrait's — would be biometric data, which Dwarpal never keeps. This one is made from a few smooth rules.

@@ 5-6
`FACE_POINTS` — 478, as many points as MediaPipe's face mesh, which the verify page's guidance tracks: the hero shows the kind of thing the check looks at, without being anyone.

@@ 8
The **golden angle**, about 137.5°: turning by it again and again never lines points up, which is why sunflower seeds use it.

@@ 10-13
**`bump`** — a smooth hill: 1 at its centre (`cx`, `cy`), falling away over `wx` across and `wy` up and down. Adding or subtracting bumps shapes the face.

@@ 15-20
**`facePoints`** — the points as one flat list (x, y, z, x, y, z, …), the form the graphics card takes. The docstring describes the method: points spread evenly over the front of a sphere, then pressed into a face.

@@ 21-23
One `Float32Array` (a list of 32-bit numbers, as graphics cards use) with room for every point, then each point in turn.

@@ 24-27
A **Fibonacci lattice**: the heights go evenly from top (`1`) to bottom (`-1`); `ring` is the sphere's radius at that height; and each point turns one golden angle further round.

@@ 28-29
Its place on the sphere. `Math.abs` keeps every point on the front half: a face, not a whole head.

@@ 31-33
Press the sphere into an egg: 74 % as wide as tall, narrowing towards the chin (more the lower it is), and 60 % as deep.

@@ 34-37
Then the features, as bumps in depth: a long nose down the middle (forward), two hollows for the eyes (back), and a little fullness for the lips.

@@ 39-42
Store the point in its three places in the list, and return the list.
