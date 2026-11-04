---
fingerprint: dd731e6e6cf1e760
---
**The render detector's own data** (decision D22, 2 Nov 2026; ADR-0021): a tool that films and files clips — of real people only under a standing written consent, and of made-up people we render — splits them by person, and deletes a person's clips when they withdraw.

@@ 1-7
The module's docstring: the render detector's own data (decision D22, ADR-0021) — clips of consenting real people and of made-up people we render — and where it lives: `.datasets/render-detector/`, which git ignores, so no clip can be committed.

@@ 9
The project-wide type-hint setting.

@@ 11-26
Command-line options, CSV files, fingerprints (for the splits), patterns, copying and deleting folders, the error stream, TOML (the consent register's format), counting, the types of functions and of things that can be gone through one by one, data classes, paths, the types for a fixed set of words; OpenCV (the camera, the screen and JPEG files) and NumPy (a frame is an array of pixels).

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

@@ 47-54
**`Clip`**: one clip's line in `clips.csv` — its ID, kind, person, camera, room and light, and for a real person the consent it was filmed under.

@@ 56-58
Every kind except `real` is a render: the label the detector learns.

@@ 61-66
**`Consent`**: one entry of the consent register — its ID (the one written on the signed form), the person, when it was given, and when it was withdrawn (empty while it stands).

@@ 68-70
A consent stands until it is withdrawn.

@@ 73-78
**`read_clips`**: the list of clips, or none yet. The `type: ignore` is because a CSV row's values are plain text, while `kind` expects one of three words; `check` catches a wrong one.

@@ 81-86
**`write_clips`**: the whole list written again, sorted, with a header line taken from `Clip`'s fields.

@@ 89-97
**`load_consents`**: the register, as a dictionary from consent ID to `Consent`; empty if there is no register yet. Dates are kept as text: they are only compared and printed.

@@ 100-101
**`consent_problem`** — the one rule every clip passes, when filmed and again at every `check`: why it may not be kept, or `None`.

@@ 102-105
The kind must be known, and the person's ID must fit the kind: no real person can be filed as a render, nor a render as a person.

@@ 106-107
A render has no one to give consent, so a consent ID on it is a mistake.

@@ 108-110
A real clip needs a consent in the register…

@@ 111-112
…given by that same person…

@@ 113-114
…and not withdrawn.

@@ 115
Nothing wrong.

@@ 118-126
**`problems`**: every clip checked — the rule above, and that it has frames at all — each problem named by its clip. `check` prints them and fails if there are any; a consent withdrawn but not yet acted on shows up here.

@@ 129-132
**`split_of`**: training (70 %), validation (15 %) or test (15 %), from a fingerprint of the person's ID alone — so every clip of one person lands in the same split, and the test measures people the model has never seen. The same ID gives the same answer on any machine.

@@ 135-137
The next clip ID for a person and kind, such as `person-001-real-002`.

@@ 140-149
**`record`**: one clip's frames, kept as JPEGs, under a kind, person, camera and setting — and a consent, for a real person.

@@ 150-152
The camera's and setting's names are checked first: they become part of a folder's path.

@@ 153-155
Then the rule: nothing is written for a clip that may not be kept.

@@ 156-159
The clip's ID and its own new folder (`mkdir` fails if it already exists, so nothing is overwritten).

@@ 170-171
The clip joins the list.

@@ 183-184
**`inject`**: the *injected* attack. A virtual camera hands the browser a render's frames directly, so these clips are the rendered frames themselves, copied from `renders/<person>/<light>/`.

@@ 185-187
Sequences already added are skipped, so `inject` can be run again after every new render.

@@ 188-194
Each sequence folder, in order. A person's own files beside their lights (the render script's `person.json`) are passed over — they were taken for a light at first (4 Nov); so are empty folders and sequences already added.

@@ 195-197
The folder names must be a made-up person's ID and a short light name; anything else stops with its path.

@@ 198-200
The clip (camera `none`: no camera was involved) and its folder.

@@ 201-208
The frames placed — linked, or copied. If anything stops it, the half-made clip's folder is deleted and the clips added so far are written to the list before the error goes on — the first real run left two orphan folders behind that blocked the next one.

@@ 209-212
Added to the list, which is written once at the end, and the new clips returned.

@@ 215-216
**`withdraw`**: a person changed their mind, so their clips are deleted.

@@ 217-219
Only once the register says the consent was withdrawn — the register stays the record of why.

@@ 220-223
Every clip filmed under that consent: its folder deleted…

@@ 224-227
…its line dropped from the list. The prepared crops (`render_detector.prepare`) hold faces too, and are gathered from every clip at once, so they are all deleted and must be prepared again. The number of clips deleted is returned.

@@ 284-296
**`camera_frames`**: frames from a webcam, for the given number of seconds at the camera's own frame rate (30 if it doesn't say). `yield` hands each frame on as it arrives; `finally` releases the camera even if something fails. Not run by the tests (`pragma: no cover`): they have no webcam.

@@ 299-301
**`main`**: the command line. Every command takes `--folder`, so the tests can work in a temporary one.

@@ 302-305
Three short commands: `check`, `split` and `inject`.

@@ 306-313
**`record`** and its options. `--consent` isn't required by the parser but by the rule, so a missing one gets the rule's own explanation.

@@ 319-320
**`withdraw`**, with the consent's ID.

@@ 321-322
The options read, and the folder.

@@ 335-338
Injecting and withdrawing print how many clips changed.

@@ 339-342
The split: how many clips of each kind each split holds.

@@ 343-346
Otherwise, `check`: the problems, or the all-clear; exit code 1 if there are any.

@@ 347-349
A refusal (a missing consent, a bad name) is printed as one line, without a traceback, and fails.

@@ 350
Success.

@@ 353-354
Run as a program, `main`'s answer becomes the exit code.

@@ 39-40
**`SETTLE`**: how many camera frames to drop while the first rendered frame is on screen — half a second at 30 frames a second, while the camera adjusts its exposure to the bright screen.

@@ 42-44
Three names for types used below: a **frame** (a picture's bytes), **`Show`** (puts a frame on the screen) and **`Grab`** (takes one frame from the camera, or nothing when it has stopped).

@@ 230-235
**`read_frame`**: one rendered frame. OpenCV answers *nothing* for a file it can't read; that is refused by name instead of failing later somewhere less clear.

@@ 238-240
**`played`**: a rendered sequence shown on a screen and filmed **in step** — each rendered frame shown, then one camera frame taken of it, so every camera frame shows one known rendered frame. A function that `yield`s hands over each frame as it is taken: `record` writes it before the next is shown.

@@ 241-243
The sequence's images in order; an empty folder is refused.

@@ 244-247
The first frame is shown and the camera's frames are taken and dropped, `settle` times.

@@ 248-253
Then each rendered frame in turn: shown, filmed, handed on. If the camera stops, so does the clip.

@@ 256-258
**`film`**: a `screen_render` clip of the made-up person whose sequence it is (its folder's parent is the person's ID). It goes through `record`, so every rule applies — and because `played` is only started when `record` asks for its first frame, a refused clip never shows anything.

@@ 261-262
**`full_screen`**: the real screen and webcam (not run by the tests: they have neither).

@@ 263-265
The webcam, opened (or refused).

@@ 266-267
A window filling the whole screen, so the camera sees only the render.

@@ 269-271
**show**: the frame into the window; `waitKey(1)` lets the window draw it.

@@ 273-275
**grab**: one frame from the webcam, or nothing if it has stopped.

@@ 277-279
**close**: the webcam released and the window closed.

@@ 281
The three handed back together.

@@ 314-318
**`film`** and its options: the sequence's folder, the camera's name, the screen, room and light, and the webcam's number.

@@ 160-165
Each frame written as a JPEG at quality 95, numbered from 1; no frames at all (a camera that delivered nothing) is refused.

@@ 166-169
Whatever stops the filming — no frames, an unreadable render, even Ctrl+C (`BaseException` catches that too) — the clip's folder is deleted before the error goes on, so no half-written clip is left behind to block the next one with the same ID.

@@ 323-327
Filming a person: the webcam's frames go straight to `record`.

@@ 328-334
Filming a render: the full-screen window and webcam, the clip, and both closed afterwards even if something fails (`finally`).

@@ 174-176
**`place`**: one rendered frame into a clip, as a **hard link** — a second name for the same file on the disk, so 40 people's renders (6.8 GB) don't take their space twice. Deleting either name leaves the other.

@@ 177-180
Where the disk can't link (another drive, or a file system without links), the frame is copied.
