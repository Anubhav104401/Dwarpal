---
fingerprint: f9ba1d676be89c7a
---
**Tests for the render detector's own data** (decision D22, 2 Nov 2026).

@@ 1
What this file tests: consent comes first, a person is never in two splits, and withdrawing deletes.

@@ 3
The project-wide type-hint setting.

@@ 5-11
Paths, OpenCV (to write fake rendered frames), NumPy (for fake frames), pytest, and the module under test.

@@ 14-15
Three tiny 8 × 8 frames, each a different grey: enough to write as JPEGs.

@@ 18-23
A consent register in the temporary folder with one consent, `c-001`, given by `person-001` — withdrawn on a date, if one is passed.

@@ 26-31
No register yet: a real clip is refused. Then a register: filming `person-002` under `person-001`'s consent is refused too.

@@ 32-34
The right person under their own consent is kept, with its three frames.

@@ 35
And `check` finds nothing wrong.

@@ 38-46
Renders: a render filed as a real person, a render with a consent ID, a camera name with capitals and spaces, and a clip with no frames are each refused, with the reason in the message.

@@ 47-48
A proper one is kept, and counts as rendered.

@@ 51-56
A rendered sequence of two frames, and a note that isn't an image.

@@ 57-60
`inject` adds it once as an injected clip, under its light set-up's name…

@@ 61
…with both frames and without the note…

@@ 62
…and running it again adds nothing.

@@ 65-70
A person's clip and a render's. Withdrawing before the register says so is refused.

@@ 71-72
The register now says withdrawn; `check` fails, because a clip filmed under it is still there.

@@ 75-79
`withdraw` deletes that one clip and its folder, and the prepared crops with it; the render stays, and `check` passes again.

@@ 82-86
A thousand IDs: each always lands in the same split, and the shares come out close to 70 / 15 / 15.

@@ 73-74
Prepared crops on disk, as `render_detector.prepare` would leave them.

@@ 89-93
A rendered sequence of four frames, each a different grey (0, 60, 120, 180).

@@ 94-101
A fake screen that records what it was shown, and a fake camera that sees whatever is on the screen.

@@ 103-105
Filming: the first frame is shown for the settling frames, then each frame once, in order; the clip is a `screen_render` of `render-007`, the sequence's person.

@@ 106-107
And each kept frame is the camera's picture of the matching rendered frame (JPEG may shift a grey by a step or two).

@@ 109-110
A folder whose parent isn't a made-up person's ID is refused…

@@ 111-116
…and an empty sequence is refused without showing anything.

@@ 117
Neither left a half-written clip folder behind.
