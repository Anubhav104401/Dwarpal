---
fingerprint: e05d3bb5df5fdf9a
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
`timeout-minutes: 15` — if something hangs, stop after 15 minutes instead of GitHub's default of six hours.

@@ 20
`steps:` — the job's steps, run in order.

@@ 21
`uses: actions/checkout@v7.0.1` — a published **action** that downloads this repository's code onto the machine. Every job starts from an empty machine, so this always comes first.

The exact version tag is pinned: a newer release can only arrive through a deliberate, visible change to this file.

@@ 22-25
`astral-sh/setup-uv@v10.3.0` — installs **uv**:

- `version: "0.13.1"` — the same uv version as on the developer's machine;
- `enable-cache: true` — keep downloaded packages between runs, which makes later runs much faster.

@@ 26
`run: uv sync --locked` — install Python 3.13 and every locked package. `--locked` means: **fail** if `uv.lock` doesn't exactly match the `pyproject.toml` files. Someone who changed a dependency but forgot to update the lockfile is told immediately.

@@ 27
`run: uv run tasks.py check` — the same single command developers run locally (§5.0.3): lint, types, tests and the book in strict mode. CI and developers can never disagree about what "passing" means.

@@ 29
`javascript:` — the second job, running at the same time on its own machine.

@@ 30-32
Its title, the same pinned Ubuntu machine, and the same 15-minute limit.

@@ 33
`steps:` — this job's steps.

@@ 34
Download the code, as in the first job.

@@ 35
`pnpm/action-setup@v6.1.0` — installs **pnpm**. No version is given here, because the action reads the `packageManager` field of `package.json` (pnpm 12.11.2), so the version lives in one place only.

@@ 36-39
`actions/setup-node@v7.1.0` — installs **Node.js 24** (the LTS line in `package.json`). `cache: pnpm` keeps pnpm's package store between runs.

@@ 40
`run: pnpm install --frozen-lockfile` — install exactly what `pnpm-lock.yaml` says, and **fail** if the lockfile is out of date. This is the JavaScript twin of `uv sync --locked`.

@@ 41
`run: pnpm lint` — Biome's formatting and lint checks.

@@ 42
`run: pnpm typecheck` — TypeScript checks for every package (none exist yet).

@@ 43
`run: pnpm test` — JavaScript tests for every package (none exist yet).

@@ 45
`infrastructure:` — the third job: proving the development databases start correctly on a completely clean machine.

@@ 46-48
Its title, machine and a 10-minute limit.

@@ 49
`steps:` — this job's steps.

@@ 50
Download the code.

@@ 51
Start PostgreSQL and Valkey and **wait until both report healthy**. If either image can't be downloaded, or either health check never passes, this step fails. GitHub's Ubuntu machines come with Docker already installed.

@@ 52
Stop the containers and delete their data volumes, leaving the machine clean. GitHub discards the machine anyway, but cleaning up after yourself is a good habit.
