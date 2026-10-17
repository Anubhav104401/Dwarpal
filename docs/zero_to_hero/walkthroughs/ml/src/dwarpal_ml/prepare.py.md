---
fingerprint: 31a44f4afb6fb972
---
**Face preparation**: for every image in a manifest, find the face, straighten and crop it, and save the result — using exactly the code the inference service uses on webcam frames (§5.1.1). This matters more than it sounds. A model learns whatever its training pictures look like: if training faces were cropped one way and live faces another, the model would be judged on pictures unlike anything it learned from (§2.17).

```
.datasets/raw/fairface/…margin125….zip   ──►  for each image:  decode → detect → pick the central face
                                                                  → quality measurements → align to 256×256
                                                                  → fingerprint
                                          ──►  .datasets/processed/fairface.zip     (97,645 aligned faces, 1.7 GB)
                                          ──►  .datasets/manifest/fairface.faces.csv (one row per image: outcome,
                                                                                      measurements, fingerprint)
```

All 97,698 FairFace images take about **45 seconds**, spread over 24 processor cores.

@@ 1-4
The docstring, with the command.

@@ 6
The project-wide type-hint setting.

@@ 8-18
Standard-library tools: `argparse`, `math` (for distances), `os` (to count processor cores), `sys`, `zipfile`, `Counter`, `ProcessPoolExecutor` (running work in several processes at once), `ExitStack` (closing a changing number of files safely), `dataclass`, `repeat`, and `Path`.

@@ 20-21
**OpenCV** (`cv2`) and **NumPy**, the image and number libraries the vision library is built on (§4.9).

@@ 23-24
From the ML package: the manifest's location, its `Row` type, reading and writing tables; and the register.

@@ 25-27
From the shared vision library: decoding, the face detector, alignment and quality checks, and the `Image` and `Face` types.

@@ 29
`PROCESSED` — prepared faces go to `.datasets/processed/`, which Git ignores like the rest of `.datasets/`.

@@ 30
`DETECTOR` — the YuNet face-detector model, downloaded in Phase 1 (`models/third_party.json`).

@@ 31
`SIZE = 256` — faces are saved at 256×256 pixels, with exactly the framing the service uses at 224×224, only larger. Training will cut slightly smaller pieces from them at random positions (a standard way of adding variety, §2.15) and shrink them to 224.

@@ 32
`JPEG_QUALITY = 95` — saved as high-quality JPEG: about 20 KB a face, with no visible loss.

@@ 33
`CHUNK = 500` — images are handed to the worker processes 500 at a time.

@@ 34-35
`ZIP_TIME` — every file in a zip records a date and time. Using a fixed one (1 January 1980, the earliest a zip can store) means preparing the same images twice gives byte-for-byte the same zip — a test checks this. Results that can be reproduced exactly can be checked by anyone.

@@ 38-49
**`Prepared`** — what happened to one image:

- `status` — `ok`, or why not: `undecodable`, `no_face` or `unalignable`;
- `faces` — how many faces the detector found;
- the quality measurements of the chosen face (`detector_score`, `eye_distance_px`, `brightness`, `sharpness`, `yaw_ratio` — §5.1.1) and the names of any quality rules it broke (`flags`);
- `phash` — the face's **perceptual hash** (below), as 16 hexadecimal digits.

The `= 0` and `= ""` are default values, so a failure can be recorded with just the image and its status.

@@ 52
**`central_face`** — when a photo shows several people, choose the face nearest the middle. FairFace made each image by centring it on the labelled person, so the central face is the one the age label belongs to — and the most confident face may well be someone else's, nearer the camera.

@@ 53
The picture's height and width.

@@ 55-57
The distance from a face's centre to the picture's centre. `math.hypot(a, b)` is √(a² + b²): Pythagoras's theorem, the straight-line distance.

@@ 59
The face with the smallest distance. `min(…, key=distance)` compares the faces by their distance, but returns the face itself.

@@ 62
**`perceptual_hash`** — a 64-bit fingerprint of what a picture *looks like*. A SHA-256 fingerprint (§X.5) changes completely if a single pixel changes; a perceptual hash barely changes when a photo is resized, re-saved or slightly recoloured. Two copies of one photo get nearly the same hash. That makes it a quick way to shortlist possible duplicates (`dedup.py`).

@@ 63-64
Turn the picture grey and shrink it to 32×32 pixels: only the broad pattern of light and dark is kept.

@@ 65
The **discrete cosine transform** (DCT) describes the little picture as a sum of wave patterns, from smooth (top-left of the result) to fine (bottom-right) — the same idea JPEG compression is built on. The top-left 8×8 values hold the 64 smoothest patterns: the picture's overall structure. `flatten` lays them out in one row.

@@ 66
Each of the 64 values becomes one bit: is it above the middle value (the **median**)? The first value — the picture's overall brightness — is left out when finding the median, so that a brighter copy of a photo gets the same bits.

@@ 67
Pack the 64 true/false values into 8 bytes, and read them as one whole number.

@@ 70
**`prepare_one`** — one image, from bytes to an aligned face. It returns the record and the face as JPEG bytes (empty bytes when there's no face).

@@ 71-74
Decode the image with the vision library's careful decoder, which checks the file before decoding it (§5.1.1). Anything it refuses is recorded as `undecodable`.

@@ 75-77
Find the faces. None at all: `no_face`.

@@ 78
Choose the central face.

@@ 79
Measure its quality. `assess` judges the *first* face of the list, so the chosen face goes first, followed by the others (`*` unpacks them into the list). The quality rules are the ones for live webcam frames; here they are only **recorded**, never used to drop a face. Dataset photos break them often (a quarter of FairFace's faces are turned too far to one side for the live check) and a model needs to learn from such faces too. The records feed the data report.

@@ 80-83
Straighten and crop the face to 256×256. If its landmarks are impossible to align, record `unalignable`.

@@ 84
Encode the aligned face as JPEG. `imencode` returns a success flag and the bytes; `[1]` takes the bytes.

@@ 85-96
The record of a success: the measurements, each rounded to a sensible number of decimals so the table stays readable; the quality flags joined into one text such as `not_frontal|too_dark`; and the perceptual hash of the *aligned* face, written as 16 hexadecimal digits (`:016x`).

@@ 97
Return the record and the JPEG bytes.

@@ 100
**`prepare_chunk`** — prepare 500 images. This is the work one process does at a time.

@@ 101
`setNumThreads(1)` — tell OpenCV to use a single thread. The work is already spread over one process per core; if each process also started threads of its own, they would fight over the same cores.

@@ 102
Each chunk loads its own detector: objects like this can't be shared between processes. Loading takes a few milliseconds — nothing, next to 500 images.

@@ 103
The results so far.

@@ 104-108
Open each zip file the rows need, once. `ExitStack` remembers every file opened inside it and closes them all at the end, even if something fails halfway.

@@ 109
Read the image's bytes from inside the zip, and prepare it.

@@ 110
Return the chunk's results.

@@ 113
**`prepare`** — prepare a whole manifest, using several processes.

@@ 114
Cut the rows into chunks of 500.

@@ 115-116
Create the output folder; write to a `.part` file first, as in the fetch command, so a half-finished run is never mistaken for a finished one.

@@ 117
The records, in manifest order.

@@ 118
Start the **process pool** — `workers` copies of Python, each able to run `prepare_chunk` — and open the output zip. `ZIP_STORED` means "don't compress": JPEGs are already compressed, and compressing them again would only waste time.

@@ 119
`pool.map` sends the chunks to the workers and hands back their results **in the original order**, as they become ready. `repeat(folder)` supplies the same folder to every chunk. `enumerate(…, 1)` counts the chunks from 1.

@@ 120-123
Keep every record. For each face that was prepared, add its JPEG to the zip under the image's name, with the fixed timestamp.

@@ 124
Show progress on one line: `\r` returns to the start of the line, so each update overwrites the last; `flush=True` shows it immediately.

@@ 125-126
After the last chunk, end the progress line.

@@ 127
Rename the finished zip to its real name.

@@ 128
Return the records.

@@ 131
**`summary`** — what to print at the end.

@@ 132-133
Count the outcomes, and every quality flag (`split("|")` separates them again).

@@ 134-135
One line for outcomes and one for flags, most common first. The second line says plainly that flagged faces are kept.

@@ 136
Join the lines.

@@ 139-143
**`main`** — the dataset's name, and how many processes to use: by default one per processor core (`os.cpu_count()`; `or 1` covers the rare system that can't say).

@@ 144-147
Refuse a dataset that isn't approved — the rule is checked at every step that touches the data.

@@ 148-149
Read the manifest and prepare its images into `.datasets/processed/<name>.zip`.

@@ 150-152
Write the records to `.datasets/manifest/<name>.faces.csv`, print the summary, report success.

@@ 155-156
Run `main` when the module is started as a program. On Windows this guard is essential: each worker process starts by importing this module, and without the guard every worker would start a pool of its own.
