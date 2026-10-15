# ADR-0005: Train our own age model that outputs a full age distribution

- **Status:** Accepted — 2026-10-15

## Context
A February 2026 benchmark of 34 models (arXiv 2602.07815) found most open specialist models classified 39–100 % of minors as adults at the 18 threshold. Zero-shot VLMs did so 16–29 % of the time, and would send faces to third parties. Commercial APIs mean outsourcing biometrics. The strongest open specialist (MiVOLO) reports about 4.2 years MAE face-only, but is not trained for gate safety.

## Decision
- Fine-tune our own model from strong pre-trained backbones (ConvNeXt-V2, face-pretrained ViT, DINOv2 — chosen by experiment).
- The model outputs a **probability distribution over ages 0–100**, using label-distribution learning (KL loss) plus an L1 term on the expected age.
- An optional **safety-weighted term** penalises probability mass above N for training samples just below N.
- Temperature-scale the outputs for calibration.
- MiVOLO and off-the-shelf models are kept as **benchmarks to beat**, never in the runtime path.

## Consequences
- **Good:** one model serves every policy age (13/16/18/21) via `P(age ≥ N)`; uncertainty is explicit; we control data, evaluation and licensing.
- **Cost:** training infrastructure and data work. Public datasets are mostly research-only, so **v1 weights are for research/demonstration**; commercial use requires licensed data ([ADR-0018](0018-licence-policy.md)).

## Alternatives considered
Off-the-shelf libraries (unsafe for gates), cloud APIs (privacy, cost, lock-in), VLM prompting (privacy, latency, cost, accuracy on minors), direct use of MiVOLO checkpoints (not gate-trained; detector licence issues).
