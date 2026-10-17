"""Exact-age calibration: set the safety lines on one half of an exact-age dataset with risk control (§2.14), then
measure the decisions those lines make on the other half, which is opened once.

uv run --package dwarpal-ml python -m dwarpal_ml.calibrate .runs/<run> utkface
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from dwarpal_ml.evaluate import Floats, bands, fit_temperature, predict, rate, softmax
from dwarpal_ml.manifest import Row
from dwarpal_ml.register import dataset
from dwarpal_ml.risk import MINOR_SPAN, CalibrationError, Scored, calibrate

LIMITS = (13, 16, 18, 21)
# Tried from strictest to loosest: the first budget the data can certify is used, and every stricter one it couldn't
# is recorded with the reason.
BUDGETS = (0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20)
# Adults, by years above the limit: N to N+2, N+3 to N+6, N+7 to N+11, and N+12 and over.
ADULT_BANDS = ((0, 2), (3, 6), (7, 11), (12, None))
AGE_RANGES = ((0, 12), (13, 17), (18, 24), (25, 39), (40, 59), (60, 100))


def over(probabilities: Floats, limit: int) -> Floats:
    return np.asarray(probabilities[:, limit:].sum(axis=1), dtype=np.float64)


def cells(by_group: bool) -> str:
    return "age and group" if by_group else "age"


def certify(people: list[Scored], limit: int) -> dict[str, Any]:
    refused = []
    for budget in BUDGETS:
        for by_group in (True, False):
            try:
                thresholds = calibrate(people, limit, budget, by_group=by_group)
            except CalibrationError as error:
                refused.append({"risk_budget": budget, "cells": cells(by_group), "reason": str(error)})
                continue
            return {"thresholds": asdict(thresholds), "cells": cells(by_group), "refused": refused}
    return {"thresholds": None, "cells": None, "refused": refused}


def decide(p_over: Floats, tau_pass: float, tau_fail: float) -> NDArray[np.str_]:
    return np.where(p_over >= tau_pass, "pass", np.where(p_over <= tau_fail, "fail", "step_up"))


def outcomes(decisions: NDArray[np.str_]) -> dict[str, Any]:
    return {outcome: rate(decisions == outcome) for outcome in ("pass", "step_up", "fail")}


def decisions_view(probabilities: Floats, rows: list[Row], thresholds: dict[str, Any], limit: int) -> dict[str, Any]:
    ages = np.array([row.age_exact for row in rows])
    groups = np.array([row.group for row in rows])
    decisions = decide(over(probabilities, limit), thresholds["tau_pass"], thresholds["tau_fail"])
    minors = (ages >= limit - MINOR_SPAN) & (ages < limit)
    view: dict[str, Any] = {
        "minors_passed_by_age": {
            str(age): rate(decisions[ages == age] == "pass") for age in range(limit - MINOR_SPAN, limit)
        },
        "minors_passed": rate(decisions[minors] == "pass"),
        "minors_passed_by_group": {
            group: rate(decisions[minors & (groups == group)] == "pass") for group in sorted(set(groups))
        },
        "younger_passed": rate(decisions[ages < limit - MINOR_SPAN] == "pass"),
        "adults": {},
    }
    for start, end in ADULT_BANDS:
        chosen = (ages >= limit + start) & (ages <= (limit + end if end is not None else 200))
        name = f"{limit + start}-{limit + end}" if end is not None else f"{limit + start}+"
        view["adults"][name] = outcomes(decisions[chosen])
    return view


def exact_accuracy(probabilities: Floats, rows: list[Row]) -> dict[str, Any]:
    ages = np.array([row.age_exact for row in rows], dtype=np.float64)
    error = np.abs(probabilities @ np.arange(probabilities.shape[1]) - ages)
    by_range: dict[str, float | None] = {}
    for low, high in AGE_RANGES:
        chosen = error[(ages >= low) & (ages <= high)]
        by_range[f"{low}-{high}"] = float(chosen.mean()) if len(chosen) else None
    return {"mae": float(error.mean()), "mae_by_age": by_range}


def summary(calibration: dict[str, Any], results: dict[str, Any]) -> str:
    lines = [f"{results['dataset']} test: {results['faces']:,} faces, MAE {results['accuracy']['mae']:.2f} years"]
    for limit, certified in calibration["limits"].items():
        thresholds = certified["thresholds"]
        if thresholds is None:
            lines.append(f"{limit}: no budget up to {BUDGETS[-1]:.0%} could be certified")
            continue
        view = results["limits"][limit]
        ages = ", ".join(f"{age} {r['rate']:.1%}" for age, r in view["minors_passed_by_age"].items())
        lines.append(
            f"{limit}: budget {thresholds['risk_budget']:.1%} per {certified['cells']}, tau_pass "
            f"{thresholds['tau_pass']:.4f}, tau_fail {thresholds['tau_fail']:.4f}; minors passed {ages}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml calibrate", description="Calibrate thresholds on exact ages")
    parser.add_argument("run", type=Path, help="a run folder in .runs/")
    parser.add_argument("name", help="an approved dataset with exact ages")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    entry = dataset(args.name)
    if entry.age_labels != "exact":
        print(f"refused  {entry.name} has no exact ages")
        return 1
    target = args.run / f"evaluation-{entry.name}-test.json"
    if target.exists():
        print(f"refused  {args.run.name} has already been evaluated on {entry.name}'s test split: {target.name}")
        return 1
    val_logits, val_rows = predict(args.run, "val", args.workers)
    temperature = fit_temperature(val_logits, *bands(val_rows))
    logits, rows = predict(args.run, "calib", args.workers, entry.name)
    probabilities = softmax(logits, temperature)
    calibration: dict[str, Any] = {
        "run": args.run.name,
        "dataset": entry.name,
        "age_source": entry.age_source,
        "temperature": temperature,
        "faces": len(rows),
        "limits": {},
    }
    for limit in LIMITS:
        people = [
            Scored(row.age_exact or 0, row.group, float(p))
            for row, p in zip(rows, over(probabilities, limit), strict=True)
        ]
        calibration["limits"][str(limit)] = certify(people, limit)
    (args.run / f"calibration-{entry.name}.json").write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    logits, rows = predict(args.run, "test", args.workers, entry.name)
    probabilities = softmax(logits, temperature)
    results: dict[str, Any] = {
        "run": args.run.name,
        "dataset": entry.name,
        "age_source": entry.age_source,
        "faces": len(rows),
        "temperature": temperature,
        "accuracy": exact_accuracy(probabilities, rows),
        "limits": {
            str(limit): decisions_view(probabilities, rows, certified["thresholds"], limit)
            for limit, certified in ((int(k), v) for k, v in calibration["limits"].items())
            if certified["thresholds"] is not None
        },
    }
    target.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(summary(calibration, results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
