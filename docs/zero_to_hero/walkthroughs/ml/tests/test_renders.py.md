---
fingerprint: 074bb8d62dd834c6
---
**Tests for the render detector's own data** (decision D22, 2 Nov 2026).

@@ 1
What this file tests: consent comes first, a person is never in two splits, and withdrawing deletes.

@@ 3
The project-wide type-hint setting.

@@ 5-10
Paths, NumPy (for fake frames), pytest, and the module under test.

@@ 13-14
Three tiny 8 × 8 frames, each a different grey: enough to write as JPEGs.

@@ 17-22
A consent register in the temporary folder with one consent, `c-001`, given by `person-001` — withdrawn on a date, if one is passed.

@@ 25-30
No register yet: a real clip is refused. Then a register: filming `person-002` under `person-001`'s consent is refused too.

@@ 31-33
The right person under their own consent is kept, with its three frames.

@@ 34
And `check` finds nothing wrong.

@@ 37-45
Renders: a render filed as a real person, a render with a consent ID, a camera name with capitals and spaces, and a clip with no frames are each refused, with the reason in the message.

@@ 46-47
A proper one is kept, and counts as rendered.

@@ 50-55
A rendered sequence of two frames, and a note that isn't an image.

@@ 56-59
`inject` adds it once as an injected clip, under its light set-up's name…

@@ 60
…with both frames and without the note…

@@ 61
…and running it again adds nothing.

@@ 64-69
A person's clip and a render's. Withdrawing before the register says so is refused.

@@ 70-71
The register now says withdrawn; `check` fails, because a clip filmed under it is still there.

@@ 72-75
`withdraw` deletes that one clip and its folder; the render stays, and `check` passes again.

@@ 78-82
A thousand IDs: each always lands in the same split, and the shares come out close to 70 / 15 / 15.
