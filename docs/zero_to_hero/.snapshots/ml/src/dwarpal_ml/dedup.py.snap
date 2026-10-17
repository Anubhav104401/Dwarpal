"""Near-duplicate removal: find faces that are the same photo, and keep one copy, in the most protected split.

Two stages: perceptual hashes cheaply shortlist pairs that might be the same photo, then the fine detail of each
shortlisted pair is compared to confirm it.

uv run --package dwarpal-ml python -m dwarpal_ml.dedup fairface
"""

from __future__ import annotations

import argparse
import csv
import sys
import zipfile
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy.cluster.hierarchy import DisjointSet

from dwarpal_ml.manifest import MANIFESTS, Row, age_label, read_manifest, write_table
from dwarpal_ml.prepare import PROCESSED
from dwarpal_ml.register import dataset
from dwarpal_vision import decode_image

# Both limits were chosen by looking at FairFace's pairs on either side of them (docs/reports/phase-2.md).
SIEVE_DISTANCE = 10
MIN_SIMILARITY = 0.6
DETAIL_SIZE = 64
DETAIL_BLUR = 2.0
BLOCK = 256
# A duplicate keeps the copy whose split is hardest to reach: the exam outranks the safety check, and so on.
SPLIT_PRIORITY = {"test": 0, "calib": 1, "val": 2, "train": 3}

type Vector = NDArray[np.float32]


@dataclass(frozen=True)
class Duplicate:
    image_id: str
    split: str
    kept: str
    kept_split: str
    similarity: float
    same_label: bool


def close_pairs(hashes: NDArray[np.uint64], max_distance: int = SIEVE_DISTANCE) -> Iterator[tuple[int, int]]:
    for start in range(0, len(hashes), BLOCK):
        block = hashes[start : start + BLOCK]
        rest = hashes[start:]
        distances = np.bitwise_count(block[:, None] ^ rest[None, :])
        for i, j in zip(*np.nonzero(distances <= max_distance), strict=True):
            if i < j:
                yield start + int(i), start + int(j)


def fine_detail(jpeg: bytes) -> Vector:
    gray = cv2.cvtColor(decode_image(jpeg), cv2.COLOR_BGR2GRAY)
    pixels = cv2.resize(gray, (DETAIL_SIZE, DETAIL_SIZE), interpolation=cv2.INTER_AREA).astype(np.float32)
    detail = (pixels - cv2.GaussianBlur(pixels, (0, 0), DETAIL_BLUR)).flatten()
    detail -= detail.mean()
    return detail / max(float(np.linalg.norm(detail)), 1e-6)


def similarity(a: Vector, b: Vector) -> float:
    return float(np.dot(a, b))


class Details:
    def __init__(self, archive: zipfile.ZipFile, rows: list[Row]) -> None:
        self.archive = archive
        self.rows = rows
        self.cache: dict[int, Vector] = {}

    def __getitem__(self, index: int) -> Vector:
        if index not in self.cache:
            self.cache[index] = fine_detail(self.archive.read(self.rows[index].image_id))
        return self.cache[index]


def confirmed_pairs(
    pairs: Iterable[tuple[int, int]], details: Details, min_similarity: float = MIN_SIMILARITY
) -> Iterator[tuple[int, int, float]]:
    for a, b in pairs:
        score = similarity(details[a], details[b])
        if score >= min_similarity:
            yield a, b, score


def groups_of(count: int, pairs: Iterable[tuple[int, int, float]]) -> list[list[int]]:
    links = DisjointSet(range(count))
    for a, b, _ in pairs:
        links.merge(a, b)
    return [sorted(group) for group in links.subsets() if len(group) > 1]


def resolve(rows: list[Row], groups: list[list[int]], details: Details) -> list[Duplicate]:
    duplicates = []
    for group in groups:
        keep = min(group, key=lambda index: (SPLIT_PRIORITY[rows[index].split], rows[index].image_id))
        for index in group:
            if index != keep:
                row, kept = rows[index], rows[keep]
                duplicates.append(
                    Duplicate(
                        image_id=row.image_id,
                        split=row.split,
                        kept=kept.image_id,
                        kept_split=kept.split,
                        similarity=round(similarity(details[index], details[keep]), 4),
                        same_label=age_label(row) == age_label(kept),
                    )
                )
    return duplicates


def faces_with_hashes(name: str) -> tuple[list[Row], NDArray[np.uint64]]:
    with (MANIFESTS / f"{name}.faces.csv").open(encoding="utf-8", newline="") as source:
        phash = {record["image_id"]: record["phash"] for record in csv.DictReader(source) if record["status"] == "ok"}
    rows = [row for row in read_manifest(MANIFESTS / f"{name}.csv") if row.image_id in phash]
    return rows, np.array([int(phash[row.image_id], 16) for row in rows], dtype=np.uint64)


def find_duplicates(rows: list[Row], hashes: NDArray[np.uint64], faces: Path) -> list[Duplicate]:
    with zipfile.ZipFile(faces) as archive:
        details = Details(archive, rows)
        confirmed = confirmed_pairs(close_pairs(hashes), details)
        return resolve(rows, groups_of(len(rows), confirmed), details)


def summary(rows: list[Row], duplicates: list[Duplicate]) -> str:
    crossing = Counter(f"{d.split} -> {d.kept_split}" for d in duplicates)
    disagree = sum(not d.same_label for d in duplicates)
    lines = [f"{len(rows):,} faces: {len(duplicates):,} duplicates removed, {disagree:,} with a different age label"]
    lines.append("removed -> kept: " + ", ".join(f"{pair} {count:,}" for pair, count in sorted(crossing.items())))
    removed = {d.image_id for d in duplicates}
    usable = Counter(row.split for row in rows if row.image_id not in removed)
    lines.append("usable: " + ", ".join(f"{split} {count:,}" for split, count in sorted(usable.items())))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml dedup", description="Find and remove near-duplicate faces")
    parser.add_argument("name", help="a dataset prepared by dwarpal_ml.prepare")
    args = parser.parse_args(argv)
    entry = dataset(args.name)
    rows, hashes = faces_with_hashes(entry.name)
    duplicates = find_duplicates(rows, hashes, PROCESSED / f"{entry.name}.zip")
    write_table(Duplicate, duplicates, MANIFESTS / f"{entry.name}.duplicates.csv")
    print(summary(rows, duplicates))
    return 0


if __name__ == "__main__":
    sys.exit(main())
