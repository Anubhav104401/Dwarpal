---
fingerprint: dbfd5380a2ecdccb
---
**Specimen documents** (Phase 6, §5.6.2): test passports that no one owns. Testing a document check needs photos of documents, and real ones belong to real people. Instead, this module draws the passport of ICAO's fictional holder from the state of "Utopia" — the same specimen ICAO Doc 9303 prints — with any dates of birth and expiry, and then makes it look photographed.

The tests read these specimens with Tesseract, and the browser test uploads one.

@@ 1-8
The module's docstring: what a specimen is, the rule that no real person's document is ever used, and how to make one from the command line — a portrait in, a JPEG out, with optional dates of birth and expiry as `YYMMDD`.

@@ 10
The project-wide type-hint setting.

@@ 12-18
`sys` (for the command line), `Path`, OpenCV, NumPy and the image type.

@@ 20
`WEIGHTS` — ICAO's check-digit weights, 7, 3, 1, repeating.

@@ 23-24
**`check_digit`** — ICAO 9303's check digit, so the specimen's zone is valid. The API has its own copy in its parser: the vision library and the API don't depend on each other, and a test (§5.6.2) shows both agree with ICAO's printed specimen.

@@ 26-27
A character's value: a digit as itself, `<` as 0, `A` to `Z` as 10 to 35.

@@ 29
Weight the values 7, 3, 1, 7, 3, 1…, add them up, and keep the last digit.

@@ 32-33
**`passport_zone`** — a passport's two MRZ lines for ICAO's specimen holder (Anna Maria Eriksson of Utopia), with the dates asked for.

@@ 34
The specimen's personal number, padded with fillers to its 14 characters.

@@ 35-38
The second line: document number and its check digit, nationality `UTO`, birth date and check digit, sex, expiry and check digit, personal number and check digit.

@@ 39-40
The composite check digit covers the number, birth date, expiry and personal number with their check digits — exactly the slices ICAO lists. The first line is the type, issuer and name, padded to 44.

@@ 43-44
**`page`** — the data page, flat and perfect: a photo, a few printed fields, and the MRZ at the bottom.

@@ 45-47
The font (one of OpenCV's built-in *Hershey* fonts, which needs no font file and carries no licence question), the ink colour, the zone's lines, and the spacing between characters for each layout — MRZ characters sit at a fixed pitch.

@@ 48
A pale page, 1250 × 900 pixels.

@@ 49-53
Cut the portrait to a passport photo's shape — 4 wide by 5 tall — from its middle, and place it on the left of the page.

@@ 54-56
The title and three printed lines, one of which says plainly that this is not a real document.

@@ 57-61
The MRZ, one character at a time, each centred in its fixed-width cell, with smooth edges (`LINE_AA`).

@@ 62
Return the page.

@@ 65-66
**`photographed`** — the page as a phone might take it.

@@ 67-73
A random generator with a fixed seed (so each seed always gives the same photo); the page's four corners; where they land in the photo — tilted, with random wobble of up to 40 pixels; and the **perspective transform** that maps one to the other, applied on a dark "table".

@@ 74-77
A slight blur, and sensor noise: random changes of brightness, computed in a wider number type so they can't wrap round, then clipped back to 0–255.

@@ 80-85
**`specimen_jpeg`** — all three steps, encoded as a JPEG at quality 85, as a phone or browser would send it.

@@ 88-94
From the command line: read the portrait, take the dates given (or born 1 January 1990, expiring 1 January 2036), and write the specimen. A portrait that can't be read stops with a message.
