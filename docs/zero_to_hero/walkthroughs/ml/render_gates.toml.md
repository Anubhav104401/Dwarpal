---
fingerprint: f386494ee439a6dc
---
**The render detector's release gates** (§5.9.4).

@@ 1-6
What the file is: the render detector's release gates, checked by `render_detector evaluate`, each naming a value in `evaluation.json`. Provisional, for the owner to confirm. Each uses the *upper* end of its 95 % interval, so a small test can't pass by luck.

@@ 8-12
**Renders caught**: at most 10 % of rendered faces taken for real.

@@ 14-18
**Real people refused**: at most 10 % of real faces taken for renders. The threshold aims at 5 %; the gate allows for the test's own uncertainty.

@@ 20-24
At least **5 real people** in the test, none seen in training…

@@ 26-30
…and at least **5 made-up people**.
