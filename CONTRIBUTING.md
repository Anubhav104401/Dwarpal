# Contributing to Dwarpal

## Definition of Done

A change is done only when **all** of these hold. They are copied from the [roadmap](docs/design/05_roadmap.md).

1. Formatted and lint-clean (`uv run tasks.py lint`, `pnpm lint`); strictly type-checked (`uv run tasks.py typecheck`, `pnpm typecheck`).
2. Tested at the right layer (`uv run tasks.py test`, `pnpm test`). Domain rules have property-based tests where invariants exist.
3. No secrets, camera frames or personal data in code, logs, fixtures or tests.
4. **Explained in the Zero-to-Hero book.** Every changed source file has an up-to-date walkthrough, and `uv run tasks.py book` passes at 100 %.
5. Significant decisions have an ADR in `docs/adr/`; design documents are updated if a design changed.
6. CI is green.

`uv run tasks.py check` runs everything the Python CI job runs.

## Keeping the book in step with the code

Walkthroughs live in `docs/zero_to_hero/walkthroughs/`, mirroring the repository. The builder lives at `docs/zero_to_hero/build.py`.

| Situation | Command |
| :-- | :-- |
| New source file | `uv run docs/zero_to_hero/build.py --new path/to/file` creates a skeleton with a `TODO` per line; replace each `TODO` with an explanation |
| Edited source file | `uv run docs/zero_to_hero/build.py --reanchor path/to/file` moves notes to follow the edit and marks notes on changed code `TODO(review)` |
| Explanations reviewed and correct | `uv run docs/zero_to_hero/build.py --stamp path/to/file` records the new fingerprint and snapshot |

## Commits

- Small, focused commits.
- Messages are written in the imperative ("Add risk-control thresholds to manifest").
- The body explains *why*.
- Never commit `.env` files, datasets, model weights or anything containing a face.
