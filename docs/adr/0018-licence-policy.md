# ADR-0018: Licence policy — only permissive components in the runtime path

- **Status:** Accepted — 2026-10-15

## Context
Popular face components carry restrictive licences: YOLOv8 is AGPL-3.0, InsightFace weights are non-commercial, and many datasets are research-only. A deployable product must know exactly what it is allowed to do.

## Decision
- **Runtime path** (images that serve users): only permissive licences — MIT, BSD, Apache-2.0, ISC, PSF, MPL-2.0 for unmodified libraries. No AGPL or GPL services linked in-process; no non-commercial model weights.
- **Licence register:**
    - `ml/datasets.yaml` for datasets;
    - model manifests for weights (including the data lineage);
    - SBOMs for packages, generated in CI.
- **Our own trained weights** inherit dataset restrictions. v1 weights are labelled *research/demonstration*. Commercial deployment requires retraining on licensed data, which needs no code change ([ADR-0014](0014-onnx-serving-registry-and-gates.md)).
- **Benchmark-only components** (e.g. MiVOLO, InsightFace) may be used offline for comparison, never shipped.
- Third-party model licences (MiniFASNet, SFace, …) are **verified from upstream** before first use and recorded.

## Consequences
- **Good:** no licence surprises; an honest statement of what the system may be used for.
- **Cost:** some best-in-class components are excluded; verification effort per new component.

## Alternatives considered
Ignoring licences for a student project — rejected, because the project is meant to be deployable and teachable, and licence literacy is part of what it teaches.

## Update — 1 Nov 2026

The project owner chose the **Apache License 2.0** for the repository's own code ([LICENSE](../../LICENSE)), when the repository was made public. Trained model weights still inherit the terms of their training data, as above.
