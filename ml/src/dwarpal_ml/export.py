"""Export a trained, calibrated age model to ONNX for serving, prove it gives the same answers, and write its manifest.

uv run --package dwarpal-ml python -m dwarpal_ml.export .runs/<run> utkface --version age-convnext-tiny-2026.10.17
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime
import torch
from numpy.typing import NDArray
from safetensors.torch import load_file
from torch import nn

from dwarpal_ml.data import fit, usable_rows
from dwarpal_ml.evaluate import bands, fit_temperature, predict
from dwarpal_ml.model import AgeModel
from dwarpal_ml.prepare import DETECTOR, PROCESSED, central_face
from dwarpal_ml.register import ROOT, dataset
from dwarpal_vision import FaceDetector, align_face, decode_image, to_model_input

REGISTRY = ROOT / "models" / "registry" / "age"
OPSET = 18
PARITY_FACES = 512
# The exported model must agree with PyTorch to within this, on every probability of every face.
TOLERANCE = 1e-4
BURST = 5
LIMIT = 18

type Floats = NDArray[np.float64]


class Served(nn.Module):
    """The trained model with its calibration built in: pixels in, temperature-corrected probabilities out."""

    def __init__(self, model: AgeModel, temperature: float) -> None:
        super().__init__()
        self.model = model
        self.temperature = temperature

    def forward(self, pixels: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.model(pixels).float() / self.temperature, dim=-1)


def load_served(run: Path, temperature: float) -> Served:
    record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    model = AgeModel(record["config"]["backbone"])
    model.load_state_dict(load_file(str(run / "model.safetensors")))
    return Served(model, temperature).eval()


def export(served: Served, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    example = torch.zeros(BURST, 3, 224, 224)
    faces = torch.export.Dim("faces", min=1, max=64)
    program = torch.onnx.export(
        served,
        (example,),
        input_names=["pixels"],
        output_names=["probabilities"],
        dynamic_shapes={"pixels": {0: faces}},
        opset_version=OPSET,
        dynamo=True,
        verbose=False,
    )
    if program is None:
        raise RuntimeError("the ONNX exporter returned nothing")
    program.save(str(target), external_data=False)


def session(path: Path, threads: int = 0) -> onnxruntime.InferenceSession:
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = threads
    return onnxruntime.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


def run_onnx(model: onnxruntime.InferenceSession, batch: NDArray[np.float32]) -> Floats:
    return np.asarray(model.run(["probabilities"], {"pixels": batch})[0], dtype=np.float64)


def expected(probabilities: Floats) -> Floats:
    return np.asarray(probabilities @ np.arange(probabilities.shape[1]), dtype=np.float64)


def parity(served: Served, model: onnxruntime.InferenceSession, faces: list[NDArray[np.uint8]]) -> dict[str, Any]:
    gaps = []
    for start in range(0, len(faces), 64):
        batch = to_model_input(faces[start : start + 64])
        with torch.no_grad():
            reference = served(torch.from_numpy(batch)).double().numpy()
        gaps.append(np.abs(reference - run_onnx(model, batch)).max(axis=1))
    largest = float(np.concatenate(gaps).max())
    return {
        "faces": len(faces),
        "largest_probability_gap": largest,
        "tolerance": TOLERANCE,
        "passed": largest <= TOLERANCE,
    }


def serving_path(model: onnxruntime.InferenceSession, name: str, count: int) -> dict[str, Any]:
    entry = dataset(name)
    rows = [row for row in usable_rows(name) if row.split == "val"][:count]
    detector = FaceDetector(DETECTOR)
    trained, served = [], []
    with zipfile.ZipFile(PROCESSED / f"{name}.zip") as prepared, zipfile.ZipFile(entry.folder / rows[0].archive) as raw:
        for row in rows:
            image = decode_image(raw.read(row.member))
            faces = detector.detect(image)
            if not faces:
                continue
            trained.append(fit(decode_image(prepared.read(row.image_id))))
            served.append(align_face(image, central_face(image, faces)))
    training_view = np.concatenate(
        [run_onnx(model, to_model_input(trained[i : i + 64])) for i in range(0, len(trained), 64)]
    )
    serving_view = np.concatenate(
        [run_onnx(model, to_model_input(served[i : i + 64])) for i in range(0, len(served), 64)]
    )
    age_gap = np.abs(expected(training_view) - expected(serving_view))
    chance_gap = np.abs(training_view[:, LIMIT:].sum(axis=1) - serving_view[:, LIMIT:].sum(axis=1))
    return {
        "faces": len(trained),
        "mean_age_gap_years": float(age_gap.mean()),
        "age_gap_95th_percentile_years": float(np.percentile(age_gap, 95)),
        "mean_gap_in_chance_of_18_or_over": float(chance_gap.mean()),
    }


def latency(model: onnxruntime.InferenceSession, face: NDArray[np.uint8], repeats: int = 100) -> dict[str, float]:
    batch = to_model_input([face] * BURST)
    run_onnx(model, batch)
    times = []
    for _ in range(repeats):
        started = time.perf_counter()
        run_onnx(model, batch)
        times.append((time.perf_counter() - started) * 1000.0)
    return {
        "faces_per_call": BURST,
        "p50_ms": float(np.percentile(times, 50)),
        "p95_ms": float(np.percentile(times, 95)),
    }


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(
    run: Path, calibration_name: str, version: str, model_file: Path, checks: dict[str, Any]
) -> dict[str, Any]:
    record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    calibration = json.loads((run / f"calibration-{calibration_name}.json").read_text(encoding="utf-8"))
    trained_on, measured_on = dataset(record["config"]["dataset"]), dataset(calibration_name)
    thresholds = [
        {
            "min_age": int(limit),
            **{
                key: certified["thresholds"][key]
                for key in ("risk_budget", "tau_pass", "tau_fail", "minor_bound", "adult_bound")
            },
            "cells": certified["cells"],
        }
        for limit, certified in calibration["limits"].items()
        if certified["thresholds"] is not None
    ]
    return {
        "name": "age",
        "version": version,
        "serves": version,
        "calibrated": False,
        "note": (
            "Thresholds are risk-controlled on exact ages, but per age only, at the budgets listed, on ages that were "
            "estimated rather than documented. The release standard (NFR-01: 2 % per age and group) is not met, so "
            "this model may decide test-mode sessions only."
        ),
        "permitted_use": "non-commercial research only",
        "model": {
            "file": model_file.name,
            "sha256": sha256_of(model_file),
            "bytes": model_file.stat().st_size,
            "opset": OPSET,
            "input": "pixels: float32 [faces, 3, 224, 224], RGB, 0-255, aligned by dwarpal_vision.align_face",
            "output": "probabilities: float32 [faces, 101], P(age = 0 ... 100), temperature-corrected",
            "temperature": calibration["temperature"],
        },
        "training": {
            "run": run.name,
            "backbone": record["config"]["backbone"],
            "pretrained": record.get("pretrained"),
            "dataset": {"name": trained_on.name, "licence": trained_on.licence, "age_source": trained_on.age_source},
            "git": record["git"],
        },
        "calibration": {
            "dataset": measured_on.name,
            "licence": measured_on.licence,
            "age_source": measured_on.age_source,
            "faces": calibration["faces"],
        },
        "thresholds": thresholds,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml export", description="Export a calibrated age model to ONNX")
    parser.add_argument("run", type=Path, help="a run folder in .runs/, already calibrated")
    parser.add_argument("calibration", help="the exact-age dataset it was calibrated on")
    parser.add_argument("--version", required=True, help="the model's version name in the registry")
    args = parser.parse_args(argv)
    record = json.loads((args.run / "run.json").read_text(encoding="utf-8"))
    val_logits, val_rows = predict(args.run, "val", 6)
    temperature = fit_temperature(val_logits, *bands(val_rows))
    served = load_served(args.run, temperature)
    target = REGISTRY / args.version / "model.onnx"
    export(served, target)
    onnx_model = session(target)
    name = record["config"]["dataset"]
    with zipfile.ZipFile(PROCESSED / f"{name}.zip") as prepared:
        rows = [row for row in usable_rows(name) if row.split == "val"][:PARITY_FACES]
        faces = [fit(decode_image(prepared.read(row.image_id))) for row in rows]
    checks = {
        "parity": parity(served, onnx_model, faces),
        "serving_path": serving_path(onnx_model, name, PARITY_FACES),
        "cpu_latency": latency(session(target, threads=1), faces[0]),
    }
    built = manifest(args.run, args.calibration, args.version, target, checks)
    # "\n" line endings on every system, as the repository and its JSON formatter expect.
    target_manifest = REGISTRY / args.version / "manifest.json"
    target_manifest.write_text(json.dumps(built, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(checks, indent=2))
    return 0 if checks["parity"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
