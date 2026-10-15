# ADR-0017: Living documentation — a generated Zero-to-Hero book with fingerprinted walkthroughs

- **Status:** Accepted — 2026-10-15

## Context
The owner requires a single HTML book, in `docs/zero_to_hero/`, that explains every line of code to an absolute beginner, grown alongside development. Hand-maintained HTML would be unwieldy, would drift from the code, and "every line" would be unverifiable.

## Decision
- Chapters are Markdown; each source file has a **walkthrough**: notes keyed to line ranges, plus a header recording the file's **SHA-256 fingerprint** (first 16 hex digits).
- `docs/zero_to_hero/build.py` compiles everything into one self-contained HTML file (inline CSS/JS, no external requests). It:
    - computes **line coverage** per file;
    - flags **stale** explanations when the fingerprint changes;
    - scans the repository for unexplained files;
    - emits a **coverage ledger**.
- `build.py --strict` runs in CI and fails on any unexplained, stale or missing walkthrough. Lockfiles and the generated book are excluded by policy.
- All files are read and written as UTF-8, with normalised line endings.

## Consequences
- **Good:** "every line explained" is mechanically verifiable; explanations live next to their code's history; the book can't silently fall behind.
- **Cost:** every code change requires a walkthrough update. Line-anchored notes need re-anchoring after edits; a `--reanchor` helper based on diffs against a stored snapshot is planned to reduce this cost.

## Alternatives considered
Hand-written HTML (unmaintainable), auto-generated API docs only (no beginner explanations, no "why"), literate programming (forces the code's structure to follow the prose).
