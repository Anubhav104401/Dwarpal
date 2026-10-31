from __future__ import annotations

import json
from pathlib import Path

from dwarpal_ml.export import adult_outcomes


def measured(rate: float, of: int) -> dict[str, float]:
    return {"rate": rate, "count": round(rate * of), "of": of, "lower": 0.0, "upper": 1.0}


def test_each_lines_adult_outcomes_come_from_the_test_split_rounded(tmp_path: Path) -> None:
    band = {"pass": measured(0.13333, 330), "step_up": measured(0.77272, 330), "fail": measured(0.09393, 330)}
    evaluation = {"limits": {"18": {"adults": {"18-20": band}}, "21": {"minors_passed": {}}}}
    (tmp_path / "evaluation-utkface-test.json").write_text(json.dumps(evaluation), encoding="utf-8")
    assert adult_outcomes(tmp_path, "utkface") == {
        18: [{"ages": "18-20", "faces": 330, "pass": 0.1333, "step_up": 0.7727, "fail": 0.0939}],
        21: [],
    }


def test_without_a_measured_test_split_there_is_nothing_to_show(tmp_path: Path) -> None:
    assert adult_outcomes(tmp_path, "utkface") == {}
