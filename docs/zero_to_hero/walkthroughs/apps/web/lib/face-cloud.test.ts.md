---
fingerprint: 6b4a14dbb043e10e
---
Tests for the **3D hero's face** (§5.5.10): its size, that it is the same every time, its shape, and its balance.

@@ 1-3
Vitest's tools, and the face under test.

@@ 5-7
The face once, a helper that reads point `i` as `{x, y, z}` (`?? 0` satisfies TypeScript, which can't know the list is long enough), and all the points that way.

@@ 9-16
**Test — 478 points, each three ordinary numbers inside a small box**: no `NaN`, no infinity, nothing beyond ±1.

@@ 18-20
**Test — the same face every time**: nothing random, so the page looks the same for everyone and the tests can rely on it.

@@ 22-27
**Test — taller than wide, and facing forward**: the spread of heights beats the spread of widths, and no point sits far behind the face.

@@ 29-33
**Test — the nose is the nearest point, in the middle**: the point with the largest depth is near the centre line and near mid-height.

@@ 35-39
**Test — both halves alike**: about as many points left of the middle as right of it (within 10 %).
