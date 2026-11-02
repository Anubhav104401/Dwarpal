---
fingerprint: bb57f7c2d5ea9ca8
---
**Tests for the render detector** (§5.9.4).

@@ 1-2
What this file tests: crops only from clips that may be kept, a network that learns, honest thresholds, and an export that needs passing gates and answers as PyTorch does.

@@ 4
The project-wide type-hint setting.

@@ 6-15
Paths, NumPy, pytest, PyTorch; the modules under test; the face type, the service's wrapper and the crop.

@@ 17
The three splits.

@@ 20-26
**`OneFace`** stands in for the face finder: one face, the middle half of every picture.

@@ 29-37
**`people`**: IDs that fill every split with `per_split` people each — chosen by trying numbers until `split_of` has put enough in each.

@@ 40-50
**`frames`**: fake pictures. Real faces as random speckle, renders as smooth colour ramps — a difference a small network learns in a few epochs, so the test is about the machinery, not about faces.

@@ 53-56
**`clips`**: a folder of clips shared by the tests below (`module` scope: made once). Three real and three made-up people per split…

@@ 57-61
…a consent for each real person…

@@ 62-67
…and 12 frames per person, filed through `renders.record` — so the consent rules apply here too.

@@ 70-72
Preparing every frame: 72 crops per split (6 people × 12).

@@ 73-76
The test split holds 80 × 80 crops of both labels and both kinds, and no person in it is in training.

@@ 78-85
A clip whose frames have vanished makes `check` fail, and `prepare` refuses; the folder is put back afterwards, even if the test fails (`finally`).

@@ 88-93
A network built from the shapes alone answers two chances that add up to 1, for each of four faces.

@@ 96-101
`augment` keeps an 80 × 80 picture of bytes, and changes it.

@@ 102
Three real crops and one rendered: each real one weighs 1/3, the rendered one 1, so both labels are drawn equally often.

@@ 105-108
100 real scores spread from 0 to 0.99, and 10 renders at 0.999.

@@ 109-111
The threshold calls at most 5 % of the real ones rendered — and is as low as that allows: a little lower calls more.

@@ 112
At that threshold the balanced error is small: every render caught, at most 5 % of the real refused.

@@ 115-119
Train for 4 epochs from scratch, with progress lines collected: four lines, and a saved network.

@@ 121-125
Evaluated against a gate it can't pass (50 real people): the test rests on 3 real and 3 made-up people, and both error rates are low — the network learnt.

@@ 126-127
So the export is refused, naming the gate.

@@ 129-134
With a gate it passes, the export writes the ONNX file and a manifest that says *recorded only*.

@@ 136-143
The inference service's wrapper, running the exported file through OpenCV, gives the same chance as the trained PyTorch network, to within 1 in 10,000.

@@ 144-145
And a missing file is refused when the wrapper is made, not at the first face.
