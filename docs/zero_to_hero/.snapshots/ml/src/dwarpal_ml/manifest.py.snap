"""The unified manifest: every image of every approved dataset as one row of the same shape, with a fixed split.

uv run --package dwarpal-ml python -m dwarpal_ml.manifest fairface
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
import tarfile
import zipfile
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import astuple, dataclass, fields
from pathlib import Path
from typing import TYPE_CHECKING

from dwarpal_ml.register import RAW, Dataset, dataset

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

MANIFESTS = RAW.parent / "manifest"
# FairFace writes its top band "more than 70", although its README says "70+": both mean 70 and over.
AGE_RANGE = re.compile(r"^(?:(\d+)-(\d+)|(\d+)\+|more than (\d+))$")
# UTKFace keeps its labels in each file's name: age_sex_group_datetime.jpg (a few files break the pattern).
UTKFACE_NAME = re.compile(r"^(\d+)_([01])_([0-4])_\d+\.jpg$")
UTKFACE_GROUPS = ("White", "Black", "Asian", "Indian", "Others")
# The model answers for ages 0 to 100; the handful of faces labelled older are left out.
AGES_SERVED = 101
# A fixed timestamp for every file written into a zip, so the same input always makes the same bytes.
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class Row:
    image_id: str
    dataset: str
    archive: str
    member: str
    age_low: int
    age_high: int | None
    age_exact: int | None
    sex: str
    group: str
    licence: str
    split: str


def parse_age_range(text: str) -> tuple[int, int | None]:
    match = AGE_RANGE.match(text.strip())
    if match is None:
        raise ValueError(f"not an age range: {text!r}")
    if match[1] is not None:
        return int(match[1]), int(match[2])
    return int(match[3] or match[4]), None


def split_for(image_id: str, official_split: str) -> str:
    if official_split == "val":
        return "test"
    bucket = int.from_bytes(hashlib.sha256(image_id.encode("utf-8")).digest()[:4]) % 100
    if official_split == "evaluation":
        return "calib" if bucket < 50 else "test"
    return "train" if bucket < 80 else "val" if bucket < 90 else "calib"


def fairface_rows(entry: Dataset) -> Iterator[Row]:
    archive = "fairface-img-margin125-trainval.zip"
    with zipfile.ZipFile(entry.folder / archive) as images:
        present = set(images.namelist())
    for official in ("train", "val"):
        with (entry.folder / f"fairface_label_{official}.csv").open(encoding="utf-8", newline="") as labels:
            for record in csv.DictReader(labels):
                member = record["file"]
                if member not in present:
                    continue
                low, high = parse_age_range(record["age"])
                image_id = f"fairface/{member}"
                yield Row(
                    image_id=image_id,
                    dataset=entry.name,
                    archive=archive,
                    member=member,
                    age_low=low,
                    age_high=high,
                    age_exact=None,
                    sex=record["gender"].lower(),
                    group=record["race"],
                    licence=entry.licence,
                    split=split_for(image_id, official),
                )


def repack(parts: list[Path], target: Path) -> None:
    partial = target.with_name(target.name + ".part")
    with zipfile.ZipFile(partial, "w", zipfile.ZIP_STORED) as out:
        for part in parts:
            with tarfile.open(part) as tar:
                for member in tar:
                    handle = tar.extractfile(member) if member.isfile() else None
                    if handle is not None:
                        out.writestr(zipfile.ZipInfo(member.name, date_time=ZIP_TIME), handle.read())
    partial.replace(target)


def utkface_rows(entry: Dataset) -> Iterator[Row]:
    archive = "utkface-in-the-wild.zip"
    if not (entry.folder / archive).is_file():
        repack([entry.folder / item.name for item in entry.files], entry.folder / archive)
    with zipfile.ZipFile(entry.folder / archive) as images:
        members = sorted(images.namelist())
    for member in members:
        label = UTKFACE_NAME.match(member.rsplit("/", 1)[-1])
        if label is None or int(label[1]) >= AGES_SERVED:
            continue
        image_id = f"utkface/{member}"
        yield Row(
            image_id=image_id,
            dataset=entry.name,
            archive=archive,
            member=member,
            age_low=int(label[1]),
            age_high=int(label[1]),
            age_exact=int(label[1]),
            sex=("male", "female")[int(label[2])],
            group=UTKFACE_GROUPS[int(label[3])],
            licence=entry.licence,
            split=split_for(image_id, "evaluation"),
        )


ADAPTERS: dict[str, Callable[[Dataset], Iterator[Row]]] = {"fairface": fairface_rows, "utkface": utkface_rows}


def write_table[T: DataclassInstance](kind: type[T], rows: Iterable[T], path: Path) -> list[T]:
    kept = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow([field.name for field in fields(kind)])
        for row in kept:
            writer.writerow(["" if value is None else value for value in astuple(row)])
    return kept


def write_manifest(rows: Iterable[Row], path: Path) -> list[Row]:
    return write_table(Row, rows, path)


def optional_int(text: str) -> int | None:
    return int(text) if text else None


def read_manifest(path: Path) -> list[Row]:
    with path.open(encoding="utf-8", newline="") as source:
        return [
            Row(
                image_id=record["image_id"],
                dataset=record["dataset"],
                archive=record["archive"],
                member=record["member"],
                age_low=int(record["age_low"]),
                age_high=optional_int(record["age_high"]),
                age_exact=optional_int(record["age_exact"]),
                sex=record["sex"],
                group=record["group"],
                licence=record["licence"],
                split=record["split"],
            )
            for record in csv.DictReader(source)
        ]


def age_label(row: Row) -> str:
    return f"{row.age_low}-{row.age_high}" if row.age_high is not None else f"{row.age_low}+"


def summary(rows: list[Row]) -> str:
    by_split = Counter(row.split for row in rows)
    by_age = Counter((row.age_low, age_label(row)) for row in rows)
    by_group = Counter(row.group for row in rows)
    lines = [f"{len(rows):,} images"]
    lines.append("splits: " + ", ".join(f"{name} {count:,}" for name, count in sorted(by_split.items())))
    lines.append("ages:   " + ", ".join(f"{label} {count:,}" for (_, label), count in sorted(by_age.items())))
    lines.append("groups: " + ", ".join(f"{name} {count:,}" for name, count in sorted(by_group.items())))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml manifest", description="Build a dataset's manifest")
    parser.add_argument("name", choices=sorted(ADAPTERS))
    args = parser.parse_args(argv)
    entry = dataset(args.name)
    if not entry.approved:
        print(f"refused  {entry.name}: not approved in ml/datasets.toml")
        return 1
    rows = write_manifest(ADAPTERS[args.name](entry), MANIFESTS / f"{entry.name}.csv")
    print(summary(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
