---
fingerprint: f2b4f9bbe1a99e71
---
**Timing in bands** (Phase 7, §5.5.2): how long face checks take, kept only as counts per band, and the median worked out from those counts. Pure functions, so they can be tested without a database.

@@ 1-4
What the module is for, and how bands are named: by where they start.

@@ 6
Newer type-hint syntax on older Pythons.

@@ 8
`Mapping`: any read-only dictionary, here band → count.

@@ 10-11
**`BANDS`** — where each band starts, in seconds: every 5 seconds up to 20, where most checks should finish (the target is a median of 15 s), then wider. The last starts at 5 minutes and has no end.

@@ 14-16
**`band_of`** — the band a time falls in: the largest start not above it. `default=0` covers a negative time (if two clocks disagree), which then counts as the first band.

@@ 19-22
**`band_end`** — the start of the next band up, or `None` for the last band.

@@ 25-27
**`median_band`** — the band holding the middle check. With an even number of checks there are two middles; the slower one is used, so a tie never flatters the figure.

@@ 28-30
No checks: no median.

@@ 31
Which check is the middle one, counting from 1: with 5 checks the 3rd; with 4, the 3rd (the slower of the 2nd and 3rd). `//` divides and drops the remainder.

@@ 32-36
Walk the bands from fastest to slowest, adding up their counts; the first band where the running total reaches the middle check holds it.

@@ 37
The loop always returns, because the counts add up to the total; this line only says so, for the type checker and the reader.
