# ADR-0016: Step-up verifiers — ID-document MRZ first, Aadhaar Secure QR second

- **Status:** Accepted — 2026-10-15 (owner decision)

## Context
Adults inside the estimation buffer need a stronger method ([ADR-0003](0003-waterfall-face-estimation-then-step-up.md)). Browsers cannot read passport chips. India's DPDP Rules mention verification via tokens from authorised entities such as DigiLocker. Aadhaar's Secure QR carries a UIDAI digital signature over the holder's data, including date of birth.

## Decision
All verifiers implement one `StepUpVerifier` interface. Policies list the allowed methods.

1. **MRZ (first):**
    - capture of the document data page plus a live selfie;
    - MRZ detection, OCR and our own **ICAO 9303** parser (TD1/TD2/TD3) with check-digit validation and bounded OCR-confusion repair;
    - expiry and age rules;
    - a selfie ↔ portrait 1:1 face match (licence-checked model).

   Assurance: **basic**, because there is no chip reading and no forensics.
2. **Aadhaar Secure QR (second, India-only by policy):**
    - QR decoded in the browser;
    - server-side decompression and field parsing per UIDAI's published specification, and **RSA-SHA256 signature verification** with UIDAI's offline-verification certificate;
    - date-of-birth check, then a selfie ↔ QR-photo match.

   Assurance: **standard** for date-of-birth authenticity, reviewed after the face-match evaluation. No Aadhaar data is stored. Explicit consent is required. It is labelled "requires legal review before production use".

## Consequences
- **Good:** a worldwide fallback plus a cryptographically strong, India-relevant one; a pluggable design ready for EU wallets (OpenID4VP/SD-JWT VC) later.
- **Cost:** OCR and face-match components; regulated-data handling for Aadhaar; honest assurance labelling.

## Alternatives considered
A mock verifier only (leaves young-looking adults stranded); DigiLocker APIs (require organisational onboarding); credit-card checks (payment-provider dependency; weak in India); digital wallets (ecosystems still rolling out; planned for v2).
