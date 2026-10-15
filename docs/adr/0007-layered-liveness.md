# ADR-0007: Layered liveness including randomised pose and screen-light challenges

- **Status:** Accepted — 2026-10-15

## Context
In July 2025 users passed Discord's UK age check with video-game characters; a predictable "open your mouth" step was defeated by a game's photo mode. Attack classes: print, screen replay, masks and make-up, CGI/3D renders, virtual-camera injection, payload replay, proxies and trial-and-error ([Stage 1 §5.6](../design/01_problem_analysis.md)).

## Decision
Fuse independent layers into one liveness risk score:

| Layer | Signal |
| :-- | :-- |
| L1 | Capture quality gate |
| L2 | Passive PAD (MiniFASNet ensemble, Apache-2.0) |
| L3 | **Randomised head-pose challenge**, server-issued with a one-time nonce and verified server-side from the frames |
| L4 | **Screen-light reflection challenge** — a random, seizure-safe colour sequence whose reflection on skin must correlate in time (a soft signal) |
| L5 | Injection heuristics (virtual-camera labels, automation flags, timing/encoding anomalies) |
| L6 | *(stretch)* CGI-render detector |
| L7 | *(deferred)* deepfake detector slot |

Retry limits and per-device budgets stop trial-and-error. The UI never reveals which signal fired.

## Consequences
- **Good:** defeats static and pre-recorded media and raises the cost of real-time rendering attacks; no single point of failure.
- **Cost:** more client and server code; the light signal is weak in bright ambient light (treated as soft); accessibility constraints on light patterns (WCAG 2.3.1).
- Proxy attacks (an adult doing the check) remain a residual risk acknowledged by regulators.

## Alternatives considered
Single passive PAD model (brittle), blink/smile challenges only (proven bypassable), commercial liveness SDKs (outsourced biometrics, cost), deepfake detectors now (poor generalisation).
