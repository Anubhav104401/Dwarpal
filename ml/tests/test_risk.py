"""Tests for risk-controlled thresholds: the bound itself, the threshold search, and the refusals."""

from __future__ import annotations

import random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dwarpal_ml.risk import (
    CalibrationError,
    Scored,
    calibrate,
    cells_of,
    clopper_pearson_upper,
    minimum_cell_size,
    passes_at,
    tau_pass_for,
    worst_bound,
)


def test_zero_passes_need_149_people_to_prove_two_percent() -> None:
    assert minimum_cell_size(0.02) == 149
    assert clopper_pearson_upper(0, 149) <= 0.02 < clopper_pearson_upper(0, 148)
    assert clopper_pearson_upper(5, 5) == 1.0


@given(st.integers(1, 2000).flatmap(lambda n: st.tuples(st.integers(0, n), st.just(n))))
def test_the_bound_never_falls_below_what_was_seen(case: tuple[int, int]) -> None:
    successes, trials = case
    assert clopper_pearson_upper(successes, trials) >= successes / trials


@given(st.integers(1, 500), st.integers(0, 499))
def test_more_passes_never_lower_the_bound_and_more_people_never_raise_it(trials: int, successes: int) -> None:
    successes = min(successes, trials - 1)
    assert clopper_pearson_upper(successes + 1, trials) >= clopper_pearson_upper(successes, trials)
    assert clopper_pearson_upper(successes, trials + 1) <= clopper_pearson_upper(successes, trials)


def population(seed: int, per_cell: int = 200, groups: tuple[str, ...] = ("a", "b")) -> list[Scored]:
    rng = random.Random(seed)  # noqa: S311 - reproducible test data, not secrets
    people = []
    for age in range(8, 40):
        for group in groups:
            centre = min(0.98, max(0.02, (age - 12) / 12))
            people += [Scored(age, group, min(0.999, max(0.001, rng.gauss(centre, 0.15)))) for _ in range(per_cell)]
    return people


@given(st.integers(0, 10_000))
def test_the_pass_threshold_is_safe_and_the_lowest_safe_one(seed: int) -> None:
    people = population(seed)
    tau, bound = tau_pass_for(people, 18, 0.02)
    minors = cells_of((f"{p.age}{p.group}", p.p_over) for p in people if 13 <= p.age < 18)
    assert bound == worst_bound(minors, passes_at(tau), 0.05) <= 0.02
    lower = max((s for cell in minors.values() for s in cell if s < tau), default=None)
    if lower is not None:
        assert worst_bound(minors, passes_at(lower), 0.05) > 0.02


def test_calibration_gives_both_thresholds_in_order() -> None:
    thresholds = calibrate(population(1), 18, 0.02)
    assert 0.0 <= thresholds.tau_fail < thresholds.tau_pass <= 1.0
    assert thresholds.minor_bound <= 0.02
    assert thresholds.adult_bound <= 0.01


def test_too_few_people_in_any_cell_is_refused_and_named() -> None:
    people = [p for p in population(2) if not (p.age == 15 and p.group == "b")]
    people += [Scored(15, "b", 0.1)] * 100
    with pytest.raises(CalibrationError, match=r"age 15 · b \(100\)"):
        tau_pass_for(people, 18, 0.02)


def test_a_missing_age_is_refused() -> None:
    with pytest.raises(CalibrationError, match=r"ages \[16\]"):
        tau_pass_for([p for p in population(3) if p.age != 16], 18, 0.02)


def test_a_model_that_cannot_tell_ages_apart_passes_and_fails_no_one() -> None:
    blind = [Scored(age, "a", 0.5) for age in range(8, 40) for _ in range(800)]
    thresholds = calibrate(blind, 18, 0.02)
    assert thresholds.tau_fail < 0.5 < thresholds.tau_pass


def test_a_model_that_separates_perfectly_gets_lines_that_never_cross() -> None:
    minors = [Scored(age, "a", 0.9) for age in range(13, 18) for _ in range(800)]
    adults = [Scored(age, "a", 0.95) for age in range(21, 40) for _ in range(800)]
    thresholds = calibrate(minors + adults, 18, 0.02)
    assert 0.9 <= thresholds.tau_fail < thresholds.tau_pass <= 0.95
    assert thresholds.minor_bound <= 0.02
    assert thresholds.adult_bound <= 0.01
