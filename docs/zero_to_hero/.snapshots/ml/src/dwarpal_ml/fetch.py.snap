"""Download an approved dataset's files into .datasets/raw/<name>/ and keep only files whose fingerprints match.

uv run --package dwarpal-ml python -m dwarpal_ml.fetch fairface
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import httpx

from dwarpal_ml.register import Dataset, DatasetFile, dataset


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_file(item: DatasetFile, folder: Path) -> bool:
    target = folder / item.name
    if target.is_file() and sha256_of(target) == item.sha256:
        print(f"present  {item.name}")
        return True
    if not item.url.startswith("https://"):
        print(f"refused  {item.name}: only https downloads are allowed")
        return False
    folder.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    with httpx.stream("GET", item.url, follow_redirects=True, timeout=120.0) as response:
        response.raise_for_status()
        with partial.open("wb") as out:
            for chunk in response.iter_bytes():
                out.write(chunk)
    actual = sha256_of(partial)
    if actual != item.sha256:
        partial.unlink()
        print(f"MISMATCH {item.name}: expected {item.sha256}, got {actual}; file discarded")
        return False
    partial.replace(target)
    print(f"fetched  {item.name} ({item.bytes:,} bytes)")
    return True


def fetch(entry: Dataset) -> bool:
    if not entry.approved:
        print(f"refused  {entry.name}: not approved in ml/datasets.toml ({entry.licence})")
        return False
    if not entry.files:
        print(f"refused  {entry.name}: no pinned files in ml/datasets.toml")
        return False
    results = [fetch_file(item, entry.folder) for item in entry.files]
    return all(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml fetch", description="Download an approved dataset")
    parser.add_argument("name", help="a dataset name from ml/datasets.toml")
    args = parser.parse_args(argv)
    return 0 if fetch(dataset(args.name)) else 1


if __name__ == "__main__":
    sys.exit(main())
