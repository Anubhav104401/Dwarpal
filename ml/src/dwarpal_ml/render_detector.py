"""The render detector (liveness level 6, ADR-0021): MiniFASNet V2, retaught to tell a real face from a rendered one.

The anti-spoofing network already looks for what a camera sees of a screen or a print; here its last layer is replaced
by one with two answers — real, rendered — and the whole network is trained on our own clips (dwarpal_ml.renders).

uv run --package dwarpal-ml python -m dwarpal_ml.render_detector prepare
uv run --package dwarpal-ml python -m dwarpal_ml.render_detector train --epochs 10
uv run --package dwarpal-ml python -m dwarpal_ml.render_detector evaluate .runs/render-...
uv run --package dwarpal-ml python -m dwarpal_ml.render_detector export .runs/render-... --version 0.1.0
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import cv2
import numpy as np
import onnxruntime
import torch
from numpy.typing import NDArray
from safetensors.torch import load_file, save_file
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

from dwarpal_ml.antispoof import THIRD_PARTY, MiniFASNet, State
from dwarpal_ml.evaluate import check, rate
from dwarpal_ml.export import OPSET
from dwarpal_ml.register import ROOT
from dwarpal_ml.renders import DATA, IMAGES, load_consents, problems, read_clips, split_of
from dwarpal_vision import Face, FaceDetector, decode_image
from dwarpal_vision.antispoof import SIZE, crop

BASE = THIRD_PARTY / "minifasnet_v2_2.7.pth"
SHAPES = Path(__file__).with_name("minifasnet_v2_shapes.json")
SCALE = 2.7
RENDERED = 1
CROPS = DATA / "crops"
RUNS = ROOT / ".runs"
GATES = ROOT / "ml" / "render_gates.toml"
# Real people the detector may wrongly call rendered, when its threshold is chosen: 5 %.
BPCER_TARGET = 0.05
TOLERANCE = 1e-4
# Our own frames, not a stranger's upload: a rendered 1280 x 720 PNG is often over the service's 512 KB limit.
FRAME_BYTES = 16 * 1024 * 1024

type Pixels = NDArray[np.uint8]


class Detector(Protocol):
    def detect(self, image: Pixels) -> list[Face]: ...


# --- the network ---


def base_state(pretrained: bool, weights: Path = BASE) -> State:
    """MiniFASNet V2's weights, or — without them — tensors of the right shapes only, for a network trained from
    scratch (and for tests on machines without the weights)."""
    if pretrained:
        # weights_only=True: tensors only, never pickled code.
        raw = torch.load(weights, map_location="cpu", weights_only=True)  # nosemgrep
        return {name.removeprefix("module."): tensor for name, tensor in raw.items()}
    shapes: dict[str, list[int]] = json.loads(SHAPES.read_text(encoding="utf-8"))
    return {name: torch.empty(shape) for name, shape in shapes.items()}


class RenderNet(nn.Module):
    """Pixels (blue-green-red, 0-255, 80 x 80) in; the chances of [real, rendered] out."""

    def __init__(self, state: State, pretrained: bool) -> None:
        super().__init__()
        self.body = MiniFASNet(state)
        if pretrained:
            self.body.load_state_dict(state, strict=True)
        embedding = self.body.prob.in_features
        self.body.prob = nn.Linear(embedding, 2, bias=False)

    def forward(self, pixels: torch.Tensor) -> torch.Tensor:
        result: torch.Tensor = self.body(pixels)
        return result


# --- the data ---


def face_crops(frames: Sequence[Path], detector: Detector, every: int) -> list[Pixels]:
    """The face of every `every`-th frame, cropped as MiniFASNet sees it; frames without exactly one face are
    skipped."""
    crops = []
    for path in frames[::every]:
        image = decode_image(path.read_bytes(), max_bytes=FRAME_BYTES)
        faces = detector.detect(image)
        if len(faces) == 1:
            crops.append(crop(image, faces[0].box, SCALE))
    return crops


def prepare(detector: Detector, folder: Path = DATA, every: int = 5) -> dict[str, int]:
    """Every clip's face crops, gathered into one file per split. Refused while any clip may not be kept, so a
    withdrawn consent can never reach the training data."""
    found = problems(read_clips(folder), load_consents(folder), folder)
    if found:
        raise ValueError(f"run `renders check` first: {found[0]}")
    gathered: dict[str, dict[str, list[Any]]] = {}
    for clip in read_clips(folder):
        frames = sorted(p for p in (folder / "clips" / clip.clip_id).iterdir() if p.suffix.lower() in IMAGES)
        crops = face_crops(frames, detector, every)
        split = gathered.setdefault(split_of(clip.identity), {"pixels": [], "labels": [], "kinds": [], "people": []})
        split["pixels"] += crops
        split["labels"] += [int(clip.rendered)] * len(crops)
        split["kinds"] += [clip.kind] * len(crops)
        split["people"] += [clip.identity] * len(crops)
    target = folder / "crops"
    target.mkdir(parents=True, exist_ok=True)
    for name, split in gathered.items():
        np.savez_compressed(
            target / f"{name}.npz",
            pixels=np.asarray(split["pixels"], dtype=np.uint8).reshape(-1, SIZE, SIZE, 3),
            labels=np.asarray(split["labels"], dtype=np.int64),
            kinds=np.asarray(split["kinds"], dtype=str),
            people=np.asarray(split["people"], dtype=str),
        )
    return {name: len(split["labels"]) for name, split in sorted(gathered.items())}


@dataclass(frozen=True)
class Split:
    pixels: Pixels
    labels: NDArray[np.int64]
    kinds: NDArray[np.str_]
    people: NDArray[np.str_]


def load_split(name: str, crops: Path = CROPS) -> Split:
    with np.load(crops / f"{name}.npz") as data:
        return Split(data["pixels"], data["labels"], data["kinds"], data["people"])


def augment(pixels: Pixels, rng: np.random.Generator) -> Pixels:
    """Changes a camera or a video call could make: a mirror image, other brightness and contrast, and JPEG
    compression."""
    if rng.random() < 0.5:
        pixels = pixels[:, ::-1]
    gain, shift = rng.uniform(0.7, 1.3), rng.uniform(-25.0, 25.0)
    pixels = np.clip(pixels.astype(np.float32) * gain + shift, 0, 255).astype(np.uint8)
    if rng.random() < 0.5:
        quality = int(rng.integers(40, 95))
        _, encoded = cv2.imencode(".jpg", pixels, [cv2.IMWRITE_JPEG_QUALITY, quality])
        pixels = np.asarray(cv2.imdecode(encoded, cv2.IMREAD_COLOR), dtype=np.uint8)
    return np.ascontiguousarray(pixels)


class Crops(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    def __init__(self, split: Split, training: bool, seed: int = 0) -> None:
        self.split = split
        self.training = training
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.split.labels)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        pixels = self.split.pixels[index]
        if self.training:
            pixels = augment(pixels, self.rng)
        tensor = torch.from_numpy(pixels.astype(np.float32).transpose(2, 0, 1).copy())
        return tensor, torch.tensor(self.split.labels[index])


def balanced_weights(labels: NDArray[np.int64]) -> list[float]:
    """Each crop's chance of being drawn, so that real and rendered crops are drawn equally often."""
    counts = np.bincount(labels, minlength=2).astype(np.float64)
    return [float(1.0 / counts[label]) for label in labels]


# --- training ---


@dataclass(frozen=True)
class Config:
    epochs: int = 10
    batch_size: int = 64
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    pretrained: bool = True
    seed: int = 0


def scores_of(model: RenderNet, split: Split, batch_size: int = 256) -> NDArray[np.float64]:
    """The chance that each crop is rendered."""
    model.eval()
    loader = DataLoader(Crops(split, training=False), batch_size=batch_size)
    with torch.no_grad():
        chances = [model(pixels)[:, RENDERED] for pixels, _ in loader]
    return torch.cat(chances).double().numpy() if chances else np.zeros(0)


def settle_batch_norm(model: RenderNet, split: Split, batches: int = 20, batch_size: int = 64) -> None:
    """Measure batch normalisation's averages again, exactly, over training crops. During training they are only
    running estimates, which lag far behind after a short training, and the answers in evaluation use them."""
    norms = [m for m in model.modules() if isinstance(m, nn.modules.batchnorm._BatchNorm)]
    for norm in norms:
        norm.reset_running_stats()
        norm.momentum = None  # a plain average over every batch seen
    model.train()
    loader = DataLoader(Crops(split, training=False), batch_size=batch_size, shuffle=True)
    with torch.no_grad():
        for index, (pixels, _) in enumerate(loader):
            if index == batches:
                break
            model(pixels)
    for norm in norms:
        norm.momentum = 0.1
    model.eval()


def balanced_error(scores: NDArray[np.float64], labels: NDArray[np.int64], threshold: float = 0.5) -> float:
    """The average of the two mistakes at one threshold: renders taken for real, and real people taken for renders."""
    rendered = scores >= threshold
    missed = float(np.mean(~rendered[labels == RENDERED])) if (labels == RENDERED).any() else 0.0
    refused = float(np.mean(rendered[labels != RENDERED])) if (labels != RENDERED).any() else 0.0
    return (missed + refused) / 2


def train(config: Config, crops: Path = CROPS, runs: Path = RUNS, report: Callable[[str], None] = print) -> Path:
    """Train, keep the epoch with the lowest balanced error on the validation split, and record the run."""
    torch.manual_seed(config.seed)
    training, validation = load_split("train", crops), load_split("validation", crops)
    for name, split in (("train", training), ("validation", validation)):
        if set(split.labels.tolist()) != {0, RENDERED}:
            raise ValueError(f"the {name} split needs both real and rendered faces: film real people first")
    model = RenderNet(base_state(config.pretrained), config.pretrained)
    sampler = WeightedRandomSampler(balanced_weights(training.labels), len(training.labels), replacement=True)
    loader = DataLoader(Crops(training, training=True, seed=config.seed), config.batch_size, sampler=sampler)
    optimiser = torch.optim.AdamW(model.parameters(), config.learning_rate, weight_decay=config.weight_decay)
    steps = max(1, config.epochs * len(loader))
    schedule = torch.optim.lr_scheduler.LambdaLR(optimiser, lambda step: 0.5 * (1 + math.cos(math.pi * step / steps)))
    run = runs / f"render-{datetime.now(UTC):%Y%m%d-%H%M%S}"
    run.mkdir(parents=True)
    history, best = [], math.inf
    for epoch in range(1, config.epochs + 1):
        model.train()
        started, losses = time.monotonic(), []
        for pixels, labels in loader:
            chances = model(pixels)
            loss = nn.functional.nll_loss(torch.log(chances.clamp_min(1e-7)), labels)
            optimiser.zero_grad()
            torch.autograd.backward(loss)
            optimiser.step()
            schedule.step()
            losses.append(loss.item())
        settle_batch_norm(model, training)
        error = balanced_error(scores_of(model, validation), validation.labels)
        history.append({"epoch": epoch, "loss": float(np.mean(losses)), "validation_error": error})
        seconds = time.monotonic() - started
        report(f"epoch {epoch}: loss {np.mean(losses):.4f}, validation error {error:.3f} ({seconds:.0f} s)")
        if error < best:
            best = error
            save_file(model.state_dict(), str(run / "model.safetensors"))
    record = {"config": asdict(config), "history": history, "best_validation_error": best}
    (run / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return run


def load_run(run: Path) -> RenderNet:
    model = RenderNet(base_state(pretrained=False), pretrained=False)
    model.load_state_dict(load_file(str(run / "model.safetensors")), strict=True)
    return model.eval()


# --- evaluation ---


def threshold_for(scores: NDArray[np.float64], labels: NDArray[np.int64], target: float = BPCER_TARGET) -> float:
    """The lowest threshold that calls at most `target` of the real crops rendered."""
    real = np.sort(scores[labels != RENDERED])
    if len(real) == 0:
        return 0.5
    allowed = math.floor(target * len(real))
    return float(np.nextafter(real[len(real) - 1 - allowed], np.inf))


def measure(split: Split, scores: NDArray[np.float64], threshold: float) -> dict[str, Any]:
    """APCER (renders taken for real) overall and for each kind of render, and BPCER (real people taken for renders),
    each with a 95 % interval; and how many people the measurement rests on."""
    rendered = scores >= threshold
    attacks = split.labels == RENDERED
    results: dict[str, Any] = {
        "threshold": threshold,
        "apcer": rate(~rendered[attacks]),
        "bpcer": rate(rendered[~attacks]),
        "by_kind": {kind: rate(~rendered[split.kinds == kind]) for kind in sorted(set(split.kinds[attacks]))},
        "people": {
            "real": len(set(split.people[~attacks])),
            "rendered": len(set(split.people[attacks])),
        },
    }
    return results


def evaluate(run: Path, crops: Path = CROPS, gates: Path = GATES) -> dict[str, Any]:
    """Choose the threshold on the validation split, measure on the test split, and check the release gates."""
    model = load_run(run)
    validation, test = load_split("validation", crops), load_split("test", crops)
    threshold = threshold_for(scores_of(model, validation), validation.labels)
    results: dict[str, Any] = {"test": measure(test, scores_of(model, test), threshold)}
    results["gates"] = check(results, gates)
    (run / "evaluation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


# --- export ---


def export(run: Path, version: str, models: Path = ROOT / "models" / "registry" / "render") -> Path:
    """The trained network as ONNX, proven to answer as PyTorch does, with a manifest; only after the gates pass."""
    evaluation = json.loads((run / "evaluation.json").read_text(encoding="utf-8"))
    failed = [gate["name"] for gate in evaluation["gates"] if not gate["passed"]]
    if failed:
        raise ValueError(f"the release gates failed: {', '.join(failed)}")
    model = load_run(run)
    target = models / version
    target.mkdir(parents=True, exist_ok=True)
    onnx_file = target / "render.onnx"
    program = torch.onnx.export(
        model,
        (torch.zeros(4, 3, SIZE, SIZE),),
        input_names=["pixels"],
        output_names=["probabilities"],
        # Any number of faces at once, from 1 to 64.
        dynamic_shapes={"pixels": {0: torch.export.Dim("faces", min=1, max=64)}},
        opset_version=OPSET,
        dynamo=True,
        verbose=False,
    )
    if program is None:
        raise RuntimeError("the ONNX exporter returned nothing")
    program.save(str(onnx_file), external_data=False)
    gap = parity(model, onnx_file)
    if gap > TOLERANCE:
        raise ValueError(f"ONNX answers differ from PyTorch's by {gap:.1e}")
    manifest = {
        "name": "render",
        "version": version,
        "model": {
            "file": onnx_file.name,
            "input": "pixels: float32 [faces, 3, 80, 80], blue-green-red, 0-255, cropped 2.7 face-sizes",
            "output": "probabilities: float32 [faces, 2], P(real), P(rendered)",
            "threshold": evaluation["test"]["threshold"],
        },
        "training": {
            "run": run.name,
            "base": "MiniFASNet V2 2.7 (Apache-2.0)",
            "data": "our own clips, ADR-0021",
        },
        "evaluation": evaluation["test"],
        "use": "recorded only",
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target


def parity(model: RenderNet, onnx_file: Path, samples: int = 8) -> float:
    session = onnxruntime.InferenceSession(str(onnx_file), providers=["CPUExecutionProvider"])
    pixels = np.random.default_rng(0).integers(0, 256, (samples, 3, SIZE, SIZE)).astype(np.float32)
    with torch.no_grad():
        reference = model(torch.from_numpy(pixels)).numpy()
    return float(np.abs(reference - session.run(None, {"pixels": pixels})[0]).max())


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - runs on the owner's data
    parser = argparse.ArgumentParser(prog="dwarpal-ml render_detector", description="Train the render detector")
    commands = parser.add_subparsers(dest="command", required=True)
    preparing = commands.add_parser("prepare", help="face crops from every clip, per split")
    preparing.add_argument("--every", type=int, default=5, help="use every n-th frame")
    training = commands.add_parser("train")
    training.add_argument("--epochs", type=int, default=Config.epochs)
    training.add_argument("--from-scratch", action="store_true", help="without MiniFASNet's weights")
    evaluating = commands.add_parser("evaluate")
    evaluating.add_argument("run", type=Path)
    exporting = commands.add_parser("export")
    exporting.add_argument("run", type=Path)
    exporting.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            detector = FaceDetector(THIRD_PARTY / "face_detection_yunet_2023mar.onnx")
            print(prepare(detector, every=args.every))
        elif args.command == "train":
            print(train(Config(epochs=args.epochs, pretrained=not args.from_scratch)))
        elif args.command == "evaluate":
            results = evaluate(args.run)
            print(json.dumps(results, indent=2))
            return 0 if all(gate["passed"] for gate in results["gates"]) else 1
        else:
            print(export(args.run, args.version))
    except (ValueError, FileNotFoundError) as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
