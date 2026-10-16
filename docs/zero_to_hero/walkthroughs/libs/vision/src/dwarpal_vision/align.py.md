---
fingerprint: 58b1c0d8a685d15b
---
**Face alignment.** People hold their heads tilted, near or far, off to one side. Before an AI model looks at a face, we rotate, scale and shift the picture so that the **eyes, nose and mouth always land on the same pixel positions**. The model can then spend its effort on what changes with age, not on where the face happens to be.

!!! kid "Explain like I'm six"
    Before comparing two handwriting samples, you'd first turn both pages the same way up and make them the same size. Alignment does that for faces.

The movement we use is a **similarity transform**: rotation + uniform scaling + shifting. It never stretches or squashes the face, so the person's proportions are left untouched. That matters a lot for age, because proportions change as children grow (§1.6).

@@ 1
The docstring: what alignment achieves.

@@ 3
The project-wide type-hint setting.

@@ 5-6
OpenCV for the geometry; NumPy for the coordinate arrays.

@@ 8-9
Our own `Image` type and the `Face` record from the detector.

@@ 11-14
**The template** — where the five points should land in a 112 × 112 face picture, in the same order as YuNet's landmarks: right eye, left eye, nose tip, right mouth corner, left mouth corner.

These coordinates are the standard template used throughout face research (it comes from the ArcFace work). Using a known standard rather than invented numbers means our crops resemble those many pre-trained models were built on — which matters for Phase 2.

@@ 17
**`template(size, margin)`** — scale the 112-pixel template to any output size, leaving a **margin** around the face. Age clues also live outside the tight eyes-to-mouth area: the forehead, hairline, jaw and cheeks.

@@ 18
The scale factor: from 112 to `size` pixels, shrunk by the margin. With `size = 224` and `margin = 0.25`: 224 / 112 × 0.75 = **1.5**. The face occupies about the central 75 % of the picture.

@@ 19
Move the template's centre (56, 56) to the origin, scale it, then move it to the new picture's centre (`size / 2`). Every point is multiplied by the same factor, so the proportions are kept.

@@ 22
**`align_face`** — returns a `size × size` aligned crop of one face. The defaults (224 pixels, 25 % margin) suit typical vision models. Phase 2 may tune the margin by experiment.

@@ 23
**Work out the transform.** `cv2.estimateAffinePartial2D` finds the best rotation + scale + shift that moves the five detected points onto the five template points. "Partial" affine means *no* stretching or shearing — exactly a similarity transform.

`method=cv2.LMEDS` (*least median of squares*) is a **robust** fit. If one landmark is badly placed — say a mouth corner hidden by a hand — it is effectively outvoted by the others instead of spoiling the whole fit. The result is a 2 × 3 matrix; the underscore discards a second output (which points were trusted).

@@ 24-25
If no transform can be found — for example, if all five points sit on top of each other — fail clearly instead of producing a garbage picture.

@@ 26
**Apply the transform.** `cv2.warpAffine` builds the new picture: for every output pixel it looks up where that pixel comes from in the original.

- `INTER_LINEAR` blends the four nearest original pixels, for smooth results.
- `BORDER_REPLICATE` fills any area outside the original photo by repeating its edge pixels, rather than with black. Black bars would be an unnatural signal that a model might wrongly learn from.

@@ 27
Return the crop as an 8-bit `Image`, explicitly typed (see `decode.py`, line 55).
