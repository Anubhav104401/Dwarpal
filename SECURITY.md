# Security policy

Dwarpal handles biometric data in transit and issues signed age attestations, so security reports are taken seriously.

## Reporting a vulnerability

Please **do not open a public issue**. Report it privately through the repository's *Security → Report a vulnerability* page (GitHub private vulnerability reporting) once the repository is published. Include steps to reproduce and the impact you expect.

## Security invariants (any violation is a vulnerability)

1. No camera frame, face crop, face embedding, document image or Aadhaar payload is ever persisted, logged or traced.
2. No error path, timeout or missing signal can produce a `pass` outcome (fail closed).
3. A relying party can never read another relying party's data (enforced by application checks **and** PostgreSQL row-level security).
4. Age tokens are verifiable only with Dwarpal's published keys. Private signing keys are encrypted at rest and never leave the API.
5. Webhook deliveries never target private, loopback or link-local network addresses.

## Supported versions

Pre-release: only the `main` branch is supported.
