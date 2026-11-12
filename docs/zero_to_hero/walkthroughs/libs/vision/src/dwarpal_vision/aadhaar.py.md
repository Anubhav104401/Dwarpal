---
fingerprint: 79b59b3224104108
---
The reader for **Aadhaar Secure QR codes** (Part 7, §7.3–§7.4). It does three jobs, each a small function: find the code in a picture (`read_qr`), turn its text into bytes (`unpack`), and split those bytes into the parts an age check needs (`parse`). It **decides nothing** and **trusts nothing**: whether UIDAI really signed the code is checked by the inference service's key ring, and whether the person is old enough by the API.

The second half of the file makes **specimens**: made-up codes in the real layout, for tests. No real Aadhaar is ever needed to test this module.

@@ 1-3
The module's docstring, first paragraph: what the module does — find, unpack, split — and what it leaves to others: the signature.

@@ 5-8
The layout of a Secure QR, in one paragraph. It is worth reading slowly, because the whole file follows it: a long decimal **number** → written as bytes it is a **gzip** file → unzipped it is **text fields**, each ended by the byte 255 → then the **photo** → then, sometimes, two 32-byte **hashes** → and last, 256 bytes of **signature** over everything before.

@@ 10-12
The privacy rule of this module: of all the code holds, only the date of birth, the photo and the signature are taken out. The name, address and reference number are never turned into text here.

@@ 14
The project-wide type-hint setting.

@@ 16-19
From Python itself: `re` (patterns in text), `zlib` (unzipping), the types `Callable` (a function passed as a value) and `Iterator` (something that hands out items one at a time), and `dataclass`.

@@ 21-22
OpenCV (pictures, and its QR reader) and NumPy (the grids of numbers pictures are kept in).

@@ 24
`Image` — the project's name for a picture: a NumPy grid of whole numbers from 0 to 255.

@@ 26
`SIGNATURE_BYTES` — an RSA signature made with a 2,048-bit key is always exactly 2,048 bits long: 256 bytes. That is how the reader knows where the signature starts: 256 bytes from the end.

@@ 27
`END_OF_FIELD` — the byte that ends each text field. 255 was a clever choice by UIDAI: in the text encoding used (ISO-8859-1) it is the letter "ÿ", which no Indian name or address contains.

@@ 28
`MAX_DIGITS` — the largest QR code that exists (version 40) holds 7,089 digits, so text longer than this can't have come from one. Checked before any work is done on it.

@@ 29-31
`CHUNK` — a real surprise met while writing this file (§7.4). Python can hold numbers of any size, but since 2022 it refuses to convert **text of more than 4,300 digits** into a number in one step: such conversions are slow, and attackers used them to stall servers. A Secure QR's number has about 5,000 digits. So the number is built 4,000 digits at a time.

@@ 32
`MAX_UNPACKED` — a real code unzips to a few thousand bytes. Unzipping stops at 64 kB whatever the data claims: this is the guard against a **zip bomb**, a tiny file made to unzip into gigabytes and fill the server's memory.

@@ 33
`MAX_PHOTO_SIDE` — the photo in a code is small; one that decodes to more than 1,024 pixels on a side is not what a Secure QR holds, and is refused.

@@ 34-36
`BIRTH_FIELD_V1` — which field holds the date of birth, counting from 0. In the first layout (2018) the fields run: email/mobile marker, reference number, name, **date of birth** — so it is field 3. Every later layout puts its version (`V2`, …) in front, which makes it field 4.

@@ 37-38
The two ways a JPEG 2000 picture can begin: as a whole file (12 fixed bytes that spell "jP") or as a bare "code stream" (4 fixed bytes). Finding either is how the photo's start is found.

@@ 39
`VERSION` — the pattern "the letter V and a digit from 2 to 9", for bytes (`rb"…"`): how a versioned layout begins.

@@ 40-42
The three ways UIDAI has written a date of birth: day first (`01-01-1990` or `01/01/1990`), year first (`1990-01-01`), and — for people whose exact date isn't on record — the year alone (`1990`). The round brackets in the patterns capture the parts.

@@ 43-44
`SCALES` — the sizes the picture is tried at, in order: as it is, half as big again, twice as big, and three-quarters. Measured while building this (§7.3): OpenCV often fails to read a dense code at one size and reads it at another.

@@ 47-52
**`SecureQrError`** — raised when something isn't a Secure QR. Like the MRZ's error, it carries a short, stable `code` for programs (always `aadhaar_qr_unreadable` here) beside the message for people.

@@ 55-61
**`SecureQr`** — the parts taken from a code: its layout version, the date of birth (as `YYYY-MM-DD`, or `YYYY`), the photo's bytes, every byte the signature covers, and the signature. `frozen=True`: once read, it can't be changed. Look at what is **not** here: no name, no address, no number.

@@ 64-66
**`_views`** — hands out the same picture in several forms, for `read_qr` to try in turn. (The leading underscore marks a helper meant for this file only.) First it is made grey, if it has colours: a QR code is black and white, and colour only gets in the way.

@@ 67-72
At each size in `SCALES`: the grey picture as it is, or resized — `INTER_CUBIC` when enlarging (smooth), `INTER_AREA` when shrinking (it averages, which removes noise). `yield` hands one out and pauses until the next is asked for, so a picture that is read at the first size never pays for the others.

@@ 73
Last, pure black and white: every pixel is made 0 or 255, with the dividing brightness chosen by **Otsu's method** (it finds the level that best separates the dark pixels from the light ones). This helps with a grey, low-contrast photo.

@@ 76-79
**`read_qr`** — the text of a QR code in the picture, if it could be a Secure QR. The docstring gives the practical limit: at up to 177 little squares a side, the code must fill most of the picture.

@@ 80
OpenCV has two QR readers. `QRCodeDetectorAruco` is the newer one; in our measurements it read dense codes that the older `QRCodeDetector` could not (§7.3).

@@ 81-85
Try each view. OpenCV sometimes raises an error on a picture it can't handle, instead of answering "no code"; that counts as "not read at this size", and the next view is tried.

@@ 86-88
Accept the text only if it could be a Secure QR: nothing but the digits 0–9, and more than 256 of them. A QR code with a web address in it, say, is ignored — and the caller goes on to look for an MRZ. No view gave such text: `None`.

@@ 91-94
**`unpack`** — from the code's text to the bytes it stands for. First the cheap checks: only digits, and not more than a QR code can hold.

@@ 95-98
Build the number 4,000 digits at a time (see `CHUNK`). For each piece: shift what we have left by the piece's length — multiply by 10 to that power — and add the piece. It is the way you would read "12" then "34" as 1,234: 12 × 100 + 34.

@@ 99
Write the number as bytes. `bit_length()` says how many bits it needs; adding 7 and dividing by 8 rounds up to whole bytes. `"big"`: the most significant byte first, as UIDAI wrote it.

@@ 100
An unzipper. The odd-looking `16 + zlib.MAX_WBITS` tells zlib that the data is wrapped the **gzip** way (with gzip's header and checksum), not as a bare stream.

@@ 101-104
Unzip — but never more than `MAX_UNPACKED` bytes. If the bytes aren't gzip data at all, zlib raises an error, and we say the code is unreadable. (`from None` hides zlib's own error message: ours says enough.)

@@ 105-107
Two more refusals. `unconsumed_tail`: there was more to unzip than the limit allows — the zip bomb. `not unzip.eof`: the data stopped before gzip's end mark — the number was cut short. Otherwise, the bytes.

@@ 110-119
**`_born`** — the date-of-birth field in one fixed form. Day-first becomes `YYYY-MM-DD`; year-first already is (only the separators are made dashes); a year alone stays a year. The `:=` ("walrus") both stores the match and tests it. Anything else: unreadable. Whether the date *exists* (no 30 February) is checked later, by the API.

@@ 122-124
**`parse`** — split the unzipped bytes into parts. The docstring states how the privacy rule is kept in code: the fields before the date of birth are **counted past, not read**.

@@ 125-127
Too short to hold a signature: refuse. Otherwise cut the bytes in two — the last 256 are the signature, everything before is what it signs.

@@ 128-130
Does it begin with a version? Then the version is the digit after "V", and the date of birth is one field later than in the first layout.

@@ 131-135
Walk to the start of the date-of-birth field: find the next 255, step past it, as many times as there are fields in front. `find` answers −1 when there is no more 255, so `start` becoming 0 means the data ran out: not a Secure QR. The bytes walked over — the reference number and the name — are never looked at.

@@ 136-139
Find the end of the field, and turn just those few bytes into text. ISO-8859-1 is the encoding UIDAI's specification names; it maps every byte to one character, so decoding can never fail.

@@ 140
Find where the photo starts: the first place after the date of birth where either JPEG 2000 beginning appears. `min(…, default=-1)` picks the earlier of those found, or −1 if neither is there.

@@ 141-143
The photo is everything from there to the end of the signed part. That may include the two hashes after it; the comment says why that is harmless — a JPEG 2000 reader stops at the picture's own end mark. No photo found: empty bytes. Then hand back the parts.

@@ 146-149
**`decode_photo`** — the photo's bytes as a picture. No bytes: no picture.

@@ 150-156
Let OpenCV decode it, in colour. Bytes that only *look* like a JPEG 2000 can make OpenCV raise an error or answer `None`; both mean "no picture", as does a picture larger than a Secure QR's photo can be.

@@ 159-166
**`specimen_photo`** — for specimens: shrink a portrait to 160 by 200 pixels and squeeze it as JPEG 2000 to about 2 kB (`…_X1000, 20` asks for a file 2 % the size of the raw pixels). That is roughly how small and how squeezed a real code's photo is, so the tests meet the same blur the real thing has.

@@ 169-171
**`specimen_data`** — a made-up code's bytes. `sign` is a function the caller passes in: it takes the bytes to sign and returns a signature. The tests pass one that signs with a throwaway key — never UIDAI's, which nobody outside UIDAI has. So a specimen can never be taken for a real Aadhaar by any real reader.

@@ 172-179
The fields of the first layout, in order, with fictional values: the email/mobile marker (`0`: neither registered), a reference number no Aadhaar has, a name, the date of birth, the gender, and the eleven address fields. "Utopia" is the made-up country ICAO uses on specimen passports.

@@ 180-181
Later layouts put the version first, and the last four digits of the mobile number after the address.

@@ 182-183
Join them: each field as ISO-8859-1 bytes with a 255 after it, then the photo. Sign that, and put the signature on the end — exactly the shape `parse` takes apart.

@@ 186-189
**`pack`** — the opposite of `unpack`: zip the bytes the gzip way, at the strongest setting (9), and read the result as one big number.

@@ 190-194
Write the number as digits 4,000 at a time, for the same reason `unpack` reads it that way: `divmod` cuts off the last 4,000 digits, `zfill` keeps their leading zeros, and the pieces are put back in order. `lstrip("0")` removes the zeros in front of the first piece.

@@ 197-199
**`specimen_png`** — a picture of a QR code holding `text`.

@@ 200-204
OpenCV's QR **writer**, set to "numeric" mode (digits pack tightest: about 3⅓ bits each) and the lowest error correction (`L`), as a Secure QR is. The `type: ignore` notes are for mypy only: OpenCV's type hints forgot the writer, though it exists.

@@ 205-206
Enlarge each little square to `module` pixels — `INTER_NEAREST` keeps the edges sharp — and add a white margin 8 squares wide: readers need that "quiet zone" to find the code's edge.

@@ 207-210
Encode as PNG, which keeps every pixel exactly. Return the bytes.
