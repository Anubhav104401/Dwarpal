## 5.6 Phase 6 — step-up verifiers

A face estimate is quick and private, but sometimes it can't be sure: a 19-year-old who looks 16, poor light, an attempt that looked like a replay. Then the decision is **step up** (§3.7): offer a stronger method. Phase 6 builds two, from the roadmap (§3.9):

| Order | Method | Status |
| :-: | :-- | :-- |
| 1 | **ID document (MRZ)** — read the machine-readable zone of a passport or ID card, check it, and match its photo to a selfie | 🟡 the MRZ parser and age rule (§5.6.1); reading from a photo and the face match wait for approved downloads |
| 2 | **Aadhaar Secure QR** (India) — verify UIDAI's digital signature on the QR code, then match its photo | 🗓 waits for UIDAI's official specification and certificate |

### 5.6.1 Reading the machine-readable zone

Every passport, and most ID cards, carry two or three lines of capital letters, digits and `<` along the bottom of the photo page: the **machine-readable zone**, defined by ICAO Doc 9303 so that border machines anywhere can read any country's documents. Each important field is followed by a **check digit**, and a final **composite** check digit covers almost everything, so a misread or altered character is noticed.

!!! kid "Explain like I'm six — the counting game"
    Imagine writing your birthday as numbers, then adding them up in a special way and writing down just the last digit of the answer. If anyone later changes one of the numbers, the special sum comes out different, and the last digit no longer matches. That last digit is the check digit.

This step builds the part that can be proved without a camera: given the zone's text, check every check digit, work out the dates, and decide on age. It repairs typical OCR confusions — the letter `O` read for the digit `0`, `I` for `1`, `S` for `5`, `B` for `8` — but **only** when exactly one repair makes a failing check digit pass, and it reports every repair, so whoever reviews a decision can see it.

!walk services/api/src/dwarpal_api/domain/mrz.py

!walk services/api/tests/test_mrz.py

**What the tests prove**:
- ICAO's own specimen documents read correctly in all three layouts (TD1, TD2, TD3), with the check digits the standard prints;
- a hundred randomly generated passports read back exactly;
- any single changed digit in a date of birth is caught;
- a tampered year is refused, and an `O` misread for `0` is repaired and reported;
- only the year and month of birth leave the reader, never a name or number;
- the age rule fails an expired document, and counts a birthday from its day (with leap days falling on 1 March).

!!! honest "Honest limitation"
    - **A valid MRZ isn't a genuine document.** Check digits catch mistakes, not forgeries: anyone can compute them. A browser can't read a passport's chip, and Dwarpal does no forensic checks of the printing. So a document check counts as **basic** assurance, and must be paired with a match between the document's photo and a live selfie, which waits for an approved face-match model.
    - **Reading the zone from a photo isn't built yet**: it needs an OCR engine and a model trained on the MRZ typeface, both downloads awaiting approval.
