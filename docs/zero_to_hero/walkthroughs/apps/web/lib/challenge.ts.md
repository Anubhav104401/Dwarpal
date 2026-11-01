---
fingerprint: 8bd256131433cf4d
---
The verify page's side of the **liveness challenge** (§5.3): the shape of a challenge, the browser's signals, how a head pose is read from the face, and how the server's answer is checked before the page plays it.

Two numbers describe the head here, exactly as on the server: **yaw** (how far it is turned sideways) and **pitch** (how far it is tilted up). Using the same formulas on both sides means the page and the server agree on what a pose is — the page only decides *when* to take a photo, and the server checks the photo itself.

@@ 1
The doc comment: what the server asked for, how a pose is read, what the browser reports.

@@ 3
`Pose` — the three head poses, as a TypeScript **union type**: a value of this type must be exactly one of these three texts.

@@ 4
`Phase` — what a photo is labelled with: `"baseline"` (looking straight ahead, during the colours) or one of the poses. `| Pose` adds all three of them.

@@ 6-11
**`Challenge`** — a challenge as the page uses it: its ID, the poses in order, the colours, and how long each colour lasts (`stepMs`). The page spells names in its own style (`stepMs`), not the API's (`step_ms`); `readChallenge` converts.

@@ 13-19
**`Signals`** — what the browser reports about itself: whether a program is driving it, whether the camera looks virtual, how long the page was hidden, and whether the colours were shown. The comment repeats the rule: the server never trusts these on their own.

@@ 21-27
**`HeadAngles`** — the two numbers, with what they mean:

- `yaw` — the sideways turn. **Positive when the person turns to their left.** Photos are not mirrored, so a person turning to their left moves their nose towards the *right* of the picture;
- `pitch` — where the nose sits between the eyes and the mouth. About 0.55 looking straight ahead; smaller when the head tilts back, because the nose appears to rise towards the eyes.

@@ 29-31
The comment explains the page's **targets**: shifts from the person's own frontal angles, set **well above** the server's limits (0.18 for a turn, 0.03 for looking up). In the owner's tests, the page's landmarks (MediaPipe's mesh) read a head as more turned than the server's (YuNet's five points) did. Aiming higher on the page means that when its meter is full, the photos pass on the server too.

@@ 32-33
`TURN_SHIFT = 0.25` and `RAISE_SHIFT = 0.12` — the page's targets for a turn and for lifting the chin.

@@ 34
`FRONTAL_YAW = 0.15` — the guidance asks people to look straighter than this before starting.

@@ 36
The three poses as a list, for checking the server's answer. `readonly` — it can't be changed.

@@ 37
`COLOUR` — a **regular expression** for a web colour: `#` and exactly six hexadecimal digits, the same rule as the server's contract.

@@ 38-40
`VIRTUAL_CAMERA` — names that virtual-camera programs give their pretend cameras: OBS, ManyCam, XSplit, Snap Camera and others. Such a program can feed *any* video — including a recording or a deepfake — to the page as if it were a camera. In the pattern:

- `\b` — a word boundary, so `ndi` matches the word "NDI" but not the inside of another word;
- `( … | … )` — any one of the names;
- `i` at the end — ignore upper and lower case.

As the comment says, the page only *reports* a match. Some people use these programs for ordinary video calls; the server weighs it with everything else.

@@ 42
**`isVirtualCamera`** — whether a camera's name matches. `.test` returns `true` or `false`.

@@ 44-45
**`poseProgress`** — how much of the pose's target the head has reached, from its frontal angles: 0 (not at all, or the wrong way) to 1 (enough). It drives the on-screen meter, and a full meter (1) is what the page waits for.

@@ 46
Its inputs: the pose, the head's angles now, and the frontal angles to measure from.

@@ 47-52
How far the head has moved in the pose's direction, as a share of the target: for a left turn, the rise in yaw divided by `TURN_SHIFT`; for a right turn, the fall in yaw; for looking up, the fall in pitch divided by `RAISE_SHIFT`. `a ? b : c ? d : e` is a chain of choices: "if a, b; otherwise if c, d; otherwise e".

@@ 53-54
Keep it between 0 and 1: a turn the wrong way gives a negative share, shown as 0; a turn past the target, as 1.

@@ 56
**`median`** — the middle value of a list of numbers.

@@ 57
Sort a copy (`[...values]` copies the list, so the caller's list isn't reordered), smallest first. `(a, b) => a - b` tells `sort` to compare numbers by size; without it, JavaScript would sort them as text.

@@ 58
The position of the middle.

@@ 59-60
With an odd number of values, the one in the middle; with an even number, the average of the two middle ones. The `?? 0` parts only satisfy TypeScript, which can't know those positions exist.

@@ 62-63
**`frontalAngles`** — the person's angles when facing the camera: the median of the landmarker readings taken with the baseline photos, as on the server. `readonly` promises the list isn't changed.

@@ 64-66
No readings — the landmarker couldn't see a face, or isn't running: `null`. The page can't measure poses then, so it simply waits out each pose's time.

@@ 67-68
The median yaw and the median pitch.

@@ 70-73
**`Point`** — a position in the picture: `x` across, `y` down. MediaPipe gives positions as fractions of the picture's width and height, from 0 to 1.

@@ 75
**`middle`** — the point halfway between two points.

@@ 77-78
**`anglesFrom`** — the head's angles from four points of the face: the two eyes, the nose tip and the middle of the mouth. As the comment says, the formulas are the server's (`quality.py`).

@@ 79
The point between the eyes.

@@ 80
The distance between the eyes — `Math.hypot` is Pythagoras: the length of the line from one eye to the other. `Math.max(…, 1e-6)` (one millionth) keeps it from ever being zero, so the division below can't fail.

@@ 81
How far the mouth is below the eyes, also never zero.

@@ 82-83
**Yaw**: how far the nose is to the side of the eyes' midpoint, measured in eye distances. **Pitch**: how far down from the eyes the nose sits, as a fraction of the way to the mouth. Dividing makes both independent of how big the face is in the picture.

@@ 85-86
**`readChallenge`** — check and convert the server's answer. The page treats the answer as untrusted data (`Record<string, unknown>`: an object whose values could be anything) and refuses anything it can't play exactly.

@@ 87
Take the four fields out, renaming `challenge_id` to `id` and `step_ms` to `stepMs` as they come (`challenge_id: id` means "the field `challenge_id`, into a variable named `id`").

@@ 88-99
**Every check at once**, joined with `&&` ("and"): the ID is a non-empty text; `poses` is a non-empty list (`Array.isArray`) whose every item (`every`) is a known pose; `colours` is a list of at least two items, each a well-formed colour; `stepMs` is a number from 400 to 2000. `pose as Pose` only tells TypeScript to allow the comparison; `includes` does the real check.

@@ 100-102
If anything is wrong, stop with an error — the camera screen shows it like a camera error.

@@ 103-104
Return the challenge in the page's own shape. Thanks to the checks, the type assertions (`as Pose[]`) are safe.
