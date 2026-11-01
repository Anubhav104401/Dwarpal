---
fingerprint: 03fbac38253c1b4a
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

@@ 8-9
**A 7-day cooldown** (added in Phase 2): `exclude-newer = "7 days"` tells uv to ignore every release published in the last seven days, as the JavaScript side already does (`pnpm-workspace.yaml`, §5.1.4). Brand-new releases are where supply-chain attacks and fresh bugs show up first; a week gives the world time to notice. Turning it on caught six pins chosen before the rule existed — FastAPI, Hypothesis, Markdown, NumPy, Pydantic and pydantic-settings — and each was stepped back to its newest release that was at least a week old. The whole test suite passed unchanged.

@@ 10-12
**`override-dependencies`** (Phase 7, decision D15, 1 Nov 2026) — versions uv must use wherever these packages appear in the tree, whatever the package asking for them wanted. The security scanners (pip-audit and Trivy, §7) found known flaws in the versions our dependencies pulled in; these are the fixed releases. Pillow, the image library, jumps a major version to 13; it comes in through torchvision, so only training uses it, and the ML tests ran again after the change.

@@ 14
`[tool.uv.workspace]` — this file is the root of a **uv workspace**: several packages sharing one lockfile and one environment (§4.2).

@@ 15
`members = [...]` — which folders are workspace packages:

- `services/*` — every folder in `services` (api, inference);
- `libs/*` — every folder in `libs` (contracts, vision);
- `ml`.

Each member has its own `pyproject.toml`. 

And since Phase 9, `packages/sdk-python` — the Python SDK (§5.9.1), a workspace member so its tests run with the rest.

@@ 17
`[dependency-groups]` — named groups of libraries that are needed for *working on* the project, but are never part of any package that gets shipped. This table is a recent official Python standard (PEP 735).

@@ 18-29
The **`dev` group** — tools for developers, each pinned to an exact version with `==`:

- `httpx` 0.28.1 — an HTTP client library (added in Phase 1). Tests use it to call our services without a real network, and the model-download script uses it to fetch model files;
- `hypothesis` 6.168.5 — **property-based testing** (added in Phase 1). Instead of a few examples picked by hand, a test states a *rule* that must always hold, and Hypothesis invents hundreds of inputs trying to break it (§4.14);
- `mypy` 2.4.0 — the type checker;
- `onnx` 1.23.2 — builds a tiny ONNX model for the inference service's tests (added in Phase 2);
- `pytest` 9.1.1 — the test runner;
- `ruff` 0.17.0 — the linter and formatter;
- `scipy-stubs` — type stubs for SciPy, the maths library the risk-control code uses (added in Phase 2), so mypy can check every call into it;
- `testcontainers` 4.15.0 — starts real, throwaway databases in Docker for the tests and removes them afterwards (added in Phase 1, §4.14);
- `types-docker` — **type stubs** (explained in the next note) for the `docker` library, which the database tests use to ask whether Docker is running. mypy now checks the tests too (see `files` below), so it needs to know that library's types.

`schemathesis` 4.31.1 (Phase 4) — **contract testing**: it reads the API's published document, generates thousands of requests from it, and checks every answer against what the document promises (§5.4.5).

@@ 30-35
The **`docs` group** — what the book builder needs:

- `markdown` 3.11 and `pygments` 2.21.0 — the converter and the highlighter (Part X);
- `types-markdown` and `types-pygments` — **type stubs**: files that describe the *types* used by a library which doesn't ship them itself, so mypy can check our calls into it. Their version numbers end with a date, which is how the typeshed project numbers its stubs.

@@ 37
`[tool.ruff]` — settings for Ruff (both the linter and the formatter).

@@ 38
`line-length = 120` — the longest line allowed. The common default of 88 is designed for narrow screens. 120 fits a modern screen, and still fits side by side with the explanation column in this book.

@@ 39
`target-version = "py313"` — the oldest Python our code must run on. Ruff then only suggests syntax that Python 3.13 understands.

@@ 40
`include = ["*.py", "*.pyi", "**/pyproject.toml"]` — which files Ruff looks at: Python code, type stubs (`.pyi`), and `pyproject.toml` files.

!!! real "Real world — why this line exists"
    Ruff 0.17 also formats Python code *inside Markdown files* by default. On its first run, it quietly re-aligned the comments in a code example in a design document. In this project, Markdown holds **teaching examples** that must stay exactly as written, so Ruff is now limited to real Python files.

@@ 41
`extend-exclude = [...]` — never check the book's `.snapshots` folder, which holds *copies* of code from the last stamp (§X.6). Checking copies would report every warning twice.

@@ 42
`src = [...]` — where *our own* code lives: each package's `src` folder, plus the book folder. Ruff's import sorter uses this list to tell **first-party** imports (our `dwarpal_*` packages) from **third-party** ones (FastAPI, NumPy, …), and it groups them separately. Without the line, Ruff took `dwarpal_contracts` for an outside library and mixed it in with FastAPI. The list mirrors mypy's `mypy_path` below, so both tools agree on what "ours" means.

@@ 44
`[tool.ruff.lint]` — settings for the linter part.

@@ 45
`select = [...]` — the rule families switched on: pycodestyle, Pyflakes, isort, bugbear, pyupgrade, simplify, comprehensions, pathlib, bandit security, naming, Ruff's own, datetime, performance, return. §4.3 has a table with an example for each.

@@ 47
`[tool.ruff.lint.per-file-ignores]` — specific rules switched off for specific files, each for a stated reason.

@@ 48
`"tasks.py" = ["S603"]` — rule S603 warns whenever a program starts another program (`subprocess`). That is risky when the command is built from untrusted text, because someone could sneak in extra commands. In `tasks.py` every command is a fixed list written in the file itself, and no shell is involved, so the warning is a false alarm there — and only there.

@@ 49
`"**/tests/**" = ["S101"]` — rule S101 warns about `assert`, because Python can be told to *skip* assert statements. That makes them unsafe for checks in real code. In tests, `assert` *is* the checking mechanism, and pytest never skips it.

@@ 51
`[tool.mypy]` — settings for the type checker.

@@ 52
`python_version = "3.13"` — check the code as Python 3.13 would see it.

@@ 53
`strict = true` — switch on every strictness option. For example: every function must have type hints, no silent `Any`, and every generic type such as `dict` must say what it holds.

@@ 54
`warn_unreachable = true` — warn about code that can never run. This usually means a condition is wrong.

@@ 55
`explicit_package_bases = true` — work out each file's module name from the folders listed in `mypy_path`. This is needed because our packages live in separate `src` folders.

@@ 56
`exclude = [...]` — a **regular expression** for paths mypy must skip. `[/\\]` means "a forward slash or a backslash", so the pattern matches `.snapshots` as a folder on both Linux and Windows. The single quotes make it a *literal* TOML string, so the backslashes reach mypy exactly as typed.

@@ 57
`mypy_path` — where mypy should look for our packages' source code: each package's `src` folder, plus the book folder (for `build.py`). The comma-separated form works on every operating system. Since Phase 9 also `packages/sdk-python`, the Python SDK (§5.9.1), and `services/api/tests`, so the type checker finds the test passkey device (§5.9.2).

@@ 58-73
`files = [...]` — what mypy checks when you simply run `mypy`:

- the task runner;
- `infra/scripts` — helper scripts such as the model downloader (added in Phase 1);
- the book builder and its tests;
- every package's source folder (`src`);
- every package's `tests` folder (added in Phase 1; the ML package's in Phase 2).

Why type-check tests? A test with a type mistake can pass **for the wrong reason**. Imagine the check `outcome != "fail"` where `outcome` is, by mistake, a whole response object instead of a piece of text. An object and a text can never be equal, so the check always passes — even when the answer really *was* "fail". mypy's strict mode reports comparisons between things that can never be equal.

When mypy was first pointed at the tests, it found exactly one problem: OpenCV's blur function returns a picture whose type is vaguer than the quality checker expects. It was fixed the same way as in the real code, with `np.asarray(..., dtype=np.uint8)` (§4.9). Since Phase 9 also `packages/sdk-python`, the Python SDK (§5.9.1).

@@ 75-78
**A mypy exception for timm** (added in Phase 2). In strict mode, mypy only accepts names a library explicitly marks as public. timm makes `create_optimizer_v2` and `ModelEmaV3` public in the ordinary Python way but without that marking, so mypy is told to accept them for timm only.

@@ 80-83
**A mypy exception for ONNX** (added in Phase 2): ONNX Runtime ships no type information, and the `onnx` library's is incomplete, so mypy is told not to demand it for these two. Our code's own types are still checked fully.

@@ 85
`[tool.pytest.ini_options]` — settings for pytest (the name is historical: pytest settings once lived only in `.ini` files).

@@ 86
`minversion = "9.0"` — refuse to run with a pytest older than 9.0.

@@ 87
`testpaths` — where pytest looks for tests when run without arguments: the book's tests, then every package under `services`, `libs` and `ml`. Inside those folders pytest collects files whose names start with `test_`. Since Phase 9 also `packages/sdk-python`, the Python SDK (§5.9.1).

@@ 88
`pythonpath` — folders added to Python's search path during tests: the book folder, so `test_build.py` can simply write `import build`; and, since Phase 9, the API's tests folder, so two test files can share `passkey_device.py` (§5.9.2).

@@ 89
`addopts` — options added to every pytest run:

- `-ra` — print a short summary of every test that didn't simply pass (skipped, failed, …);
- `--strict-markers` — a misspelled test label is an error, not silently ignored;
- `--strict-config` — a misspelled setting in this file is an error;
- `--import-mode=importlib` — import test files without modifying Python's search path, so tests in different packages can't clash by having the same file name.

@@ 90
`xfail_strict = true` — some tests can be marked "expected to fail" (for a known bug). If such a test unexpectedly *passes*, treat that as a failure, so the outdated marker gets noticed and removed.
