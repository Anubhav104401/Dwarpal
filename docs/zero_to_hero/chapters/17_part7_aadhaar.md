# Part 7 — Aadhaar: checking an age from a signed QR code

On **12 November 2026**, two days after launch, the owner asked: *can Dwarpal check an age from an Aadhaar card — as a demo, for learning and for showing to professors and interviewers?* It can, and by the end of that day it did, in test checks. This part explains everything about it from zero: what Aadhaar is, what is inside the big QR code on every Aadhaar, how a signature proves the code is real, how each piece of Dwarpal was changed, what the law asks, and what stands between this demo and a product.

!!! kid "Explain like I'm six"
    Your school gives you a report card. Anyone could write "A+" on a piece of paper — so the head teacher **stamps** the real one with a stamp only she has. Aadhaar's big QR code is a tiny report card with your birthday and your photo in it, and UIDAI's stamp on it. Dwarpal now does three things: it reads the tiny card, it checks the stamp is really UIDAI's, and it checks the photo in the card is **you**, by looking at your face. Then it forgets everything except "old enough" or "not old enough".

## 7.1 The whole idea on one page

```text
  THE PERSON                         DWARPAL (test checks only)
  ───────────                        ─────────────────────────────────────────────────────
  a picture of the big QR code  ──►  1. find the QR code in the picture          (OpenCV)
  on their Aadhaar                   2. its 5,000 digits → bytes → unzip         (Python)
                                     3. split: date of birth | photo | signature
                                     4. did UIDAI sign it?   ──► 5 public keys    (RSA)
  a short selfie, turning       ──►  5. is the selfie a live person?             (liveness, as always)
  their head when asked              6. is it the person in the code's photo?    (face match)
                                     7. old enough on today's date?              (arithmetic)
                                     ─────────────────────────────────────────────────────
  "old enough: yes/no"          ◄──  a signed token, methods: document_aadhaar_qr + face_match
                                     kept: which key signed, year and month of birth. Nothing else.
```

Seven steps, and only step 7 can say "pass". Each of the others can only say "try again" or "no".

| Piece | Where it lives | Section |
| :-- | :-- | :-- |
| Finding and reading the code | `libs/vision/src/dwarpal_vision/aadhaar.py` | §7.3, §7.4 |
| UIDAI's keys, and checking the signature | `services/inference/src/dwarpal_inference/aadhaar.py` and the folder `uidai_keys` beside it | §7.5 |
| The document check that calls both | `services/inference/src/dwarpal_inference/document.py` | §7.6 |
| What may leave the AI service | `libs/contracts/src/dwarpal_contracts/document.py` | §7.6 |
| The rules that decide | `services/api/src/dwarpal_api/domain/stepup.py` | §7.7 |
| The words the person sees | `apps/web/messages/en.json`, `hi.json`; `verify-flow.tsx` | §7.8 |

Nothing was added to the database, no new address was added to the API, and **nothing was downloaded except five small certificate files from UIDAI**. The Aadhaar check rides on the document check that Phase 6 built for passports (§5.6).

## 7.2 Aadhaar in two minutes

**Aadhaar** is a 12-digit number that the Indian government gives to each resident, after taking their photo, fingerprints and iris scans. The agency that runs it is **UIDAI**, the Unique Identification Authority of India. More than a billion people have one.

There are several ways to check an Aadhaar, and they differ in one thing that matters enormously: **whether UIDAI's computers are asked**.

| Way | How it works | Asks UIDAI's servers? | Who may do it |
| :-- | :-- | :-- | :-- |
| **Online authentication** (a one-time code to the person's phone, a fingerprint, or a face) | The checker sends the Aadhaar number to UIDAI and gets "yes/no" or the person's details (e-KYC) | **Yes** | Only organisations UIDAI has licensed (called AUAs and KUAs), or others working through one |
| **Offline e-KYC file** | The person downloads a signed, password-locked file of their details and hands it over | No | Since December 2025: organisations **registered** with UIDAI as offline verifiers |
| **Verifiable credential from the new Aadhaar app** | The person's phone shares only the details they pick — for instance just the date of birth | No | The same registered organisations |
| **Secure QR code** (this part) | The code printed on the Aadhaar holds signed details; anyone with UIDAI's public keys can check it | No | See §7.10 |

Dwarpal uses the last one, because it is the only one a student project can build without a licence, a registration, or UIDAI's cooperation: UIDAI **publishes** what is in the code and the keys that check it.

!!! key "Key idea — \"offline\" means UIDAI never hears about it"
    When Dwarpal checks a Secure QR, no message goes to UIDAI. UIDAI doesn't learn that you used your Aadhaar, when, or on which website. The proof travels **with the code**: a signature that anyone can check and only UIDAI can make. This is the same idea as Dwarpal's own age tokens (§5.4), one level up: a website checks Dwarpal's signature without calling Dwarpal; Dwarpal checks UIDAI's signature without calling UIDAI.

!!! real "Real world — the invigilator and the PAN card"
    Before an online coding exam, the owner's invigilator scanned the QR code on each candidate's **PAN card**. New PAN cards (since 2018) carry a QR code with the holder's photo, name, parent's name, date of birth and signature, also digitally signed. So why didn't we use that? Because, as far as we could find, its format is **not published**: it is read with a specific app from the companies that print PAN cards, and nobody else can check its signature. The invigilator almost certainly used that app and compared the photo on screen with the face in front of them. Aadhaar's code can be built on because UIDAI published its keys. An open format is what lets an outsider verify.

## 7.3 Reading a very dense QR code

### What a QR code is

A **QR code** is a square grid of small black and white squares, called **modules**. Three big squares in the corners tell a reader where the code is and which way up. The rest is data, plus spare information for repairing damage (**error correction**).

QR codes come in 40 sizes, called **versions**. Version 1 is 21 modules a side and holds 41 digits. Version 40 is **177 modules a side** and holds **7,089 digits**. A Secure QR is near the top of that range: our specimen has 5,437 digits and is 161 modules a side — about 26,000 little squares.

!!! kid "Explain like I'm six"
    A normal QR code is like big writing on a poster: you can read it from across the street. Aadhaar's is like a whole page of tiny print squeezed onto a stamp. To read it, you have to hold it close and still.

### What we measured before trusting it

OpenCV, the vision library Dwarpal already uses (§5.1), has **two** QR readers. Before building anything, both were tried on made-up codes of Aadhaar's size, as clean drawings and as simulated phone photos (tilted, blurred, noisy, saved as JPEG):

| | Older reader (`QRCodeDetector`) | Newer reader (`QRCodeDetectorAruco`) |
| :-- | :-- | :-- |
| Clean drawing, 4,500–6,500 digits | read some, missed some | **read all** |
| Photo, each module 10 pixels wide | — | **read all** |
| Photo, each module 7 pixels wide | — | **read all**, sometimes only after enlarging the picture |
| Photo, each module 4 pixels wide, slightly blurred | — | read only after enlarging 1.5–2 times |
| Photo, 4 pixels, more blurred | — | **not read** |

Two decisions came out of that table:

1. **Use the newer reader, and try several sizes.** `read_qr` tries the picture as it is, then 1.5 times, 2 times and 0.75 times as big, then in pure black and white, and stops at the first that gives a code.
2. **Tell the person to fill the picture with the code.** A document photo may be 2,000 pixels wide; a 161-module code that fills most of it gets about 10 pixels a module, which reads reliably. The same code small in a corner does not. This is why a sharp screenshot of the e-Aadhaar PDF works best, and why a computer's webcam mostly won't.

No new library was needed. Had OpenCV failed, the fallback was a dedicated barcode library (`zxing-cpp`), which would have been a download to ask the owner about.

## 7.4 From 5,000 digits to a date of birth

### The layers, like a parcel

A Secure QR's content is wrapped in layers. `unpack` and `parse` remove them one at a time:

| Layer | What it is | How it is removed |
| :-- | :-- | :-- |
| 1 | **Text of digits**, about 5,000 of them | It is one enormous whole number, written in decimal |
| 2 | That number, written as **bytes** | `number.to_bytes(…)` |
| 3 | Those bytes are a **gzip file** (zipped data, as `.gz` files are) | `zlib`, with a size limit |
| 4 | Unzipped: **fields**, a **photo**, maybe two **hashes**, a **signature** | Cut at fixed places (below) |

Why did UIDAI do it this way? A QR code stores **digits** more tightly than anything else: 3⅓ bits per digit, against 8 bits for a byte of ordinary data mode on many readers. Zipping first makes the data smaller; writing it as a number lets it use digit mode.

### The layout of the unzipped bytes

```text
  V2 ÿ 3 ÿ ref-number ÿ name ÿ DOB ÿ gender ÿ …11 address fields… ÿ last-4-of-mobile ÿ [photo] [email hash] [mobile hash] [signature]
  │    │                       └── the only field Dwarpal reads                         │                                   └ last 256 bytes
  │    └ 0–3: which of email/mobile are registered                                     └ JPEG 2000
  └ the version (the first, 2018 layout has no version field)                    "ÿ" is the byte 255: it ends each field
```

`parse` finds the signature by **counting from the end** (always the last 256 bytes), and the date of birth by **counting field ends from the start** (the fourth or fifth 255, depending on the version). It never turns the reference number, the name or the address into text. They are stepped over as bytes.

!!! key "Key idea — privacy by not reading"
    The safest way to protect a name is never to hold it. The parser has no variable that ever contains the holder's name or address. The reference number (which contains the last four digits of the Aadhaar number) is likewise never read. Three walls then stand in the way of a leak: the parser doesn't read them; the message from the AI service to the API has **no field** for them (`AadhaarReading`, §7.6); and a test checks that the made-up holder's name appears nowhere in the service's answer.

### A surprise: Python refuses long numbers

The first run of the new code stopped with: *"Exceeds the limit (4300 digits) for integer string conversion"*. Python can calculate with numbers of any size, but since 2022 it refuses to convert **text longer than 4,300 digits** into a number, or back, in one step. The conversion gets slow for huge inputs (its time grows with the square of the length), and attackers had used it to stall servers by sending enormous numbers.

The limit can be raised for the whole program, but that would remove the protection everywhere. Instead `unpack` and `pack` convert **4,000 digits at a time**: read "12" then "34" as 12 × 100 + 34. The work stays small because the text was already refused if longer than 8,000 digits.

### A second guard: the zip bomb

A **zip bomb** is a small file made to unzip into something gigantic: 200 kB of zeros zips to a few hundred bytes, which fits in a QR code. A service that unzips whatever it is given can be made to fill its memory. `unpack` tells zlib to stop at 64 kB, and refuses anything that wants more. A test builds such a bomb and checks it is stopped.

!walk libs/vision/src/dwarpal_vision/aadhaar.py

!walk libs/vision/tests/test_aadhaar.py

## 7.5 The signature: how a picture can prove it is real

Everything so far could be faked. Anyone who has read §7.4 can make a QR code that unpacks to "born 1 January 1960" with any photo they like — our own tests do exactly that. What a forger **cannot** make is the last 256 bytes.

### Signing, in plain words

UIDAI has a **key pair** (§0.9, §6.3): a private key that only UIDAI holds, and a public key that it publishes. They are numbers with a special relationship: what one "locks", only the other "opens".

1. UIDAI takes all the bytes of the code except the last 256 and computes their **SHA-256 hash**: a 32-byte fingerprint that changes completely if any one bit changes (§X.5).
2. It "locks" that fingerprint with its **private key**. The result is the **signature**, 256 bytes, and it goes on the end of the code.
3. Dwarpal computes the same fingerprint from the same bytes, "opens" the signature with UIDAI's **public key**, and compares. Equal: the bytes are exactly what UIDAI signed. Different: they were changed, or UIDAI never signed them.

The kind of key is **RSA** with 2,048 bits. RSA's secret is two huge prime numbers; the public key contains their product. Multiplying two primes is easy, and finding them back from the product is, for numbers this size, beyond every computer on Earth. The exact recipe is called `SHA256withRSA` (PKCS #1 version 1.5), and it is the one UIDAI's specification names.

!!! try "Try it yourself"
    One of the tests does what a cheat would: it takes a properly signed specimen, changes the birth year from **1990 to 1980**, keeps the old signature, and asks the key ring. The answer is `None`: no key accepts it. Run it: `uv run pytest services/inference/tests/test_aadhaar.py -k changed_byte`.

### Certificates, and why we keep expired ones

A public key is published inside a **certificate**: a small file saying "this key belongs to UIDAI", itself signed by a higher authority (India's licensed certifying authorities), with a start and an end date. UIDAI changes its signing key every two or three years. Its website lists five certificates for Secure QR codes and offline e-KYC, and Dwarpal ships all five:

| Certificate file | Key valid | SHA-256 of the file (start) |
| :-- | :-- | :-- |
| `uidai_offline_publickey_26022019.cer` | 27 Apr 2017 – 9 Apr 2019 | `b6696efb937378db` |
| `uidai_offline_publickey_29032019.cer` | 15 Mar 2019 – 28 Feb 2021 | `89208e69e3da8667` |
| `uidai_offline_publickey_26022021.cer` | 26 Feb 2021 – 27 Feb 2024 | `288475ef50ac1e73` |
| `uidai_offline_publickey_17022026.cer` | 21 Feb 2024 – 16 Feb 2026 | `68607e079d81ecbf` |
| `uidai_offline_publickey_2026.cer` | 3 Feb 2026 – 3 Feb 2029 | `1ea1c3468af58196` |

They were downloaded on 12 November 2026 from `uidai.gov.in` → *Build with us* → *Developer resources* → *Data and downloads*, under "Public key certificate details for validating the digital signature of Aadhaar Paperless Offline e-KYC and Secure QR Code" (decision D46; the full fingerprints are in `docs/reports/pending-decisions.md`).

Four of the five have **expired**. For a website, an expired certificate means "don't trust this". Here it is different: an Aadhaar letter printed in 2020 carries a signature made in 2020 with 2020's key, and it is never re-signed. What must be true is that the key **was UIDAI's**, and UIDAI's own list says so. So all five stay on the ring, and `signer` reports **which** one signed, which is recorded with the check.

!!! honest "Honest limitation"
    Dwarpal trusts these five files because they came from UIDAI's website over HTTPS. It does not (yet) check each certificate's own chain up to India's root authority, and it cannot know if UIDAI **withdraws** a key. A production service would do both, and would watch UIDAI's page for a sixth certificate: until it is added, codes signed with a new key are refused (safely: "not signed by UIDAI", never a false pass).

!walk services/inference/src/dwarpal_inference/aadhaar.py

!walk services/inference/tests/test_aadhaar.py

## 7.6 Inside the AI service: one more kind of document

Phase 6 built the **document check** (§5.6): a photo of a passport's data page and a short selfie go to the inference service, which reads the page's machine-readable zone, finds the printed face, and compares it with the selfie. Aadhaar joins as a second kind of document, through the same door:

1. The selfie goes through the face pipeline exactly as before: quality, liveness, anti-spoofing.
2. **New:** the document picture is first searched for a Secure QR. This comes before the MRZ search because a QR's dense pattern can look like lines of print to the MRZ finder.
3. If there is one: unpack it, split it, ask the key ring who signed it, decode the photo inside it.
4. The face comparison is the same code as for passports, but the "document's photo" is now the one **from inside the code**, enlarged first (§7.9).
5. If there is no QR code, everything happens as it did in Phase 6.

What leaves the service is a new, deliberately small message:

```python
class AadhaarReading(Contract):
    signed_by: str | None   # which UIDAI key signed it — or None
    born: str | None        # "1990-01-01", or "1990"
    problem: str | None     # "aadhaar_qr_unreadable", when there is no date
```

Three fields. There is no place to put a name, and `Contract` forbids extra fields (§5.2), so a future mistake that tried to send one would fail in tests rather than leak.

The service's readiness answer gained one item, `"aadhaar_keys": "5"`, so a deploy can see that the certificates arrived inside the image.

## 7.7 The rules that decide

The API's `decide_document` (§5.6.3) gained a branch, `decide_aadhaar`. As everywhere in Dwarpal, the rules run in a fixed order, doubt never passes, and only the last line can say "pass":

| # | Rule | If it fails | Reason code |
| :-- | :-- | :-- | :-- |
| 1 | The session is a **test** session | Try again with a passport | `aadhaar_test_only` |
| 2 | The selfie is a live person | As for any document | `liveness_…` |
| 3 | A date of birth came out of the code | Try again | `aadhaar_qr_unreadable` |
| 4 | **UIDAI signed the code** | Try again | `aadhaar_signature_invalid` |
| 5 | The date can exist, and isn't in the future | Try again | `aadhaar_qr_unreadable` |
| 6 | Exactly one face in the code's photo | Try again | `document_face_not_found` |
| 7 | The selfie's face matches it | Try again | `face_mismatch` |
| 8 | Old enough today | **Fail**, at once | `under_age`, `aadhaar_qr` |
| | All of the above | **Pass** | `document_over_age`, `aadhaar_qr` |

"Try again" becomes "fail" on the third attempt, as for passports.

Three choices are worth explaining:

- **Test sessions only (rule 1).** A live check is one a real website relies on. This feature is a demonstration, with no registration at UIDAI and a legal question still open (§7.10). So the API refuses an Aadhaar code in a live session, and says so first, before any other complaint.
- **A year alone counts as its last day.** Some people's Aadhaar holds only a year of birth. Someone "born in 2008" may have been born on 31 December 2008, so that is the date used. A person is never taken for older than they might be.
- **No expiry check.** A passport expires, and an expired one fails. A date of birth that UIDAI signed doesn't stop being true.

The age token a passing session gets says how it was decided: its `methods` claim is `["face_estimation", "document_aadhaar_qr", "face_match"]` (or without the first, in a session that began at the document). A website can therefore tell an Aadhaar-based "yes" from a passport-based one.

## 7.8 What the person sees, and what is kept

On the verify page, a **test** session's document step shows one more paragraph, in English or Hindi. It says an Aadhaar Secure QR works too; that the code should fill the picture; what is checked (UIDAI's signature), what is read (only the date of birth), what is compared (the selfie with the photo inside the code); what is never read out or kept (the Aadhaar number, name and address); and that **using Aadhaar is the person's choice** — a passport works as well. That paragraph is the notice the law expects a person to get before their Aadhaar is used (§7.10). Three new messages cover the three new ways it can go wrong.

**What is kept afterwards**, for a check decided by an Aadhaar code:

| Kept in the database | Never kept — and never even read out of the code |
| :-- | :-- |
| Which UIDAI certificate's key signed the code | The Aadhaar number (the code holds only its last 4 digits, inside the reference number) |
| The **year and month** of birth (the year alone, if that is all the code has) | The name, gender and address |
| How alike the two faces were (one number) | The photo, the picture of the code, the selfie |
| The outcome and its reason codes | The day of birth |

An end-to-end test reads the stored record back from the database and checks that the specimen's name and reference number are not in it.

## 7.9 The face inside the code

The photo in a Secure QR must fit in a QR code, so it is tiny and heavily compressed: a JPEG 2000 of roughly 1–2 kB. Our specimen's is 160 by 200 pixels at 1.9 kB. Can a face-matching network work with that? It was measured, on the test portrait:

| Photo in the code | How alike the matcher finds it to the full portrait (pass mark: 0.363) |
| :-- | :-- |
| 160 × 200, 7.7 kB | 0.91 |
| 160 × 200, 3.8 kB | 0.86 |
| 160 × 200, 1.9 kB (the specimen) | 0.71 |
| 160 × 200, 1.0 kB | 0.33 — **below the pass mark** |
| 96 × 120, 1.4 kB | 0.59 |
| 96 × 120, 0.7 kB | 0.21 |
| 64 × 80, 1.2 kB | 0.43 |
| 64 × 80, 0.6 kB | no face found |

Two lessons: the photo has to be **enlarged** before the face detector sees it (at its own size the detector sometimes found no face; `QR_PHOTO_SIDE` enlarges the shorter side to 320 pixels), and the face must **fill** the photo, as on an ID photo. The first specimen squeezed the whole astronaut picture, face small in the middle, into 160 × 200 — and scored 0.21 against itself.

!!! honest "Honest limitation"
    These numbers compare a photo with **itself**, squeezed. A real check compares a webcam selfie taken today with an enrolment photo that may be ten years old, taken in different light. That is harder, and it has not been measured, because the project has no consented set of real Aadhaar photos — and must not collect one. The pass mark (0.363) is the face matcher's standard one. The first real trial — the owner, with their own Aadhaar — will show whether honest people are turned away. If they are, the right answer is to say so, not to lower the mark until it passes.

## 7.10 The law, in plain words

!!! warn "Careful — this is an engineer's reading, not legal advice"
    The points below are how the rules read to us from the Aadhaar Act, UIDAI's public pages, and summaries by law firms of the December 2025 amendment. UIDAI's own regulations and handbook were not all readable from its website while this was built. Before anyone but the owner uses this with a real Aadhaar on the public site, and long before any commercial use, a lawyer must confirm each line.

**What the demo relies on.**

- Checking an Aadhaar without asking UIDAI's servers is called **offline verification** in the Aadhaar Act, and using Aadhaar that way is **voluntary** for the person.
- Whoever does it must, as we read the Act's section on offline verification: get the person's **consent** first; tell them what is collected and why, and that **other documents are accepted**; use what they learn **only for that purpose**; and **not collect, use or store the Aadhaar number or biometric information**.
- The December 2025 amendment created a **register** of offline verifiers. The summaries we found say that those who verify from a **QR code or a copy of the Aadhaar** need not register, while those who use the offline e-KYC file, the new app's verifiable credential, or UIDAI's offline **face** verification must.

**The open question.** The Act's definition of *biometric information* includes the **photograph**. Dwarpal compares the selfie with the photo from the code. It keeps neither picture, only one number saying how alike they were. Whether that comparison counts as "using biometric information", and whether it is a kind of face verification that only registered verifiers may do, is exactly what a lawyer must answer. Until then: **test sessions only**, the owner's **own** Aadhaar for trials, and the notice of §7.8 in front of anyone else.

**From demo to product: what to get, in order.**

| # | Step | Why |
| :-- | :-- | :-- |
| 1 | A **registered company** (or LLP) | Registrations and licences are given to organisations, not to a student's project |
| 2 | A **lawyer's opinion** on the points above | Before real users |
| 3 | Registration with UIDAI as an **Offline Verification Seeking Entity (OVSE)** | It opened in January 2026. It allows the new Aadhaar app's **verifiable credential**, where the person shares only what they choose — for an age check, ideally just the date of birth. That is a better design than the QR code, which always carries the name and address too |
| 4 | Compliance with the **Digital Personal Data Protection Act, 2023** and its rules | Notice, consent, security, telling people and the regulator about a breach, deleting data when its purpose is over, and stricter duties for children's data |
| 5 | An **age model** trained and calibrated on data licensed for commercial use | The current one is for non-commercial research only (§6.15) |
| 6 | A **bought domain**, and more than one server | §6.7, §6.13 |
| — | *Probably not needed:* a licence for **online** authentication (AUA/KUA) | That is for asking UIDAI's servers; an age check doesn't need it |

## 7.11 Trying it

The Aadhaar check is part of the **document step**, which a session reaches when the face check can't decide (a "step-up", §5.6). On the demo shop that happens when the age model isn't sure — most often for people in their early twenties.

1. Get a sharp picture of the **large** QR code: best, a screenshot of your e-Aadhaar PDF with the code as big as the screen allows; or a close, flat, well-lit phone photo of the printed code. (The small QR code on some old cards is the pre-2018 kind, unsigned: it won't work.)
2. Start a check on the demo shop. When it asks for a document, choose that picture.
3. Take the selfie, turning your head as asked.
4. The check answers. In the console, the session's record shows the reasons (`document_over_age`, `aadhaar_qr`) and which UIDAI key signed your code.

If it says the code couldn't be read, the picture isn't sharp or large enough (§7.3). If it says the selfie didn't match, see §7.9 — and tell us, because that is the measurement we don't have.

## 7.12 How it was built, and what went wrong on the way

| Step | What happened |
| :-- | :-- |
| Finding UIDAI's files | UIDAI's website had been reorganised; every old link to the QR specification and certificates was dead. The certificates were found by browsing its new *Developer resources* pages. The **specification PDF** was not found; the layout in §7.4 is the long-published one, as implemented by many open-source readers. **A real Aadhaar is its final test**: if the layout were wrong, UIDAI's signature would not check |
| Could OpenCV read it? | Measured first (§7.3), so no new library was needed |
| The 4,300-digit limit | Met on the first run (§7.4) |
| The squashed astronaut | The first face-match test scored 0.21 against itself: the specimen's photo had been squashed out of shape and the face was too small in it (§7.9) |
| A lost test marker | Inserting two new tests above an old one separated the old test from its `@pytest.mark.anyio` line, and three tests "failed" with *async functions are not natively supported*. A reminder that a decorator belongs to the function directly below it |
| An honest test name | A test named "a certificate that is not RSA is refused" was really testing "a file that is not a certificate". It was renamed to say what it does |

All of it is covered by tests that use **no real Aadhaar**: 15 for the reader, 7 for the key ring and the AI service, 15 for the rules, and 3 end-to-end through the real API, database and AI service.

!!! honest "Honest limitation"
    - **Not yet tried with a real Aadhaar.** Every test uses specimens. The first real code may show a layout detail or a date form this reader doesn't know; it would then say "unreadable", never a false pass.
    - **Face match against a real enrolment photo is unmeasured** (§7.9).
    - **A code is not revocable.** If an Aadhaar is cancelled, old printed codes still verify. Only UIDAI's online services know the current state.
    - **A code can be copied.** Its signature proves UIDAI made it, not that the person showing it owns it. The face match and the liveness check are what tie it to a living person, and they are only as strong as §7.9 and Phase 3 make them.
    - **The whole code reaches Dwarpal's server**, name and address included, for the fraction of a second it takes to read. It is held only in memory and never written anywhere, but it does arrive. The app's verifiable credential (§7.10, step 3) would avoid even that.
    - **The legal question of §7.10 is open.**

## 7.13 If an interviewer asks

**"How does your Aadhaar check work?"** The Secure QR on an Aadhaar is a gzip-compressed record — demographics, a JPEG 2000 photo — signed by UIDAI with RSA-2048 and SHA-256. I decode the QR, verify the signature against UIDAI's published certificates, take only the date of birth, and match a live selfie against the photo inside the code. No call to UIDAI is made. (§7.1)

**"Why should anyone trust a QR code?"** They shouldn't trust the code; they trust the signature. I can generate a code that says anything, and my tests do. But without UIDAI's private key, the signature fails. Changing one byte of a real code breaks it too. (§7.5)

**"What stops a child using a parent's Aadhaar?"** The face match against the photo in the code, and the liveness check on the selfie. That is also the weakest link, and I say so: the photo is tiny and may be years old. (§7.9)

**"What personal data do you store?"** For an Aadhaar check: which UIDAI key signed, the year and month of birth, a similarity score, and the outcome. The name, address and number are never parsed, there is no field for them between my services, and a test asserts they are absent. (§7.4, §7.8)

**"What surprised you?"** Python refusing to convert a 5,000-digit string to an integer — a denial-of-service protection added in 2022. I convert in chunks instead of lifting the limit globally. (§7.4)

**"What attacks did you think about?"** Forged codes (signature), altered codes (signature), someone else's code (face match and liveness), a zip bomb in the QR (a decompression limit), a QR that isn't Aadhaar's (format checks before any work), and oversized input (length limits first). (§7.4, §7.5)

**"Why keep expired certificates?"** Because documents signed years ago are still in people's wallets. Expiry tells you not to accept **new** signatures from a key; it doesn't make old ones false. (§7.5)

**"Is this legal to run commercially?"** Not as it stands, and it is switched off for live checks. Commercial use needs a registered entity, registration with UIDAI as an offline verifier, legal advice on using the photo, and data-protection compliance. The better long-term design is the Aadhaar app's verifiable credential, which shares only the date of birth. (§7.10)

**"Why not call UIDAI's API?"** That is online authentication, open only to licensed agencies. Offline verification also has a privacy advantage: UIDAI never learns where the person used their Aadhaar. (§7.2)

**"How did you test without real Aadhaar data?"** With specimens: the real layout, fictional contents, signed by a throwaway key made in the test. UIDAI's key ring must refuse them — one test asserts that — and a ring holding the throwaway certificate accepts them, which exercises the accepting path. (§7.12)
