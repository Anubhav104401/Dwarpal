---
fingerprint: da53738cd7fe947e
---
**Reading the MRZ from a photo** (Phase 6, §5.6.2): the step the parser (§5.6.1) was waiting for. A phone photo of a passport is tilted, blurred and noisy; this module finds the machine-readable zone in it, straightens it, and has Tesseract read it.

!!! key "Key idea — read here, check there"
    Reading and checking are kept apart. This module only reads, and reads imperfectly: OCR makes mistakes. The API's parser then decides what can be trusted, with every check digit. A wrong reading can't become a wrong answer; at worst it becomes "try again".

@@ 1-2
The module's docstring: find the MRZ band in a photo, straighten it, and have Tesseract read it. Checking what was read is the API parser's job; this module only reads.

@@ 4
The project-wide type-hint setting.

@@ 6-8
`re` (regular expressions, to strip unwanted characters), `subprocess` (to run Tesseract as a separate program) and `Sequence`, a type for lists and tuples.

@@ 10-13
OpenCV, NumPy and the image type.

@@ 15
`ALPHABET` — the only 37 characters an MRZ may hold.

@@ 16
`WORK_WIDTH` — the band is looked for in a copy of the photo scaled to 800 pixels wide, so the shapes used below work at any photo size.

@@ 17
`LINE_HEIGHT` — the height in pixels each line of the band is scaled to before reading: capital letters about 30 pixels tall are what Tesseract reads best. (Tried on specimens: 45 read every passport; smaller or larger read fewer.)

@@ 18
`MIN_LINE` — a line Tesseract returns with fewer than 20 characters is a stray mark, not an MRZ line (the shortest has 30).

@@ 19
`NOT_THE_ALPHABET` — a pattern matching any character outside the MRZ alphabet, to delete them.

@@ 22-23
`TesseractError` — Tesseract couldn't be run, or it failed: a problem of the service, never of the person, so the check is retried.

@@ 26-29
**`find_mrz`** — find the MRZ band: cut it out, turn it level, in grey. The docstring gives the idea: the MRZ is a block of dark characters on a light ground, much wider than tall, with small even gaps, and the steps below melt such a block into one solid shape.

@@ 30-32
Make a grey copy; scale it to the working width (remembering the `scale`); and blur it very slightly, which smooths away sensor noise without losing letters.

@@ 33-34
**Black-hat** — a *morphological* operation: it keeps dark details smaller than a 13 × 5 rectangle — characters — and drops large dark areas such as the photo or the table around the document.

@@ 35-37
Where brightness changes from left to right (a **Sobel** filter): the edges of characters, strongest in rows of text. The result is stretched to the 0–255 range of an ordinary grey image.

@@ 38-39
**Closing** with a wide, low rectangle (21 × 5) fills the gaps *between* characters, so each line of text becomes a bar.

@@ 40
**Otsu's threshold** turns the grey picture into black and white, choosing the cut-off automatically from the picture itself.

@@ 41-42
Closing again with a large square (25 × 25) joins the lines of the zone into one blob; then **erosion** shaves its edges three times, cutting thin bridges to nearby print.

@@ 43-44
Find the outlines of all the blobs (`findContours`), and look at them largest first.

@@ 45-47
`minAreaRect` — the smallest rectangle around a blob, at any angle: its centre, size and angle. It may describe a lying rectangle as a standing one, so width and height are swapped (and the angle turned) when needed.

@@ 48-49
Is it shaped like an MRZ? At least four times as wide as tall, and across at least 40 % of the picture.

@@ 50-52
Back to the full-size photo's scale: the centre, and a size with a margin — erosion trimmed the blob's edges, and Tesseract needs some clear space around letters.

@@ 53-55
Turn the whole grey photo by the band's angle around its centre, so the band lies level (`warpAffine`, filling the corners with white), then cut the band out (`getRectSubPix`).

@@ 56
No blob looked like an MRZ: `None`.

@@ 59-63
**`zone_lines`** — Tesseract's text, made into MRZ lines. Its docstring states the privacy rule: the line holding only names is blanked after its first five characters, so no name ever leaves the service that read it.

@@ 64-65
Each line in capitals, with spaces and anything outside the MRZ alphabet removed; then only lines long enough to be MRZ lines.

@@ 66-69
Two lines (a passport or a TD2 card): keep the first line's document type and issuer, and fill the rest with `<`. Three lines (a TD1 card): the third is all names, so it becomes all `<`.

@@ 70
Return the lines.

@@ 73-76
**`Tesseract`** — runs the OCR engine on one picture at a time, through **pipes**: the picture goes in on its standard input and the text comes back on its standard output, so nothing is written to disk. The command that starts it is a setting.

@@ 78-80
Keep the command (as a list of words) and how long one reading may take.

@@ 82-90
**`available`** — does Tesseract answer at all? Run it with `--version`; any failure (the program missing, an error, a timeout) means no.

@@ 92-96
**`read`** — read a band. First size its letters: a band more than 5.5 times as wide as tall has two lines, otherwise three; scale it so each line gets `LINE_HEIGHT` pixels.

@@ 97-101
Scale up smoothly (`INTER_CUBIC`), add a 20-pixel border copied from the band's own edge, and encode it as a PNG (lossless) for the pipe.

@@ 102-106
Tesseract's arguments:
- `stdin stdout` — read the picture from the pipe and write the text to the pipe;
- `--psm 6` — *page segmentation mode* 6: treat the picture as one uniform block of text;
- `-l eng` — the English model;
- a **whitelist** of the MRZ's 37 characters — nothing else may come out;
- no dictionaries: Tesseract normally prefers real words, and MRZ lines aren't words.

@@ 107-112
Run it with the picture as input, collecting its output, within the time limit. If it can't start or runs too long: `TesseractError`.

@@ 113-115
A non-zero exit code means it failed: `TesseractError`, with the start of its error message. Otherwise return the text it read.
