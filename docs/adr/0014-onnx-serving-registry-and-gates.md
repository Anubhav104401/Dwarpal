# ADR-0014: ONNX Runtime serving; model registry with manifests and release gates

- **Status:** Accepted — 2026-10-15

## Context
Models will be retrained, replaced (e.g. by a model trained on licensed data) and quantised. A model change is a behaviour change for a safety gate and must be reviewed like code. Serving must be fast on CPU and independent of the training framework.

## Decision
- Export to **ONNX** and serve with **ONNX Runtime**: CPU by default, CUDA where available. INT8 quantisation is used only when the gates still pass.
- **Registry:** `models/registry/<name>/<version>/manifest.json` records:
    - file hashes and the input specification;
    - temperature, risk-control thresholds per (N, ε) and metrics;
    - datasets with their licences, and the training commit.

  The manifest is committed; weights are fetched by a hash-verified script.
- **Release gates** in CI (`ml/gates.yaml`): FAR-minor upper bound, fairness gap, adult pass rate, latency and ONNX parity. A failing gate blocks promotion.
- **Shadow mode:** new versions score traffic (aggregate statistics only) before taking over. Instant rollback.
- Every release ships an auto-generated **model card**.

## Consequences
- **Good:** framework-independent fast serving; reproducible, auditable model changes; safe upgrades.
- **Cost:** export and parity work; manifest discipline.

## Alternatives considered
Serving PyTorch directly (heavier images, slower CPU inference), Triton/BentoML/Ray Serve (more infrastructure than one model family needs), weights in git or LFS (bloat; licence-sensitive weights shouldn't sit in public repositories).
