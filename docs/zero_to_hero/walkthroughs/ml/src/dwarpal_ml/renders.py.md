---
fingerprint: 9f5f1c3aefb4e62f
---
**The render detector's own data** (decision D22, 2 Nov 2026; ADR-0021): a tool that films and files clips — of real people only under a standing written consent, and of made-up people we render — splits them by person, and deletes a person's clips when they withdraw.

@@ 1-7
The module's docstring: the render detector's own data (decision D22, ADR-0021) — clips of consenting real people and of made-up people we render — and where it lives: `.datasets/render-detector/`, which git ignores, so no clip can be committed.

@@ 9
The project-wide type-hint setting.

@@ 11-26
Command-line options, CSV files, fingerprints (for the splits), patterns, copying and deleting folders, the error stream, TOML (the consent register's format), counting, typed collections, data classes, paths, the types for a fixed set of words; OpenCV (the camera and JPEG files) and NumPy (a frame is an array of pixels).

@@ 28
The repository's root, from the licence register's module.

@@ 30
Where everything is kept.

@@ 32-33
The three **kinds** of clip, written once as a type (so the type checker rejects a misspelt kind) and read back as a tuple, for the command line's choices.

@@ 34-36
Who may appear in each kind: `person-NNN` — a real person, never by name — only in `real` clips; `render-NNN` — one of our made-up people — only in rendered ones.

@@ 37
Short, lower-case names for cameras and settings (`laptop`, `study-dim`): they become part of folder names.

@@ 38
Which files count as a rendered frame.

@@ 41-48
**`Clip`**: one clip's line in `clips.csv` — its ID, kind, person, camera, room and light, and for a real person the consent it was filmed under.

@@ 50-52
Every kind except `real` is a render: the label the detector learns.

@@ 55-60
**`Consent`**: one entry of the consent register — its ID (the one written on the signed form), the person, when it was given, and when it was withdrawn (empty while it stands).

@@ 62-64
A consent stands until it is withdrawn.

@@ 67-72
**`read_clips`**: the list of clips, or none yet. The `type: ignore` is because a CSV row's values are plain text, while `kind` expects one of three words; `check` catches a wrong one.

@@ 75-80
**`write_clips`**: the whole list written again, sorted, with a header line taken from `Clip`'s fields.

@@ 83-91
**`load_consents`**: the register, as a dictionary from consent ID to `Consent`; empty if there is no register yet. Dates are kept as text: they are only compared and printed.

@@ 94-95
**`consent_problem`** — the one rule every clip passes, when filmed and again at every `check`: why it may not be kept, or `None`.

@@ 96-99
The kind must be known, and the person's ID must fit the kind: no real person can be filed as a render, nor a render as a person.

@@ 100-101
A render has no one to give consent, so a consent ID on it is a mistake.

@@ 102-104
A real clip needs a consent in the register…

@@ 105-106
…given by that same person…

@@ 107-108
…and not withdrawn.

@@ 109
Nothing wrong.

@@ 112-120
**`problems`**: every clip checked — the rule above, and that it has frames at all — each problem named by its clip. `check` prints them and fails if there are any; a consent withdrawn but not yet acted on shows up here.

@@ 123-126
**`split_of`**: training (70 %), validation (15 %) or test (15 %), from a fingerprint of the person's ID alone — so every clip of one person lands in the same split, and the test measures people the model has never seen. The same ID gives the same answer on any machine.

@@ 129-131
The next clip ID for a person and kind, such as `person-001-real-002`.

@@ 134-143
**`record`**: one clip's frames, kept as JPEGs, under a kind, person, camera and setting — and a consent, for a real person.

@@ 144-146
The camera's and setting's names are checked first: they become part of a folder's path.

@@ 147-149
Then the rule: nothing is written for a clip that may not be kept.

@@ 150-153
The clip's ID and its own new folder (`mkdir` fails if it already exists, so nothing is overwritten).

@@ 154-156
Each frame written as a JPEG at quality 95, numbered from 1.

@@ 157-159
No frames at all (a camera that delivered nothing): the empty folder is removed and the clip refused.

@@ 160-161
The clip joins the list.

@@ 164-165
**`inject`**: the *injected* attack. A virtual camera hands the browser a render's frames directly, so these clips are the rendered frames themselves, copied from `renders/<person>/<light>/`.

@@ 166-168
Sequences already added are skipped, so `inject` can be run again after every new render.

@@ 169-173
Each sequence folder's images, in order; an empty folder, or one already done, is passed over.

@@ 174-176
The folder names must be a made-up person's ID and a short light name; anything else stops with its path.

@@ 177-179
The clip (camera `none`: no camera was involved) and its folder.

@@ 180-181
The frames copied — not moved, so a render can be made again.

@@ 182-185
Added to the list, which is written once at the end, and the new clips returned.

@@ 188-189
**`withdraw`**: a person changed their mind, so their clips are deleted.

@@ 190-192
Only once the register says the consent was withdrawn — the register stays the record of why.

@@ 193-196
Every clip filmed under that consent: its folder deleted…

@@ 197-198
…its line dropped from the list, and the number deleted returned.

@@ 201-213
**`camera_frames`**: frames from a webcam, for the given number of seconds at the camera's own frame rate (30 if it doesn't say). `yield` hands each frame on as it arrives; `finally` releases the camera even if something fails. Not run by the tests (`pragma: no cover`): they have no webcam.

@@ 216-218
**`main`**: the command line. Every command takes `--folder`, so the tests can work in a temporary one.

@@ 219-222
Three short commands: `check`, `split` and `inject`.

@@ 223-230
**`record`** and its options. `--consent` isn't required by the parser but by the rule, so a missing one gets the rule's own explanation.

@@ 231-232
**`withdraw`**, with the consent's ID.

@@ 233-234
The options read, and the folder.

@@ 235-239
Filming: the webcam's frames go straight to `record`.

@@ 240-243
Injecting and withdrawing print how many clips changed.

@@ 244-247
The split: how many clips of each kind each split holds.

@@ 248-251
Otherwise, `check`: the problems, or the all-clear; exit code 1 if there are any.

@@ 252-254
A refusal (a missing consent, a bad name) is printed as one line, without a traceback, and fails.

@@ 255
Success.

@@ 258-259
Run as a program, `main`'s answer becomes the exit code.
