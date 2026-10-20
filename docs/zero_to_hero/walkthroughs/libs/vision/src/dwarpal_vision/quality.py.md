---
fingerprint: d6a9ee613dfb9b7b
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

@@ 36
`pitch_ratio` — how far the head is tilted up or down (added in Phase 3, for the liveness challenge's "look up"). It has a default, `0.0`, so it must come last: Python requires fields with defaults to follow those without.

@@ 39
**`face_region`** — cut the face's rectangle out of the picture.

@@ 40-41
The box from the detector, and the picture's height and width.

@@ 42-43
**Clamp the box to the picture.** A face near the edge can have a box that pokes outside the photo — even negative coordinates. `max(0, …)` and `min(width, …)` keep every side inside. `int(…)` rounds down to whole pixels.

@@ 44
**Slicing**: `image[top:bottom, left:right]` takes rows `top` to `bottom` and columns `left` to `right`. NumPy returns a *view* of the original pixels, with nothing copied.

@@ 47
**`yaw_ratio` — how far is the head turned sideways?** When you look straight at the camera, your nose tip sits halfway between your eyes. Turn your head and it moves towards one eye.

@@ 48
Unpack the three landmarks we need: the two eyes and the nose tip.

@@ 49
The x position of the point halfway between the eyes.

@@ 50
How far the nose is from that midpoint, **divided by the eye distance**. Dividing makes the measure independent of how big the face is in the picture: near or far, the same head turn gives the same number. Roughly, 0 means facing the camera and ±0.25 means clearly turned.

`max(…, 1.0)` prevents dividing by zero if the two eye points ever coincide.

@@ 53
**`pitch_ratio` — how far is the head tilted up or down?** The same idea as `yaw_ratio`, turned on its side. YuNet's five landmarks are the two eyes, the nose tip and the two mouth corners.

@@ 54-55
The height (y) of the point halfway between the eyes, and of the point halfway between the mouth corners. In pictures, y grows *downwards*: the mouth's y is larger than the eyes'.

@@ 56
Where the nose tip sits between eyes and mouth, as a fraction: 0 would be level with the eyes, 1 level with the mouth. Facing the camera it is usually about 0.5. **Look up**, and the nose tip appears to rise towards the eyes in the picture, so the ratio falls. Dividing by the eyes-to-mouth distance makes it independent of how big the face is. `max(…, 1.0)` prevents dividing by zero.

@@ 59
**`people`** (added in Phase 3) — how many *different people* the detections show. Its inputs: the detections (most confident first), the quality rules, and the picture's size (height, width), when known. It answers with a whole number.

@@ 60-64
The docstring gives the rule, and the owner's tests behind it. YuNet sometimes reports the same face twice (a box inside the face: a beard, a lit cheek), and in the owner's room it reported a small, steady face-like shape at the side of every photo. But when the owner held a phone up to the camera and peeked from behind it, their own partly hidden face showed — in the middle, or large at the edge — and that *should* count as a second person.

@@ 65-66
No detections: nobody.

@@ 67-68
The main face — the most confident detection — and its box: left edge, top edge, width, height.

@@ 69-73
First, the detections whose centre lies **outside** the main face's box. A box inside the face is the same face detected twice. `a <= b <= c` is Python's way of writing "b is between a and c"; `face.box[0] + face.box[2] / 2` is the centre's x position.

@@ 74-79
Of those, a detection counts as another person if it is **at least as large as the main face** — however unsure the detector is. As the comment says, a face closer to the camera than the main one is a real person, often partly hidden or cut off by the edge, which lowers the detector's confidence. A poster or a speck is never that large.

@@ 80-85
… **or** if it is confident (at least the rules' 0.8) and big enough: at least a quarter of the main face's size in the middle of the picture, or half anywhere else. The answer is the main face plus the others that counted.

@@ 88-90
**`central`** — whether a face's centre lies in the middle of the picture: its central 60 % across and 80 % down. As the docstring says, a partly hidden second face there is more likely the person holding up a phone than a poster at the side.

@@ 91-92
Without the picture's size, nothing counts as central (the stricter rule applies).

@@ 93-95
The picture's height and width, the face's box, and the test: is the centre between 20 % and 80 % of the width, and between 10 % and 90 % of the height?

@@ 98
**`assess` — check one frame.** It receives the picture and the faces the detector found, most confident first.

@@ 99-100
**No face at all** → the single flag `no_face`.

@@ 101
Judge the main face: the most confident one.

@@ 102
Count the people, once, for the checks and the result below — passing the picture's height and width, so faces in its middle can be told apart from faces at its edges.

@@ 103-105
Cut it out. If the clamped box is empty (a degenerate detection), treat it as no face — still reporting how many people were seen.

@@ 106
Convert to **greyscale**, keeping only how light each pixel is. Brightness and sharpness don't need colour.

@@ 107
**Brightness** — the average grey value (0–255), divided by 255 to give 0–1.

@@ 108
Resize the face to a standard 112 × 112 before measuring sharpness. Without this, a large face would look "sharper" than a small one just because it has more pixels. `INTER_AREA` is the best method for shrinking.

@@ 109
**Sharpness, measured by the variance of the Laplacian.**

- The **Laplacian** is a filter that responds strongly wherever brightness changes suddenly — at edges and fine detail — and weakly in smooth areas.
- A sharp photo has many strong, varied responses; a blurred one has only weak ones.
- The **variance** (how spread out the responses are) is therefore a single number for "how much crisp detail" there is.

`cv2.CV_64F` keeps the results as precise decimals, so negative values aren't cut off. This is a classic, fast, well-understood blur measure.

@@ 110
How far the head is turned (`yaw_ratio`, above).

@@ 111-119
**Every check, by name**, as a dict of *flag name → did this check fail?*:

- `multiple_faces` — a **second** face with a high score. Someone else in view could mean a helper, or a photo held up next to the user;
- `low_confidence` — the detector isn't sure this is a face;
- `too_dark` / `too_bright` — brightness outside the allowed range;
- `too_blurry` — not enough sharp detail;
- `face_too_small` — eyes less than 40 pixels apart;
- `not_frontal` — the head is turned too far.

Since Phase 3, `multiple_faces` uses `people`'s count, so a second box on the same face, or a small shape in the background, no longer counts.

@@ 120
Keep the names of the checks that failed, in a stable order. The decision engine picks the most useful advice to show from these.

@@ 121-130
Return the full result: the number of people seen, the detector's score, the brightness — clipped into 0–1 as a guarantee: it can't actually exceed 1, but the contracts insist on the range, and an explicit clip makes that certain — and the other measurements. The last value is the head's tilt, `pitch_ratio`, added in Phase 3.
