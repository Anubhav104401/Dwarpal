"""The age model: any backbone with 101 outputs, wrapped so that it takes plain RGB pixels."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import timm
import torch
from torch import nn

from dwarpal_ml.register import ROOT
from dwarpal_ml.targets import AGES

MODELS = ROOT / "models"
# The colour statistics of ImageNet, which pretrained backbones were trained with: they expect exactly these.
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


class UnapprovedWeightsError(LookupError):
    """No pinned, licence-checked pretrained weights are registered for this backbone."""


@dataclass(frozen=True)
class Weights:
    name: str
    file: Path
    sha256: str
    licence: str


def pretrained_weights(backbone: str, register: Path = MODELS / "third_party.json") -> Weights:
    entries = json.loads(register.read_text(encoding="utf-8"))["models"]
    for entry in entries:
        if entry["use"] == "training" and entry.get("timm") == backbone:
            weights = Weights(entry["name"], register.parent / entry["file"], entry["sha256"], entry["licence"])
            break
    else:
        raise UnapprovedWeightsError(f"no approved pretrained weights for {backbone} in {register.name}")
    if not weights.file.is_file():
        raise FileNotFoundError(f"{weights.file} is missing: run infra/scripts/fetch_models.py --training")
    if hashlib.sha256(weights.file.read_bytes()).hexdigest() != weights.sha256:
        raise ValueError(f"{weights.file} does not match its pinned fingerprint")
    return weights


class AgeModel(nn.Module):
    """Pixels in (RGB, 0-255, shaped batch, 3, height, width), one score per age from 0 to 100 out."""

    mean: torch.Tensor
    std: torch.Tensor

    def __init__(self, backbone: str, weights: Weights | None = None, drop_path: float = 0.0) -> None:
        super().__init__()
        self.backbone = timm.create_model(
            backbone,
            pretrained=weights is not None,
            pretrained_cfg_overlay={"file": str(weights.file)} if weights is not None else None,
            num_classes=AGES,
            drop_path_rate=drop_path,
        )
        self.register_buffer("mean", torch.tensor(MEAN).view(1, 3, 1, 1) * 255.0)
        self.register_buffer("std", torch.tensor(STD).view(1, 3, 1, 1) * 255.0)

    def forward(self, pixels: torch.Tensor) -> torch.Tensor:
        scaled = (pixels.float() - self.mean) / self.std
        logits: torch.Tensor = self.backbone(scaled.contiguous(memory_format=torch.channels_last))
        return logits
