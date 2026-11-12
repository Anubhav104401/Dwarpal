---
fingerprint: a45012c1a1a94f72
---
The tests of the Aadhaar Secure QR check inside the inference service (Part 7): the key ring, and the document endpoint reading a code. Their trick is worth understanding. Nobody outside UIDAI has UIDAI's private key, so no test can make a code that UIDAI's ring accepts. Instead the tests make **their own issuer** — a key pair created for the test run and thrown away after — and show two things: UIDAI's ring **refuses** its codes, and a ring holding its certificate **accepts** them. The same code runs either way; only the folder of trusted certificates differs.

@@ 1-5
The file's docstring: no real Aadhaar is used; the specimens are signed with a throwaway key, which UIDAI's keys must refuse, and a second ring shows the accepting path.

@@ 7
The project-wide type-hint setting.

@@ 9-12
For the test client helper, dates for the certificate's validity, and paths.

@@ 14-17
OpenCV and NumPy (to cut the portrait), httpx (to call the service in memory), and pytest.

@@ 18-21
From `cryptography`: the tools to **make** a key and a certificate — the tests play UIDAI's part here, which the service itself never does.

@@ 22
FastAPI's app type, for the helper below.

@@ 24-28
The contracts; the key ring and where UIDAI's certificates are; the service's app and settings; and the vision library's specimen makers.

@@ 30-31
The repository's root, and the astronaut portrait as JPEG bytes — it plays both the selfie and the face inside the code.

@@ 32
`NO_OCR` — a Tesseract command that doesn't exist. These tests never read an MRZ, so they run on any computer, with or without Tesseract.

@@ 35-38
**`issuer`** — the stand-in for UIDAI's signing key: RSA, 2,048 bits, the same kind. `scope="module"` makes it once for the whole file: generating an RSA key takes a noticeable fraction of a second.

@@ 41-43
**`keys_dir`** — a folder holding the stand-in's certificate, as UIDAI's folder holds UIDAI's.

@@ 44-55
Build a certificate: a name, the same name as its issuer (it is **self-signed** — it vouches for itself, which is fine for a test), the public key, a random serial number, valid from yesterday to tomorrow, signed with the private key.

@@ 56-59
Save it twice, in the two forms a certificate file can take: PEM (text) and DER (raw bytes). The key ring must read both.

@@ 62-66
**`specimen`** — a made-up Secure QR's bytes with the portrait (cut close round the face) inside, signed by the stand-in exactly as UIDAI signs: RSA with PKCS #1 v1.5 padding over a SHA-256 hash.

@@ 69-74
**`client_for`** — a test client for the app: starts it (which loads the models and the key ring), and talks to it in memory, with no network.

@@ 77-80
**`check`** — one document check: three selfie frames (the portrait) and the document's picture, as a PNG.

@@ 81-87
Post them to the document endpoint, ask `/readyz` too, and return the analysis (checked against the contract) and the readiness answer.

@@ 90-93
**UIDAI's ring.** It holds five keys — the five certificates UIDAI publishes for Secure QR codes — and every one is 2,048 bits. If a file went missing from the folder, this fails.

@@ 94-95
And it refuses the specimen: properly made, properly signed — but not by UIDAI. This is the forgery test at its plainest.

@@ 98-102
**A ring names the signer.** The test folder gives a ring of two entries (the same certificate in PEM and in DER)…

@@ 103-105
…and it names the key that signed the specimen.

@@ 106-107
**One changed byte breaks it.** Take the signed bytes and change the birth year from 1990 to 1980 — what a cheat would do to look older — keeping the old signature. No key accepts it. A signature covers every byte; that is the point of one.

@@ 110-113
**A file that isn't a certificate** stops the ring from being built at all, with an error at start-up — rather than a service that quietly trusts nothing, or something wrong.

@@ 116-121
**The whole path**, with the ring that trusts the stand-in: a specimen born on 15 August 2001, drawn as a QR picture, sent as the document.

@@ 122-124
The answer says it was an Aadhaar code, signed by `test_issuer`, born `2001-08-15` (the day-first date turned round); and there is no MRZ zone and no zone problem.

@@ 125-127
One face was found in the code's own photo, the selfie matches it well (above 0.5; the pass mark is 0.363), and the selfie's three frames were usable.

@@ 128-129
**The privacy check**: the word "Specimen" — the made-up holder's name — is nowhere in the service's answer. And readiness reports the two keys on this ring.

@@ 132-138
**The same specimen, shown to the real ring.** It is read — the date comes out — but `signed_by` is `None`. This is exactly what would happen if someone drew their own "Aadhaar" code and showed it to the live site. Readiness reports UIDAI's five keys.

@@ 141-147
**A QR code of digits that isn't a Secure QR** (the digits 1234567890, forty times): recognised as an attempt at one, and answered with `aadhaar_qr_unreadable` — no date, no face, no similarity.

@@ 150-155
**Switched off** (`aadhaar_qr=False`): the same picture is not looked at as an Aadhaar code at all, and readiness reports `"0"` keys.
