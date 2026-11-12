---
fingerprint: 87bd83396e7b798c
---
The tests of the Secure QR reader (Part 7). They never touch a real Aadhaar: every code is a **specimen** the module makes itself, with fictional fields, the public-domain astronaut portrait, and — in this file — a "signature" of plain filler bytes, because signatures are not this module's business.

@@ 1-6
The file's docstring: what is tested, and why no real Aadhaar is needed — the layout is UIDAI's published one, so a made-up code in that layout exercises the same code paths.

@@ 8
The project-wide type-hint setting.

@@ 10-11
`zlib`, to build a zip bomb for one test; `Path`, to find the fixture.

@@ 13-15
OpenCV and NumPy (pictures), and pytest.

@@ 17-29
The code under test: the image decoder the inference service uses, and from the Aadhaar module its reader functions, its error, and its specimen makers.

@@ 31-32
The test portrait: the astronaut photo used throughout the project's tests, read once.

@@ 33
`FILLER` — 256 bytes, simply 0 to 255 in order, standing where a signature would be. No key made them, so no key ring would accept them; for *these* tests that doesn't matter.

@@ 36
`ID_PHOTO` — the portrait cut close round the face (rows 20–245, columns 133–313), as an ID photo is. This matters: a Secure QR's photo is so small that a face filling only a corner of it would be a smudge.

@@ 39-40
**`specimen`** — a made-up code's bytes with the given date of birth and layout version. The `lambda` is the "signer": whatever it is asked to sign, it answers `FILLER`.

@@ 43-47
**The 4,300-digit limit** (§7.4). A specimen's number is longer than Python converts in one step, and still goes there and back unchanged: `unpack(pack(data)) == data`. If the chunked conversion in either direction were wrong by one digit, this would fail.

@@ 50-55
**Every date form UIDAI has printed** is read into one form: day-first with dashes, day-first with slashes, year-first, and the year alone. `parametrize` runs the test once per pair.

@@ 58-61
**Both layouts**, the first (no version) and the later one (`V2`), give the same date of birth…

@@ 62-66
…and for each: the signature is the last 256 bytes; signed part plus signature is the whole code again (nothing lost, nothing added); and the photo decodes to 160 by 200 pixels in colour.

@@ 69-73
**A code without a photo** is still read: the date of birth comes out, the photo is empty, and decoding "no photo" gives `None` — as do bytes that merely begin like a JPEG 2000.

@@ 76-84
Four things that aren't a Secure QR: too short for a signature; long enough but without any field ends; fields in the right places but "not a date" where the date should be; and data that ends before the date-of-birth field.

@@ 85-88
Each is refused with the one stable code, `aadhaar_qr_unreadable`. `pytest.raises` passes only if the error is raised.

@@ 91-95
**Text that isn't a Secure QR's number**: a web address, a number too short to unzip, 9,000 digits (more than any QR code holds), and a real specimen's number with its last 40 digits cut off — which unzips partway and then stops without gzip's end mark.

@@ 98-102
**The zip bomb.** 200 kB of zeros zip down to a few hundred bytes — small enough to fit in a QR code. `unpack` stops at its 64 kB limit and refuses with the message "…more than a Secure QR holds". Without the limit, a single small picture could make the service unzip as much as its memory holds.

@@ 105-109
**Finding the code in a picture**: a specimen drawn as a QR code and decoded the way an upload is, is read back digit for digit. And the astronaut's portrait, which has no code in it, gives `None` — so a passport photo will go on to the MRZ reader.

@@ 112-115
**A photo, not a perfect drawing.** Start from the flat picture of the code…

@@ 116-121
…and view it as a camera held slightly askew would: `getPerspectiveTransform` works out the "lean" that moves the picture's four corners to four slightly different places, and `warpPerspective` applies it, filling the uncovered edge with light grey.

@@ 122-123
Blur it a little, as an imperfectly focused lens does. The code is still read. (Stronger blur, or a code that fills less of the picture, is where reading fails: §7.3 has the measurements.)
