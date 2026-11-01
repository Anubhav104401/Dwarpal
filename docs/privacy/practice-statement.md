# Age assurance practice statement

> **Draft — not legally reviewed.** The owner has not yet arranged a legal review (O5, 1 Nov 2026); nothing here should be relied on or published as final until one is done. In the style of ISO/IEC 27566-1 (Age assurance systems — framework), which asks providers to publish how their system works, how well it performs, and what it does with data. Statements describe the system as built on 26 Oct 2026; figures marked *pending* will be filled from the final model card.

## 1. The service

Dwarpal checks whether a person meets a website's minimum age. The website sends the person to Dwarpal's verify page; Dwarpal estimates their age from a few seconds of camera, checks that a live person is present, and returns a **signed yes/no** for the website's age line. Dwarpal never learns who the person is, and never stores their face.

## 2. Methods and assurance

| Method | What it shows | Indicator of confidence |
| :-- | :-- | :-- |
| **Facial age estimation** with liveness | that the person very probably meets the age line, with a stated error budget | *basic*, rising with the policy's risk budget |
| **ID document (MRZ)** — step-up, in development | that a valid-looking document states an old-enough date of birth, matched to a live selfie | *basic* (no chip reading, no forensic checks) |
| **Aadhaar Secure QR** — step-up, planned (India) | a UIDAI-signed date of birth, matched to a live selfie | *standard* for the date of birth (subject to review) |

Every result says which method and policy version produced it (the token's `methods` and `policy` claims).

## 3. Decision rules

- Three outcomes: **pass**, **fail**, or **step up** to a stronger method when the estimate is uncertain (ADR-0003, ADR-0006).
- The line for *pass* is set so that, for people just under the age line, the chance of passing stays within the policy's **risk budget** (2 % by default), with a 95 % statistical upper bound (Clopper–Pearson).
- Liveness failures lead to *retry*, then *reject*; signs of a manipulated camera lead to *step up*. The reasons shown to the person are deliberately general.
- Each further attempt in a session raises the bar; sessions, devices and network addresses have attempt budgets.
- A failure of any internal component can never produce a *pass*: the system fails closed.

## 4. Performance

| Measure | Figure |
| :-- | :-- |
| Minors under 18 passing an 18+ check (band average, upper bound) | *pending final model card* (release gate: ≤ 5 %) |
| Adults 25+ passing without step-up | *pending* (release gate: ≥ 85 %) |
| Largest gap between groups | *pending* (release gate: ≤ 2 percentage points) |
| Presentation-attack results | owner red team, Phase 3: 0 of 3 posed-photo and 0 of 4 video-replay attacks passed; virtual-camera and deepfake attacks not yet tested |

The current served model is a **stand-in** until calibration passes the release gates; live checks are refused until then.

## 5. Privacy

- Face images exist only in memory during one request, and no part of the system can store them.
- Kept: numbers about each attempt and the session's outcome, for the website's retention period (90 days by default), then deleted; anonymous daily counts.
- Not kept: images, names, identity numbers, IP addresses in logs.
- The website receives only a signed statement for its age line, its own reference, and the outcome — never an age estimate, an image, or an identity.

## 6. Security

Signed tokens (Ed25519) with keys sealed under a master key; tenant isolation by database row-level security; hash-chained audit log; console protected by Argon2id passwords, one-time codes and CSRF defences; published API contract tested automatically. See the threat model (`docs/security/threat-model.md`).

## 7. Accessibility and acceptability

The verify page gives plain-language guidance, works with keyboard and screen readers, avoids rapid flashing, offers a calm mode for people sensitive to motion, and always offers another method.

## 8. Contact and complaints

_(to be completed: operator name, contact for data-protection requests and complaints, supervisory authority)_
