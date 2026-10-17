"""The licence register (ml/datasets.toml): which datasets exist, what their licences allow, and their pinned files."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTER = ROOT / "ml" / "datasets.toml"
RAW = ROOT / ".datasets" / "raw"


@dataclass(frozen=True)
class DatasetFile:
    name: str
    url: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class Dataset:
    name: str
    title: str
    licence: str
    permitted_use: str
    citation: str
    age_labels: str
    age_source: str
    subject: str
    approved: bool
    files: tuple[DatasetFile, ...]

    @property
    def folder(self) -> Path:
        return RAW / self.name


class UnknownDatasetError(LookupError):
    """The register has no dataset of this name."""


def load_register(path: Path = REGISTER) -> dict[str, Dataset]:
    entries = tomllib.loads(path.read_text(encoding="utf-8"))["dataset"]
    datasets = {}
    for entry in entries:
        files = tuple(DatasetFile(f["name"], f["url"], f["sha256"], int(f["bytes"])) for f in entry.get("files", []))
        datasets[entry["name"]] = Dataset(
            name=entry["name"],
            title=entry["title"],
            licence=entry["licence"],
            permitted_use=entry["permitted_use"],
            citation=entry["citation"],
            age_labels=entry["age_labels"],
            age_source=entry.get("age_source", "not recorded"),
            subject=entry.get("subject", "central"),
            approved=bool(entry["approved"]),
            files=files,
        )
    return datasets


def dataset(name: str, path: Path = REGISTER) -> Dataset:
    try:
        return load_register(path)[name]
    except KeyError:
        raise UnknownDatasetError(name) from None
