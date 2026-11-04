---
fingerprint: 60cfa21e5a30cd1d
---
**Tests for the render detector** (§5.9.4).

@@ 1-2
What this file tests: crops only from clips that may be kept, a network that learns, honest thresholds, and an export that needs passing gates and answers as PyTorch does.

@@ 4
The project-wide type-hint setting.

@@ 6-16
Paths, OpenCV (to write a large PNG), NumPy, pytest, PyTorch; the modules under test; the face type, the service's wrapper and the crop.

@@ 18
The three splits.

@@ 21-27
**`OneFace`** stands in for the face finder: one face, the middle half of every picture.

@@ 30-38
**`people`**: IDs that fill every split with `per_split` people each — chosen by trying numbers until `split_of` has put enough in each.

@@ 41-51
**`frames`**: fake pictures. Real faces as random speckle, renders as smooth colour ramps — a difference a small network learns in a few epochs, so the test is about the machinery, not about faces.

@@ 54-57
**`clips`**: a folder of clips shared by the tests below (`module` scope: made once). Three real and three made-up people per split…

@@ 58-62
…a consent for each real person…

@@ 63-68
…and 12 frames per person, filed through `renders.record` — so the consent rules apply here too.

@@ 71-73
Preparing every frame: 72 crops per split (6 people × 12).

@@ 74-77
The test split holds 80 × 80 crops of both labels and both kinds, and no person in it is in training.

@@ 79-86
A clip whose frames have vanished makes `check` fail, and `prepare` refuses; the folder is put back afterwards, even if the test fails (`finally`).

@@ 97-102
A network built from the shapes alone answers two chances that add up to 1, for each of four faces.

@@ 105-110
`augment` keeps an 80 × 80 picture of bytes, and changes it.

@@ 111
Three real crops and one rendered: each real one weighs 1/3, the rendered one 1, so both labels are drawn equally often.

@@ 114-117
100 real scores spread from 0 to 0.99, and 10 renders at 0.999.

@@ 118-120
The threshold calls at most 5 % of the real ones rendered — and is as low as that allows: a little lower calls more.

@@ 121
At that threshold the balanced error is small: every render caught, at most 5 % of the real refused.

@@ 124-128
Train for 4 epochs from scratch, with progress lines collected: four lines, and a saved network.

@@ 130-134
Evaluated against a gate it can't pass (50 real people): the test rests on 3 real and 3 made-up people, and both error rates are low — the network learnt.

@@ 135-136
So the export is refused, naming the gate.

@@ 138-143
With a gate it passes, the export writes the ONNX file and a manifest that says *recorded only*.

@@ 145-152
The inference service's wrapper, running the exported file through OpenCV, gives the same chance as the trained PyTorch network, to within 1 in 10,000.

@@ 153-154
And a missing file is refused when the wrapper is made, not at the first face.

@@ 89-94
A PNG of random speckle (which doesn't compress) 640 × 640 — over a megabyte, twice the service's upload limit — is cropped like any other frame. The first real renders were refused before this.
