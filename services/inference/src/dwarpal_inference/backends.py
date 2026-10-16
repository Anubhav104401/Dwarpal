"""Age models. Phase 1 ships a stand-in so the whole system can be built before the real model is trained."""

from __future__ import annotations

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from dwarpal_vision import Image

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
