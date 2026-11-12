---
fingerprint: eaf02f06c71716f5
---
The **key ring** for Aadhaar Secure QR codes (Part 7, §7.5): UIDAI's public keys, and one question asked of them — *did one of you sign this?* It is the smallest file of the feature and the one everything rests on. The QR reader (`dwarpal_vision.aadhaar`) can read any code, real or home-made; this is what tells them apart.

The certificates themselves are in the folder `uidai_keys` beside this file: five `.cer` files, exactly as downloaded from UIDAI's website on 12 November 2026.

@@ 1-2
The module's docstring: what it holds (the certificates of the keys UIDAI signs with) and what it answers (which of them, if any, made a code's signature).

@@ 4-6
Why that answer is the whole of a code's worth: anyone can draw a QR code that *says* "born in 1990". Only UIDAI's **private** key can make the 256 bytes that these **public** keys accept for it.

@@ 8
The project-wide type-hint setting.

@@ 10
`Path`, for the folder of certificates.

@@ 12-15
From the `cryptography` library: `x509`, which reads certificates (X.509 is the standard format of a certificate, the same as a website's HTTPS one); the error it raises for a signature that doesn't check; SHA-256; and RSA with its "padding" — the agreed way of shaping what gets signed.

@@ 17-19
`UIDAI_KEYS` — the folder of UIDAI's certificates, found relative to this file (`__file__`), so it works wherever the service is installed. The comment says where on UIDAI's website they came from.

@@ 20
`PEM_START` — a certificate file comes in two forms: **DER**, raw bytes, or **PEM**, the same bytes written as text between `-----BEGIN CERTIFICATE-----` lines. A file that starts like this is PEM.

@@ 23-26
**`KeyRing`** — the keys, each under its certificate's file name. The docstring answers a question an interviewer may well ask: *four of the five certificates have expired — why keep them?* Because a card printed in 2020 carries a signature made with 2020's key, and is never printed again. For a website, an expired certificate is a warning; here, what counts is only that the key **was UIDAI's** when it signed.

@@ 28-29
Start with an empty dictionary: name → public key.

@@ 30-33
For every `.cer` file in the folder, in name order: read it, choose the right loader for its form (PEM or DER), and take the **public key** out of the certificate. A certificate holds more — who it belongs to, who issued it, its dates — but the key is the part that checks signatures.

@@ 34-36
A Secure QR is signed with RSA, so anything else in this folder is a mistake: stop at once, at start-up, naming the file. Otherwise keep the key under the file's name without `.cer` (`path.stem`), such as `uidai_offline_publickey_2026`.

@@ 38-39
**`signer`** — the name of the key that made `signature` over `signed`, or `None`.

@@ 40-42
Try each key. `verify` does the mathematics (§7.5): it "opens" the signature with the public key and compares what comes out with the SHA-256 fingerprint of the signed bytes. `PKCS1v15` and `SHA256` are the padding and hash UIDAI's specification names (written there as `SHA256withRSA`).

@@ 43-46
`verify` returns nothing when the signature checks and raises `InvalidSignature` when it doesn't: then go on to the next key. The first key that accepts it is named. None did: `None` — the code was not signed by any key UIDAI has published, or a single byte of it was changed after signing.
