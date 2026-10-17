"""Age models: a stand-in for building the system, and trained models exported to ONNX (Phase 2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Protocol

import numpy as np
import onnxruntime
from numpy.typing import NDArray

from dwarpal_vision import Image, to_model_input

AGES = np.arange(101, dtype=np.float64)


class AgeBackend(Protocol):
    version: str

    def predict(self, faces: list[Image]) -> NDArray[np.float64]: ...


class StubAgeBackend:
    def __init__(self, age: float, spread: float) -> None:
        weights = np.exp(-0.5 * ((AGES - age) / spread) ** 2)
        self._row = weights / weights.sum()
        self.version = f"stub-age-{age:g}"

    def predict(self, faces: list[Image]) -> NDArray[np.float64]:
        return np.tile(self._row, (len(faces), 1))


class ModelFileError(ValueError):
    """The model file is missing or is not the file its manifest pins."""


class OnnxAgeBackend:
    """A trained model exported to ONNX, loaded from its folder in the model registry."""

    def __init__(self, folder: Path, threads: int = 1) -> None:
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        model = folder / manifest["model"]["file"]
        if not model.is_file():
            raise ModelFileError(f"{model} is missing")
        if hashlib.sha256(model.read_bytes()).hexdigest() != manifest["model"]["sha256"]:
            raise ModelFileError(f"{model} does not match the fingerprint in its manifest")
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = threads
        self._session = onnxruntime.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])
        self.version: str = manifest["version"]

    def predict(self, faces: list[Image]) -> NDArray[np.float64]:
        probabilities = self._session.run(["probabilities"], {"pixels": to_model_input(faces)})[0]
        return np.asarray(probabilities, dtype=np.float64)
