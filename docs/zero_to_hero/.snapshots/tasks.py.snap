"""Developer tasks for Dwarpal: one entry point for every check, on every operating system.

uv run tasks.py check       everything CI runs: lint, types, tests, book
uv run tasks.py lint        ruff lint + formatting check
uv run tasks.py format      apply ruff formatting and safe automatic fixes
uv run tasks.py typecheck   mypy in strict mode
uv run tasks.py test        pytest
uv run tasks.py book        build the Zero-to-Hero book in strict mode
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

TASKS: dict[str, list[list[str]]] = {
    "lint": [[PYTHON, "-m", "ruff", "check", "."], [PYTHON, "-m", "ruff", "format", "--check", "."]],
    "format": [[PYTHON, "-m", "ruff", "format", "."], [PYTHON, "-m", "ruff", "check", "--fix", "."]],
    "typecheck": [[PYTHON, "-m", "mypy"]],
    "test": [[PYTHON, "-m", "pytest"]],
    "book": [[PYTHON, "docs/zero_to_hero/build.py", "--strict"]],
}
TASKS["check"] = TASKS["lint"] + TASKS["typecheck"] + TASKS["test"] + TASKS["book"]


def run(name: str) -> int:
    for command in TASKS[name]:
        shown = " ".join(command[1:])
        print(f"\n> {shown}", flush=True)
        code = subprocess.run(command, cwd=ROOT, check=False).returncode
        if code != 0:
            print(f"\n{name}: FAILED at '{shown}' (exit code {code})")
            return code
    print(f"\n{name}: OK")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print(__doc__)
        return 2
    return run(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
