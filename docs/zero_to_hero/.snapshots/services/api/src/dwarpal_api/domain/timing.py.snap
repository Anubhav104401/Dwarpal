"""How long face checks take, kept only as counts per band of time, so no one person's timing is ever stored.

A band is named by where it starts: 10 means "10 seconds or more, but under 15". The last band, 300, has no end.
"""

from __future__ import annotations

from collections.abc import Mapping

# Finer where most checks finish (the design's target is a median of 15 seconds or less, NFR-02), coarser after.
BANDS = (0, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 300)


def band_of(seconds: float) -> int:
    """The band a time falls in. A time below zero (clocks disagreeing) counts as the first band."""
    return max((start for start in BANDS if seconds >= start), default=0)


def band_end(start: int) -> int | None:
    """Where a band ends: the next band's start, or None for the last."""
    later = [band for band in BANDS if band > start]
    return later[0] if later else None


def median_band(counts: Mapping[int, int]) -> tuple[int, int | None] | None:
    """The band holding the middle check, as its start and end, or None if there are no checks. With an even number,
    the slower of the two middle checks is used, so a tie never makes the answer sound quicker than it is."""
    total = sum(counts.values())
    if total == 0:
        return None
    middle = total // 2 + 1  # counting from 1: the 3rd of 5, or the 3rd of 4
    seen = 0
    for start in sorted(counts):
        seen += counts[start]
        if seen >= middle:
            return start, band_end(start)
    raise AssertionError("unreachable: the counts add up to the total")
