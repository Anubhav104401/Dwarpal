"""Copy what Git tracks into a folder of its own, for scanners that should see only the project's real files.

uv run python infra/scripts/committed_copy.py .scan/committed

Trivy, scanning the working folder through Docker on Windows, crawled for over a quarter of an hour: the folder also
holds model weights, datasets, a test video and installed packages, none of which Git tracks. This copy is the code as
committed or about to be (tracked files, as they are now on disk) — seconds to scan, and exactly what could leak.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(target: Path) -> int:
    shutil.rmtree(target, ignore_errors=True)
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout  # noqa: S607
    names = [name for name in listed.decode("utf-8").split("\0") if name]
    copied = 0
    for name in names:
        source = ROOT / name
        if source.is_file():  # a tracked file deleted but not yet committed is skipped
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied += 1
    print(f"copied {copied} tracked files to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
