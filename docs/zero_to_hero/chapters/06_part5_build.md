# Part 5 — Building it, file by file

This is the main event: every file of the project, in the order it was built, explained line by line. Each phase of the roadmap adds a chapter here.

## 5.0 Phase 0 — the foundations

Phase 0 builds no features. It builds the **workshop**: the folder structure, the toolchains, the quality robots, the local databases and the automatic checks. Every later phase depends on them.

Here is the repository at the end of Phase 0 (design documents, ADRs, chapters and walkthroughs left out for brevity):

```
.
├── .editorconfig              editor settings everyone shares
├── .gitattributes             line endings + binary files, for Git
├── .gitignore                 what Git must never see
├── .python-version            "use Python 3.13"
├── .github/workflows/ci.yml   continuous integration
├── pyproject.toml             Python workspace + tool settings
├── uv.lock                    exact Python library versions (generated)
├── tasks.py                   one command for every check
├── package.json               JavaScript workspace root
├── pnpm-workspace.yaml        where JavaScript packages live
├── pnpm-lock.yaml             exact JavaScript library versions (generated)
├── turbo.json                 task pipeline for JavaScript packages
├── biome.json                 JavaScript/JSON formatter + linter settings
├── README.md  CONTRIBUTING.md  SECURITY.md
├── infra/compose/
│   ├── compose.yaml           PostgreSQL 18 + Valkey 9 for development
│   └── .env.example           the settings you may override
├── packages/config/
│   ├── package.json           @dwarpal/config
│   └── tsconfig.base.json     shared TypeScript rules
├── services/
│   ├── api/                   pyproject.toml + src/dwarpal_api/__init__.py
│   └── inference/             pyproject.toml + src/dwarpal_inference/__init__.py
├── libs/
│   ├── contracts/             pyproject.toml + src/dwarpal_contracts/__init__.py
│   └── vision/                pyproject.toml + src/dwarpal_vision/__init__.py
├── ml/                        pyproject.toml + src/dwarpal_ml/__init__.py
└── docs/
    ├── design/  adr/          Stages 1–5 and the 18 decision records
    └── zero_to_hero/          this book: build.py, template.html, book.toml, tests/, chapters/, walkthroughs/
```

!!! kid "Explain like I'm six"
    Before a new school opens, someone builds the classrooms, puts up the signs, installs the fire alarms and writes the timetable. No lessons happen yet — but without that work, no lesson could happen safely. Phase 0 is the school before the first day.

### 5.0.1 Repository hygiene

Three tiny files make sure every computer and every editor treats the project the same way.

!walk .editorconfig

!walk .gitattributes

!walk .gitignore

### 5.0.2 The Python workspace

!walk .python-version

!walk pyproject.toml

The five packages start as **skeletons**: each has a `pyproject.toml` that names it, and an `__init__.py` that marks the folder as a package and describes its purpose. Real code arrives in Phase 1. Creating them now fixes the shape of the project, and proves that the workspace, the lockfile and the tools all work with five members.

!walk services/api/pyproject.toml

!walk services/api/src/dwarpal_api/__init__.py

!walk services/inference/pyproject.toml

!walk services/inference/src/dwarpal_inference/__init__.py

!walk libs/contracts/pyproject.toml

!walk libs/contracts/src/dwarpal_contracts/__init__.py

!walk libs/vision/pyproject.toml

!walk libs/vision/src/dwarpal_vision/__init__.py

!walk ml/pyproject.toml

!walk ml/src/dwarpal_ml/__init__.py

### 5.0.3 One command for every check

!walk tasks.py

### 5.0.4 The JavaScript workspace

!walk package.json

!walk pnpm-workspace.yaml

!walk turbo.json

!walk biome.json

!walk packages/config/package.json

!walk packages/config/tsconfig.base.json

### 5.0.5 Local infrastructure

!walk infra/compose/compose.yaml

!walk infra/compose/.env.example

### 5.0.6 Continuous integration

!walk .github/workflows/ci.yml

### 5.0.7 Tests for the book builder

!walk docs/zero_to_hero/tests/test_build.py

### 5.0.8 Phase 0 — what was measured

| Check | Result |
| :-- | :-- |
| `uv sync` | 21 packages resolved and installed (Python 3.13.16, uv-managed) |
| `ruff check` + `ruff format --check` | clean |
| `mypy --strict` | no issues in 8 source files |
| `pytest` | 9 passed |
| `pnpm install` / `pnpm lint` (Biome) | 4 packages installed; clean |
| `docker compose up --wait` | PostgreSQL 18.6 and Valkey 9.1.2 healthy; `uuidv7()` available |
| Book, strict | 100 % of lines explained — see the [Coverage ledger](#coverage-ledger) |

The full phase report is in `docs/reports/phase-0.md`.
