# ADR-0009: Modular-monolith API + separate inference service + worker

- **Status:** Accepted — 2026-10-15

## Context
One developer must build and operate the system. Inference is CPU-heavy and handles biometrics; the business API is I/O-bound and handles tenant data. They scale differently and carry different risk.

## Decision
Three deployables:

- **api** — a FastAPI *modular monolith* with hexagonal layering: pure domain ← services ← adapters;
- **inference** — a stateless FastAPI + ONNX Runtime service, reachable only on an internal network;
- **worker** — the api image run with the `arq` command, for webhooks, expiry, retention and rotation.

Modules talk in-process inside the API; the API talks to inference over internal HTTP using shared Pydantic contracts (`libs/contracts`).

## Consequences
- **Good:** independent scaling of inference; a small, auditable biometric perimeter; simple transactions in one database; a fast pure-domain test suite.
- **Cost:** two services to version together (mitigated by the monorepo and shared contracts); internal network hop latency of about 1–3 ms.

## Alternatives considered
A single process for everything (inference starves the API; mixed risk), full microservices (operational overhead, distributed transactions), event-driven Kafka backbone (heavy infrastructure for our load — Valkey jobs plus an outbox suffice).
