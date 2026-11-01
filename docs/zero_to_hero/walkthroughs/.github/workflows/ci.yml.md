---
fingerprint: 0997419412bd0a1b
---
The **continuous-integration workflow** (§4.6). GitHub reads every file in `.github/workflows/`. Whenever this repository receives new code, GitHub starts fresh Linux machines and runs these three jobs on them. If any step fails, the change is marked with a red ✗.

@@ 1
`name: ci` — the workflow's name, shown on GitHub's *Actions* page and next to each commit.

@@ 3
`on:` — **when** the workflow runs.

@@ 4-5
`push:` to the `main` branch — every time new commits land on the main line of history.

@@ 6
`pull_request:` — every time someone proposes a change through a pull request. Problems are therefore found **before** the change is merged, not after.

@@ 8-9
`permissions: contents: read` — the workflow may only **read** the repository. By default GitHub gives workflows more powers, such as writing to the repository. Following the principle of **least privilege**, nothing gets a power it doesn't need. Then even a compromised tool inside the workflow couldn't modify the code.

@@ 11-13
`concurrency:` — if a new commit arrives while an earlier run for the **same branch** is still going (`group: ci-${{ github.ref }}`, where `github.ref` is the branch name), cancel the old run (`cancel-in-progress: true`). Only the newest code matters, so this saves time.

@@ 15
`jobs:` — the work, divided into **jobs** that run at the same time on separate machines.

@@ 16
`python:` — the first job's internal name.

@@ 17
`name:` — the human-readable title shown on GitHub.

@@ 18
`runs-on: ubuntu-24.04` — a fresh virtual machine running Ubuntu Linux 24.04 LTS. It is pinned, rather than "latest", so an Ubuntu upgrade can't suddenly change our results.

@@ 19
`timeout-minutes: 30` — if something hangs, stop after 30 minutes instead of GitHub's default of six hours. (It was 15 until the first run on GitHub, whose machines took longer than that for the whole suite.)

@@ 20
`steps:` — the job's steps, run in order.

@@ 21
`uses: actions/checkout@3d3c…90b1 # v7.0.1` — a published **action** that downloads this repository's code onto the machine. Every job starts from an empty machine, so this always comes first.

The action is pinned to an exact **commit** (the long hexadecimal ID), with its version in a comment. A version *tag* such as `v7.0.1` is a label its owner can move to other code — and a stolen account could move it to malicious code. A commit ID names one exact piece of code forever. Semgrep flagged the tags in Phase 7; every action here is now pinned this way.

@@ 22-25
`astral-sh/setup-uv@1c37…5884 # v10.3.0` — installs **uv** (pinned by commit, as above):

- `version: "0.13.1"` — the same uv version as on the developer's machine;
- `enable-cache: true` — keep downloaded packages between runs, which makes later runs much faster.

@@ 26
`run: uv sync --locked` — install Python 3.13 and every locked package. `--locked` means: **fail** if `uv.lock` doesn't exactly match the `pyproject.toml` files. Someone who changed a dependency but forgot to update the lockfile is told immediately.

@@ 27
`run: uv run infra/scripts/fetch_models.py` — download the third-party model files the tests need (the YuNet face detector, §5.1) and **verify each one's SHA-256 fingerprint** before using it. Model files are never stored in Git (`.gitignore`), so every fresh machine — including CI's — fetches them this way. Added in Phase 1.

@@ 29
`run: uv run tasks.py check` — the same single command developers run locally (§5.0.3): lint, types, tests and the book in strict mode. CI and developers can never disagree about what "passing" means.

@@ 31
`javascript:` — the second job, running at the same time on its own machine.

@@ 32-34
Its title, the same pinned Ubuntu machine, and the same 15-minute limit. Since Phase 1 the job also *builds* everything, hence "builds" in its name.

@@ 35
`steps:` — this job's steps.

@@ 36
Download the code, as in the first job.

@@ 37
`pnpm/action-setup` (pinned by commit) — installs **pnpm**. No version is given here, because the action reads the `packageManager` field of `package.json` (pnpm 12.11.2), so the version lives in one place only.

@@ 38-41
`actions/setup-node` (pinned by commit) — installs **Node.js 24** (the LTS line in `package.json`). `cache: pnpm` keeps pnpm's package store between runs.

@@ 42
`run: pnpm install --frozen-lockfile` — install exactly what `pnpm-lock.yaml` says, and **fail** if the lockfile is out of date. This is the JavaScript twin of `uv sync --locked`.

@@ 43
`run: pnpm lint` — Biome's formatting and lint checks.

@@ 44
`run: pnpm typecheck` — TypeScript checks for every package: the SDK, both web apps and the end-to-end tests (added in Phase 1).

@@ 45
`run: pnpm test` — JavaScript unit tests for every package (Vitest, §4.20).

@@ 46
`run: pnpm build` — build every package with Turborepo: the SDK compiles to plain JavaScript, and both Next.js apps make their production builds. A build that only fails on a clean machine is caught here, not on deployment day.

@@ 48-51
**The end-to-end job** (added in Phase 1): the whole system, in a real browser, exactly as a person would use it — the demo shop, the verify page, the API and the inference service, with a fake camera. It gets 20 minutes, because it installs a browser and builds everything first.

@@ 52-53
Its steps start, like every job, by checking out the code.

@@ 54-57
Install uv, as in the Python job: the API and the inference service are Python programs.

@@ 58-62
Install pnpm and Node.js 24, as in the JavaScript job: the web apps and the test runner are JavaScript programs.

@@ 63
`uv sync --locked` — install the Python side exactly as the lockfile says.

@@ 64
Download the face-detection model, which the inference service needs (§5.1.1).

@@ 65
Install the JavaScript side exactly as its lockfile says.

@@ 66
Download the three browsers Playwright drives — Chromium, Firefox and WebKit (§4.20, §5.5.5). The first run on GitHub (1 Nov) downloaded only Chromium, and every Firefox and WebKit test failed for want of a browser. `--with-deps` also installs the system libraries a browser needs on a bare Linux machine, such as fonts.

@@ 67
`pnpm e2e` — run the end-to-end test. Its configuration starts the databases with Docker Compose, prepares a demo project, and launches all four services itself (`e2e/playwright.config.ts`).

@@ 68-73
Only **if a step failed** (`if: failure()`), upload the test's results — screenshots and Playwright's step-by-step **trace** — as an **artifact**: a file bundle attached to the CI run, kept for 7 days. A failure on a machine nobody can log into is then still easy to investigate.

@@ 75
`infrastructure:` — the third job: proving the development databases start correctly on a completely clean machine.

@@ 76-78
Its title, machine and a 10-minute limit.

@@ 79
`steps:` — this job's steps.

@@ 80
Download the code.

@@ 81
Start PostgreSQL and Valkey and **wait until both report healthy**. If either image can't be downloaded, or either health check never passes, this step fails. GitHub's Ubuntu machines come with Docker already installed.

@@ 82
Stop the containers and delete their data volumes, leaving the machine clean. GitHub discards the machine anyway, but cleaning up after yourself is a good habit.

@@ 28
Install Tesseract (§5.6.2) from Ubuntu's packages: the document tests read specimen passports with it. (On this project's Windows computers it runs in a container instead.)
