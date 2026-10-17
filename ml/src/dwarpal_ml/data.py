"""Training data: the usable faces of a dataset, how often to show each, random changes, and tensors."""

from __future__ import annotations

import csv
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from numpy.typing import NDArray
from torch.utils.data import Dataset

from dwarpal_ml.manifest import MANIFESTS, Row, read_manifest
from dwarpal_ml.targets import AGES, label_distribution
from dwarpal_vision import Image, decode_image

INPUT_SIZE = 224
FOCUS = (10, 25)
FOCUS_BOOST = 2.0

type Sample = tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]


def usable_rows(name: str) -> list[Row]:
    with (MANIFESTS / f"{name}.faces.csv").open(encoding="utf-8", newline="") as source:
        prepared = {record["image_id"] for record in csv.DictReader(source) if record["status"] == "ok"}
    with (MANIFESTS / f"{name}.duplicates.csv").open(encoding="utf-8", newline="") as source:
        removed = {record["image_id"] for record in csv.DictReader(source)}
    rows = read_manifest(MANIFESTS / f"{name}.csv")
    return [row for row in rows if row.image_id in prepared and row.image_id not in removed]


def band_of(row: Row) -> tuple[int, int]:
    if row.age_exact is not None:
        return row.age_exact, row.age_exact
    return row.age_low, row.age_high if row.age_high is not None else AGES - 1


def sampling_weights(rows: list[Row]) -> NDArray[np.float64]:
    bands = [band_of(row) for row in rows]
    counts = Counter(bands)
    weights = np.array([counts[band] ** -0.5 for band in bands])
    focus = np.array([low <= FOCUS[1] and high >= FOCUS[0] for low, high in bands])
    weights[focus] *= FOCUS_BOOST
    return np.asarray(weights / weights.sum(), dtype=np.float64)


def fit(image: Image, size: int = INPUT_SIZE) -> Image:
    return np.asarray(cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA), dtype=np.uint8)


class Augment:
    """Random changes that keep a face recognisably the same face, then webcam-like damage."""

    def __init__(self, size: int = INPUT_SIZE, seed: int | None = None) -> None:
        self.size = size
        self.seed = seed
        self.generator: np.random.Generator | None = None

    @property
    def rng(self) -> np.random.Generator:
        # Created on first use, inside each loader process, from that process's own seed: copies made before the
        # processes start would otherwise all make the same "random" changes.
        if self.generator is None:
            self.generator = np.random.default_rng(self.seed if self.seed is not None else torch.initial_seed())
        return self.generator

    def chance(self, probability: float) -> bool:
        return bool(self.rng.random() < probability)

    def __call__(self, image: Image) -> Image:
        return self.webcam(self.colour(self.geometry(image)))

    def geometry(self, image: Image) -> Image:
        height, width = image.shape[:2]
        zoom = self.rng.uniform(0.92, 1.08) * self.size / width
        angle = self.rng.uniform(-10.0, 10.0)
        matrix = np.asarray(cv2.getRotationMatrix2D((width / 2, height / 2), angle, zoom), dtype=np.float64)
        centre = np.array([self.size - width, self.size - height], dtype=np.float64) / 2
        matrix[:, 2] += centre + self.rng.uniform(-0.04, 0.04, 2) * self.size
        out = cv2.warpAffine(
            image, matrix, (self.size, self.size), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101
        )
        if self.chance(0.5):
            out = out[:, ::-1]
        return np.ascontiguousarray(out, dtype=np.uint8)

    def colour(self, image: Image) -> Image:
        pixels = image.astype(np.float32)
        grey = pixels @ np.array([0.114, 0.587, 0.299], dtype=np.float32)
        pixels = grey[..., None] + (pixels - grey[..., None]) * self.rng.uniform(0.7, 1.3)
        pixels = (pixels - grey.mean()) * self.rng.uniform(0.7, 1.3) + grey.mean()
        pixels *= self.rng.uniform(0.7, 1.3)
        return np.clip(pixels, 0, 255).astype(np.uint8)

    def webcam(self, image: Image) -> Image:
        out = image
        if self.chance(0.5):
            gamma = self.rng.uniform(0.6, 1.4)
            table = (np.linspace(0.0, 1.0, 256) ** gamma * 255.0).astype(np.uint8)
            out = np.asarray(cv2.LUT(out, table), dtype=np.uint8)
        if self.chance(0.3):
            out = np.asarray(cv2.GaussianBlur(out, (0, 0), self.rng.uniform(0.3, 1.5)), dtype=np.uint8)
        if self.chance(0.2):
            out = self.motion_blur(out)
        if self.chance(0.3):
            out = self.downscale(out)
        if self.chance(0.3):
            noise = self.rng.normal(0.0, self.rng.uniform(2.0, 10.0), out.shape)
            out = np.clip(out.astype(np.float64) + noise, 0, 255).astype(np.uint8)
        if self.chance(0.5):
            quality = int(self.rng.integers(30, 91))
            out = decode_image(cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, quality])[1].tobytes())
        return np.ascontiguousarray(out, dtype=np.uint8)

    def motion_blur(self, image: Image) -> Image:
        length = int(self.rng.integers(3, 10))
        kernel = np.zeros((length, length), dtype=np.float32)
        kernel[length // 2, :] = 1.0
        turn = cv2.getRotationMatrix2D(((length - 1) / 2, (length - 1) / 2), float(self.rng.uniform(0, 180)), 1.0)
        turned = np.asarray(cv2.warpAffine(kernel, turn, (length, length)), dtype=np.float32)
        return np.asarray(cv2.filter2D(image, -1, turned / max(float(turned.sum()), 1e-6)), dtype=np.uint8)

    def downscale(self, image: Image) -> Image:
        height, width = image.shape[:2]
        factor = self.rng.uniform(0.25, 0.6)
        size = (max(8, int(width * factor)), max(8, int(height * factor)))
        small = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
        return np.asarray(cv2.resize(small, (width, height), interpolation=cv2.INTER_LINEAR), dtype=np.uint8)


def to_tensor(image: Image) -> torch.Tensor:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1)


@dataclass
class FaceDataset(Dataset[Sample]):
    """The faces of one split. Each loader process is sent only this short description and reads the rows itself:
    on Windows, the next process can't start until the previous one has taken everything it was sent."""

    dataset: str
    split: str
    faces: Path
    augment: Augment | None = None
    size: int = INPUT_SIZE
    limit: int = 0
    loaded: list[Row] | None = field(default=None, repr=False)
    archive: zipfile.ZipFile | None = field(default=None, repr=False)

    @property
    def rows(self) -> list[Row]:
        if self.loaded is None:
            rows = [row for row in usable_rows(self.dataset) if row.split == self.split]
            self.loaded = rows[: self.limit] if self.limit else rows
        return self.loaded

    def __getstate__(self) -> dict[str, Any]:
        return {**self.__dict__, "loaded": None, "archive": None}

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> Sample:
        if self.archive is None:
            cv2.setNumThreads(1)
            self.archive = zipfile.ZipFile(self.faces)
        row = self.rows[index]
        image = decode_image(self.archive.read(row.image_id))
        image = self.augment(image) if self.augment is not None else fit(image, self.size)
        low, high = band_of(row)
        target = torch.from_numpy(label_distribution(row.age_low, row.age_high, row.age_exact))
        return to_tensor(image), target, torch.tensor(float(low)), torch.tensor(float(high))
