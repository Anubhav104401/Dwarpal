## 5.6 Phase 6 — step-up verifiers

A face estimate is quick and private, but sometimes it can't be sure: a 19-year-old who looks 16, poor light, an attempt that looked like a replay. Then the decision is **step up** (§3.7): offer a stronger method. Phase 6 builds two, from the roadmap (§3.9):

| Order | Method | Status |
| :-: | :-- | :-- |
| 1 | **ID document (MRZ)** — read the machine-readable zone of a passport or ID card, check it, and match its photo to a selfie | 🟢 the parser and age rule (§5.6.1); reading from a photo, the face match and the API's document check (§5.6.2); the verify page's screens (§5.6.3) |
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
    - **A valid MRZ isn't a genuine document.** Check digits catch mistakes, not forgeries: anyone can compute them. A browser can't read a passport's chip, and Dwarpal does no forensic checks of the printing. So a document check counts as **basic** assurance, and must be paired with a match between the document's photo and a live selfie, which §5.6.2 adds.
    - Reading the zone from a photo came next, in §5.6.2.

### 5.6.2 Reading a document from a photo, and matching its face

The parser (§5.6.1) needed text. This step gets it from a photo, and adds the other half of a document check — is the person holding the document the person on it? — then puts both behind the API. Two downloads made it possible, approved on 1 November (decisions D6b and D7b): **Tesseract**, a free OCR engine, run in a small locked-down container; and **SFace**, OpenCV's face recogniser.

The check, from the person's side: the face check couldn't decide, so they photograph their passport's data page and take a selfie, turning their head as asked. Then:

1. **The inference service** finds the MRZ band in the photo, straightens it and has Tesseract read it — blanking the names line before the text leaves the service; finds the face printed on the page; and compares it with each selfie frame. The selfie also goes through the ordinary face pipeline, liveness and all.
2. **The API** decides, in a fixed order: a live selfie; a zone that passes every check digit; one face on the document, matching the selfie's; and only then the age rule. Doubt means *try again* — three tries — then *fail*; never *pass*.
3. **The token** says how the answer was reached: `methods: ["face_estimation", "document_mrz", "face_match"]`, still at `basic` assurance.

!!! key "Key idea — reading is imperfect, so checking is strict"
    Tesseract's English model was not trained on the MRZ typeface, and reads the long runs of `<` badly. Rather than trust it, the parser looks for the **simplest** reading that passes every check digit: first the text as read, then with one character dropped or added, then two — trying an empty optional field too, since that is what OCR misreads most. It accepts a reading only if it is the **only** one at that level. Every repair is reported in the decision's reasons.

    Measured on 40 photographed specimen passports with random dates: **31 read right, none wrong**, 9 refused ("take the photo again"); 11 of the 31 needed a repair. A property test drops a character anywhere in thousands of zones, and the reading is always the true dates — or no reading at all.

!!! kid "Explain like I'm six — a careful reader"
    Imagine a friend reading you a long number over a bad phone line. Sometimes they say a digit twice or skip one. You know a secret rule the real number follows, so you try fixing it one small way at a time. If exactly one fix makes the rule work, you take it. If two different fixes both work, you ask them to read it again — you never just pick one.

Testing a document check needs photos of documents, and real ones belong to real people. So the tests draw their own: the passport of ICAO's fictional holder from the state of Utopia, with whatever dates a test needs, tilted, blurred and noised as a phone would take it (`specimen.py`).

!walk infra/ocr/Dockerfile

!walk libs/vision/src/dwarpal_vision/document.py

!walk libs/vision/src/dwarpal_vision/match.py

!walk libs/vision/src/dwarpal_vision/specimen.py

!walk libs/contracts/src/dwarpal_contracts/document.py

!walk services/inference/src/dwarpal_inference/document.py

!walk services/api/src/dwarpal_api/domain/stepup.py

!walk services/api/tests/test_stepup.py

!walk libs/vision/tests/test_document.py

The document check does more work than the face check, so since 2 November the API waits up to 20 seconds for it rather than 5 (`document_timeout_s`): CI's machines are shared and sometimes slow, and the end-to-end test had twice seen "the checker is busy" instead of a result. That wasn't the whole story — it happened once more on 3 November — so the test now also says, when it fails, what the inference service makes of the passport at that moment.

!walk services/api/tests/test_inference_client.py

The parser (`read_ocr`), the inference service's settings and endpoints, the API's flow endpoints, use cases, size limits and inference client, the contracts' list, the compose file (the OCR container), the model list (SFace), CI (Tesseract on GitHub's machines) and the tests of the parser, the API and the inference service changed too; each was re-explained.

**What the tests prove**:
- end to end through the API, with real OCR: a face check that can't decide sends the person to the document check; an adult's specimen passport passes and a 12-year-old's fails; the token names the methods; and of the document only its kind, issuer, year and month of birth and expiry are kept — no name, no number;
- the document check is open only to a session the face check sent there, and only once it has decided;
- every kind of doubtful evidence — no zone, a refuted check digit, no face or two, faces that don't match, no liveness — is retried, then fails, and never passes;
- the reader finds the band on a tilted photo and not on a face; the matcher matches a face to its printed copy and not to a scrambled one.

!!! honest "Honest limitation"
    - **ID cards read poorly.** Passports (TD3) read well on the specimens; TD2 cards 9 times in 10; but TD1 cards — the three-line kind — rarely, because Tesseract loses the end of their lines. A model trained on the MRZ typeface (OCR-B) would help; the usual one has no licence, so it would have to be trained (decision D6c).
    - **The specimens are not real photos.** They are drawn in an ordinary font, not OCR-B, and photographed by a program. How the reader does on real passports under real light is unmeasured.
    - **The face-match threshold is OpenCV's**, measured on celebrity photos of similar quality, not on a printed passport photo against a webcam.
    - **SFace was trained on faces collected without consent** (D7b). The owner accepted it knowing this; it is recorded with the model.
    - The verify page's screens for it came next, in §5.6.3.

### 5.6.3 The document check on the verify page

The last piece of the MRZ route is the person's side of it. Until now, a face check that couldn't decide ended with "We need a stronger check" and a button back to the website. Now that screen offers the stronger check itself:

1. **"Use a passport or ID card"** — or, quietly underneath, "Not now", for someone who would rather not.
2. **What will happen, before anything is chosen**: a photo of the document's page; a short selfie, and why; exactly what is read, that the name and document number are never kept, and that both photos are deleted straight after. Then one button — on a phone it opens the rear camera, on a computer a file picker.
3. **The photo is prepared in the browser**: scaled to at most 2000 pixels and re-encoded under 1 MB. Redrawing it also leaves behind whatever else the file carried, such as where it was taken.
4. **A selfie** with the very same camera screen as a face check — its challenge, poses and colours — so the person behind the camera must be live.
5. **The answer**: "You're all set", a fail, or a tip and another try ("We couldn't find the lines of letters and <<< at the bottom of the photo page…"), with the tries left.

!!! key "Key idea — consent before capture"
    The design asks that a document check explain itself before a single picture is taken. The three steps on the screen say what is collected, why, what is kept (only the year and month of birth) and what is deleted. Choosing the photo is the person's own act, after reading them.

The browser test drives it all: it makes a session that the face check sends to the step-up (three attempts whose frames aren't pictures at all), opens the verify page, chooses the specimen passport, lets the fake camera play the selfie — the same face as on the specimen — and checks the website's token: a pass, by `face_estimation`, `document_mrz` and `face_match`. The document screen is checked by axe, too.

!walk apps/web/lib/document-photo.ts

!walk apps/web/lib/document-photo.test.ts

!walk e2e/tests/axe.ts

The verify page, its flow client and tips, the page frame (a quiet button), the browser tests' configuration (the specimen, the test key, Tesseract for the inference service), the age-check test and the accessibility test changed too; each was re-explained.

!!! honest "Honest limitation"
    - **Desktop users need a photo file.** On a computer, the button opens a file picker: they must already have a photo of their document. A live document camera on the page — with guidance to fill the frame and avoid glare, as the design describes — would serve them better, and would also stop someone choosing a photo of someone else's document taken earlier; the face match still guards against that.
    - **The Hindi version** of these screens waits for the Hindi work (decision D2).
