---
fingerprint: ddbc58505aaaeae8
---
**Tests for the document camera's guide** (decision D43, 9 Nov 2026).

@@ 1-3
Vitest, and what is tested: the guide's shape and `guideShare`.

@@ 5
**Tests for `guideShare`.**

@@ 6-10
A wide webcam picture (1920 × 1080): the guide is 90 % of its height, and its sides keep the passport page's proportions (`toBeCloseTo`: equal to a few decimal places, as calculations with fractions are).

@@ 12-16
An older 4:3 webcam picture, and a phone's upright one…

@@ 17-21
…each get a guide 90 % of their width and no taller than 90 % of their height, again in the page's shape.

@@ 22-23
End of the tests.
