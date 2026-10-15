---
fingerprint: 843fb0835ebbfca7
---
The **root `pyproject.toml`** is the control centre of the Python side of the project. It is not a package itself — Python packaging calls this a *virtual* workspace root. It does three jobs:

1. names the **workspace members** — our five Python packages;
2. lists the **developer tools**, with exact versions;
3. holds the **settings** for those tools: Ruff, mypy, pytest.

@@ 1-3
Comments explaining what this file is. In TOML, `#` starts a comment. The first line uses a real long dash `—`, which is fine because the file is UTF-8.

@@ 5
`[tool.uv]` — settings for **uv** itself. Every tool reads its own `[tool.<name>]` table and ignores the others.

@@ 6
`required-version = ">=0.13.1"` — refuse to run with an older uv. Older versions might resolve or install things differently, so this prevents "it works with my uv" surprises.

@@ 7
`default-groups = ["dev", "docs"]` — when uv installs the project (`uv sync`, or automatically before `uv run`), include the two dependency groups below. Without this, `uv run` would install only `dev`, and the book's tools would be missing.

@@ 9
`[tool.uv.workspace]` — this file is the root of a **uv workspace**: several packages sharing one lockfile and one environment (§4.2).

@@ 10
`members = [...]` — which folders are workspace packages:

- `services/*` — every folder in `services` (api, inference);
- `libs/*` — every folder in `libs` (contracts, vision);
- `ml`.

Each member has its own `pyproject.toml`.

@@ 12
`[dependency-groups]` — named groups of libraries that are needed for *working on* the project, but are never part of any package that gets shipped. This table is a recent official Python standard (PEP 735).

@@ 13-17
The **`dev` group** — the quality robots of §4.3, each pinned to an exact version with `==`:

- `mypy` 2.4.0 — the type checker;
- `pytest` 9.1.1 — the test runner;
- `ruff` 0.17.0 — the linter and formatter.

@@ 18-23
The **`docs` group** — what the book builder needs:

- `markdown` 3.11.1 and `pygments` 2.21.0 — the converter and the highlighter (Part X);
- `types-markdown` and `types-pygments` — **type stubs**: files that describe the *types* used by a library which doesn't ship them itself, so mypy can check our calls into it. Their version numbers end with a date, which is how the typeshed project numbers its stubs.

@@ 25
`[tool.ruff]` — settings for Ruff (both the linter and the formatter).

@@ 26
`line-length = 120` — the longest line allowed. The common default of 88 is designed for narrow screens. 120 fits a modern screen, and still fits side by side with the explanation column in this book.

@@ 27
`target-version = "py313"` — the oldest Python our code must run on. Ruff then only suggests syntax that Python 3.13 understands.

@@ 28
`include = ["*.py", "*.pyi", "**/pyproject.toml"]` — which files Ruff looks at: Python code, type stubs (`.pyi`), and `pyproject.toml` files.

!!! real "Real world — why this line exists"
    Ruff 0.17 also formats Python code *inside Markdown files* by default. On its first run, it quietly re-aligned the comments in a code example in a design document. In this project, Markdown holds **teaching examples** that must stay exactly as written, so Ruff is now limited to real Python files.

@@ 29
`extend-exclude = [...]` — never check the book's `.snapshots` folder, which holds *copies* of code from the last stamp (§X.6). Checking copies would report every warning twice.

@@ 31
`[tool.ruff.lint]` — settings for the linter part.

@@ 32
`select = [...]` — the rule families switched on: pycodestyle, Pyflakes, isort, bugbear, pyupgrade, simplify, comprehensions, pathlib, bandit security, naming, Ruff's own, datetime, performance, return. §4.3 has a table with an example for each.

@@ 34
`[tool.ruff.lint.per-file-ignores]` — specific rules switched off for specific files, each for a stated reason.

@@ 35
`"tasks.py" = ["S603"]` — rule S603 warns whenever a program starts another program (`subprocess`). That is risky when the command is built from untrusted text, because someone could sneak in extra commands. In `tasks.py` every command is a fixed list written in the file itself, and no shell is involved, so the warning is a false alarm there — and only there.

@@ 36
`"**/tests/**" = ["S101"]` — rule S101 warns about `assert`, because Python can be told to *skip* assert statements. That makes them unsafe for checks in real code. In tests, `assert` *is* the checking mechanism, and pytest never skips it.

@@ 38
`[tool.mypy]` — settings for the type checker.

@@ 39
`python_version = "3.13"` — check the code as Python 3.13 would see it.

@@ 40
`strict = true` — switch on every strictness option. For example: every function must have type hints, no silent `Any`, and every generic type such as `dict` must say what it holds.

@@ 41
`warn_unreachable = true` — warn about code that can never run. This usually means a condition is wrong.

@@ 42
`explicit_package_bases = true` — work out each file's module name from the folders listed in `mypy_path`. This is needed because our packages live in separate `src` folders.

@@ 43
`exclude = [...]` — a **regular expression** for paths mypy must skip. `[/\\]` means "a forward slash or a backslash", so the pattern matches `.snapshots` as a folder on both Linux and Windows. The single quotes make it a *literal* TOML string, so the backslashes reach mypy exactly as typed.

@@ 44
`mypy_path` — where mypy should look for our packages' source code: each package's `src` folder, plus the book folder (for `build.py`). The comma-separated form works on every operating system.

@@ 45-53
`files = [...]` — what mypy checks when you simply run `mypy`:

- the task runner;
- the book builder and its tests;
- every package's source folder.

@@ 55
`[tool.pytest.ini_options]` — settings for pytest (the name is historical: pytest settings once lived only in `.ini` files).

@@ 56
`minversion = "9.0"` — refuse to run with a pytest older than 9.0.

@@ 57
`testpaths` — where pytest looks for tests when run without arguments: the book's tests, and later each package's tests.

@@ 58
`pythonpath = ["docs/zero_to_hero"]` — add the book folder to Python's search path during tests, so `test_build.py` can simply write `import build`.

@@ 59
`addopts` — options added to every pytest run:

- `-ra` — print a short summary of every test that didn't simply pass (skipped, failed, …);
- `--strict-markers` — a misspelled test label is an error, not silently ignored;
- `--strict-config` — a misspelled setting in this file is an error;
- `--import-mode=importlib` — import test files without modifying Python's search path, so tests in different packages can't clash by having the same file name.

@@ 60
`xfail_strict = true` — some tests can be marked "expected to fail" (for a known bug). If such a test unexpectedly *passes*, treat that as a failure, so the outdated marker gets noticed and removed.
