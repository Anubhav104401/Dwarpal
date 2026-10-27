---
fingerprint: 8ad209dfa0f972fb
---
`tasks.py` gives every project check a short name, and runs it the same way on Windows, macOS and Linux. `uv run tasks.py check` is the single command that runs everything CI runs (§4.7).

@@ 1-12
**The docstring** doubles as the **help text**: line 165 prints it whenever the command is used wrongly. Each line shows one task and what it does.

The usage lines start at the left edge. Ruff's formatter removed their indentation, because a docstring's common indentation is treated as layout, not content. The printed help looks the same either way.

The `test` line says what the task runs: the services and libraries, then the ML package — in two separate processes (below). Phase 7 added three tasks that check the system from the outside: `scan`, `zap` and `load`.

@@ 14
`from __future__ import annotations` — the same type-hint setting used in every Python file of the project.

@@ 16
`os` — to read the `UV` environment variable.

@@ 17
`import subprocess` — Python's tool for **starting other programs** and waiting for them to finish. Every task here is really another program: ruff, mypy, pytest, the book builder.

@@ 18
`import sys` — gives access to `sys.executable`, `sys.argv` (the words typed on the command line) and `sys.exit`.

@@ 19
`from pathlib import Path` — the path object, used to find the project root.

@@ 21
`ROOT = Path(__file__).resolve().parent` — the folder this file lives in, which is the project root. Every task runs from here, wherever you start it.

@@ 22
`PYTHON = sys.executable` — the full path of the Python interpreter running this script.

!!! why "Why run tools as `python -m ruff` instead of just `ruff`?"
    `uv run` starts this script with the project's own Python, from `.venv`. Running each tool as "*this* Python, module `ruff`" (`-m` means *run a module*) guarantees that every task uses the exact tool versions in the project's environment, never some other copy that happens to be installed on the computer.

@@ 23
**`UV`** — the uv program: `uv` if it's on the `PATH`, or wherever the `UV` environment variable says (on the owner's computer it isn't on the `PATH`).

@@ 24-25
**`TOOL`** — the start of a command that runs a tool **in a throwaway environment of its own**: `uv tool run --from pip-audit==2.10.1 pip-audit`. The scanners and Locust pull in dozens of libraries with their own exact pins; installed into the project they could clash with its own. `--exclude-newer "7 days"` keeps the 7-day cooldown for everything they bring.

@@ 26
**`SCAN`** — the folder where every scan and load test leaves its output (`.scan/`, ignored by Git).

@@ 28-39
**`TASKS` — the table of tasks.** The type hint `dict[str, list[list[str]]]` reads: "a dict from a task name to a list of commands, where each command is a list of words".

!!! key "Key idea — commands as lists, not strings"
    `["ruff", "check", "."]` instead of `"ruff check ."`. A list is handed to the operating system word by word, with **no shell** in between. Nothing can be misread: a space inside a path stays inside the path, and no stray character can sneak in an extra command. This is the safe way to run programs, and it is why Ruff's warning about subprocess calls (S603) is turned off for this file only (§5.0.2).

The tasks:

- `lint` — Ruff's linter, then its formatter in *check-only* mode;
- `format` — apply formatting and the safe automatic fixes;
- `typecheck` — mypy (it reads its settings from `pyproject.toml`);
- `test` — pytest, **twice**: first the book's, the services' and the libraries' tests, then the ML package's. The comment gives the reason. Once, in five full runs, Python crashed while importing a PyTorch library into a process that had already loaded OpenCV's and ONNX Runtime's native code — a clash between compiled libraries, not a failing test. In separate processes they never meet. (Giving pytest folders on the command line overrides the `testpaths` list in `pyproject.toml`.)
- `book` — the book builder in strict mode.

@@ 40
**`check` is built from the others** by joining their command lists with `+`: lint, then types, then tests, then the book. Cheap checks come first, so mistakes are reported as early as possible.

@@ 41-42
**`scan`** (Phase 7, decision D9) — three scanners, run in turn. First **pip-audit**, which compares each Python package's exact version against public databases of known flaws. It needs a plain list of them…

@@ 43-55
…so `uv export` writes one, from the lockfile exactly as it stands (`--frozen`): every package of every member and group, without hashes, and without the workspace's own packages, which aren't on PyPI to be checked.

@@ 56
Run pip-audit on that list: `--disable-pip` and `--no-deps` mean "check exactly these, install nothing, resolve nothing".

@@ 57-65
**Semgrep**, which reads the source code looking for patterns of known mistakes (an SQL query built from user text, a disabled certificate check, a hard-coded secret). `p/default` is its standard rule set, fetched from Semgrep's registry; `--metrics=off` sends nothing back; `--error` makes any finding fail the step.

@@ 66-76
Folders Semgrep should skip: installed packages, the datasets, the book's snapshots, and the web app's copied third-party files.

@@ 77-79
**Trivy** looks for three things at once: known flaws in the lock files' versions, secrets committed by mistake, and unsafe settings in container files. Scanning the working folder through Docker on Windows took over 15 minutes, because it also holds models, datasets and installed packages. So a script first copies just the files Git tracks into `.scan/committed`.

@@ 80-98
Then Trivy runs in its own container (`aquasec/trivy:0.76.0`), with that copy mounted read-only, and a named Docker volume to keep its vulnerability database between runs (it downloads about half a gigabyte the first time). Only `HIGH` and `CRITICAL` findings are reported, and any makes the step fail (`--exit-code 1`).

@@ 99
End of the scan steps.

@@ 100-103
**`zap`** — **OWASP ZAP**, a scanner that looks at a running site from outside, as an attacker would see it. It runs in Docker, with `.scan` mounted so its reports land there. The servers must already be running and reachable from Docker: `host.docker.internal` is how a container reaches the computer it runs on.

@@ 104-105
The **baseline** scan of the web app: ZAP follows every link from the console's sign-in page and checks each answer passively — headers, cookies, leaked details — without attacking. `-J` saves a JSON report; `-I` means warnings alone don't fail the step.

@@ 106-117
The **API scan**: ZAP reads the published OpenAPI document and sends each operation requests, checking the answers the same way.

@@ 118-137
**`load`** (Phase 7, decision D10) — **Locust**, which simulates many people at once (`infra/load/locustfile.py`): 50 people (`--users`), added 5 a second, for 3 minutes, against the API on this computer, without its web interface (`--headless`), saving the timings as CSV files.

@@ 140-141
**`KEEP_GOING`** — the tasks that run every step even after one fails: for a scan, one scanner's findings shouldn't hide another's.

@@ 144
**`run(name)`** runs one task and returns its **exit code**: 0 means success.

@@ 145-146
Make sure the output folder exists, and start a list of failed steps.

@@ 147
For each command in the task, in order…

@@ 148
…make a readable version for display. `command[1:]` skips the long interpreter path, and `" ".join` glues the words with spaces.

@@ 149
Print it as `> -m ruff check .`. `flush=True` pushes the text out immediately. Otherwise Python might hold it in a buffer, and it would appear *after* the tool's own output, which would be confusing.

@@ 150
**Run the command and wait.**

- `cwd=ROOT` runs it from the project root.
- `check=False` means "don't raise an exception if it fails — we'll look at the result ourselves".
- `.returncode` is the program's exit code.

@@ 151-158
**When a step fails.** Say which, and which exit code. For most tasks, stop at once and pass the code on — there's no point type-checking code that doesn't even pass the linter. For scans, note it and carry on; at the end, report how many steps found problems and fail with code 1.

@@ 159-160
Every command succeeded: say so, and return `0`.

@@ 163
**`main()`** — what happens when you run the file.

@@ 164-166
**Wrong usage** — no task name, too many words, or an unknown task. Print the help (the docstring) and return `2`. By long convention, exit code 2 means "you used the command incorrectly", as opposed to 1, "the work failed".

@@ 167
Otherwise run the requested task. `sys.argv[1]` is the first word after the script name.

@@ 170-171
**The entry point**: run `main()` only when the file is executed directly, and pass its result to `sys.exit`, so CI sees the real exit code.
