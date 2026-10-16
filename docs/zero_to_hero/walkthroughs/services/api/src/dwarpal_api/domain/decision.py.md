---
fingerprint: 83b1198d05b97e25
---
The **decision engine** — the most important seventy lines in the project. It receives what the inference service found, and answers one of five words: **pass**, **fail**, **step up**, **retry** or **reject**. Everything else in the system exists to feed it good evidence, or to act on its answer.

The rules are checked **in a fixed order**, and the first rule that applies gives the answer (§3.7, "The decision engine, in order"):

```
no analysis at all? ...................... retry or step up   "analysis_unavailable"
made by the wrong model? ................. retry or step up   "model_mismatch"
fewer than 3 usable frames? .............. retry or step up   the main problem, e.g. "too_dark"
frames disagree by more than 8 years? .... retry or step up   "inconsistent_frames"
probability missing or broken? ........... retry or step up   "analysis_incomplete"
p ≥ τ (pass threshold, raised per retry) . PASS               "age_over_threshold"
p ≤ τ_fail ............................... FAIL               "age_under_threshold"
anything else ............................ STEP UP            "age_uncertain"
```

"Retry or step up" means: another try while the person has attempts left; on the last attempt, a stronger check instead.

!!! key "Fail closed"
    **Pass** can only come from one line — the sixth rule — and only after the five checks above it found nothing wrong. Missing data, a crashed service, a broken number: each leads to *retry*, *step up* or *fail*, never to *pass*. A system built this way is said to **fail closed**, like a fire door that locks when the power goes out, rather than swinging open.

The engine is **pure** (see `domain/__init__.py`): no database, no network, no clock. That is why it can be tested so thoroughly — `test_domain.py` includes **property-based tests** that throw hundreds of random probabilities at it and check that its promises always hold (§4.14).

@@ 1-5
The module docstring: pure rules in a fixed order; "pass" only from the last rule; doubtful evidence never passes.

@@ 7
The project-wide type-hint setting.

@@ 9-13
The tools:

- `math` — for `isnan`, explained below;
- `statistics` — Python's built-in statistics module, for the standard deviation;
- `Counter` — a dict that **counts** things: `Counter(["a", "b", "a"])` is `{"a": 2, "b": 1}`;
- `dataclass` — the class-writing helper;
- `StrEnum` — explained at `Outcome`.

@@ 15-16
The engine's inputs: a `Policy` and its `Thresholds` (from `policy.py`), and a `FaceAnalysis` — the inference service's report, whose shape is fixed by the shared contracts package (§5.1.1).

@@ 18
`MIN_USABLE_FRAMES = 3` — at least three frames must pass every quality check. One lucky frame isn't enough evidence; three that agree are much harder to fake by accident.

@@ 19
`MAX_FRAME_SPREAD_YEARS = 8.0` — the frames' age estimates may differ by up to 8 years (as a standard deviation, explained below). A bigger spread means the frames tell different stories — perhaps two different people, or a photo held up for some frames only — so none of them is trusted.

@@ 20
`RETRY_HARDENING = 0.02` — every retry raises the pass threshold by 2 percentage points. "Keep trying until the model guesses high" is exactly what a determined teenager would do; a rising bar makes that strategy *worse* with every attempt.

@@ 21-31
`ADVICE_ORDER` — the quality problems, from most to least fundamental. When frames fail, the person gets **one** clear tip, for the *first* problem in this list that occurred: if the picture couldn't even be read (`undecodable`), advice about lighting would be pointless. These are exactly the flags made by the vision library's quality checks, plus `undecodable` from the inference pipeline (§5.1.1).

@@ 34
**`Outcome`** — the five possible answers. A `StrEnum` is a fixed set of named values that are *also* ordinary text: `Outcome.PASS == "pass"` is true, so outcomes can be stored in the database and sent as JSON with no conversion, while code can't misspell them.

@@ 35
`PASS = "pass"` — old enough. The comment after `#` silences one linter rule: Ruff's security check S105 suspects that a name like `PASS` holding text is a hard-coded **password**. Here it is an outcome's name, and the comment says so — every silenced warning in this project carries its reason.

@@ 36
`FAIL` — confidently too young.

@@ 37
`STEP_UP` — too close to call: send the person to a stronger method, such as an ID document (Phase 6).

@@ 38
`RETRY` — the evidence wasn't good enough; try again, with a tip.

@@ 39
`REJECT` — a suspected attack, such as a photo of a photo. Nothing produces it yet: it is reserved for the liveness checks of Phase 3, so that every other part of the system already knows how to handle it.

@@ 42-47
**`Decision`** — the engine's answer, read-only:

- `outcome` — one of the five;
- `reasons` — short machine-readable codes explaining why, such as `("too_dark",)`. The type `tuple[str, ...]` means "a tuple of any number of strings"; a tuple can't be changed after it's made;
- `p_over` — the probability the decision was based on, if it got that far;
- `tau_effective` — the threshold actually used, after retry hardening.

The last two are recorded with every attempt, so any decision can be explained later (auditability).

@@ 50
**`dominant_problem`** — the one tip to give when frames fail.

@@ 51
Count every flag of every frame. The expression inside `Counter(...)` is a **generator** with two `for` parts, read left to right: for each frame, for each flag in that frame — produce the flag.

@@ 52
`next(...)` returns the first value a generator produces: here, the first flag in `ADVICE_ORDER` that was counted at least once. If none was, it returns the **default** given after the comma: `"no_usable_frames"`.

@@ 55-57
**`decide`** — the engine itself. Its inputs:

- `policy` and `thresholds` — what is being checked, and the model's calibrated bars;
- `analysis` — the report, or `None` if the inference service didn't deliver one;
- `attempt_index` — which attempt this is, counting from 0;
- `model_ok` — whether the report came from a model this manifest covers (the caller checks with `serves_model`).

@@ 58
First, work out what a "not good enough" answer should be: `STEP_UP` if this is the person's last allowed attempt, otherwise `RETRY`. With 3 attempts, indexes 0 and 1 give `RETRY` and index 2 gives `STEP_UP`. Computing it once keeps the five checks below short.

@@ 59-60
**Rule 1:** no analysis at all — the inference service was down, too slow, or sent something malformed.

@@ 61-62
**Rule 2:** the report came from a model the thresholds weren't made for. Thresholds are only valid for the exact model they were calibrated on, so no decision is taken.

@@ 63-64
**Rule 3:** no age estimate, or fewer than three usable frames. The reason is the main problem, so the person can fix it.

@@ 65-67
**Rule 4:** the frames disagree. `pstdev` is the **population standard deviation**: roughly, the typical distance of each value from the average. For estimates 30, 31 and 29 it is about 0.8 years; for 15, 45 and 30 it is about 12 years — too much. The `len(means) > 1` check comes first because a spread needs at least two values.

@@ 68
Read `p`: the probability that the person is **at least the policy's age**, from the report's `p_over` dict. `.get(...)` returns `None` instead of crashing if that age is missing.

@@ 69-70
**Rule 5:** a missing or **NaN** probability. NaN — "not a number" — is a special value that floating-point maths produces for undefined results such as 0 ÷ 0.

!!! warn "Careful — the strangest value in computing"
    Every comparison with NaN is **false**: `NaN >= 0.95` is false, *and* `NaN < 0.95` is false. Code that says "pass unless `p` is below the bar" would therefore pass a NaN. This explicit check catches it, and a test in `test_domain.py` feeds NaN to the engine to prove it never passes.

@@ 71
**Retry hardening.** The bar for this attempt is `tau_pass` plus 0.02 per earlier attempt — with the stub manifest: 0.95, then 0.97, then 0.99. `min(0.999, …)` caps it just below certainty, because no estimate can ever be 100 % sure, so a bar of 1.0 would make passing impossible.

@@ 72-73
**Rule 6 — the only way to pass:** `p` is at least the bar. The decision records `p` and the bar used.

@@ 74-75
**Rule 7:** `p` is at or below `tau_fail` — the model is confident the person is too young.

@@ 76
**Rule 8:** anything in between is genuinely uncertain — often someone close to the age limit. The fair answer is neither yes nor no but "let's check properly": step up.
