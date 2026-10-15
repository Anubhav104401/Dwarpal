---
fingerprint: b65855566e18fb42
---
`tasks.py` gives every project check a short name, and runs it the same way on Windows, macOS and Linux. `uv run tasks.py check` is the single command that runs everything CI runs (§4.7).

@@ 1-9
**The docstring** doubles as the **help text**: line 44 prints it whenever the command is used wrongly. Each line shows one task and what it does.

The usage lines start at the left edge. Ruff's formatter removed their indentation, because a docstring's common indentation is treated as layout, not content. The printed help looks the same either way.

@@ 11
`from __future__ import annotations` — the same type-hint setting used in every Python file of the project.

@@ 13
`import subprocess` — Python's tool for **starting other programs** and waiting for them to finish. Every task here is really another program: ruff, mypy, pytest, the book builder.

@@ 14
`import sys` — gives access to `sys.executable`, `sys.argv` (the words typed on the command line) and `sys.exit`.

@@ 15
`from pathlib import Path` — the path object, used to find the project root.

@@ 17
`ROOT = Path(__file__).resolve().parent` — the folder this file lives in, which is the project root. Every task runs from here, wherever you start it.

@@ 18
`PYTHON = sys.executable` — the full path of the Python interpreter running this script.

!!! why "Why run tools as `python -m ruff` instead of just `ruff`?"
    `uv run` starts this script with the project's own Python, from `.venv`. Running each tool as "*this* Python, module `ruff`" (`-m` means *run a module*) guarantees that every task uses the exact tool versions in the project's environment, never some other copy that happens to be installed on the computer.

@@ 20-26
**`TASKS` — the table of tasks.** The type hint `dict[str, list[list[str]]]` reads: "a dict from a task name to a list of commands, where each command is a list of words".

!!! key "Key idea — commands as lists, not strings"
    `["ruff", "check", "."]` instead of `"ruff check ."`. A list is handed to the operating system word by word, with **no shell** in between. Nothing can be misread: a space inside a path stays inside the path, and no stray character can sneak in an extra command. This is the safe way to run programs, and it is why Ruff's warning about subprocess calls (S603) is turned off for this file only (§5.0.2).

The tasks:

- `lint` — Ruff's linter, then its formatter in *check-only* mode;
- `format` — apply formatting and the safe automatic fixes;
- `typecheck` — mypy (it reads its settings from `pyproject.toml`);
- `test` — pytest;
- `book` — the book builder in strict mode.

@@ 27
**`check` is built from the others** by joining their command lists with `+`: lint, then types, then tests, then the book. Cheap checks come first, so mistakes are reported as early as possible.

@@ 30
**`run(name)`** runs one task and returns its **exit code**: 0 means success.

@@ 31
For each command in the task, in order…

@@ 32
…make a readable version for display. `command[1:]` skips the long interpreter path, and `" ".join` glues the words with spaces.

@@ 33
Print it as `> -m ruff check .`. `flush=True` pushes the text out immediately. Otherwise Python might hold it in a buffer, and it would appear *after* the tool's own output, which would be confusing.

@@ 34
**Run the command and wait.**

- `cwd=ROOT` runs it from the project root.
- `check=False` means "don't raise an exception if it fails — we'll look at the result ourselves".
- `.returncode` is the program's exit code.

@@ 35-37
**Stop at the first failure.** Print which task and which command failed, and pass the failing exit code on. There's no point type-checking code that doesn't even pass the linter.

@@ 38-39
Every command succeeded: say so, and return `0`.

@@ 42
**`main()`** — what happens when you run the file.

@@ 43-45
**Wrong usage** — no task name, too many words, or an unknown task. Print the help (the docstring) and return `2`. By long convention, exit code 2 means "you used the command incorrectly", as opposed to 1, "the work failed".

@@ 46
Otherwise run the requested task. `sys.argv[1]` is the first word after the script name.

@@ 49-50
**The entry point**: run `main()` only when the file is executed directly, and pass its result to `sys.exit`, so CI sees the real exit code.
