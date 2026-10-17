---
fingerprint: b7a73bc5d020c854
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

@@ 29-32
The page's limits, **a little stricter than the server's** (the comment gives the server's: 0.35 and 0.38). A pose must be turned to a yaw of at least 0.4, or tilted to a pitch of 0.35 or less. Being stricter means a photo the page is happy with will also satisfy the server — so honest people aren't failed by a small disagreement. `FRONTAL_YAW = 0.15`: the guidance asks people to look straighter than this before starting.

@@ 34-38
**`CUES`** — the instruction shown for each pose. "Slowly" matters: a fast turn blurs, and the camera may miss it. `Record<Pose, string>` makes TypeScript check that every pose has exactly one instruction.

@@ 40
The three poses as a list, for checking the server's answer. `readonly` — it can't be changed.

@@ 41
`COLOUR` — a **regular expression** for a web colour: `#` and exactly six hexadecimal digits, the same rule as the server's contract.

@@ 42-44
`VIRTUAL_CAMERA` — names that virtual-camera programs give their pretend cameras: OBS, ManyCam, XSplit, Snap Camera and others. Such a program can feed *any* video — including a recording or a deepfake — to the page as if it were a camera. In the pattern:

- `\b` — a word boundary, so `ndi` matches the word "NDI" but not the inside of another word;
- `( … | … )` — any one of the names;
- `i` at the end — ignore upper and lower case.

As the comment says, the page only *reports* a match. Some people use these programs for ordinary video calls; the server weighs it with everything else.

@@ 46
**`isVirtualCamera`** — whether a camera's name matches. `.test` returns `true` or `false`.

@@ 48
**`reached`** — whether the head shows the given pose.

@@ 49-51
Turned to the left: yaw at least `TURNED_YAW`.

@@ 52-54
Turned to the right: yaw at most `-TURNED_YAW` — the same distance, the other way.

@@ 55-56
Otherwise the pose is `look_up`: pitch at most `RAISED_PITCH`.

@@ 58-61
**`Point`** — a position in the picture: `x` across, `y` down. MediaPipe gives positions as fractions of the picture's width and height, from 0 to 1.

@@ 63
**`middle`** — the point halfway between two points.

@@ 65-66
**`anglesFrom`** — the head's angles from four points of the face: the two eyes, the nose tip and the middle of the mouth. As the comment says, the formulas are the server's (`quality.py`).

@@ 67
The point between the eyes.

@@ 68
The distance between the eyes — `Math.hypot` is Pythagoras: the length of the line from one eye to the other. `Math.max(…, 1e-6)` (one millionth) keeps it from ever being zero, so the division below can't fail.

@@ 69
How far the mouth is below the eyes, also never zero.

@@ 70-71
**Yaw**: how far the nose is to the side of the eyes' midpoint, measured in eye distances. **Pitch**: how far down from the eyes the nose sits, as a fraction of the way to the mouth. Dividing makes both independent of how big the face is in the picture.

@@ 73-74
**`readChallenge`** — check and convert the server's answer. The page treats the answer as untrusted data (`Record<string, unknown>`: an object whose values could be anything) and refuses anything it can't play exactly.

@@ 75
Take the four fields out, renaming `challenge_id` to `id` and `step_ms` to `stepMs` as they come (`challenge_id: id` means "the field `challenge_id`, into a variable named `id`").

@@ 76-87
**Every check at once**, joined with `&&` ("and"): the ID is a non-empty text; `poses` is a non-empty list (`Array.isArray`) whose every item (`every`) is a known pose; `colours` is a list of at least two items, each a well-formed colour; `stepMs` is a number from 400 to 2000. `pose as Pose` only tells TypeScript to allow the comparison; `includes` does the real check.

@@ 88-90
If anything is wrong, stop with an error — the camera screen shows it like a camera error.

@@ 91-92
Return the challenge in the page's own shape. Thanks to the checks, the type assertions (`as Pose[]`) are safe.
