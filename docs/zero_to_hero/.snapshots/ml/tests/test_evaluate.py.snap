"""Tests for the evaluation protocol: probabilities, temperature, intervals, calibration, views, gates and the lock."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from dwarpal_ml import evaluate
from dwarpal_ml.manifest import Row
from dwarpal_ml.targets import AGES


def row(low: int, high: int | None, group: str = "a", sex: str = "female") -> Row:
    return Row("x", "d", "a.zip", "x", low, high, None, sex, group, "CC0", "val")


def peaked(ages: list[int], sharpness: float = 4.0) -> np.ndarray:
    logits = np.zeros((len(ages), AGES))
    for i, age in enumerate(ages):
        logits[i] = -sharpness * np.abs(np.arange(AGES) - age) / 5
    return logits


def test_probabilities_add_up_to_one_and_temperature_sharpens_or_softens() -> None:
    logits = peaked([20, 50])
    for temperature in (0.5, 1.0, 2.0):
        assert evaluate.softmax(logits, temperature).sum(axis=1) == pytest.approx([1.0, 1.0])
    assert (
        evaluate.softmax(logits, 0.5)[0, 20]
        > evaluate.softmax(logits, 1.0)[0, 20]
        > evaluate.softmax(logits, 2.0)[0, 20]
    )


def test_the_fitted_temperature_undoes_overconfidence() -> None:
    rng = np.random.default_rng(0)
    centres = rng.integers(5, 80, 3000)
    honest = peaked(centres.tolist(), sharpness=1.0)
    truth = np.array([rng.choice(AGES, p=p) for p in evaluate.softmax(honest)])
    overconfident = honest * 3.0
    temperature = evaluate.fit_temperature(overconfident, truth.astype(float), truth.astype(float))
    assert temperature == pytest.approx(3.0, rel=0.15)


@given(st.integers(1, 400).flatmap(lambda n: st.tuples(st.integers(0, n), st.just(n))))
def test_the_interval_always_contains_the_observed_rate(case: tuple[int, int]) -> None:
    count, trials = case
    lower, upper = evaluate.interval(count, trials)
    assert 0.0 <= lower <= count / trials <= upper <= 1.0


def test_a_perfectly_calibrated_forecast_has_no_calibration_error() -> None:
    probability = np.repeat([0.05, 0.35, 0.75], 100)
    truth = np.concatenate([np.arange(100) < 5, np.arange(100) < 35, np.arange(100) < 75])
    assert evaluate.calibration_error(probability, truth) == pytest.approx(0.0)
    assert evaluate.calibration_error(np.full(100, 0.9), np.zeros(100, dtype=bool)) == pytest.approx(0.9)


def test_clear_minors_and_clear_adults_are_chosen_by_their_whole_band() -> None:
    rows = [row(3, 9), row(10, 19), row(20, 29), row(30, 39)]
    probabilities = evaluate.softmax(peaked([25, 15, 25, 35]))
    view = evaluate.limit_view(probabilities, *evaluate.bands(rows), 18)
    minors, adults = view["clear_minors_rated_over"], view["clear_adults_rated_under"]
    assert (minors["count"], minors["of"]) == (1, 1)
    assert (adults["count"], adults["of"]) == (0, 1)


def test_every_view_is_reported_and_the_gap_is_worst_over_best() -> None:
    rows = [row(20, 29, "a"), row(20, 29, "b", "male"), row(3, 9, "a"), row(70, None, "b", "male")]
    results = evaluate.evaluate(peaked([31, 33, 6, 80]), rows, 1.0)
    assert list(results["bands"]) == ["3-9", "20-29", "70-100"]
    assert set(results["groups"]) == {"a", "b"}
    assert set(results["sexes"]) == {"female", "male"}
    maes = [group["band_mae"] for group in results["groups"].values()]
    assert results["fairness"]["band_mae_ratio"] == pytest.approx(max(maes) / min(maes))


def test_the_gap_between_groups_is_defined_even_when_one_is_perfect() -> None:
    assert evaluate.gap([2.0, 1.6]) == pytest.approx(1.25)
    assert evaluate.gap([0.0, 0.0]) == 1.0
    assert evaluate.gap([1.0, 0.0]) is None


def test_gates_pass_and_fail_by_their_limits(tmp_path: Path) -> None:
    gates = tmp_path / "gates.toml"
    gates.write_text(
        '[[gate]]\nname = "low"\nmetric = "a.b"\nmax = 1.0\nwhy = "-"\n'
        '[[gate]]\nname = "high"\nmetric = "c"\nmin = 5\nwhy = "-"\n'
        '[[gate]]\nname = "missing"\nmetric = "d"\nmax = 1.0\nwhy = "-"\n',
        encoding="utf-8",
    )
    outcomes = evaluate.check({"a": {"b": 0.5}, "c": 4, "d": None}, gates)
    assert [(gate["name"], gate["passed"]) for gate in outcomes] == [("low", True), ("high", False), ("missing", False)]


def test_the_project_gates_all_name_real_results() -> None:
    rows = [row(3, 9, "a"), row(20, 29, "b"), row(40, 49, "a"), row(3, 9, "b")]
    results = evaluate.evaluate(peaked([6, 25, 45, 7]), rows, 1.0)
    assert all(gate["value"] is not None for gate in evaluate.check(results))


def test_the_test_split_is_evaluated_only_once(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "evaluation-test.json").write_text("{}", encoding="utf-8")
    assert evaluate.main([str(tmp_path), "--split", "test"]) == 1
    assert "already been evaluated" in capsys.readouterr().out
