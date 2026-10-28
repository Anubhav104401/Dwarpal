"""Developer tasks for Dwarpal: one entry point for every check, on every operating system.

uv run tasks.py check       everything CI runs: lint, types, tests, book
uv run tasks.py lint        ruff lint + formatting check
uv run tasks.py format      apply ruff formatting and safe automatic fixes
uv run tasks.py typecheck   mypy in strict mode
uv run tasks.py test        pytest: the services and libraries, then the ML package
uv run tasks.py book        build the Zero-to-Hero book in strict mode
uv run tasks.py scan        security scans: pip-audit, Semgrep and Trivy (downloads their databases and rules)
uv run tasks.py zap         OWASP ZAP's baseline scans of the web app and the API, against servers already running
uv run tasks.py load        the Locust load test, against servers already running (see infra/load/locustfile.py)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
UV = os.environ.get("UV", "uv")
# The scanners and Locust run as separate tools, never installed into the project; the 7-day cooldown still applies.
TOOL = [UV, "tool", "run", "--exclude-newer", "7 days", "--from"]
SCAN = ROOT / ".scan"

TASKS: dict[str, list[list[str]]] = {
    "lint": [[PYTHON, "-m", "ruff", "check", "."], [PYTHON, "-m", "ruff", "format", "--check", "."]],
    "format": [[PYTHON, "-m", "ruff", "format", "."], [PYTHON, "-m", "ruff", "check", "--fix", "."]],
    "typecheck": [[PYTHON, "-m", "mypy"]],
    # Two runs: the ML tests load PyTorch, which once crashed while being imported into a process that had already
    # loaded OpenCV's and ONNX Runtime's native libraries. Each in its own process, they can't meet.
    "test": [
        [PYTHON, "-m", "pytest", "docs/zero_to_hero/tests", "services", "libs"],
        [PYTHON, "-m", "pytest", "ml"],
    ],
    "book": [[PYTHON, "docs/zero_to_hero/build.py", "--strict"]],
}
TASKS["check"] = TASKS["lint"] + TASKS["typecheck"] + TASKS["test"] + TASKS["book"]
TASKS["scan"] = [
    # pip-audit checks the exact locked versions; the workspace's own packages aren't on PyPI, so they're left out.
    [
        UV,
        "export",
        "--frozen",
        "--all-packages",
        "--all-groups",
        "--no-hashes",
        "--no-emit-workspace",
        "--format",
        "requirements-txt",
        "-o",
        str(SCAN / "requirements.txt"),
    ],
    [*TOOL, "pip-audit==2.10.1", "pip-audit", "--disable-pip", "--no-deps", "-r", str(SCAN / "requirements.txt")],
    [
        *TOOL,
        "semgrep==1.182.0",
        "semgrep",
        "scan",
        "--config",
        "p/default",
        "--metrics=off",
        "--error",
        "--exclude",
        "node_modules",
        "--exclude",
        ".venv",
        "--exclude",
        ".datasets",
        "--exclude",
        ".snapshots",
        "--exclude",
        "apps/web/public",
        "--exclude",
        ".scan",
        # Reviewed 28 Oct and left out, each for a reason: the migrations write fixed SQL from constant lists of table
        # names; pinning memory is performance advice; and the cooldown rule misses ours (`exclude-newer`, pyproject).
        "--exclude",
        "services/api/src/dwarpal_api/migrations",
        "--exclude-rule",
        "trailofbits.python.automatic-memory-pinning.automatic-memory-pinning",
        "--exclude-rule",
        "package_managers.uv.uv-missing-dependency-cooldown.uv-missing-dependency-cooldown",
    ],
    # Trivy reads the lock files (known flaws), looks for committed secrets, and checks container files, in a copy of
    # just the files Git tracks: the working folder also holds models, datasets and packages, which took it 15 minutes.
    [PYTHON, "infra/scripts/committed_copy.py", str(SCAN / "committed")],
    [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{SCAN / 'committed'}:/src:ro",
        "-v",
        "dwarpal-trivy-cache:/root/.cache",
        "aquasec/trivy:0.76.0",
        "fs",
        "--quiet",
        "--scanners",
        "vuln,secret,misconfig",
        "--severity",
        "HIGH,CRITICAL",
        "--exit-code",
        "1",
        "/src",
    ],
]
# OWASP ZAP's baseline scans: the web app's pages (spidered, checked without attacking) and every API operation in the
# published document. Both servers must be running, listening beyond this computer's loopback (Docker reaches them
# as host.docker.internal): the API with `--host 0.0.0.0`, the web app with `--hostname 0.0.0.0`.
ZAP = ["docker", "run", "--rm", "-v", f"{SCAN}:/zap/wrk:rw", "zaproxy/zap-stable:20261016"]
TASKS["zap"] = [
    [*ZAP, "zap-baseline.py", "-t", "http://host.docker.internal:3000/console", "-J", "zap-web.json", "-I"],
    [
        *ZAP,
        "zap-api-scan.py",
        "-t",
        "http://host.docker.internal:8000/openapi.json",
        "-f",
        "openapi",
        "-J",
        "zap-api.json",
        "-I",
    ],
]
TASKS["load"] = [
    [
        *TOOL,
        "locust==2.46.7",
        "locust",
        "-f",
        "infra/load/locustfile.py",
        "--headless",
        "--users",
        "50",
        "--spawn-rate",
        "5",
        "--run-time",
        "3m",
        "--host",
        "http://127.0.0.1:8000",
        "--csv",
        str(SCAN / "load"),
    ],
]


# Scans run to the end even when one finds something, so a single run shows every scanner's findings.
KEEP_GOING = {"scan", "zap"}


def run(name: str) -> int:
    SCAN.mkdir(exist_ok=True)
    failed: list[str] = []
    for command in TASKS[name]:
        shown = " ".join(command[1:])
        print(f"\n> {shown}", flush=True)
        code = subprocess.run(command, cwd=ROOT, check=False).returncode
        if code != 0:
            print(f"\n{name}: FAILED at '{shown}' (exit code {code})")
            if name not in KEEP_GOING:
                return code
            failed.append(shown)
    if failed:
        print(f"\n{name}: {len(failed)} step(s) found problems or failed")
        return 1
    print(f"\n{name}: OK")
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in TASKS:
        print(__doc__)
        return 2
    return run(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
