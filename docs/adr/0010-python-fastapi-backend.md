# ADR-0010: Python 3.13 + FastAPI + SQLAlchemy 2 for the backend

- **Status:** Accepted — 2026-10-15

## Context
The ML ecosystem (PyTorch, ONNX Runtime, OpenCV, MediaPipe) is Python-first. Throughput is bound by inference, not by HTTP framework overhead. The project must be teachable line by line.

## Decision
- **Python 3.13**, managed per project by **uv** (independent of the machine's Python 3.14, which parts of the ML stack still lag).
- **FastAPI** + Pydantic v2 (typed request/response models, automatic OpenAPI 3.1); **Uvicorn** server.
- **SQLAlchemy 2** async ORM on **asyncpg**; **Alembic** migrations.
- **arq** for background jobs.
- **structlog** for JSON logs; **OpenTelemetry** for traces and metrics.
- Quality tooling: **ruff** (lint + format), **mypy --strict**, **pytest** (+ Hypothesis, Testcontainers, Schemathesis).

## Consequences
- **Good:** one backend language shared with ML; strong typing at boundaries; huge ecosystem; first-class async.
- **Cost:** Python's per-request CPU overhead is higher than Go or Rust (irrelevant next to model inference); the GIL is mitigated because heavy work runs in native libraries and thread pools.

## Alternatives considered
Go or Rust API with a Python inference service (two backend languages to teach and maintain), Node.js/NestJS (splits ML from API), Django (heavier and sync-first), Litestar (good, smaller ecosystem).
