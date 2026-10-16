# Architecture Decision Records

An ADR records one significant decision. Each file gives the decision, its context, the alternatives that were rejected and the consequences we accept. Records are **immutable once accepted**: a changed decision gets a *new* ADR that supersedes the old one, so the history of our reasoning is never rewritten.

Format: a lightweight version of [MADR](https://adr.github.io/madr/). Status values: `Proposed`, `Accepted`, `Superseded by ADR-NNNN`, `Deprecated`.

| ADR | Decision | Status |
| :-- | :-- | :-- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions as ADRs | Accepted |
| [0002](0002-hosted-age-assurance-platform.md) | Build a hosted B2B age-assurance platform (not a client-side gate) | Accepted |
| [0003](0003-waterfall-face-estimation-then-step-up.md) | Waterfall: multi-frame facial estimation first, step-up when unsure | Accepted |
| [0004](0004-client-guides-server-decides.md) | The client guides, the server decides | Accepted |
| [0005](0005-own-distributional-age-model.md) | Train our own age model that outputs a full age distribution | Accepted |
| [0006](0006-risk-controlled-three-outcome-gate.md) | Risk-controlled thresholds and a three-outcome gate | Accepted |
| [0007](0007-layered-liveness.md) | Layered liveness incl. randomised pose and screen-light challenges | Accepted |
| [0008](0008-signed-age-tokens.md) | EdDSA-signed minimal age tokens, JWKS, HMAC-signed webhooks | Accepted |
| [0009](0009-modular-monolith-plus-inference-service.md) | Modular-monolith API + separate inference service + worker | Accepted |
| [0010](0010-python-fastapi-backend.md) | Python 3.13 + FastAPI + SQLAlchemy 2 for the backend | Accepted |
| [0011](0011-postgresql-rls-and-valkey.md) | PostgreSQL 18 with row-level security; Valkey for ephemeral state | Accepted |
| [0012](0012-nextjs-frontend-monorepo.md) | Next.js 16 + Tailwind 4 + shadcn/ui; pnpm + Turborepo monorepo | Accepted |
| [0013](0013-no-biometric-storage.md) | No biometric storage: memory-only processing, read-only FS, tmpfs | Accepted |
| [0014](0014-onnx-serving-registry-and-gates.md) | ONNX Runtime serving; model registry with manifests and release gates | Accepted |
| [0015](0015-single-vm-compose-deployment.md) | Deploy on a single VM with Docker Compose and Caddy; Helm chart as artefact | Accepted |
| [0016](0016-step-up-mrz-then-aadhaar.md) | Step-up verifiers: ID-document MRZ first, Aadhaar Secure QR second | Accepted |
| [0017](0017-generated-zero-to-hero-book.md) | Living documentation: a generated Zero-to-Hero book with fingerprinted walkthroughs | Accepted |
| [0018](0018-licence-policy.md) | Licence policy: only permissive components in the runtime path | Accepted |
| [0019](0019-fully-specified-ed25519-alg.md) | Sign age tokens with the fully-specified JOSE algorithm `Ed25519` (RFC 9864) — refines 0008 | Accepted |
| [0020](0020-boolean-age-over-claims.md) | State the age result as a boolean claim named after its age, `age_over_18: true` — refines 0008 | Accepted |
