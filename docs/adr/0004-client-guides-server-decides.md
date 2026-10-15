# ADR-0004: The client guides, the server decides

- **Status:** Accepted — 2026-10-15

## Context
Running models in the browser maximises privacy, but browsers offer no hardware attestation for web pages, so any client-computed result can be forged. Running only on the server gives users no live feedback, which means more bad captures and more retries.

## Decision
- The browser runs **MediaPipe Face Landmarker** only for *guidance*: framing, lighting, head-pose tracking for challenge prompts. It also gathers client signals.
- The **server** independently re-derives everything from the raw frames — detection, pose, quality, liveness and age — and alone decides.
- Client signals are inputs to fusion, **never trusted on their own**.

## Consequences
- **Good:** forgery-resistant decisions with a smooth UX; fewer wasted attempts.
- **Cost:** frames must travel to the server (TLS; memory-only processing per [ADR-0013](0013-no-biometric-storage.md)); MediaPipe WASM (~ several MB) loads on the verify route only.

## Alternatives considered
- Client-only inference — forgeable.
- Server-only inference — poor UX and higher retry rates.
- Server-side streaming over WebRTC/WebSocket for real-time server guidance — far more complex for little gain over client-side guidance.
