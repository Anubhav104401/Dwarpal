# Dwarpal — privacy-first AI age assurance

> *द्वारपाल — the guardian at the door, who decides who may enter.*

Dwarpal lets any website ask **"is this live person over N?"** and get back a **cryptographically signed yes/no**.

- It estimates age from a few seconds of camera video.
- It checks that a real, live person is present — not a photo, a screen, a mask or a video-game character.
- When it is unsure, it asks for a stronger check (an ID document, or India's Aadhaar Secure QR).
- **It never stores a face**, and the website never learns the user's identity or estimated age.

> **Status:** Phase 0 (foundations) of the [roadmap](docs/design/05_roadmap.md). Nothing is deployed yet.

## Why it exists

Laws now require real age checks for age-restricted content: the UK Online Safety Act, the EU DSA, US state laws, Australia's under-16 social-media law, and India's DPDP Rules. "Are you 18? Yes/No" doesn't work, and freely available age models let far too many minors through. Dwarpal is engineered around the number that matters — **how many minors near the threshold get through** — with a statistically calculated safety margin, layered liveness checks and a no-storage privacy architecture.

Read the reasoning: [problem analysis](docs/design/01_problem_analysis.md) · [solution options](docs/design/02_solution_options.md) · [implementation design](docs/design/03_implementation_design.md) · [architecture](docs/design/04_architecture.md) · [roadmap](docs/design/05_roadmap.md) · [decision records](docs/adr/README.md).

**Learn everything from zero:** open [`docs/zero_to_hero/zero_to_hero.html`](docs/zero_to_hero/zero_to_hero.html) in a browser. It is a single book that explains every line of code in this repository, for someone who has never programmed.

## Quick start (development)

Prerequisites:

- [uv](https://docs.astral.sh/uv/) 0.13+ — it installs the right Python (3.13) by itself;
- Node.js 24 LTS with [pnpm](https://pnpm.io/) 12;
- Docker with Compose.

```bash
uv sync                                                    # Python 3.13 + every Python tool, from uv.lock
pnpm install                                               # JavaScript tools, from pnpm-lock.yaml
docker compose -f infra/compose/compose.yaml up -d --wait  # PostgreSQL 18 + Valkey 9, healthy
uv run tasks.py check                                      # lint, types, tests, and the book in strict mode
pnpm lint                                                  # JavaScript/JSON lint and formatting check
```

## Repository map

| Path | What lives there |
| :-- | :-- |
| `apps/` | Next.js apps — website + verify flow + console, and the demo shop (from Phase 1) |
| `packages/` | TypeScript packages — design system, capture, SDKs, shared config |
| `services/api` | FastAPI modular monolith — RP/flow/console APIs, decision engine, tokens |
| `services/inference` | FastAPI + ONNX Runtime — the face pipeline (in memory only) |
| `libs/` | Python code shared by services and ML (`contracts`, `vision`) |
| `ml/` | Datasets, training, evaluation, risk control, export, model cards |
| `infra/` | Docker Compose, Caddy, observability, Helm, scripts |
| `docs/` | Design documents, ADRs, the Zero-to-Hero book |

## Privacy promise (enforced by architecture, not just policy)

Frames are processed in memory and discarded within the request. There is no table, file, bucket or log where a face could be stored, and the services that touch faces run on read-only filesystems with no outbound network. See [ADR-0013](docs/adr/0013-no-biometric-storage.md).

## Licence

Not yet chosen by the project owner. Until a licence file is added, all rights are reserved. Note that any trained model weights inherit the terms of their training datasets, which are largely research-only (see [ADR-0018](docs/adr/0018-licence-policy.md)).
