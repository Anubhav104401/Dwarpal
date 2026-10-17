"""Train an age model: a backbone with 101 outputs, taught label distributions, with every run recorded.

uv run --package dwarpal-ml python -m dwarpal_ml.train --backbone resnet26d --epochs 30 --workers 14
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import timm
import torch
from safetensors.torch import save_file
from timm.optim import create_optimizer_v2
from timm.utils import ModelEmaV3
from torch import nn
from torch.utils.data import DataLoader, WeightedRandomSampler

from dwarpal_ml.data import INPUT_SIZE, Augment, FaceDataset, sampling_weights
from dwarpal_ml.manifest import MANIFESTS
from dwarpal_ml.model import AgeModel, pretrained_weights
from dwarpal_ml.prepare import PROCESSED
from dwarpal_ml.register import ROOT
from dwarpal_ml.targets import age_loss, distance_to_band, expected_age

RUNS = ROOT / ".runs"
MEMORY_WARNING = 0.92


@dataclass(frozen=True)
class Config:
    dataset: str = "fairface"
    backbone: str = "resnet26d"
    pretrained: bool = False
    drop_path: float = 0.0
    epochs: int = 30
    batch_size: int = 128
    learning_rate: float = 2e-3
    weight_decay: float = 0.05
    warmup_epochs: int = 2
    ema_decay: float = 0.999
    image_size: int = INPUT_SIZE
    workers: int = 12
    seed: int = 0
    limit: int = 0


def learning_rate_factor(step: int, total: int, warmup: int) -> float:
    if step < warmup:
        return (step + 1) / warmup
    progress = (step - warmup) / max(1, total - warmup)
    return 0.5 * (1.0 + math.cos(math.pi * min(1.0, progress)))


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader[Any], device: torch.device) -> dict[str, float]:
    model.eval()
    loss = miss = hits = count = 0.0
    for images, targets, low, high in loader:
        images, targets = images.to(device, non_blocking=True), targets.to(device, non_blocking=True)
        low, high = low.to(device), high.to(device)
        with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
            logits = model(images)
        distance = distance_to_band(expected_age(logits), low, high)
        loss += float(age_loss(logits, targets, low, high)) * len(images)
        miss += float(distance.sum())
        hits += float((distance == 0).sum())
        count += len(images)
    return {"loss": loss / count, "band_mae": miss / count, "band_accuracy": hits / count}


def gpu_memory_share(device: torch.device) -> float:
    if device.type != "cuda":
        return 0.0
    return torch.cuda.max_memory_reserved(device) / torch.cuda.get_device_properties(device).total_memory


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_state() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT, check=False).stdout.strip()  # noqa: S603, S607 - fixed git commands

    return {"commit": git("rev-parse", "HEAD"), "uncommitted_changes": bool(git("status", "--porcelain"))}


def loader(
    dataset: FaceDataset, config: Config, workers: int, sampler: WeightedRandomSampler | None = None
) -> DataLoader[Any]:
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        sampler=sampler,
        num_workers=workers,
        persistent_workers=workers > 0,
        pin_memory=torch.cuda.is_available(),
        drop_last=sampler is not None,
    )


def train(config: Config, run: Path) -> dict[str, Any]:
    torch.manual_seed(config.seed)
    torch.backends.cudnn.benchmark = True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    faces = PROCESSED / f"{config.dataset}.zip"
    train_set = FaceDataset(config.dataset, "train", faces, Augment(config.image_size), config.image_size, config.limit)
    val_set = FaceDataset(config.dataset, "val", faces, None, config.image_size, config.limit)
    train_rows, val_rows = train_set.rows, val_set.rows
    sampler = WeightedRandomSampler(
        sampling_weights(train_rows).tolist(),
        num_samples=len(train_rows),
        generator=torch.Generator().manual_seed(config.seed),
    )
    # Each loader process takes a while to start on Windows (it loads PyTorch); validation needs far fewer.
    train_loader = loader(train_set, config, config.workers, sampler)
    val_loader = loader(val_set, config, config.workers // 4)

    weights = pretrained_weights(config.backbone) if config.pretrained else None
    model = AgeModel(config.backbone, weights, config.drop_path).to(device)
    ema = ModelEmaV3(model, decay=config.ema_decay, use_warmup=True)
    optimizer = create_optimizer_v2(model, "adamw", lr=config.learning_rate, weight_decay=config.weight_decay)
    steps = config.epochs * len(train_loader)
    warmup = config.warmup_epochs * len(train_loader)
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda step: learning_rate_factor(step, steps, warmup))

    record: dict[str, Any] = {
        "config": asdict(config),
        "started": datetime.now(UTC).isoformat(timespec="seconds"),
        "git": git_state(),
        "data": {
            "train": len(train_rows),
            "val": len(val_rows),
            "fingerprints": {path.name: sha256_of(path) for path in sorted(MANIFESTS.glob(f"{config.dataset}*.csv"))},
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "timm": timm.__version__,
            "device": torch.cuda.get_device_name(device) if device.type == "cuda" else platform.processor(),
        },
        "pretrained": {"name": weights.name, "sha256": weights.sha256, "licence": weights.licence} if weights else None,
        "parameters": sum(p.numel() for p in model.parameters()),
        "epochs": [],
    }
    run.mkdir(parents=True, exist_ok=True)
    best = math.inf
    step = 0
    for epoch in range(1, config.epochs + 1):
        model.train()
        started, total, seen = time.perf_counter(), 0.0, 0
        for images, targets, low, high in train_loader:
            images = images.to(device, non_blocking=True)
            targets, low, high = (t.to(device, non_blocking=True) for t in (targets, low, high))
            with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                logits = model(images)
            loss = age_loss(logits, targets, low, high)
            optimizer.zero_grad(set_to_none=True)
            torch.autograd.backward(loss)
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            step += 1
            ema.update(model, step)
            total += float(loss.detach()) * len(images)
            seen += len(images)
        seconds = time.perf_counter() - started
        peak = gpu_memory_share(device)
        if peak > MEMORY_WARNING:
            print(f"warning: {peak:.0%} of GPU memory used; on Windows the rest spills to system memory, very slowly")
        metrics = evaluate(ema.module, val_loader, device)
        record["epochs"].append(
            {
                "epoch": epoch,
                "train_loss": round(total / seen, 4),
                **{name: round(value, 4) for name, value in metrics.items()},
                "seconds": round(seconds, 1),
                "images_per_second": round(seen / seconds, 1),
                "gpu_memory_share": round(peak, 3),
            }
        )
        if metrics["band_mae"] < best:
            best = metrics["band_mae"]
            save_file({k: v.contiguous() for k, v in ema.module.state_dict().items()}, str(run / "model.safetensors"))
            record["best"] = record["epochs"][-1]
        (run / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        latest = record["epochs"][-1]
        print(
            f"epoch {epoch:>3}/{config.epochs}  loss {latest['train_loss']:.4f}  val band-MAE {latest['band_mae']:.3f}"
            f"  in band {latest['band_accuracy']:.1%}  {latest['images_per_second']:.0f} img/s",
            flush=True,
        )
    return record


def parse(argv: list[str] | None) -> Config:
    parser = argparse.ArgumentParser(prog="dwarpal-ml train", description="Train an age model")
    for field in fields(Config):
        option = f"--{field.name.replace('_', '-')}"
        if isinstance(field.default, bool):
            parser.add_argument(option, action=argparse.BooleanOptionalAction, default=field.default)
        else:
            parser.add_argument(option, type=type(field.default), default=field.default)
    return Config(**vars(parser.parse_args(argv)))


def main(argv: list[str] | None = None) -> int:
    config = parse(argv)
    name = f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{config.backbone}"
    record = train(config, RUNS / name)
    print(f"run {name}: best val band-MAE {record['best']['band_mae']:.3f} at epoch {record['best']['epoch']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
