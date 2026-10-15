# ADR-0006: Risk-controlled thresholds and a three-outcome gate

- **Status:** Accepted — 2026-10-15

## Context
Hand-picked buffers ("pass if estimate ≥ 25") are the industry baseline (NIST Challenge-T), but the number is arbitrary and says nothing about the actual rate of minors passing for a given model. The safety requirement is stated as a rate (NFR-01: FAR-minor ≤ 2 % target, ≤ 5 % gate).

## Decision
- Every policy states a **risk budget** ε at confidence 1 − δ (default δ = 0.05).
- For each threshold age N, offline calibration chooses τ_pass(N, ε): the smallest threshold on `P(age ≥ N)` such that the **one-sided Clopper–Pearson upper bound** of the pass rate is ≤ ε **for every exact age in N−5…N−1 and every labelled demographic group**, taking the most conservative.
- τ_fail(N) is chosen so adults aged N+3 and over are almost never hard-failed.
- Outcomes:
    - `pass` if p ≥ τ_eff;
    - `fail` if p ≤ τ_fail;
    - otherwise `step_up`;
    - plus `retry` (quality or integrity) and `reject` (suspected attack).
- τ_eff rises with each retry. Any missing or invalid input can never produce `pass` (**fail closed**).

## Consequences
- **Good:** a statistical, auditable statement — *"with 95 % confidence, at most ε of 13–17-year-olds in the calibration distribution pass"*; safety stays fixed when the model is weaker, and the cost shows up as more step-ups.
- **Cost / caveat:** the guarantee holds for the calibration distribution (dataset photos), not automatically for webcams. This is mitigated by quality gating, webcam-style augmentation, an extra margin and drift monitoring, and is stated in the model card. Cells with few samples force stricter thresholds.

## Alternatives considered
Point-estimate threshold (unsafe), fixed Challenge-25 (arbitrary, kept as a baseline for comparison), conformal prediction intervals (considered; the per-age risk-control bound targets our exact safety metric more directly).
