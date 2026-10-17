---
fingerprint: 80568ce19262f852
---
Every frame arrives as raw bytes from the internet, which means **from anyone**. This module turns those bytes into a picture (a NumPy array of pixels), but only after checking, cheaply and *before* decoding, that they are what they claim to be and that they are not dangerously large.

!!! warn "Careful — the decompression bomb"
    Compressed images can be tiny on disk and enormous in memory. A PNG of a single colour measuring 50,000 × 50,000 pixels can be a few hundred kilobytes as a file. Decoded, it needs 50,000 × 50,000 × 3 bytes ≈ **7.5 gigabytes** of memory. One such upload could crash the server. This is called a **decompression bomb**.

    The defence is to read the picture's width and height from its *header* — the first few bytes — and refuse it before decoding a single pixel.

@@ 1
The docstring states the rule: refuse anything unexpected before decoding.

@@ 3
The project-wide type-hint setting.

@@ 5
`import struct` — Python's tool for reading numbers packed into bytes, as file formats do. For example, "the next 4 bytes are a whole number, most significant byte first".

@@ 7-9
- `cv2` — OpenCV, for the actual decoding;
- `numpy` (imported as `np`, the universal convention) — arrays;
- `NDArray` — NumPy's type for "an array of a given element type", used in type hints.

@@ 11
`MAX_BYTES = 512 * 1024` — at most 512 KB per frame. A 640-pixel JPEG from our capture page is about 40–80 KB, so this is generous for honest clients and tight for abuse. It also stays below the 1 MB size above which the web framework would spill uploads into a temporary file on disk (ADR-0013).

@@ 12
`MAX_SIDE = 1920` — at most 1920 pixels on either side (Full-HD width). Our page sends 640, so anything bigger is suspicious.

@@ 13-14
**Magic numbers** — the fixed bytes every file of a format starts with:

- a JPEG always begins `FF D8 FF`;
- a PNG always begins with the eight bytes `89 50 4E 47 0D 0A 1A 0A`. The middle letters spell `PNG`, and the others are chosen so that a damaged transfer is noticed.

Checking these bytes is how we know what a file *really* is. A file's name or the label the client sends could be lies.

@@ 15
`JPEG_FRAME_MARKERS` — the codes of the JPEG segments that hold the picture's size, called **SOF** ("start of frame"). They are C0 to CF, *except* C4, C8 and CC, which mean other things (Huffman tables, a reserved code, arithmetic-coding settings). A `frozenset` is a set that can never be changed, and it answers "is this code in here?" instantly.

@@ 17
`type Image = NDArray[np.uint8]` — a **type alias**: an `Image` is an array of 8-bit unsigned whole numbers (0–255). It has shape *height × width × 3*: blue, green and red per pixel. OpenCV stores colours in **BGR** order, not RGB.

@@ 20-21
`DecodeError` — our own kind of error. Making it a *subclass* of Python's `ValueError` ("a value was unacceptable") means any code that already catches `ValueError` also catches it, while our code can catch exactly this error and nothing else.

@@ 24
**`image_size` — read (width, height) from the header, without decoding.**

@@ 25-27
**PNG.** After the 8-byte signature, every PNG has an `IHDR` ("image header") chunk:

- 4 bytes of length;
- the 4 letters `IHDR`;
- then the width (4 bytes) and the height (4 bytes), at byte positions 16–23.

`struct.unpack(">II", …)` reads two unsigned 4-byte integers (`I`), most significant byte first (`>`, *big-endian*, which PNG uses). The `len(data) >= 24` check makes sure those bytes exist.

@@ 28-29
**JPEG.** A JPEG is a sequence of **segments**, each starting with a **marker**: the byte `FF` followed by a code. Skip the first two bytes (`FF D8`, "start of image") and start reading at position 2.

@@ 30
Keep going while at least 9 more bytes remain — the most that we read from one segment.

@@ 31-32
Every segment must start with `FF`. Anything else means the file is corrupt, or not really a JPEG, so stop with an error.

@@ 33
The code byte after `FF` says what kind of segment this is.

@@ 34-36
`FF FF` is a **fill byte** that the standard allows as padding. Step over one byte and look again.

@@ 37-39
**Found the frame header.** Its layout after the marker is:

- 2 bytes of length;
- 1 byte of precision;
- then the height (2 bytes) and the width (2 bytes).

So the height and width sit at offsets 5–8. `">HH"` reads two big-endian unsigned 2-byte integers (`H`). Note the order — JPEG stores the height first — and that we return `(width, height)` like PNG does.

@@ 40-41
**Any other segment** (comments, colour tables, …): read its 2-byte length and jump over it. The length includes its own two bytes, but not the two marker bytes, hence `2 + length`. `(length,) = …` unpacks a one-item tuple.

@@ 42
Ran out of bytes without finding a frame header: corrupt.

@@ 43
Neither magic number matched, so refuse. **An allow-list (accept only these) is safer than a block-list (reject these)**, because new and unexpected formats are refused automatically.

@@ 46
**`decode_image` — bytes in, checked picture out.** `max_bytes: int = MAX_BYTES` is a parameter with a **default value**: a caller may leave it out and get the library's own limit, or pass a limit of its own. The inference service passes the shared contract's `MAX_FRAME_BYTES` (see `pipeline.py`), so the decoder can never refuse a frame that the protocol allows — even if someone raises one limit without the other. `max_side` works the same way (added in Phase 2): the service always uses the default 1,920 pixels, while dataset preparation, which reads large photos the project chose to trust, passes a roomier limit and then shrinks the picture itself (`ml/src/dwarpal_ml/prepare.py`).

@@ 47-48
**Check 1: the size of the bytes.** Empty data, or more than `max_bytes`, is refused. The message names the limit that was actually applied.

@@ 49
**Check 2: the format and dimensions**, read from the header (this also refuses non-JPEG/PNG data).

@@ 50-51
**Check 3: sensible dimensions.** Both sides must be at least 1 and at most `max_side`. The error message says exactly what was received (the tests check for the text `50000x50000`), which makes problems easy to diagnose.

@@ 52
**Only now, decode.**

- `np.frombuffer` wraps the bytes as a NumPy array *without copying* them.
- `cv2.imdecode` decompresses that into pixels.
- `cv2.IMREAD_COLOR` asks for a 3-channel BGR colour picture, even if the file was greyscale, so every later step sees the same shape.

@@ 53-54
OpenCV signals a decoding failure by returning `None` instead of raising an error. That would happen if the header looked fine but the body was damaged. We turn it into our own `DecodeError`.

@@ 55
Return the picture as an `Image` (8-bit array). `np.asarray(…, dtype=np.uint8)` doesn't copy when the array already has that type — it only makes the type explicit, which the type checker requires. OpenCV's type hints only promise "some array of numbers".
