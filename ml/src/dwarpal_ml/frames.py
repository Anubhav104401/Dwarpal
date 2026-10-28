"""How many frames should the age model see? (Phase 7, decision P1)

uv run --package dwarpal-ml python -m dwarpal_ml.frames .runs/<run> utkface

The safety lines were certified on one clean photo per person (§5.2.6). The verify page sends a burst of webcam frames,
and the inference service mixes the model's answers for the usable ones, weighted by sharpness. To cut the time an
attempt takes, it should look at fewer of them. This measures whether that changes the decisions: for every face of a
split, it makes a burst of webcam-like frames (the training augmentations: a slight turn, lighting, blur, noise, JPEG)
and decides from the clean photo, the sharpest frame, the 3 sharpest, and all of them.

It runs on the calibration split, where the lines were set: it compares the choices with each other, and touches no
threshold. The test split, opened once in Phase 2, stays closed.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from numpy.typing import NDArray
from safetensors.torch import load_file
from torch.utils.data import DataLoader, Dataset

from dwarpal_ml.calibrate import decisions_view
from dwarpal_ml.data import Augment, to_tensor, usable_rows
from dwarpal_ml.evaluate import Floats, predict, softmax
from dwarpal_ml.manifest import Row
from dwarpal_ml.model import AgeModel
from dwarpal_ml.prepare import PROCESSED
from dwarpal_vision import decode_image

BURST = 8  # frames per attempt, as the verify page sends
CHOICES = (1, 3, BURST)  # how many of the sharpest frames the age model sees
SEED = 20261027


def weight(image: NDArray[np.uint8]) -> float:
    """The inference pipeline's frame weight: sharpness (the face's detail, at 112 x 112), capped at 1. (Its other
    factor, the face detector's confidence, is left out: these photos are already cut to the face.)"""
    grey = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (112, 112), interpolation=cv2.INTER_AREA)
    return min(1.0, float(cv2.Laplacian(grey, cv2.CV_64F).var()) / 200.0)


@dataclass
class Bursts(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Each person's burst: BURST augmented frames of their photo, and each frame's weight. Seeded per person, so a
    second run makes the very same frames."""

    rows: list[Row]
    faces: Path
    archive: zipfile.ZipFile | None = field(default=None, repr=False)

    def __getstate__(self) -> dict[str, Any]:
        return {**self.__dict__, "archive": None}

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        if self.archive is None:
            cv2.setNumThreads(1)
            self.archive = zipfile.ZipFile(self.faces)
        photo = decode_image(self.archive.read(self.rows[index].image_id))
        augment = Augment(seed=SEED + index)
        frames = [augment(photo) for _ in range(BURST)]
        weights = torch.tensor([weight(frame) for frame in frames], dtype=torch.float64)
        return torch.stack([to_tensor(frame) for frame in frames]), weights


def burst_probabilities(
    run: Path, rows: list[Row], faces: Path, temperature: float, workers: int
) -> tuple[Floats, Floats]:
    """The model's age probabilities for every frame of every burst, (people, BURST, 101), and the frames' weights."""
    record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AgeModel(record["config"]["backbone"])
    model.load_state_dict(load_file(str(run / "model.safetensors")))
    model = model.to(device).eval()
    probabilities, weights = [], []
    with torch.no_grad():
        for frames, frame_weights in DataLoader(Bursts(rows, faces), batch_size=16, num_workers=workers):
            people, burst = frames.shape[:2]
            with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                logits = model(frames.flatten(0, 1).to(device)).float().cpu().numpy()
            probabilities.append(softmax(logits.astype(np.float64), temperature).reshape(people, burst, -1))
            weights.append(frame_weights.numpy())
            if len(probabilities) % 50 == 0:  # about every 800 people: this takes a while
                print(f"  {sum(len(batch) for batch in probabilities)} of {len(rows)} people", flush=True)
    return np.concatenate(probabilities), np.concatenate(weights).astype(np.float64)


def sharpest(probabilities: Floats, weights: Floats, count: int) -> Floats:
    """Mix each person's `count` sharpest frames, weighted as the pipeline weights them."""
    chosen = np.argsort(-weights, axis=1, kind="stable")[:, :count]
    picked = np.take_along_axis(probabilities, chosen[:, :, None], axis=1)
    share = np.take_along_axis(weights, chosen, axis=1)
    share = np.where(share.sum(axis=1, keepdims=True) > 0, share, 1.0)
    share = share / share.sum(axis=1, keepdims=True)
    return np.asarray((picked * share[:, :, None]).sum(axis=1), dtype=np.float64)


def summary(results: dict[str, Any]) -> str:
    lines = [f"{results['faces']} people, {BURST} frames each — {results['dataset']} {results['split']} split"]
    for limit, views in results["limits"].items():
        lines.append(f"\n{limit}+ (risk budget {views['risk_budget']}):")
        lines.append("  frames      minors passed (upper bound)   adults N+3+ stepped up")
        for name, view in views["by_choice"].items():
            minors = view["minors_passed"]
            stepped = [
                band["step_up"] for band_name, band in view["adults"].items() if band_name.split("-")[0] != limit
            ]
            count, total = sum(s["count"] for s in stepped), sum(s["of"] for s in stepped)
            lines.append(
                f"  {name:<10}  {minors['rate']:.4f} ({minors['upper']:.4f})            {count / max(total, 1):.3f}"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml frames", description="Compare decisions from bursts of frames")
    parser.add_argument("run", type=Path, help="a run folder in .runs/, already calibrated")
    parser.add_argument("name", help="the exact-age dataset it was calibrated on")
    parser.add_argument("--split", default="calib")
    # 0: make the bursts in this process. On Windows, each worker process re-imports PyTorch first, which cost more
    # than it saved here (one run, 11,301 people: about 25 minutes).
    parser.add_argument("--workers", type=int, default=0)
    args = parser.parse_args(argv)
    if args.split == "test":
        print("refused  the test split was opened once, in Phase 2; it isn't used to choose anything")
        return 1
    calibration = json.loads((args.run / f"calibration-{args.name}.json").read_text(encoding="utf-8"))
    temperature = float(calibration["temperature"])
    rows = [row for row in usable_rows(args.name) if row.split == args.split]
    clean_logits, clean_rows = predict(args.run, args.split, args.workers, args.name)
    if [row.image_id for row in clean_rows] != [row.image_id for row in rows]:
        raise RuntimeError("the cached clean predictions are for other faces")
    probabilities, weights = burst_probabilities(
        args.run, rows, PROCESSED / f"{args.name}.zip", temperature, args.workers
    )
    choices = {"clean": softmax(clean_logits, temperature)}
    choices |= {f"best {count}": sharpest(probabilities, weights, count) for count in CHOICES}
    results: dict[str, Any] = {"run": args.run.name, "dataset": args.name, "split": args.split, "faces": len(rows)}
    results["limits"] = {}
    for limit, certified in calibration["limits"].items():
        if certified["thresholds"] is None:
            continue
        results["limits"][limit] = {
            "risk_budget": certified["thresholds"]["risk_budget"],
            "by_choice": {
                name: decisions_view(chosen, rows, certified["thresholds"], int(limit))
                for name, chosen in choices.items()
            },
        }
    (args.run / f"frames-{args.name}-{args.split}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(summary(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
