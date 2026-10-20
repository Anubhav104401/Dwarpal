---
fingerprint: 2a19b9959ad7e056
---
**Telling a real face from a face presented to the camera** — a printed photo, or a phone screen showing a photo or a video. This is the empty layer L2 of ADR-0007, **passive presentation-attack detection**, filled after the owner's red-team tests showed that a phone carousel of their own posed selfies could pass every other check (§5.3.6).

It uses **MiniFASNet**: two small networks from the Silent-Face-Anti-Spoofing project (Apache-2.0), trained on thousands of real faces and attacks to spot the tell-tale look of paper and screens. Each looks at a differently sized crop around the face — one 2.7 face-sizes across, one 4 — and their answers are averaged. In the owner's tests their verdict separated real from presented faces by a wide margin: real 0.94–0.995, phone 0.006–0.195.

The file also holds a simpler, hand-made measure: the **screen pattern**, a sign of a screen's pixel grid in the face.

@@ 1-4
The module docstring: what it tells apart, with which networks, and where their ONNX files come from.

@@ 6
The project-wide type-hint setting.

@@ 8-10
A lock, `dataclass`, and paths.

@@ 12-13
OpenCV and NumPy.

@@ 15-16
The library's picture and face types.

@@ 18
The networks' input: an 80 × 80 picture.

@@ 19-20
As the comment says: the networks answer three probabilities, and the second — label 1 in the original project — is "a real face". (The other two are kinds of attack.)

@@ 23-28
**`SpoofModel`** — one network's ONNX file and the crop size it was trained on, in face-sizes (2.7 or 4).

@@ 31-33
**`crop`** — the crop the networks were trained on, as the docstring says. It must match the original project's exactly: a network judges best what it was trained to see.

@@ 34-35
The picture's size and the face's box.

@@ 36
The crop can't be larger than the picture: shrink the scale if `scale` face-sizes wouldn't fit. `max(…, 1.0)` avoids dividing by zero.

@@ 37-38
The crop's size, and its top-left corner when centred on the face.

@@ 39-40
Where the crop would cross an edge, slide it back inside — never stretch it.

@@ 41-42
Cut it out and resize it to 80 × 80, as whole-number pixels.

@@ 45-48
**`screen_pattern`** — how strongly a regular fine pattern stands out in the middle of the face. As the docstring says, re-filming a screen leaves its grid of pixels and **moiré** stripes (the wavy bands two fine grids make together) in the picture; skin has nothing so regular. It is measured on the picture as it came: resizing would smooth the pattern away.

@@ 49-52
The middle of the face: the inner 60 % of its box, kept inside the picture.

@@ 53
In grey, as decimals.

@@ 54-55
Too small to measure (under 32 pixels across): 0.

@@ 56
Subtract the average, so the overall brightness doesn't dominate what follows.

@@ 57
A **Hanning window**: a smooth weighting that fades to 0 at the edges. Without it, the crop's hard edges would themselves look like fine detail.

@@ 58
The **Fourier transform** (`fft2`) splits the picture into regular waves of every size and direction, and tells how strong each is — its **spectrum**. `fftshift` puts the slow waves in the middle and the fine ones at the edges; `np.abs` takes each wave's strength.

@@ 59-62
For each point of the spectrum, how fine its wave is: its distance from the middle, as a fraction (0 = smooth, 0.5 = the finest the picture can hold). `np.indices` gives every point's row and column numbers; `np.hypot` is Pythagoras.

@@ 63
Keep the fine waves only: between 0.15 and 0.5.

@@ 64
The answer: how far the strongest fine waves (the top 0.1 %) stand above the typical one (the median), on a logarithmic scale (`log10`: 1 means ten times stronger). A screen's regular grid makes a few very strong peaks; skin's fine detail is spread out. In the owner's tests real faces measured 0.99–1.14 and phones 1.16–1.31 — a real but narrow gap, so it is recorded, not decided on.

@@ 67-73
**`SpoofDetector`** — load the networks. Missing files are a clear error, with the command that makes them.

@@ 74
Each network from its ONNX file, kept with its crop size. OpenCV runs ONNX files directly.

@@ 75
A lock, as for the other models.

@@ 77-78
**`real`** — how likely the face is a real one in front of the camera, from 0 to 1: the two networks' average.

@@ 79-82
For each network, under the lock: its crop of the face.

@@ 83-84
As the comment says, the pixels exactly as the networks were trained on them: blue-green-red (OpenCV's order, kept), values 0–255 (not divided), channels first, a batch of one.

@@ 85
Run it and keep the "real face" probability.

@@ 86
The average of the two.
