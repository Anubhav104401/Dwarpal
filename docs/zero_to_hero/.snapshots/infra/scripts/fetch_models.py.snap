"""Download the third-party model files listed in models/third_party.json and verify their fingerprints.

uv run infra/scripts/fetch_models.py               the files serving, the verify page and the tests need
uv run infra/scripts/fetch_models.py --training    also the pretrained weights used only for training
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(entry: dict[str, str]) -> bool:
    target = MODELS / entry["file"]
    if target.is_file() and sha256_of(target) == entry["sha256"]:
        print(f"present  {entry['name']}")
        return True
    if not entry["url"].startswith("https://"):
        print(f"refused  {entry['name']}: only https downloads are allowed")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    with httpx.stream("GET", entry["url"], follow_redirects=True, timeout=60.0) as response:
        response.raise_for_status()
        with partial.open("wb") as out:
            for chunk in response.iter_bytes():
                out.write(chunk)
    actual = sha256_of(partial)
    if actual != entry["sha256"]:
        partial.unlink()
        print(f"MISMATCH {entry['name']}: expected {entry['sha256']}, got {actual}; file discarded")
        return False
    partial.replace(target)
    print(f"fetched  {entry['name']} -> {target.relative_to(ROOT).as_posix()}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download and verify third-party model files")
    parser.add_argument("--training", action="store_true", help="also fetch weights used only for training")
    args = parser.parse_args(argv)
    manifest = json.loads((MODELS / "third_party.json").read_text(encoding="utf-8"))
    wanted = [entry for entry in manifest["models"] if entry["use"] != "training" or args.training]
    results = [fetch(entry) for entry in wanted]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
