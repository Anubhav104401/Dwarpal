---
fingerprint: 898c4977b8aee522
---
**Capture quality** — the first layer of the "onion" (§3.3, Choice 6). Before judging age, check that the frame is fit to be judged:

- exactly one clear face;
- not too dark or too bright;
- sharp;
- big enough;
- looking roughly at the camera.

A bad frame produces **named flags** such as `too_dark`. The decision engine turns these into a *retry* with helpful advice, rather than guessing from poor evidence.

!!! honest "Honest limitation"
    The limits below are **sensible starting values**, chosen by reasoning, not yet by measurement. Phase 3 tunes them using genuine webcam attempts and records the evidence. They live in one settings object (`QualityRules`), so tuning them never touches the logic.

@@ 1
The docstring lists everything this module checks.

@@ 3
The project-wide type-hint setting.

@@ 5
`dataclass`, for the settings and result records.

@@ 7-8
OpenCV and NumPy.

@@ 10-11
Our `Image` type and the `Face` record.

@@ 14-15
**`QualityRules` — every limit in one place.** It is frozen, so the rules can't be changed by accident while running.

@@ 16
`min_detector_score = 0.8` — the detector must be at least 80 % sure it is a face.

@@ 17-18
Average brightness of the face must lie between **22 %** and **92 %** of full white. Below that, detail is lost in the dark; above it, skin washes out.

@@ 19
`min_sharpness = 30.0` — the blur limit, on the scale explained at line 62.

@@ 20
`min_eye_distance = 40.0` — the eyes must be at least 40 pixels apart. Below that, the face is too small (too far from the camera) for its fine details to be seen.

@@ 21
`max_yaw_ratio = 0.25` — how far the head may be turned sideways (the measure is explained at line 46).

@@ 24
`DEFAULT_RULES` — one shared copy of the defaults. Using it as a default argument (line 52) avoids creating a new object on every call, which the bugbear linter rule (B008) warns about.

@@ 27-35
**`Quality` — the result of checking one frame**: the number of faces, and the main face's score, brightness, sharpness, eye distance and yaw. `flags` is a tuple of problem names, empty for a good frame.

@@ 38
**`face_region`** — cut the face's rectangle out of the picture.

@@ 39-40
The box from the detector, and the picture's height and width.

@@ 41-42
**Clamp the box to the picture.** A face near the edge can have a box that pokes outside the photo — even negative coordinates. `max(0, …)` and `min(width, …)` keep every side inside. `int(…)` rounds down to whole pixels.

@@ 43
**Slicing**: `image[top:bottom, left:right]` takes rows `top` to `bottom` and columns `left` to `right`. NumPy returns a *view* of the original pixels, with nothing copied.

@@ 46
**`yaw_ratio` — how far is the head turned sideways?** When you look straight at the camera, your nose tip sits halfway between your eyes. Turn your head and it moves towards one eye.

@@ 47
Unpack the three landmarks we need: the two eyes and the nose tip.

@@ 48
The x position of the point halfway between the eyes.

@@ 49
How far the nose is from that midpoint, **divided by the eye distance**. Dividing makes the measure independent of how big the face is in the picture: near or far, the same head turn gives the same number. Roughly, 0 means facing the camera and ±0.25 means clearly turned.

`max(…, 1.0)` prevents dividing by zero if the two eye points ever coincide.

@@ 52
**`assess` — check one frame.** It receives the picture and the faces the detector found, most confident first.

@@ 53-54
**No face at all** → the single flag `no_face`.

@@ 55
Judge the main face: the most confident one.

@@ 56-58
Cut it out. If the clamped box is empty (a degenerate detection), treat it as no face.

@@ 59
Convert to **greyscale**, keeping only how light each pixel is. Brightness and sharpness don't need colour.

@@ 60
**Brightness** — the average grey value (0–255), divided by 255 to give 0–1.

@@ 61
Resize the face to a standard 112 × 112 before measuring sharpness. Without this, a large face would look "sharper" than a small one just because it has more pixels. `INTER_AREA` is the best method for shrinking.

@@ 62
**Sharpness, measured by the variance of the Laplacian.**

- The **Laplacian** is a filter that responds strongly wherever brightness changes suddenly — at edges and fine detail — and weakly in smooth areas.
- A sharp photo has many strong, varied responses; a blurred one has only weak ones.
- The **variance** (how spread out the responses are) is therefore a single number for "how much crisp detail" there is.

`cv2.CV_64F` keeps the results as precise decimals, so negative values aren't cut off. This is a classic, fast, well-understood blur measure.

@@ 63
How far the head is turned (line 46).

@@ 64-72
**Every check, by name**, as a dict of *flag name → did this check fail?*:

- `multiple_faces` — a **second** face with a high score. Someone else in view could mean a helper, or a photo held up next to the user;
- `low_confidence` — the detector isn't sure this is a face;
- `too_dark` / `too_bright` — brightness outside the allowed range;
- `too_blurry` — not enough sharp detail;
- `face_too_small` — eyes less than 40 pixels apart;
- `not_frontal` — the head is turned too far.

@@ 73
Keep the names of the checks that failed, in a stable order. The decision engine picks the most useful advice to show from these.

@@ 74-76
Return the full result. The brightness is clipped into 0–1 as a guarantee: it can't actually exceed 1, but the contracts insist on the range, and an explicit clip makes that certain.
