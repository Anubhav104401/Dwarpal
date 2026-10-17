"""Risk-controlled thresholds (ADR-0006): the lowest pass bar whose under-age pass rate is provably small.

For a minimum age N, the pass threshold is the lowest score bar at which, for every exact age from N-5 to N-1 and
every group, the one-sided Clopper-Pearson upper bound of the share of those people who would pass is at most the
risk budget, at confidence 1 - delta. The fail threshold is chosen the same way for adults aged N+3 and over, so
that they are almost never failed outright.
"""

from __future__ import annotations

import bisect
import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from scipy.stats import beta

DELTA = 0.05
MINOR_SPAN = 5
ADULT_MARGIN = 3
ADULT_FAIL_BUDGET = 0.01

type Cells = dict[str, list[float]]
type Count = Callable[[list[float]], int]


@dataclass(frozen=True)
class Scored:
    age: int
    group: str
    p_over: float


@dataclass(frozen=True)
class Thresholds:
    min_age: int
    risk_budget: float
    tau_pass: float
    tau_fail: float
    minor_bound: float
    adult_bound: float
    by_group: bool = True


class CalibrationError(ValueError):
    """The calibration data can't support a guarantee, and saying so is safer than returning a threshold."""


def cell_name(person: Scored, by_group: bool) -> str:
    return f"age {person.age} · {person.group}" if by_group else f"age {person.age}"


def clopper_pearson_upper(successes: int, trials: int, delta: float = DELTA) -> float:
    """The one-sided upper bound, at confidence 1 - delta, of a rate observed as `successes` out of `trials`."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError(f"need 0 <= successes <= trials and trials > 0, got {successes} of {trials}")
    if successes == trials:
        return 1.0
    return float(beta.ppf(1.0 - delta, successes + 1, trials - successes))


def minimum_cell_size(epsilon: float, delta: float = DELTA) -> int:
    """The fewest people a cell needs before even zero passes can prove a rate of at most epsilon."""
    return math.ceil(math.log(delta) / math.log(1.0 - epsilon))


def cells_of(labelled: Iterable[tuple[str, float]]) -> Cells:
    cells: dict[str, list[float]] = defaultdict(list)
    for label, score in labelled:
        cells[label].append(score)
    return {label: sorted(scores) for label, scores in cells.items()}


def check_size(cells: Cells, epsilon: float, delta: float, who: str) -> None:
    needed = minimum_cell_size(epsilon, delta)
    small = sorted(f"{label} ({len(scores)})" for label, scores in cells.items() if len(scores) < needed)
    if small:
        raise CalibrationError(f"too few {who} to certify {epsilon:.0%} (need {needed} per cell): " + "; ".join(small))


def worst_bound(cells: Cells, count: Count, delta: float) -> float:
    return max(clopper_pearson_upper(count(scores), len(scores), delta) for scores in cells.values())


def first_safe(candidates: Sequence[float], is_safe: Callable[[float], bool]) -> float:
    """The first safe candidate, given that once a candidate is safe, every later one is safe too."""
    low, high = 0, len(candidates) - 1
    while low < high:
        middle = (low + high) // 2
        if is_safe(candidates[middle]):
            high = middle
        else:
            low = middle + 1
    return candidates[low]


def passes_at(tau: float) -> Count:
    return lambda scores: len(scores) - bisect.bisect_left(scores, tau)


def fails_at(tau: float) -> Count:
    return lambda scores: bisect.bisect_right(scores, tau)


def tau_pass_for(
    people: Sequence[Scored], min_age: int, epsilon: float, delta: float = DELTA, by_group: bool = True
) -> tuple[float, float]:
    """The lowest pass threshold that keeps every under-age cell's pass rate provably at most epsilon."""
    ages = range(min_age - MINOR_SPAN, min_age)
    minors = [person for person in people if person.age in ages]
    missing = sorted(set(ages) - {person.age for person in minors})
    if missing:
        raise CalibrationError(f"no calibration data for ages {missing}")
    cells = cells_of((cell_name(person, by_group), person.p_over) for person in minors)
    check_size(cells, epsilon, delta, "minors")
    scores = sorted({score for cell in cells.values() for score in cell})
    candidates = [0.0, *(math.nextafter(score, math.inf) for score in scores)]
    tau = first_safe(candidates, lambda t: worst_bound(cells, passes_at(t), delta) <= epsilon)
    if tau > 1.0:
        raise CalibrationError("a minor scored 1.0: no pass threshold is safe")
    return tau, worst_bound(cells, passes_at(tau), delta)


def tau_fail_for(
    people: Sequence[Scored],
    min_age: int,
    epsilon: float = ADULT_FAIL_BUDGET,
    delta: float = DELTA,
    below: float = math.inf,
    by_group: bool = True,
) -> tuple[float, float]:
    """The highest fail threshold, under `below`, that keeps every group's rate of failed adults (N+3+) provably small.

    A lower fail threshold only ever fails fewer adults, so capping it below the pass threshold keeps it safe.
    """
    adults = (person for person in people if person.age >= min_age + ADULT_MARGIN)
    cells = cells_of((person.group if by_group else "adults", person.p_over) for person in adults)
    if not cells:
        raise CalibrationError(f"no calibration data for adults aged {min_age + ADULT_MARGIN} and over")
    check_size(cells, epsilon, delta, "adults")
    scores = sorted({score for cell in cells.values() for score in cell}, reverse=True)
    candidates = [*scores, math.nextafter(scores[-1], -math.inf)]
    highest = first_safe(candidates, lambda t: worst_bound(cells, fails_at(t), delta) <= epsilon)
    tau = max(0.0, min(highest, math.nextafter(below, -math.inf)))
    bound = worst_bound(cells, fails_at(tau), delta)
    if bound > epsilon:
        raise CalibrationError("an adult scored 0.0: no fail threshold is safe")
    return tau, bound


def calibrate(
    people: Sequence[Scored], min_age: int, epsilon: float, delta: float = DELTA, by_group: bool = True
) -> Thresholds:
    """Both thresholds for one minimum age and risk budget, or a CalibrationError explaining why there are none."""
    tau_pass, minor_bound = tau_pass_for(people, min_age, epsilon, delta, by_group)
    tau_fail, adult_bound = tau_fail_for(people, min_age, delta=delta, below=tau_pass, by_group=by_group)
    return Thresholds(min_age, epsilon, tau_pass, tau_fail, minor_bound, adult_bound, by_group)
