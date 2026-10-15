# ADR-0003: Waterfall — multi-frame facial estimation first, step-up when unsure

- **Status:** Accepted — 2026-10-15

## Context
Facial age estimation is fast, needs no documents and can reveal nothing but a predicate, but it is uncertain near legal thresholds. Australia's Age Assurance Technology Trial found estimation highly accurate *outside buffer zones* and recommended a layered model. Ofcom expects a challenge age well above the legal age.

## Decision
1. The primary method is **multi-frame facial age estimation**: about 8 frames over 2–4 seconds, quality-weighted.
2. When the estimate cannot confidently clear or fail the policy's gate, the outcome is **`step_up`**: the user may complete a stronger verifier ([ADR-0016](0016-step-up-mrz-then-aadhaar.md)).
3. Single photos, voice, hand images and behavioural inference are not used as primary signals.

## Consequences
- **Good:** most adults finish in seconds without documents; young-looking adults have a fair path; minors near the threshold are routed to strong checks.
- **Cost:** step-up flows to build and maintain; the step-up rate becomes a key UX metric.

## Alternatives considered
- Document-first verification — accurate, but invasive and high-friction for everyone.
- Single-photo estimation — no averaging, and no liveness evidence.
- Voice / behaviour / email-history inference — weaker accuracy, profiling concerns (DPDP bans profiling children), or third-party data needs.
