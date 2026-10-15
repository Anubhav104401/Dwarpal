# ADR-0002: Build a hosted B2B age-assurance platform

- **Status:** Accepted — 2026-10-15 (owner confirmed scope: platform + console + demo shop)

## Context
The problem statement asks for an AI system that protects minors from age-restricted online content. The gate sits on someone else's website (the *relying party*), whose operator carries the legal duty: UK OSA, EU DSA Art. 28, US state laws, Australia's SMMA and India's DPDP Rules. Regulators audit the *service* that performs the checks — its accuracy, robustness, fairness and privacy. See [Stage 1 §3](../design/01_problem_analysis.md).

## Decision
Build Dwarpal as a **hosted service**:

- the RP creates a verification session over an authenticated API;
- the user completes a hosted flow;
- the RP receives a **signed** result.

Ship it with:

- a multi-tenant **console** (keys, policies, webhooks, analytics, audit);
- JS/React/Node **SDKs**;
- a fictional **demo shop** that integrates it end to end.

## Consequences
- **Good:** the decision can't be forged by the user; one place to measure and improve accuracy and fairness; matches how the industry (Yoti, Persona, Stripe Identity, k-ID) and regulators operate.
- **Cost:** we operate servers and handle biometric data in transit, which requires the strict privacy architecture in [ADR-0013](0013-no-biometric-storage.md).

## Alternatives considered
- **Client-side gate widget** — forgeable by editing the page's JavaScript.
- **Parental-control browser extension** — owner placed it out of scope for v1; it can reuse the models later.
- **Content classifier** — a different problem (content moderation).
