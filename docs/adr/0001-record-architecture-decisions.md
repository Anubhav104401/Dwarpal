# ADR-0001: Record architecture decisions

- **Status:** Accepted — 2026-10-15
- **Deciders:** project owner; engineering (Claude)

## Context
Dwarpal is designed and built over many sessions, and must be defended in front of reviewers. Decisions made in conversation are lost; decisions buried in code comments get rewritten without anyone noticing. The Zero-to-Hero book explains *what the code does*. We also need a durable, reviewable record of *why the architecture is the way it is*.

## Decision
Every decision that is significant — expensive to reverse, cross-cutting, or likely to be questioned — gets an ADR in `docs/adr/NNNN-title.md`, using a lightweight MADR format:

- context
- decision
- consequences
- alternatives
- links

Accepted ADRs are never edited in substance. A change of mind produces a new ADR marked `Supersedes ADR-NNNN`.

## Consequences
- **Good:** reasoning survives; onboarding is faster; reviewers can audit choices; the book links to ADRs instead of repeating them.
- **Cost:** a few minutes per decision; discipline needed to write the ADR *before* or *while* implementing, not after.

## Alternatives considered
- A wiki page of decisions — drifts from the code and lives outside version control.
- Only the design documents — too long to scan, and they mix exploration with decisions.
