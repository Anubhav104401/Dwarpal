# ADR-0015: Deploy on a single VM with Docker Compose and Caddy; Helm chart as artefact

- **Status:** Accepted — 2026-10-15 (owner decision)

## Context
The system must be really deployed (public HTTPS) at modest cost, and operable by one person. Enterprise readers expect a Kubernetes path.

## Decision
- **Production target:** one Linux VM (Ubuntu 24.04 LTS, 4 vCPU / 8–16 GB). Oracle Always-Free ARM if capacity allows, otherwise a small Hetzner or similar instance.
- **Runtime:** Docker Engine + Compose, with **Caddy** for automatic TLS and routing.
- **Isolation:** separate Docker networks per trust zone; the inference and data networks are internal-only.
- **Build and deploy:**
    - images are built multi-arch in GitHub Actions, scanned, and pushed to GHCR;
    - deploys run over SSH with health-gated `up --wait` and a migration one-off;
    - nightly encrypted off-site backups, with a documented restore drill.
- **Kubernetes:** a **Helm chart** (`infra/helm/dwarpal`) mirroring the same topology, with probes, HPA and NetworkPolicies. It is linted in CI and deployed only if the target changes.

## Consequences
- **Good:** cheap, simple, real; the same containers run locally and in production; a clear upgrade path to Kubernetes.
- **Cost:** a single point of failure (the VM). Mitigated by backups and a fast rebuild script; acceptable for the demonstration SLO.

## Alternatives considered
Free-tier PaaS mix (cold starts, memory limits, vendor sprawl); Kubernetes now (operational cost); local-only (not deployable).
