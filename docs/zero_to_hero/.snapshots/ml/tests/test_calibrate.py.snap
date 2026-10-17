"""Tests for exact-age calibration: the budget search, its fallback to age-only cells, decisions and the lock."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from dwarpal_ml import calibrate
from dwarpal_ml.manifest import Row
from dwarpal_ml.risk import Scored


def row(age: int, group: str = "a") -> Row:
    return Row("x", "d", "a.zip", "x", age, age, age, "female", group, "CC0", "test")


def people(per_cell: int, groups: tuple[str, ...]) -> list[Scored]:
    rng = np.random.default_rng(0)
    crowd = []
    for age in range(8, 40):
        for group in groups:
            centre = min(0.98, max(0.02, (age - 12) / 12))
            crowd += [
                Scored(age, group, float(np.clip(rng.normal(centre, 0.1), 0.001, 0.999))) for _ in range(per_cell)
            ]
    return crowd


def test_enough_people_in_every_group_are_certified_per_group_at_the_strictest_budget() -> None:
    certified = calibrate.certify(people(400, ("a", "b")), 18)
    assert certified["cells"] == "age and group"
    assert certified["thresholds"]["risk_budget"] == 0.02
    assert certified["refused"] == []


def test_too_few_per_group_falls_back_to_age_cells_and_says_why() -> None:
    crowd = people(100, ("a", "b"))
    certified = calibrate.certify(crowd, 18)
    assert certified["cells"] == "age"
    assert certified["thresholds"]["by_group"] is False
    first = certified["refused"][0]
    assert (first["risk_budget"], first["cells"]) == (0.02, "age and group")
    assert "too few minors" in first["reason"]


def test_far_too_few_people_certify_nothing() -> None:
    certified = calibrate.certify(people(3, ("a",)), 18)
    assert certified["thresholds"] is None
    assert len(certified["refused"]) == 2 * len(calibrate.BUDGETS)


def test_the_two_lines_split_every_face_into_pass_step_up_or_fail() -> None:
    decisions = calibrate.decide(np.array([0.95, 0.5, 0.05, 0.9]), tau_pass=0.9, tau_fail=0.1)
    assert decisions.tolist() == ["pass", "step_up", "fail", "pass"]


def test_decisions_are_counted_per_exact_age_group_and_adult_band() -> None:
    rows = [row(16), row(16, "b"), row(17), row(5), row(19), row(30)]
    probabilities = np.zeros((6, 101))
    for i, p_over in enumerate([0.95, 0.2, 0.5, 0.0, 0.5, 1.0]):
        probabilities[i, 18] = p_over
        probabilities[i, 0] = 1 - p_over
    view = calibrate.decisions_view(probabilities, rows, {"tau_pass": 0.9, "tau_fail": 0.1}, 18)
    assert view["minors_passed_by_age"]["16"]["count"] == 1
    assert view["minors_passed"]["of"] == 3
    assert view["minors_passed_by_group"]["b"]["count"] == 0
    assert view["younger_passed"]["of"] == 1
    assert view["adults"]["18-20"]["step_up"]["count"] == 1
    assert view["adults"]["30+"]["pass"]["count"] == 1


def test_exact_accuracy_is_the_average_distance_in_years() -> None:
    probabilities = np.zeros((2, 101))
    probabilities[0, 20] = probabilities[1, 50] = 1.0
    accuracy = calibrate.exact_accuracy(probabilities, [row(22), row(50)])
    assert accuracy["mae"] == pytest.approx(1.0)
    assert accuracy["mae_by_age"]["18-24"] == pytest.approx(2.0)
    assert accuracy["mae_by_age"]["0-12"] is None


def test_only_exact_ages_are_calibrated_and_each_test_split_only_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert calibrate.main([str(tmp_path), "fairface"]) == 1
    (tmp_path / "evaluation-utkface-test.json").write_text("{}", encoding="utf-8")
    assert calibrate.main([str(tmp_path), "utkface"]) == 1
    out = capsys.readouterr().out
    assert "no exact ages" in out
    assert "already been evaluated" in out
