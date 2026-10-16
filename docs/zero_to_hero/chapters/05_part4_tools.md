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

## 4.8 Web servers in Python: Uvicorn, FastAPI and Pydantic

Phase 1 builds our first servers. Four ideas explain all of their code.

### The two halves of a Python web server

A Python web server is split into two programs that cooperate:

| Part | Its job | Ours |
| :-- | :-- | :-- |
| **The server** | Opens the port, speaks the HTTP protocol, receives bytes from the network, and hands each request to the application | **Uvicorn** |
| **The application** | Decides what to answer. It receives the request already understood ("POST, this path, these headers, this body") and returns a response | Our code, built with **FastAPI** |

They talk through a standard called **ASGI** (Asynchronous Server Gateway Interface). Any ASGI server can run any ASGI application. The same standard also lets our tests skip the network entirely: the test client hands requests straight to the application in memory (§5.1).

!!! kid "Explain like I'm six"
    Uvicorn is the waiter: it stands at the door, takes orders and carries plates. FastAPI is the kitchen: it reads each order and cooks the answer. ASGI is the order-slip format they agreed on, so any waiter can work with any kitchen.

### FastAPI: functions become endpoints

FastAPI turns ordinary Python functions into HTTP endpoints. A **decorator** attaches each function to a method and a path:

```python
@app.get("/livez")
async def livez() -> dict[str, str]:
    return {"status": "alive"}
```

When a `GET /livez` request arrives, FastAPI calls `livez()` and turns the returned dictionary into JSON. The type hints matter: FastAPI reads them to check incoming data and to shape outgoing answers.

!!! alt "Alternatives considered"
    **Flask** is older and simpler, but synchronous and has no built-in checking of data. **Django** is a large "batteries included" framework — more than an API needs. **Litestar** is excellent, with a smaller community. FastAPI combines typed checking, async support and a huge community (ADR-0010).

### Pydantic: data that checks itself

**Pydantic** turns a class with typed fields into a **data model** that checks every value it receives:

```python
class FrameMeta(BaseModel):
    index: Annotated[int, Field(ge=0, le=31)]
    t_ms: Annotated[float, Field(ge=0.0)]
```

`FrameMeta(index=40, t_ms=1.0)` is refused with a precise error, because 40 is above the limit of 31. The same models read and write JSON (`model_validate_json`, `model_dump_json`). Errors are therefore caught at the edge of the system, before any of our logic runs. The habit has a name: **parse, don't validate**. Turn unknown input into a trusted, typed object once, at the boundary, and the rest of the code can rely on it.

**pydantic-settings** applies the same idea to configuration. A `Settings` class whose fields are filled from environment variables — such as `DWARPAL_INFERENCE_STUB_AGE=40` — and checked like any other model. A typo in a setting stops the service at start-up instead of misbehaving later.

### Waiting without wasting: `async`, threads and back-pressure

A server spends most of its time **waiting** — for the network, the database, another service. Python's **`async`/`await`** lets one thread juggle thousands of waiting requests. At each `await`, the function steps aside, and the **event loop** runs something else until the awaited thing is ready.

!!! kid "Explain like I'm six — the chess master"
    A chess master plays 30 people at once by walking from board to board. While one opponent thinks, the master is already moving at the next board. That is the event loop. But if the master stopped to solve a two-hour puzzle at one board, all 30 games would freeze.

Image analysis is that two-hour puzzle: heavy, **blocking** computation. Running it directly in the event loop would freeze every other request, health checks included. So the inference service hands each analysis to a **worker thread** (`anyio.to_thread.run_sync`), and the event loop stays free.

Two safety rules come with threads:

1. **Locks.** When several threads share one object that changes inside itself — like the face detector's "current picture size" — a **lock** lets only one thread use it at a time. Otherwise threads trample on each other's settings, a bug called a **race condition** (`detect.py`, line 33).
2. **Back-pressure.** There are only so many worker threads, set by `workers`. When all are busy, the service immediately answers `503 Service Unavailable` with `Retry-After: 1`, instead of quietly piling up an endless queue. An overloaded system that says "not now" recovers in seconds; one that accepts everything collapses.

## 4.9 Pictures as numbers: NumPy and OpenCV

§0.1 said a picture is a grid of numbers. Two libraries make that grid easy and fast to work with.

### NumPy

**NumPy** stores numbers in **arrays**: blocks of numbers of one type, laid out in memory side by side, and processed by optimised C code instead of slow Python loops. A colour picture is an array of **shape** `(height, width, 3)`, with numbers from 0 to 255 (type `uint8`, *unsigned 8-bit integer*).

| You write | It means |
| :-- | :-- |
| `image.shape` | `(480, 640, 3)` — 480 rows, 640 columns, 3 colours |
| `image[100, 200]` | the three colour numbers of the pixel in row 100, column 200 |
| `image[0:100, 0:50]` | a rectangle of rows 0–99 and columns 0–49 — a **slice**, which shares memory with the original |
| `image * 0.12` | every number multiplied at once — *vectorised*, no loop needed |
| `gray.mean()` | the average of all the numbers |

### OpenCV

**OpenCV** (Open Source Computer Vision Library) has been the standard toolbox for image processing since 2000: decoding files, resizing, filtering, geometry, and running neural networks such as our face detector. Two of its habits catch everyone out at first:

- **Colours come in BGR order** (blue, green, red), not RGB. It's a historical choice, and every OpenCV function expects it.
- **Sizes are given as (width, height)**, but NumPy shapes are (height, width). Our code converts carefully every time (`detect.py`, line 38).

### Three image ideas used in this phase

- **Greyscale** keeps only how light each pixel is, which is enough for brightness and sharpness.
- **Filters** slide a small grid of weights over the image. The **Laplacian** filter lights up wherever brightness changes suddenly — at edges and fine detail — so a blurred photo gives only weak responses (`quality.py`, line 62).
- **Affine transforms** move every pixel with one formula: rotate, scale, shift. Alignment uses the *similarity* kind, which never stretches a face (`align.py`).

## 4.10 Remembering for good: PostgreSQL, SQLAlchemy and Alembic

§0.12 explained what a database is. The API uses one for real — **PostgreSQL** (ADR-0011) — and four ideas explain all of its database code.

### Talking to PostgreSQL: SQL, drivers and pools

Programs talk to PostgreSQL in **SQL**. Five sentences cover nearly everything the API does:

| SQL | Means |
| :-- | :-- |
| `SELECT * FROM verification_sessions WHERE id = '…'` | read the rows that match |
| `INSERT INTO projects (id, name, …) VALUES (…)` | add a row |
| `UPDATE verification_sessions SET status = 'completed' WHERE id = '…'` | change rows |
| `DELETE FROM api_keys WHERE …` | remove rows |
| `CREATE TABLE …`, `CREATE INDEX …` | change the *shape* of the data — the job of migrations, below |

A table can carry **constraints**: rules the database itself enforces, even if the program has a bug.

- a **primary key** — a column whose value is different in every row (our `id`s);
- a **foreign key** — "this column must point at a real row over there" (a session's `project_id`);
- **unique** — no two rows may share this value (an API key's `lookup`);
- **not null** — this column may never be empty.

An **index** is a sorted list kept beside a table, like the index at the back of a book. Finding "all sessions of project X" with an index takes a few steps; without one, the database reads every row.

The program doesn't speak PostgreSQL's network language itself: a **driver** does that. Ours is **asyncpg**, which waits without blocking (§4.8). Opening a connection is slow — the two sides greet each other and check the password — so a **connection pool** keeps a few connections open and lends them out, one request at a time (`db.py`).

### The ORM: tables as Python classes

Writing SQL by hand for every query is long and easy to get wrong. **SQLAlchemy** — the most widely used database toolkit for Python (ADR-0010) — offers an **ORM** (Object-Relational Mapper): each table is described as a Python class, each row becomes a Python object, and SQLAlchemy writes the SQL.

```python
async with sessions() as session:           # start a unit of work
    row = await session.get(Project, pid)   # SELECT … FROM projects WHERE id = …
    row.name = "Amber Cellars"              # only the Python object changes…
    await session.commit()                  # …until now: UPDATE …, then COMMIT
```

A SQLAlchemy **session** is one **unit of work**: it remembers every object you loaded or added, notices what changed, and at `commit()` sends all the changes together. (In this project the word *session* also means a verification session; the code keeps the two apart — see the warning in `db.py`.)

!!! alt "Alternatives considered"
    **Raw SQL** through asyncpg gives full control but means writing and checking every query by hand. **SQLModel** is a thin, friendly layer on top of SQLAlchemy, but adds one more moving part. SQLAlchemy 2 is fully typed, fully async, and works directly with mypy's strict mode.

### Transactions and locks

A **transaction** groups changes so that they all happen, or none do. Databases promise four things about transactions, remembered as **ACID**:

| Letter | Promise | In plain words |
| :-: | :-- | :-- |
| A | Atomic | all of it or nothing — never half |
| C | Consistent | every rule (constraint) still holds afterwards |
| I | Isolated | others never see your half-finished work |
| D | Durable | once it says "committed", it survives even a power cut |

When a face attempt is recorded, three things change together: a new attempt row, the session's status, and its count of attempts. Thanks to atomicity, a crash in the middle can never leave an attempt recorded with the old status.

Sometimes two requests want to change **the same row at the same moment** — say, two face attempts on one session, sent from two browser tabs. Both read "1 attempt so far", both write "2" — and one attempt vanishes. This classic bug is a **lost update**. The fix is a **row lock**:

```sql
SELECT * FROM verification_sessions WHERE id = '…' FOR UPDATE;
```

`FOR UPDATE` tells PostgreSQL: "I am going to change this row; anyone else who wants to change it must wait until my transaction ends". The second request waits a few milliseconds, then reads "2 attempts so far", and is decided correctly.

```
request A:  lock row ─ read "1" ─ decide ─ write "2" ─ commit ┐
request B:  lock row … waiting ……………………………………………………………… ┴ read "2" ─ decide ─ write "3" ─ commit
```

An **advisory lock** is the same idea for something that isn't a row: a lock with a *number* for a name, whose meaning the program decides. The API uses one so that two copies starting at the same moment can't both create a signing key (`signing.py`).

### Migrations: changing tables while the data stays

Code changes every week, but a production database is never thrown away: it holds real data. Changing its tables — a new column, a new index — must happen step by step, the same way everywhere. **Alembic** manages that:

- each change is a **migration**: a small file with an `upgrade()` (go forward) and a `downgrade()` (go back);
- each migration names the one before it, forming a chain: `0001 → 0002 → 0003 …`;
- the database keeps the number of its newest applied migration in a small table of its own, `alembic_version`;
- `upgrade head` applies whatever is missing, in order. On an up-to-date database it does nothing.

!!! kid "Explain like I'm six — renovating a house with people living in it"
    You can't knock the house down and rebuild it every time you want a new window: people live there. So every change is written down as a numbered instruction — "1. build the kitchen; 2. add a window to the kitchen" — and every copy of the house follows the same instructions, in the same order. A house built last year only needs instruction 2; a brand-new house follows both.

Our code describes the tables twice: as they should be *now* (`tables.py`), and as the steps to get there (the migrations). A **drift test** compares the two on a real database after migrating, and fails if they disagree (`test_api.py`). A forgotten migration is caught by the test suite, not by a crash in production.

## 4.11 Valkey: a notebook that forgets on purpose

Some facts only matter for minutes: "this browser may work on session X for the next 15 minutes"; "this challenge may be used once, within 2 minutes". Storing them in PostgreSQL would fill tables with rows that need cleaning up. **Valkey** is built for exactly this kind of data (ADR-0011).

Valkey is a **key-value store** that keeps everything in memory: you store a **value** under a **key** (a name), and get it back by that name — in well under a millisecond. Any value can be given a **time to live** (TTL), after which Valkey deletes it by itself.

| Command | Does | Used for |
| :-- | :-- | :-- |
| `SET key value EX 900` | store a value for 900 seconds | flow tokens |
| `GET key` | read a value (nothing if missing or expired) | checking a flow token |
| `GETDEL key` | read **and delete**, in one step | using up a challenge |
| `SET key 0 NX EX 1800` | store only if the key doesn't exist yet (`NX`) | starting a counter |
| `INCR key` | add 1 and return the new value | counting challenges |
| `PING` | "are you there?" | the readiness check |

Valkey runs commands **one at a time**, each from start to finish, so every command is **atomic**: no other command can slip in halfway. That is why `GETDEL` makes a challenge truly single-use. If two requests send the same challenge at the same instant, one gets it and the other finds nothing — a separate `GET` followed by a `DEL` would leave a gap in which both could succeed.

!!! why "Why not just keep it in the program's memory?"
    The API runs as several copies (processes) at once, and each has its own memory. A flow token stored in copy 1's memory would be unknown to copy 2. Valkey is shared by all of them, and survives a restart of any one.

!!! real "Real world — Valkey and Redis"
    For years the standard tool for this job was **Redis**. In 2024 Redis moved to licences that are not open source. The Linux Foundation then started **Valkey** from the last open-source version, under the permissive BSD licence. It speaks exactly the same language, so tools written for Redis — including the `redis` Python library we use — work unchanged. Our licence policy prefers permissive licences for everything that runs in production (ADR-0018).

## 4.12 Secrets, seals and signatures — cryptography in plain words

The API protects four kinds of secret and produces one kind of unforgeable message. Five ideas from **cryptography** — the science of protecting information — cover all of it.

### 1. Randomness nobody can predict

Keys, tokens and secrets must be impossible to guess. Python has two random-number modules, and they are not the same:

- `random` — fast and good for games and simulations, but **predictable**: after seeing enough of its output, someone can work out what comes next;
- `secrets` — uses the operating system's **cryptographically secure** generator, whose output can't be predicted.

Every secret in this project comes from `secrets` (or `os.urandom`, the same source).

### 2. Fingerprints: hashing

A **hash function** such as SHA-256 turns any input into a short fingerprint (§X.5). It only works one way: the input can't be worked out from the fingerprint. So the API stores the fingerprints of API keys, client secrets and flow tokens — never the secrets themselves — and checks an arriving secret by fingerprinting it again.

That is safe here because our secrets are long and random: guessing one by trying fingerprints is hopeless. Passwords that *people* choose are different — they can be guessed from lists of common passwords — so they need deliberately slow hash functions such as **Argon2id** (Phase 4).

Comparing fingerprints uses a **constant-time comparison**, which takes the same time however many characters match, so measuring how long a "no" takes reveals nothing (`keys.py`).

### 3. Locks with one key: AES-GCM

**Encryption** scrambles data so that only someone with the **key** can unscramble it. With **symmetric** encryption, the same key locks and unlocks. The API uses **AES-256-GCM**, the most widely used cipher in the world — your browser is almost certainly using it right now.

| Ingredient | What it is |
| :-- | :-- |
| **key** | 32 secret bytes — our master key |
| **nonce** | 12 bytes that must never repeat with the same key; not secret |
| **ciphertext** | the scrambled data |
| **tag** | 16 bytes that detect any change: a single altered bit, and decryption is refused |
| **associated data** | information that isn't hidden, but is bound to the seal — we use the key's ID |

GCM belongs to the **AEAD** family (Authenticated Encryption with Associated Data): it protects the data's *secrecy* and its *integrity* in one step. The API uses it to **seal** private signing keys before storing them (`signing.py`).

### 4. Locks with two keys: digital signatures

With **asymmetric** cryptography, keys come in pairs: a **private key**, kept secret, and a **public key**, given to everyone. For signatures:

- only the private key can **sign** a message;
- anyone with the public key can **verify** that the signature is genuine, and that not one character of the message changed since.

!!! kid "Explain like I'm six — the wax seal"
    A king seals his letters with his own signet ring, and every town has a drawing of the king's seal. Anyone can check a letter's seal against the drawing; nobody but the king can make it. Break the seal, change a word, and the seal no longer matches.

The API signs with **Ed25519**: fast, with small keys and signatures (64 bytes), and **deterministic** — signing never needs fresh randomness. That last property matters: the older ECDSA scheme needs a perfect random number for *every* signature, and a few bad ones have leaked private keys in real products. Ed25519 can't fail that way.

### 5. Tokens: JWT, JWS, JWK and JWKS

An **age token** is a **JWT** — a JSON Web Token — in its signed form, **JWS**. It is three parts, each in Base64url, joined by dots:

```
eyJhbGciOiJFZDI1NTE5Ii…   .   eyJpc3MiOiJodHRwOi8vbG9jYW…   .   Xk3f9q…
      header                         claims (payload)                signature
{"alg":"Ed25519",            {"iss": "http://localhost:8000",
 "typ":"dwarpal-age+jwt",     "aud": "prj_…", "exp": 1792140000,
 "kid":"sig_20261016_…"}      "outcome": "pass", "age_over_18": true, …}
```

The first two parts are only *encoded*, not encrypted: anyone can read the claims. The signature makes them **tamper-proof**, not secret — which is why a token must never contain anything private. Ours contains no age, no name, no picture.

Public keys are published as **JWK**s (JSON Web Keys), collected in a **JWKS** (JWK Set) at a well-known address. Each key has an ID, the `kid`, and every token's header names the `kid` that signed it.

!!! warn "Careful — let the verifier choose the algorithm, never the token"
    A token's header says which algorithm signed it. A naive verifier that simply *believes* the header can be tricked — historically, by tokens claiming `"alg": "none"` ("no signature needed"). Every verifier in this project passes an **allow-list** containing exactly one algorithm, `Ed25519`, and refuses everything else. The name itself is the new, fully-specified one from RFC 9864, which names one exact curve (ADR-0019).

### Where the keys live

```
DWARPAL_MASTER_KEY (environment) ──► opens ──► sealed private key (database)
                                                      │
                                                      ▼
                                    private key, in memory only ──► signs age tokens
                                    public key ──► /.well-known/jwks.json ──► every website
```

Stealing the database gives an attacker only sealed keys. Stealing the master key alone gives them nothing to unseal. They would need both — and the master key never touches the database, the code, or the logs.

## 4.13 Designing an API people can trust

An API is a promise: websites will write code against it and run that code for years. These are the habits that keep the promise.

### Resources, methods and versions

The API is organised around **resources** — nouns — not actions: `/v1/verification-sessions`, not `/v1/createSession`. The HTTP method says what happens to the resource (§0.8): `POST` creates one, `GET` reads one. This style is called **REST**.

Every path starts with a **version**, `/v1/`. If a change would ever break existing integrations, it goes under `/v2/`, and code written for `/v1/` keeps working.

### Who is calling? Three kinds of credential

| Credential | Held by | Lives | Sent as |
| :-- | :-- | :-- | :-- |
| **API key** `dk_test_…` / `dk_live_…` | the website's server | until revoked | `Authorization: Bearer dk_…` |
| **client secret** `vs_…_secret_…` | the verify link, in its `#fragment` | one session | the body of `/start` |
| **flow token** | the verify page, in memory | 15 minutes | `Authorization: Bearer …` |

"Bearer" means "whoever bears (carries) this may do this", which is why every one of them must be kept secret. The client secret travels in the link's **fragment** — the part after `#` — because browsers never send the fragment to any server.

**Test and live.** Every key is either a *test* key or a *live* key, and it can only see sessions of its own kind. Integrators build against test keys freely; real people are only ever judged with live keys.

### Errors that programs can read

Every error has the same shape — **problem details**, RFC 9457 — with a **stable code** that programs check, and a sentence for people:

```json
{"type": "/errors/session_not_found", "title": "session not found", "status": 404,
 "detail": "no such verification session", "code": "session_not_found", "request_id": "req_…"}
```

Some answers are deliberately vague. A malformed session ID and an unknown one get the *same* `404`; a wrong API key and an unknown one get the *same* `401`; and a rejected attempt never says *why*. Every extra detail would help someone probing the system.

### Request IDs and structured logs

Every request gets an ID, returned in the `X-Request-Id` header, printed in every error, and written in exactly one **structured** (JSON) log line. When something goes wrong, one ID connects the user's error message to the right line in the logs. What a log line never holds: bodies, keys, secrets, query strings, pictures (`logs.py`).

### Browsers and origins: CORS

An **origin** is a website's scheme, host and port together: `https://shop.example` and `https://shop.example:8443` are different origins. Browsers enforce the **same-origin policy**: a page's code may only *read* answers from its own origin — unless the other server agrees.

**CORS** (Cross-Origin Resource Sharing) is how the server agrees: it answers with headers such as `Access-Control-Allow-Origin: http://localhost:3000`. For requests that carry an `Authorization` header or a JSON body, the browser first sends a **preflight** — an `OPTIONS` request asking "may I?" — and only sends the real request if the answer is yes.

Our API allows exactly one origin: the hosted verify page. Code on any other website can't read the API's answers through a visitor's browser — and every flow endpoint also needs a token that other websites never have.

### Uploading pictures: multipart forms

JSON is text, and pictures are bytes. The standard way to send both in one request is a **multipart form**: the body is split into **parts** by a random separator line called the **boundary**. Each part has its own little header naming it:

```
--a1b2c3
Content-Disposition: form-data; name="meta"

{"frames": [{"index": 0, "t_ms": 0.0}]}
--a1b2c3
Content-Disposition: form-data; name="frame_0"; filename="frame_0.jpg"
Content-Type: image/jpeg

<the JPEG's bytes>
--a1b2c3--
```

### Saying "no" early

The cheapest attack on any service is to make it do a lot of work. The API refuses work as early as possible:

| Limit | Where | Answer |
| :-- | :-- | :-- |
| every body must declare its size | before reading the body | `411 Length Required` |
| at most 64 KiB of JSON, or 16 × 512 KiB of frames | before reading the body | `413 Content Too Large` |
| at most 16 files and 2 fields per upload | while parsing | `400` from the parser |
| each frame at most 512 KiB | while reading each frame | `413` |
| at most 6 challenges per session | before any analysis | `429 Too Many Requests` |

### Health checks

Two special endpoints answer machines, not people: `/livez` ("am I alive?" — if not, restart me) and `/readyz` ("can I do real work?" — if not, send traffic elsewhere until my database is back). Keeping them separate avoids restarting healthy programs because a database blinked (`health.py`).

## 4.14 Tests that hunt for bugs: Hypothesis and Testcontainers

### The testing pyramid

Tests come in three sizes, and a healthy project has many small ones and few big ones:

```
             ▲  end-to-end: a real browser, every service    — few, slow (§5.1.5)
            ▲▲▲  integration: real databases, real HTTP      — some, seconds each
         ▲▲▲▲▲▲▲  unit: pure functions, no I/O               — many, milliseconds each
```

Small tests pinpoint *where* a bug is. Big tests prove the pieces *fit together*. Both are needed.

### Property-based testing with Hypothesis

An ordinary test checks one example: "for 0.99, the answer is pass". A **property-based test** states a rule that must hold for *every* input, and lets the **Hypothesis** library invent inputs to try to break it:

```python
@given(st.floats(0.0, 1.0), st.floats(0.0, 1.0), st.integers(0, 2))
def test_more_evidence_of_adulthood_never_makes_the_outcome_worse(p, q, attempt):
    ...
```

`@given` says what kind of input to invent: **strategies** such as `st.floats(0.0, 1.0)` (any decimal number from 0 to 1) or `st.uuids()`. Hypothesis tries a hundred inputs per test, deliberately including awkward ones — 0, 1, numbers a hair apart. If one breaks the rule, it **shrinks** it: it keeps simplifying the failing input until it finds the simplest one that still fails, and prints it. A failure like "p = 0.95, q = 0.9500000000000001" points straight at the bug.

Properties are perfect for safety rules: "every pass clears the threshold", "retrying never makes passing easier", "a UUID survives encoding and decoding". They state the *promise itself*, not one example of it.

### Real databases in tests: Testcontainers

Integration tests could pretend to have a database, with a fake ("mock") object. But a mock only behaves the way its author *thinks* PostgreSQL behaves — and the dangerous bugs live exactly where that belief is wrong: a lock, a constraint, a type.

**Testcontainers** starts the real thing instead. A test fixture asks Docker for a fresh PostgreSQL container and a fresh Valkey container, on random free ports, migrates the database, and hands the addresses to the tests. When the test run ends, the containers are deleted. The containers start once per test run, so all the integration tests together take about ten seconds. If Docker isn't running, these tests are **skipped** with a clear message, rather than failed.

### Testing a web app without a network

httpx's **`ASGITransport`** connects an HTTP client straight to an ASGI app (§4.8): requests go from the test into the app as Python calls, with no port, no server, and no network. The integration tests run the API *and* the inference service this way, in one process, while PostgreSQL and Valkey run in their containers.

Async test functions need an event loop to run in. `@pytest.mark.anyio` asks the **AnyIO** pytest plugin to provide one, so a test can simply be an `async def` and `await` the API.

## 4.15 TypeScript: JavaScript with types

Web pages run **JavaScript** (§0.10): it is the one language every browser understands, and with **Node.js** it runs on servers too. JavaScript is flexible — perhaps too flexible. Nothing stops code from passing text where a number was meant, or from reading a property that doesn't exist; such mistakes only show up when the code runs, in front of a user.

**TypeScript** is JavaScript with **types** added. You describe what each value is meant to be, and the TypeScript compiler checks every line *before* the code runs — exactly as mypy does for Python (§4.3). Then it removes the types, and what remains is ordinary JavaScript.

```ts
function greet(name: string, age: number): string {
  return `Hello ${name}, you are ${age}`;
}
greet("Asha", "twelve");   // ✗ error before running: "twelve" is not a number
```

### The JavaScript you'll meet in this book

| You write | It means |
| :-- | :-- |
| `const x = 1;` / `let y = 2;` | a name for a value; `const` can't be reassigned, `let` can |
| `(a, b) => a + b` | an **arrow function**: a short way to write a function |
| `` `Hello ${name}` `` | a **template literal**: text with values put in |
| `const { id, status } = session;` | **destructuring**: take properties out into their own names |
| `{ ...defaults, policy: "x" }` | **spread**: copy all properties, then change some |
| `session?.id` | **optional chaining**: `undefined` instead of a crash if `session` is missing |
| `value ?? "default"` | **nullish coalescing**: the right side if the left is `null` or `undefined` |
| `x ??= y` | assign `y` only if `x` is `null` or `undefined` |
| `a === b` | **strict equality**: equal, with no conversion (`1 === "1"` is false) |
| `import { x } from "./y.js"` / `export` | **modules**: share code between files |

### The types you'll meet

| You write | It means |
| :-- | :-- |
| `string`, `number`, `boolean` | text, any number, true or false |
| `interface User { name: string; age?: number }` | an **interface**: the shape of an object; `?` marks optional parts |
| `type Ending = …` | a **type alias**: a name for any type |
| `function first<T>(list: T[]): T` | a **generic**: `T` stands for whatever type the caller uses |
| `unknown` | "could be anything — check before using it": TypeScript's safest type |
| `(value: unknown): value is string` | a **type guard**: a check that teaches TypeScript what a value is |
| `[1, 2] as const` | "this will never change": keep the exact values as types |
| `readonly`, `#secret` | can't be changed after creation; truly private to a class |

**Unions** are written with a vertical bar: `string | null` means text *or* nothing, and `"pass" | "fail"` allows exactly those two texts — any other value is an error before the code runs.

One pattern matters more than the rest in this book: the **discriminated union**.

```ts
type Stage = { kind: "loading" } | { kind: "camera"; tip: string | null };
if (stage.kind === "camera") {
  show(stage.tip);   // allowed: TypeScript knows this is the camera stage
}
```

Each shape carries a `kind`. Checking it tells TypeScript exactly which shape it has, so impossible combinations can't even be written (`verify-flow.tsx`).

### Waiting for things: promises, `async` and `await`

A **Promise** is a value that will arrive later: an answer from a server, a photo from the camera. An `async` function always returns a promise, and inside it `await` pauses until a promise comes true — without freezing the page. It is the same idea as Python's `async`/`await` (§4.8), with the browser's event loop doing the juggling.

### Strict settings, and TypeScript 7

The project's settings (`packages/config/tsconfig.base.json`, §5.0.4) switch on TypeScript's strictest checks, plus two extra ones: `noUncheckedIndexedAccess` (a list position or dictionary key might be missing — handle it) and `exactOptionalPropertyTypes` (an optional property that's left out is not the same as one set to `undefined`). They make the code a little longer, and catch whole families of bugs.

The project uses **TypeScript 7**, the version whose compiler was rewritten from JavaScript into the Go language. It checks code about ten times faster than before. It was new enough that Phase 1 *tested* whether Next.js could work with it, rather than assuming — and it could, so no fallback was needed (§5.1.4).

## 4.16 React: pages made of components

Writing a page as one giant file of HTML quickly becomes unmanageable. **React** lets you build pages from **components**: small functions that each draw one part of the page, and combine like building blocks.

```tsx
function Greeting({ name }: { name: string }) {
  return <p className="hello">Hello, {name}!</p>;
}
// …and then, elsewhere: <Greeting name="Asha" />
```

The HTML-like lines are **JSX**: inside a `.tsx` file, you write tags, and React turns them into real page elements. Three differences from HTML: `className` instead of `class`; `{…}` to put a JavaScript value into the page; and every tag must be closed (`<br />`).

The values a component receives, like `name` above, are its **props**. A special prop, `children`, holds whatever is written *between* its tags — that is how `<Shell>…</Shell>` wraps a page.

### Hooks: memory and timing for components

A component is just a function, called again every time the page must be redrawn. To remember things between calls, and to do things at the right moment, it uses **hooks** — functions whose names start with `use`:

| Hook | What it's for | Example in this book |
| :-- | :-- | :-- |
| `useState` | a value that, when changed, **redraws** the component | the verify flow's current stage |
| `useRef` | a box that keeps a value **without** redrawing | the camera's stream; the `<video>` element |
| `useEffect` | do something **after** drawing, and undo it later | open the camera, and switch it off when the screen goes away |
| `useCallback` | keep the **same** function between redraws | the camera's error callback |

An effect returns a **cleanup** function, which React calls when the component disappears; the effect's **dependency list** says when it must run again. Getting these right is what keeps a camera from staying on after its screen has gone.

!!! kid "Explain like I'm six — a puppet show"
    Each puppet (a component) knows how to act its own part. The puppeteer (React) decides when each puppet appears. When something in the story changes (state), the puppeteer redraws just the scenes that changed — and when a puppet leaves the stage, it puts its props away (cleanup) so the next scene starts tidy.

**Strict Mode.** In development, React deliberately runs effects twice — set up, clean up, set up again — to expose effects that misbehave when repeated. The verify page met exactly that: it reads a one-time secret from the address, and had to be written so that a second run still works (`verify-flow.tsx`).

## 4.17 Next.js: one framework for server and browser

React draws components; a real website needs much more around them — pages at addresses, data from servers, builds, security headers. **Next.js** is a framework that provides all of it (ADR-0012).

### Folders are addresses

In Next.js's **App Router**, the folders inside `app/` *are* the website's addresses, and special file names say what each file does:

| File | Role | Example |
| :-- | :-- | :-- |
| `page.tsx` | the page at that folder's address | `app/cellar/page.tsx` → `/cellar` |
| `layout.tsx` | a frame around every page below it | the `<html>` and `<body>` of a whole app |
| `[name]/` | a **dynamic** part of the address | `app/v/[sessionId]/` → `/v/vs_01JA…` |
| `route.ts` | code that answers requests directly, with no page | the shop's `/age-check/complete` |
| `error.tsx` | what to show if a page fails | the shop's "couldn't start" page |

### Server components and client components

By default, a Next.js component is a **server component**: it runs on the server, and only its finished HTML is sent to the browser. It can read cookies and secrets, and costs the browser nothing.

A file that starts with `"use client"` holds **client components**: they are sent to the browser as JavaScript and run there, so they can use state, effects, and browser features such as the camera.

| | Server component | Client component |
| :-- | :-- | :-- |
| Runs | on the server | in the browser |
| Can use secrets, cookies, databases | yes | never |
| Can use the camera, clicks, state | no | yes |
| In this book | the shop's pages; the verify page's outer page | the verify flow and camera screen |

This split is a security tool as much as a speed tool: the shop's API key is only ever touched by server code, so no browser could ever receive it.

### Server actions and route handlers

A **server action** — a function in a file that starts with `"use server"` — can be attached to a form. Pressing the button runs the function *on the server*. The shop's "Verify my age to enter" button works this way, which is why it can use the secret key.

A **route handler** (`route.ts`) answers requests directly — the shop's return address uses one, because it only checks things and redirects.

### Building and running

`next build` makes an optimised **production build**, and reports each address as **static** (○, prepared in advance) or **dynamic** (ƒ, drawn for each request — needed for anything that reads cookies). `next start` serves that build; `next dev` serves a development version that rebuilds whenever a file changes. Next.js 16 builds with **Turbopack**, its fast bundler.

Settings come from environment variables. Only those whose names start with `NEXT_PUBLIC_` are built into the browser's code; all others stay on the server.

!!! alt "Alternatives considered"
    **React Router** (formerly Remix) is excellent for server-rendered React too, with a smaller ecosystem. **SvelteKit** is lighter, but means leaving React's huge community of components and developers. **Astro** shines for mostly-static sites, and the verify page is an interactive app. Next.js's server/client split, its server actions, and its maturity fit Dwarpal best (ADR-0012).

## 4.18 Tailwind CSS: styling with small classes

**CSS** describes how a page looks (§0.10). The traditional way is to invent a class name for each element, and describe its look in a separate stylesheet. **Tailwind CSS** turns this around: it provides small **utility classes**, each doing one thing, which you write directly on the element.

```tsx
<button className="rounded-2xl bg-brand-500 px-5 py-3.5 font-semibold hover:bg-brand-400">
```

| Class | Means |
| :-- | :-- |
| `p-6`, `px-5`, `mt-8` | padding all round / left and right; margin on top (in steps of 0.25 rem) |
| `text-2xl`, `font-semibold` | text size; boldness |
| `bg-white/85` | a white background at 85 % opacity |
| `rounded-3xl`, `border` | rounded corners; a thin border |
| `flex`, `grid`, `items-center` | layout: rows, grids, centring |
| `sm:p-8` | only on screens at least 640 pixels wide |
| `dark:bg-zinc-950` | only in dark mode |
| `hover:…`, `focus-visible:…`, `disabled:…` | only in that state |
| `motion-safe:animate-rise` | only if the visitor hasn't asked for reduced motion |
| `bg-[radial-gradient(…)]` | an **arbitrary value**: anything Tailwind has no name for |

Tailwind reads the code, and writes CSS for *exactly* the classes in use — no forgotten styles pile up. Version 4 is configured in CSS itself: an `@theme` block in the stylesheet defines **design tokens** — the brand colour, the fonts, the animations — and each token becomes a class (`globals.css`).

The obvious cost is long lists of classes. This project gives the most repeated ones a name in code instead — `card`, `primaryButton` — so every screen shares them (`shell.tsx`).

## 4.19 The camera in a web page

A web page can use the camera only with the person's permission, and only on a **secure** page: HTTPS, or `localhost` during development (§0.9).

1. **Ask.** `navigator.mediaDevices.getUserMedia({ video: … })` asks the browser for the camera. The browser shows its own permission prompt; the page can't fake or skip it. If the person refuses, the request fails with a `NotAllowedError`.
2. **Show.** The answer is a **MediaStream** — a live flow of frames. Given to a `<video>` element (`video.srcObject = stream`), it plays as a live preview.
3. **Capture.** To take a photo, the page draws the video's current frame onto a **canvas** — an invisible drawing surface in memory — and asks the canvas for a JPEG (`canvas.toBlob(…, "image/jpeg", 0.85)`).
4. **Switch off.** Each stream is made of **tracks**; stopping every track switches the camera off, and its light with it.

The verify page adds a few habits of its own: the camera starts only after the person presses a button; the preview is mirrored (people expect a mirror) while the photos are not; and the camera is switched off the instant the burst is taken — before the upload even begins (`camera.ts`, `camera-view.tsx`).

The verify page's **Permissions-Policy** header allows the camera on its own pages only, and forbids the microphone and location outright (`next.config.ts`).

## 4.20 Testing JavaScript: Vitest and Playwright

The JavaScript side has the same pyramid of tests as the Python side (§4.14):

### Unit tests with Vitest

**Vitest** runs TypeScript tests directly and fast. Its building blocks read almost like sentences:

```ts
describe("tipFor", () => {
  it("gives the tip for the first reason it knows", () => {
    expect(tipFor(["too_dark"])).toMatch(/too dark/);
  });
});
```

When the code under test talks to the network, the test hands it a **fake**: a pretend `fetch` that records each request and answers instantly (`client.test.ts`), or the global `fetch` swapped out with `vi.stubGlobal` (`flow-api.test.ts`). The tests then check both what was *sent* and what was *understood*.

### End-to-end tests with Playwright

**Playwright** drives real browsers — Chromium, Firefox and WebKit — from test code: open this page, press that button, check that heading.

- **Find things like a person does**: `page.getByRole("button", { name: "Take photos" })`. A test written this way survives redesigns, and only works if the page is properly labelled for screen readers.
- **Wait automatically**: `await expect(heading).toBeVisible()` keeps looking until the heading appears (5 seconds by default), so tests needn't guess how long anything takes.
- **Start the system**: its `webServer` setting starts every service the test needs and waits until each answers.
- **Record failures**: a **trace** — a step-by-step recording with screenshots, network requests and page states — is kept for every failed test.

The camera is the hard part: there is no face in front of a CI server. Chromium can play a **video file as a fake camera** (`--use-file-for-fake-video-capture`), and the test makes that video from the project's public-domain test portrait (`make_fake_camera.py`). So the same "person" sits in front of the camera on every run, everywhere.
