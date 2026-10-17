"""Evaluation: one fixed protocol for every model, on validation while developing and on the test split once.

uv run --package dwarpal-ml python -m dwarpal_ml.evaluate .runs/<run>                 validation
uv run --package dwarpal-ml python -m dwarpal_ml.evaluate .runs/<run> --split test    the locked exam, once
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from safetensors.torch import load_file
from scipy.optimize import minimize_scalar
from scipy.stats import beta
from torch.utils.data import DataLoader

from dwarpal_ml.data import FaceDataset, band_of
from dwarpal_ml.manifest import Row
from dwarpal_ml.model import AgeModel
from dwarpal_ml.prepare import PROCESSED
from dwarpal_ml.register import ROOT
from dwarpal_ml.risk import ADULT_MARGIN, DELTA

GATES = ROOT / "ml" / "gates.toml"
LIMITS = (13, 16, 18, 21)
# FairFace's band edges: for each of these ages, every face is known to be entirely above or entirely below it.
EDGES = (10, 20, 30, 40, 50, 60, 70)
BINS = 10

type Floats = NDArray[np.float64]


def softmax(logits: Floats, temperature: float = 1.0) -> Floats:
    scaled = logits / temperature
    scaled = scaled - scaled.max(axis=1, keepdims=True)
    weights = np.exp(scaled)
    return np.asarray(weights / weights.sum(axis=1, keepdims=True), dtype=np.float64)


def bands(rows: list[Row]) -> tuple[Floats, Floats]:
    pairs = np.array([band_of(row) for row in rows], dtype=np.float64).reshape(-1, 2)
    return pairs[:, 0], pairs[:, 1]


def band_probability(probabilities: Floats, low: Floats, high: Floats) -> Floats:
    ages = np.arange(probabilities.shape[1])
    inside = (ages >= low[:, None]) & (ages <= high[:, None])
    return np.asarray((probabilities * inside).sum(axis=1), dtype=np.float64)


def fit_temperature(logits: Floats, low: Floats, high: Floats) -> float:
    def surprise(temperature: float) -> float:
        likelihood = band_probability(softmax(logits, temperature), low, high)
        return float(-np.log(np.clip(likelihood, 1e-12, None)).mean())

    return float(minimize_scalar(surprise, bounds=(0.25, 4.0), method="bounded").x)


def interval(successes: int, trials: int, delta: float = DELTA) -> tuple[float, float]:
    lower = 0.0 if successes == 0 else float(beta.ppf(delta / 2, successes, trials - successes + 1))
    upper = 1.0 if successes == trials else float(beta.ppf(1 - delta / 2, successes + 1, trials - successes))
    return lower, upper


def rate(flags: NDArray[np.bool_]) -> dict[str, Any]:
    count, trials = int(flags.sum()), len(flags)
    if trials == 0:
        return {"rate": None, "count": 0, "of": 0, "lower": None, "upper": None}
    lower, upper = interval(count, trials)
    return {"rate": count / trials, "count": count, "of": trials, "lower": lower, "upper": upper}


def accuracy(mean_age: Floats, low: Floats, high: Floats) -> dict[str, float]:
    miss = np.clip(low - mean_age, 0, None) + np.clip(mean_age - high, 0, None)
    return {"faces": len(miss), "band_mae": float(miss.mean()), "in_band": float((miss == 0).mean())}


def calibration_error(probability: Floats, truth: NDArray[np.bool_], bins: int = BINS) -> float:
    which = np.minimum((probability * bins).astype(int), bins - 1)
    error = 0.0
    for b in range(bins):
        members = which == b
        if members.any():
            error += abs(float(probability[members].mean()) - float(truth[members].mean())) * members.mean()
    return error


def calibration(probabilities: Floats, low: Floats, high: Floats) -> dict[str, Any]:
    errors = {}
    for edge in EDGES:
        known = (low >= edge) | (high < edge)
        over = probabilities[known, edge:].sum(axis=1)
        errors[str(edge)] = calibration_error(over, low[known] >= edge)
    return {"ece": errors, "ece_mean": float(np.mean(list(errors.values())))}


def limit_view(probabilities: Floats, low: Floats, high: Floats, limit: int) -> dict[str, Any]:
    over = probabilities[:, limit:].sum(axis=1)
    minors = rate(over[high < limit] >= 0.5)
    adults = rate(over[low >= limit + ADULT_MARGIN] < 0.5)
    return {"clear_minors_rated_over": minors, "clear_adults_rated_under": adults, "minor_rate_upper": minors["upper"]}


def gap(values: list[float]) -> float | None:
    worst, best = max(values), min(values)
    if best == 0:
        return 1.0 if worst == 0 else None
    return worst / best


def order(view: str, name: str) -> tuple[int, str]:
    return (int(name.split("-")[0]), name) if view == "bands" else (0, name)


def evaluate(logits: Floats, rows: list[Row], temperature: float) -> dict[str, Any]:
    probabilities = softmax(logits, temperature)
    mean_age = probabilities @ np.arange(probabilities.shape[1])
    low, high = bands(rows)
    indices: dict[str, dict[str, list[int]]] = {
        "bands": defaultdict(list),
        "groups": defaultdict(list),
        "sexes": defaultdict(list),
    }
    for i, row in enumerate(rows):
        indices["bands"][f"{int(low[i])}-{int(high[i])}"].append(i)
        indices["groups"][row.group].append(i)
        indices["sexes"][row.sex].append(i)
    results: dict[str, Any] = {"faces": len(rows), "temperature": temperature}
    results["overall"] = accuracy(mean_age, low, high)
    for view, members in indices.items():
        results[view] = {}
        for name in sorted(members, key=partial(order, view)):
            picked = np.array(members[name])
            results[view][name] = {
                **accuracy(mean_age[picked], low[picked], high[picked]),
                "minors_rated_18_or_over": limit_view(probabilities[picked], low[picked], high[picked], 18)[
                    "clear_minors_rated_over"
                ],
            }
    results["limits"] = {str(limit): limit_view(probabilities, low, high, limit) for limit in LIMITS}
    results["calibration"] = {
        "before": calibration(softmax(logits), low, high),
        "after": calibration(probabilities, low, high),
    }
    groups = results["groups"].values()
    band_maes = [group["band_mae"] for group in groups]
    uppers = [group["minors_rated_18_or_over"]["upper"] for group in groups if group["minors_rated_18_or_over"]["of"]]
    results["fairness"] = {
        "band_mae_ratio": gap(band_maes),
        "worst_minor_rate_upper_18": max(uppers) if uppers else None,
    }
    return results


def lookup(results: dict[str, Any], path: str) -> Any:
    value: Any = results
    for part in path.split("."):
        value = value[part]
    return value


def check(results: dict[str, Any], gates: Path = GATES) -> list[dict[str, Any]]:
    outcomes = []
    for gate in tomllib.loads(gates.read_text(encoding="utf-8"))["gate"]:
        value = lookup(results, gate["metric"])
        passed = value is not None and value <= gate.get("max", np.inf) and value >= gate.get("min", -np.inf)
        outcomes.append({"name": gate["name"], "metric": gate["metric"], "value": value, "passed": bool(passed)})
    return outcomes


def predict(run: Path, split: str, workers: int, name: str | None = None) -> tuple[Floats, list[Row]]:
    record = json.loads((run / "run.json").read_text(encoding="utf-8"))
    trained_on = record["config"]["dataset"]
    name = name or trained_on
    dataset = FaceDataset(name, split, PROCESSED / f"{name}.zip")
    cache = run / (f"logits-{split}.npy" if name == trained_on else f"logits-{name}-{split}.npy")
    if cache.is_file():
        return np.load(cache), dataset.rows
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AgeModel(record["config"]["backbone"])
    model.load_state_dict(load_file(str(run / "model.safetensors")))
    model = model.to(device).eval()
    outputs = []
    with torch.no_grad():
        for images, *_ in DataLoader(dataset, batch_size=128, num_workers=workers):
            with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                outputs.append(model(images.to(device)).float().cpu().numpy())
    logits = np.concatenate(outputs).astype(np.float64)
    np.save(cache, logits)
    return logits, dataset.rows


def summary(results: dict[str, Any]) -> str:
    overall, limit = results["overall"], results["limits"]["18"]
    minors, adults = limit["clear_minors_rated_over"], limit["clear_adults_rated_under"]
    lines = [
        f"{results['split']}: {results['faces']:,} faces, temperature {results['temperature']:.3f}",
        f"band-MAE {overall['band_mae']:.3f}, in band {overall['in_band']:.1%}",
        f"18: children under 10 rated 18+ {minors['rate']:.2%} ({minors['count']}/{minors['of']}, up to "
        f"{minors['upper']:.2%}); adults 21+ rated under 18 {adults['rate']:.2%}",
        f"calibration error {results['calibration']['before']['ece_mean']:.4f} -> "
        f"{results['calibration']['after']['ece_mean']:.4f}",
        "groups: " + ", ".join(f"{name} {group['band_mae']:.2f}" for name, group in results["groups"].items()),
    ]
    lines += [f"gate {'PASS' if g['passed'] else 'FAIL'}  {g['name']}: {g['value']}" for g in results["gates"]]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml evaluate", description="Evaluate a trained age model")
    parser.add_argument("run", type=Path, help="a run folder in .runs/")
    parser.add_argument("--split", choices=("val", "test"), default="val")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    target = args.run / f"evaluation-{args.split}.json"
    if args.split == "test" and target.exists():
        print(f"refused  {args.run.name} has already been evaluated on the test split: {target.name}")
        return 1
    val_logits, val_rows = predict(args.run, "val", args.workers)
    temperature = fit_temperature(val_logits, *bands(val_rows))
    logits, rows = (val_logits, val_rows) if args.split == "val" else predict(args.run, "test", args.workers)
    results = {"run": args.run.name, "split": args.split, **evaluate(logits, rows, temperature)}
    results["gates"] = check(results)
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(summary(results))
    return 0 if all(gate["passed"] for gate in results["gates"]) else 1


if __name__ == "__main__":
    sys.exit(main())
