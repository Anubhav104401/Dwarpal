# Phase 0 report — Foundations

**Dates:** 15 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** ✅ complete; CI green on GitHub since 2 Nov (`03f3f5b`)

## What was built

| Area | Delivered |
| :-- | :-- |
| Version control | `git init -b main`; `.gitignore`, `.gitattributes` (LF everywhere, binary types), `.editorconfig`. Nothing committed yet — awaiting the owner's go-ahead |
| Python | uv 0.13.1 (per-user install); uv-managed **Python 3.13.16**; uv workspace with five skeleton packages (`dwarpal-api`, `dwarpal-inference`, `dwarpal-contracts`, `dwarpal-vision`, `dwarpal-ml`); `dev` and `docs` dependency groups, every version pinned; `uv.lock` |
| Quality gates | Ruff (lint + format, 15 rule families), mypy `--strict`, pytest; `tasks.py` with `check / lint / format / typecheck / test / book` |
| JavaScript | pnpm 12.11.2 workspace (`apps/*`, `packages/*`); Turborepo 2.11.8; Biome 2.5.15; `@dwarpal/config` with the shared strict `tsconfig` |
| Infrastructure | `infra/compose/compose.yaml`: PostgreSQL 18.6 + Valkey 9.1.2, health-checked, bound to localhost; `.env.example` |
| CI | `.github/workflows/ci.yml`: Python, JavaScript and Compose jobs; least-privilege permissions; pinned action versions |
| Repository docs | `README.md`, `CONTRIBUTING.md` (Definition of Done, book workflow), `SECURITY.md` (security invariants) |
| Book tooling | Builder moved into the workspace; type-hinted and lint-clean; pure, tested helper functions; **snapshots + `--reanchor`**; 9 unit tests |
| Book content | Part 4 (tools of Phase 0); Part 5.0 (every Phase 0 file walked through); Part X updated |

## What was measured

| Check | Result |
| :-- | :-- |
| `uv run tasks.py check` | lint ✅ · format ✅ · mypy strict ✅ (8 files) · pytest ✅ (9 passed) · book strict ✅ |
| Book coverage | **29 files, 994/994 non-blank lines explained (100 %)**; 46,909 words |
| `pnpm install` + `pnpm lint` | ✅ (Biome clean) |
| `docker compose up --wait` | PostgreSQL 18.6 and Valkey 9.1.2 **healthy**; `SELECT uuidv7()` works |
| `--reanchor` in practice | after editing `.gitignore` and `book.toml`: notes on unchanged lines moved automatically; the edited note was flagged `TODO(review)`; coverage correctly dropped to 989/994 until reviewed |

## What changed from the plan, and why

1. **`requirements.txt` removed.** Its two pins moved into the root `pyproject.toml` `docs` group, so there is one source of truth for versions.
2. **`--reanchor` built now instead of later.** Manual renumbering after two small CSS edits proved too error-prone. Snapshots are stored with a `.snap` suffix, so that copies of `.gitignore` and `pyproject.toml` stay inert.
3. **Ruff limited to Python files.** Ruff 0.17 also formats code blocks inside Markdown; it silently edited an example in a design document. Teaching examples must stay verbatim.
4. **Biome configuration migrated** (`recommended: true` → `preset: "recommended"`) after Biome 2.5 reported a deprecation.
5. **Two Git hazards fixed before they bit**, both found while *writing explanations*: the `.env.*` pattern would have hidden the walkthrough `.env.example.md`, and un-suffixed snapshots would have acted as real configuration files.
6. **TypeScript 7 decision deferred to Phase 1.** It became npm's default in 2026. Compatibility with Next.js 16.4 will be tested when the first TypeScript code exists.

## Known limitations

- **CI has never run remotely**, because the repository isn't on GitHub yet. The workflow is valid, and its commands pass locally.
- **uv is not on PATH.** It was installed per-user via pip, at `%APPDATA%\Python\Python314\Scripts\uv.exe`. Either add that folder to PATH, or install uv with its official installer.
- **Docker Desktop must be running** for the Compose step. It was started manually for this phase.
- `.claude/launch.json` (a local preview server for the book) is intentionally untracked.

## Next: Phase 1 — walking skeleton

The demo shop creates a session, the hosted flow captures frames, the API calls the inference service (stub model + real face detection), the decision engine decides, and a signed token is verified by the demo shop — with a Playwright end-to-end test using a fake camera.
