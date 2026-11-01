---
fingerprint: 5b7a6b146cdbb104
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
`timeout-minutes: 45` — if something hangs, stop after 45 minutes instead of GitHub's default of six hours. (It was 15 until the first run on GitHub, then 30; GitHub's machines have no graphics card, and the whole suite outgrew 30 minutes there — see below.)

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

@@ 54
`javascript:` — the second job, running at the same time on its own machine.

@@ 55-57
Its title, the same pinned Ubuntu machine, and the same 15-minute limit. Since Phase 1 the job also *builds* everything, hence "builds" in its name.

@@ 58
`steps:` — this job's steps.

@@ 59
Download the code, as in the first job.

@@ 60
`pnpm/action-setup` (pinned by commit) — installs **pnpm**. No version is given here, because the action reads the `packageManager` field of `package.json` (pnpm 12.11.2), so the version lives in one place only.

@@ 61-64
`actions/setup-node` (pinned by commit) — installs **Node.js 24** (the LTS line in `package.json`). `cache: pnpm` keeps pnpm's package store between runs.

@@ 65
`run: pnpm install --frozen-lockfile` — install exactly what `pnpm-lock.yaml` says, and **fail** if the lockfile is out of date. This is the JavaScript twin of `uv sync --locked`.

@@ 66
`run: pnpm lint` — Biome's formatting and lint checks.

@@ 67
`run: pnpm typecheck` — TypeScript checks for every package: the SDK, both web apps and the end-to-end tests (added in Phase 1).

@@ 68
`run: pnpm test` — JavaScript unit tests for every package (Vitest, §4.20).

@@ 69
`run: pnpm build` — build every package with Turborepo: the SDK compiles to plain JavaScript, and both Next.js apps make their production builds. A build that only fails on a clean machine is caught here, not on deployment day.

@@ 71-74
**The end-to-end job** (added in Phase 1): the whole system, in a real browser, exactly as a person would use it — the demo shop, the verify page, the API and the inference service, with a fake camera. It gets 20 minutes, because it installs a browser and builds everything first.

@@ 75-76
Its steps start, like every job, by checking out the code.

@@ 77-80
Install uv, as in the Python job: the API and the inference service are Python programs.

@@ 81-85
Install pnpm and Node.js 24, as in the JavaScript job: the web apps and the test runner are JavaScript programs.

@@ 86
`uv sync --locked` — install the Python side exactly as the lockfile says.

@@ 87
Download the face-detection model, which the inference service needs (§5.1.1).

@@ 88
Install the JavaScript side exactly as its lockfile says.

@@ 89
Download the three browsers Playwright drives — Chromium, Firefox and WebKit (§4.20, §5.5.5). The first run on GitHub (1 Nov) downloaded only Chromium, and every Firefox and WebKit test failed for want of a browser. `--with-deps` also installs the system libraries a browser needs on a bare Linux machine, such as fonts.

@@ 90
`pnpm e2e` — run the end-to-end test. Its configuration starts the databases with Docker Compose, prepares a demo project, and launches all four services itself (`e2e/playwright.config.ts`).

@@ 91-96
Only **if a step failed** (`if: failure()`), upload the test's results — screenshots and Playwright's step-by-step **trace** — as an **artifact**: a file bundle attached to the CI run, kept for 7 days. A failure on a machine nobody can log into is then still easy to investigate.

@@ 98
`infrastructure:` — the third job: proving the development databases start correctly on a completely clean machine.

@@ 99-101
Its title, machine and a 10-minute limit.

@@ 102
`steps:` — this job's steps.

@@ 103
Download the code.

@@ 104
Start PostgreSQL and Valkey and **wait until both report healthy**. If either image can't be downloaded, or either health check never passes, this step fails. GitHub's Ubuntu machines come with Docker already installed.

@@ 105
Stop the containers and delete their data volumes, leaving the machine clean. GitHub discards the machine anyway, but cleaning up after yourself is a good habit.

@@ 28
Install Tesseract (§5.6.2) from Ubuntu's packages: the document tests read specimen passports with it. (On this project's Windows computers it runs in a container instead.)

@@ 29-30
Lint and types: the first two parts of `uv run tasks.py check`, the command developers run locally (§5.0.3), as separate steps.

@@ 31-39
The tests, one step per test run, each with its own time limit, so GitHub records how long each took. They are the same two runs as `tasks.py test`, with two additions: `-v` prints each test's name as it starts, and `--durations=15` lists the fifteen slowest at the end. `tee` shows the output and also saves it to a file; `shell: bash` makes the step fail if pytest fails, even though its output goes through `tee`.

@@ 40
The book in strict mode — the last part of `tasks.py check`.

@@ 41-46
**Test timings, as annotations.** GitHub shows a run's full log only to people signed in; *annotations* — short messages attached to a run — anyone can read, including through GitHub's public API. `if: always()` runs this step even after a failure or a step that ran out of time.

@@ 47-52
For each saved log: the slowest-tests section (from the line naming it to the next line of `=`), and the last three test names reached — if a step ran out of time, the last one is the test that was running. Each becomes one `::notice` line, which GitHub turns into an annotation (`|` stands in for line breaks, which an annotation's one line can't hold).
