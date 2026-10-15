# ADR-0013: No biometric storage — memory-only processing, read-only filesystem, tmpfs

- **Status:** Accepted — 2026-10-15

## Context
Faces of minors are among the most sensitive data that exists. Regulators (the Ofcom/ICO joint statement of March 2026; GDPR data minimisation; DPDP) expect minimisation. A breach of stored faces would be catastrophic, and *"you can't leak what you never kept"*.

## Decision
- No table, bucket, cache, log or trace may contain frames, crops, embeddings, document images or QR payloads.
- Upload parts are capped below the framework's spool-to-disk threshold, so they are never written to temporary files.
- API and inference containers run with a **read-only root filesystem** and `/tmp` as **tmpfs**. Core dumps are disabled. The inference network has **no egress**.
- A logging and tracing **redaction processor** with a deny-list, plus a **canary test**: a request carrying a known byte pattern must never appear in captured logs or spans.
- Only scores, reason codes and metadata are persisted (retention 90 days by default); from documents, only year-month of birth and check results.
- Model improvement never uses production images; offline training uses licensed datasets only.

## Consequences
- **Good:** breach impact is minimal; simple, strong privacy story; aligned with regulators' guidance.
- **Cost:** no production images for debugging or retraining — we rely on aggregate statistics, synthetic tests and red-team recordings made with explicit consent by adults on the team.

## Alternatives considered
Encrypted storage of frames "for audits or retraining" (creates the breach surface we promise doesn't exist); opt-in storage (consent from minors is legally fraught).
