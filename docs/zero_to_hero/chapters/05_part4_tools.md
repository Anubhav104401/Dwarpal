# Part 4 — The tools, one by one

Every tool is introduced here just before the code that uses it. This part grows phase by phase. Right now it covers the tools of **Phase 0 (foundations)**: version control, Python packaging, the four quality "robots", the JavaScript workspace, Docker Compose and continuous integration.

## 4.1 Git in practice

§0.15 introduced Git as a time machine for code. Here is what actually happens inside the project folder.

- `git init -b main` turned the folder into a **repository** (Git keeps its own data in a hidden `.git` folder). `-b main` names the first **branch** `main`.
- The files you edit form the **working tree**.
- `git add` puts chosen changes into the **staging area** — a draft of the next snapshot.
- `git commit` saves the staged draft as a permanent **commit**: a snapshot of every tracked file, plus a message, the author, the time, and a pointer to the previous commit. Commits form a chain, which is the project's history.
- A **remote** (like GitHub) is another copy of the repository that you **push** commits to and **pull** commits from.

!!! honest "Where we are"
    The repository has been initialised, but nothing has been committed yet. Committing is the project owner's call, and it is offered at the end of Phase 0.

### Files Git must never see: `.gitignore`

Some files must **never** enter history:

- **secrets** (`.env` files with passwords) — once committed, a secret is in history forever, even if deleted later;
- **downloaded or generated bulk** (`node_modules`, `.venv`, caches) — huge, and rebuildable from the lockfiles;
- **datasets and model weights** — huge, and licence-restricted (§0.16).

`.gitignore` lists patterns of paths Git should pretend don't exist. Its walkthrough is in §5.0.1.

### Line endings: `.gitattributes`

Windows ends each line of text with two invisible characters, *carriage return + line feed* (CRLF). Linux and macOS use only *line feed* (LF). If a Windows editor and a Linux server disagree, every line of a file appears "changed" for no visible reason, and shell scripts can break.

`.gitattributes` tells Git to **store every text file with LF**, whatever computer it was edited on. It also marks images and model files as **binary**, so Git never tries to "fix" their bytes.

## 4.2 How Python projects are organised

### Modules, packages and distributions

| Word | Meaning | Example |
| :-- | :-- | :-- |
| **Module** | One `.py` file | `build.py` |
| **Package** | A folder of modules, marked by an `__init__.py` file | `dwarpal_api/` |
| **Distribution** | A package bundled for installation, with a name and version | `dwarpal-api 0.1.0` |

The distribution's name uses a dash (`dwarpal-api`). The importable package uses an underscore (`dwarpal_api`), because a dash isn't allowed in a Python name — Python would read it as a minus sign.

### The `src` layout

Each of our packages keeps its code in a `src/` folder: `services/api/src/dwarpal_api/__init__.py`.

!!! why "Why the extra `src` folder?"
    Without it, Python can accidentally import your package straight from the folder you're standing in, even if it isn't installed properly. Tests would then pass on your machine and fail on a server. The `src` layout forces the code to be **installed** before it can be imported, so you always test what you ship.

### `pyproject.toml`

Every modern Python project describes itself in a `pyproject.toml` file (TOML, see Part X). The official sections are:

- `[project]` — name, version, description, supported Python versions, dependencies;
- `[build-system]` — which **build backend** turns the folder into an installable distribution. We use `uv_build`, the fast backend made by the uv team;
- `[tool.*]` — settings for tools (ruff, mypy, pytest, uv).

### Virtual environments

Different projects need different library versions. A **virtual environment** (`.venv`) is a private folder holding one Python interpreter plus exactly the libraries one project needs. Projects can't interfere with each other, and the computer's own Python stays clean.

### uv — one tool for all of it

**uv** is a very fast Python project manager written in Rust. In this project it:

1. **installs Python itself.** This computer's own Python is 3.14, but the project pins **3.13** (in `.python-version`), so uv downloaded its own copy of Python 3.13.16;
2. **creates the virtual environment** (`.venv` at the project root);
3. **resolves dependencies** — it works out a set of library versions that fit together — and writes them to the **lockfile** `uv.lock`;
4. **installs** exactly the locked versions (`uv sync`);
5. **runs commands** inside the environment (`uv run …`), syncing first if anything changed.

**Workspaces.** Our five Python packages (api, inference, contracts, vision, ml) are members of one **uv workspace**: one lockfile and one environment for all of them, installed in *editable* mode so code changes take effect immediately. Every package therefore always sees the same version of every library.

**Dependency groups.** Tools only developers need (ruff, mypy, pytest) live in a `dev` group; the book's tools (Markdown, Pygments) in a `docs` group. They are never shipped inside a service.

!!! alt "Alternatives considered"
    - **pip + venv** — built in, but has no lockfile and no Python installation, and is slow on big projects.
    - **Poetry** — popular, but slower, with its own non-standard metadata and no Python installation.
    - **conda** — great for scientific stacks, but heavy, and mixes non-Python packages into the environment.

    uv does all of it, follows the official standards, and is 10–100× faster than pip.

!!! real "Real world — what we measured"
    `uv sync` resolved and installed the workspace's 21 packages in under 3 seconds on first run (most of it downloading). Re-runs take milliseconds.

## 4.3 Four robots that check every change

People make mistakes; robots don't get tired. Every change in this project passes four automatic checks.

### Robot 1 — the formatter (`ruff format`)

A **formatter** rewrites code into one consistent layout: spacing, line breaks, quotes. Nobody argues about style, and code reviews focus on meaning. It *changes* files; in CI it runs with `--check`, which only *reports*.

### Robot 2 — the linter (`ruff check`)

A **linter** reads code without running it and flags likely bugs, risky patterns and outdated style. **Ruff** is a Rust-based linter that implements over 800 rules from many older tools, in milliseconds. We switched on these rule families:

| Code | Family | Catches, for example |
| :-- | :-- | :-- |
| `E`, `W` | pycodestyle | Lines too long, stray whitespace |
| `F` | Pyflakes | Unused imports, undefined names — often real bugs |
| `I` | isort | Imports in a messy order |
| `B` | bugbear | Classic traps, such as a mutable default argument shared between calls |
| `UP` | pyupgrade | Old syntax with a modern replacement |
| `SIM` | simplify | Needlessly complicated `if`/`else` |
| `C4` | comprehensions | Loops that should be comprehensions, and the reverse |
| `PTH` | pathlib | `os.path` string juggling instead of `Path` objects |
| `S` | bandit (security) | `subprocess` with a shell, weak hashes, hard-coded passwords |
| `N` | naming | `camelCase` where Python expects `snake_case` |
| `RUF` | Ruff's own | Ambiguous Unicode characters, and more |
| `DTZ` | datetime | Times without a time zone — a classic source of bugs |
| `PERF` | performance | Slow patterns in loops |
| `RET` | return | Inconsistent `return` statements |

!!! real "Real world — the first thing Ruff caught"
    On its very first run, Ruff flagged one line in the book builder: `datetime.now(timezone.utc)` should use the newer, clearer alias `datetime.now(UTC)`. Small, but it shows the robot reading every line.

### Robot 3 — the type checker (`mypy --strict`)

Python doesn't make you declare what kind of value a variable holds. The **type hints** we write (`def read_text(path: Path) -> str`) are labels for humans and tools. **mypy** reads those labels and proves that the code uses them consistently: you never pass a number where text is expected, never forget that something might be `None`, and so on. `--strict` turns on every check, including "every function must be fully labelled".

!!! real "Real world — what strict mode changed in this phase"
    mypy refused two things in the book builder:

    1. A bare `dict` must say what it contains, so it became `dict[str, Any]`: keys are text, values can be anything.
    2. The Markdown library attaches a `toc_tokens` attribute to its converter **while the program runs**, so a type checker reading the code beforehand can't know it exists. The fix, `getattr(md, "toc_tokens", [])`, reads the attribute safely and also says what to use if it's missing.

    Neither was a bug yet, but both were places where a future change could have caused one without warning.

### Robot 4 — the tests (`pytest`)

A **test** is a small program that runs a piece of real code with known inputs and checks the result:

```python
def test_fingerprint_is_stable_and_changes_with_any_edit() -> None:
    assert build.fingerprint("x = 1\n") == build.fingerprint("x = 1\n")
    assert build.fingerprint("x = 1\n") != build.fingerprint("x = 2\n")
```

`assert` means "this must be true — otherwise stop and report a failure". **pytest** finds every function whose name starts with `test_`, runs them all, and reports which passed. Phase 0 has **9 tests**, all for the book builder, because the program that checks the book must itself be checked.

## 4.4 The JavaScript side

### Node.js

**Node.js** runs JavaScript outside the browser — on servers and on developers' machines. It is what will run our Next.js websites, and all the JavaScript tools. Versions with even numbers become **LTS** (Long-Term Support) releases, maintained for about three years. We use **Node 24 LTS**.

### npm, pnpm and the lockfile

**npm** is Node's built-in package manager. We use **pnpm** instead:

- it stores each version of each library **once** on the computer and links it into projects, saving gigabytes;
- it is stricter — a package can only use libraries it actually declares, which prevents "works on my machine" bugs;
- it has first-class **workspaces**.

`package.json` records the exact pnpm version in its `packageManager` field, so every machine uses the same one. `pnpm install` writes **`pnpm-lock.yaml`**, the JavaScript lockfile.

!!! warn "Careful — install scripts are a security risk"
    When we installed pnpm itself, npm printed: *"1 package has install scripts not yet covered by allowScripts"*. An **install script** is code that a package runs automatically on your computer at install time — a favourite trick of malicious packages. Modern npm and pnpm therefore block them unless you approve them. Every install script in this project must be approved deliberately.

### Workspaces and Turborepo

`pnpm-workspace.yaml` says which folders hold workspace packages (`apps/*`, `packages/*`). The first package is `@dwarpal/config`, which holds the shared TypeScript settings.

**Turborepo** (`turbo`) runs tasks — build, typecheck, test — across all packages **in the right order**, and **caches** the results. If a package hasn't changed, its previous result is reused instantly. In `turbo.json`, `"dependsOn": ["^build"]` means "before doing this task for a package, build every package it depends on". The `^` means *dependencies*, not the package itself.

!!! honest "Where we are"
    Turbo currently prints *"No tasks were executed"*: no package has a build or test script yet. The apps arrive in Phase 1.

### Biome

**Biome** is the JavaScript world's version of Ruff: one fast tool (written in Rust) that **formats and lints** JavaScript, TypeScript, JSON and CSS. It replaces the older pair of ESLint and Prettier.

!!! real "Real world — keeping up with tools"
    Biome 2.5 printed a warning on our first configuration: the `"recommended": true` setting is deprecated in favour of `"preset": "recommended"`. Running `biome migrate --write` rewrote the configuration automatically. Tools change; reading their warnings, not ignoring them, keeps a project healthy.

### TypeScript settings

`packages/config/tsconfig.base.json` holds the strictest sensible TypeScript settings. Every app and package will *extend* it, so all of them follow the same rules. Each option is explained line by line in §5.0.4.

!!! honest "A decision deliberately postponed"
    TypeScript 7 (a complete rewrite of the compiler in the Go language) became the default version on npm in 2026. Whether Next.js 16.4 and the other tools work smoothly with it will be tested in Phase 1, when the first TypeScript code exists. Until then nothing depends on it, so nothing is pinned.

## 4.5 Docker Compose in practice

§0.14 explained images, containers and volumes. Here is what our first Compose file actually does (full walkthrough in §5.0.5):

- **Pinned image tags.** `postgres:18.6-alpine3.24` means PostgreSQL version 18.6, built on Alpine Linux 3.24 — a tiny Linux distribution, so images are small. A bare `postgres:latest` would silently change under us.
- **Settings with defaults.** `${POSTGRES_PASSWORD:-dwarpal-local-only}` means "use the environment variable if set, otherwise this default". The defaults are deliberately labelled *local-only*.
- **Ports bound to `127.0.0.1`.** `127.0.0.1:5432:5432` makes the database reachable **only from this computer**, not from other devices on the same Wi-Fi.
- **Health checks.** Docker asks each container "are you ready?" every 5 seconds (`pg_isready`, `valkey-cli ping`). `docker compose up --wait` waits until every container reports healthy, not just "started".
- **Volumes.** The data lives in named volumes (`pgdata`, `valkeydata`), so it survives restarts.

!!! real "Real world — the first run"
    Docker's status table after `up --wait`:

        postgres   postgres:18.6-alpine3.24         Up 6 seconds (healthy)   127.0.0.1:5432->5432/tcp
        valkey     valkey/valkey:9.1.2-alpine3.24   Up 6 seconds (healthy)   127.0.0.1:6379->6379/tcp

    Asking the new database for a time-ordered ID with `SELECT uuidv7();` returned `01a13f9a-4271-7e5f-851e-cbb929956ead`. Its first twelve hexadecimal digits encode the exact millisecond it was created — the property ADR-0011 relies on.

## 4.6 Continuous integration with GitHub Actions

**Continuous integration (CI)** means: every time anyone pushes code, a robot in the cloud checks out a fresh copy and runs every check. Because it starts on a clean machine each time, "it works on my computer" stops being an excuse.

On GitHub, CI is described in **workflow** files under `.github/workflows/`, written in **YAML** (a settings format based on indentation). Their building blocks are:

| Word | Meaning |
| :-- | :-- |
| `on` | Which events start the workflow (a push to `main`, a pull request) |
| `jobs` | Independent groups of work. They run **in parallel** on separate fresh machines |
| `runs-on` | The kind of machine, e.g. `ubuntu-24.04` (a Linux virtual machine) |
| `steps` | The commands of a job, in order. `uses:` runs a published **action** (a reusable step); `run:` runs a shell command |
| `permissions` | What the workflow may do on GitHub. We grant only `contents: read` — the principle of **least privilege** |

Our workflow has three jobs:

- **Python** — `uv run tasks.py check`;
- **JavaScript** — lint, typecheck, test;
- **Compose** — the databases must start healthy.

!!! honest "Where we are"
    The workflow file is written and valid, but it has never run, because the project isn't on GitHub yet. It runs automatically the first time the repository is pushed.

## 4.7 One command to check everything: `tasks.py`

Every check has its own command — ruff, mypy, pytest, the book builder. Remembering them all is error-prone, so `tasks.py` gives them short names:

```bash
uv run tasks.py check
```

That one command runs everything CI runs, stopping at the first failure, and prints which step failed.

!!! why "Why a Python script instead of a Makefile?"
    `make` is the classic tool for this, but it isn't installed on Windows by default and behaves differently across systems. A tiny Python script needs nothing but the Python the project already has, and works the same on every operating system.
