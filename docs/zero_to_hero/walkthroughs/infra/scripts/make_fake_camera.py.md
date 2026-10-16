---
fingerprint: 4aa810596647ca54
---
Makes the **fake camera's video** for the end-to-end test: the public-domain test portrait (the same one the vision tests use, §5.1.1), placed in a 640 × 480 picture and repeated as a two-second clip. Chromium plays it as if it were a webcam (see `e2e/playwright.config.ts`).

The file format is **Y4M** (YUV4MPEG2), the simplest video format there is: a one-line text header, then each frame's raw pixels, uncompressed. Chromium reads it directly, and Python can write it with no video library at all.

Pixels in Y4M are stored as **YUV**, not RGB: one channel for brightness (**Y**) and two for colour (**U** and **V**). The colour channels are stored at half the width and half the height — "4:2:0" — because human eyes notice detail in brightness far more than in colour. Video formats everywhere use this trick to save space.

@@ 1-4
The docstring, with the command that runs the script.

@@ 6
The project-wide type-hint setting.

@@ 8-9
`sys` (for the command-line argument) and `Path`.

@@ 11-12
OpenCV and NumPy (§4.9).

@@ 14
The clip's size: 640 × 480 pixels, 30 frames, 15 frames per second — two seconds, which Chromium plays in a loop.

@@ 15
The portrait's location, found from this script's own place: two folders up is the repository's top folder.

@@ 18
**`frame`** — make one frame, as Y4M's raw bytes.

@@ 19-21
Read the portrait. OpenCV returns `None` (instead of raising an error) when a file can't be read, so the script checks, and stops with a clear message.

@@ 22
A 640 × 480 canvas, filled with middle grey (128).

@@ 23
Where the portrait goes: a 480 × 480 square in the middle, starting at `(640 − 480) / 2 = 80` pixels from the left. `//` divides and drops any remainder.

@@ 24
Shrink the 512 × 512 portrait to 480 × 480 (`INTER_AREA` is OpenCV's best method for shrinking), and paste it into the middle of the canvas. `canvas[:, left : left + HEIGHT]` selects every row, and the columns from 80 to 559.

@@ 25
Convert from OpenCV's BGR colour order to **YUV I420** — the 4:2:0 layout Y4M's `C420jpeg` expects: first the full brightness plane, then the two quarter-size colour planes. `.tobytes()` takes the raw bytes.

@@ 28
**`main`** — write the clip to `target`.

@@ 29
Make the one frame; every frame of the clip is the same.

@@ 30
Create the output folder if it doesn't exist.

@@ 31
Open the file for writing **bytes** (`"wb"`).

@@ 32
The header line: `W640 H480` (size), `F15:1` (15 frames per 1 second), `Ip` (whole frames, not interlaced), `A1:1` (square pixels) and `C420jpeg` (the 4:2:0 colour layout).

@@ 33-34
Thirty times: the word `FRAME`, a line break, and the frame's bytes.

@@ 35
Say what was written.

@@ 38-39
When run as a program, write to the path given on the command line.
