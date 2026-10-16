---
fingerprint: e27776f5edb01e82
---
The **fast tests**: everything that can be checked without a database, a network or a clock — identifiers, keys, policies, the decision engine, the state machine, the production guard and the log format. All 30 finish in about two seconds.

Two styles of test appear here:

- **example tests** — "for *this* input, expect *that* output", like `decide(…, analysis(0.99), …)` must pass;
- **property tests** — "for *every* input, this rule must hold". The **Hypothesis** library invents the inputs: a hundred different ones per test by default, deliberately including awkward ones such as 0, 1, tiny fractions and huge numbers (§4.14). If any input breaks the rule, Hypothesis shrinks it to the simplest failing example and prints it.

!!! kid "Explain like I'm six — testing a seesaw"
    An example test puts one particular child on each end and checks which side goes down. A property test says: "*whoever* sits on the left, if a heavier child sits on the right, the right side must go down" — and then tries hundreds of children, including a feather and an elephant, to find one that breaks the rule.

@@ 1
The docstring lists what is tested.

@@ 3
The project-wide type-hint setting.

@@ 5-11
Standard-library tools for building test inputs: Base64, JSON, logging records, `math.nan`, UUIDs, dates and paths.

@@ 13-16
`pytest`; Hypothesis's `given` decorator and its **strategies** (`st`), which describe what kind of inputs to invent; and Pydantic's `SecretStr` and `ValidationError`.

@@ 18-32
The code under test, from every part of the domain, plus the settings, the log formatter and the contracts used to build analyses.

@@ 34
`REPO` — the repository's top folder, three levels above this file, for finding the stub manifest.

@@ 35-36
A standard policy (UK, 18+) and simple thresholds — pass at 0.95, fail at 0.05 — shared by the decision tests.

@@ 37
`RANK` — the outcomes in order from worst to best for the person: fail (0), step up (1), pass (2). It lets a test say "better" with a simple `<=`.

@@ 40-50
**`frame`** — a helper that builds one frame report: a good, frontal, sharp face by default, with any quality flags the test asks for.

@@ 53-57
**`analysis`** — a helper that builds a whole analysis with a chosen probability of being 18 or over, a number of usable frames, and optionally the per-frame age estimates (30 for every frame, unless given). Helpers like these keep each test down to the one thing it is about.

@@ 60-65
**Property: a UUIDv7 carries its version, variant and time.** For *any* time that fits in 48 bits (from 0 to 2⁴⁸ − 1, the limits Hypothesis explores), the made ID must say version 7, have the standard variant, and give the exact time back from its top bits (`>> 80` drops the 80 lower bits).

@@ 68-69
**IDs sort by time:** one made at 1,000 ms comes before one made at 2,000 ms. UUIDs can be compared with `<` directly.

@@ 72-78
**Property: any UUID survives encoding and decoding.** For any UUID Hypothesis invents, the text starts with `vs_`, is exactly 29 characters long (3 for the prefix and 26 for the body), and decodes back to the same UUID — even when written in lowercase.

@@ 81-84
**Malformed IDs are refused.** `@pytest.mark.parametrize` runs the same test once per value in the list:

- `prj_01ABC` — the wrong prefix, and too short;
- 26 `U`s — `U` isn't in Crockford's alphabet;
- 25 zeros — one symbol short;
- `vs-…` — a hyphen instead of the underscore;
- 26 `Z`s — every symbol at its maximum is a number bigger than 128 bits.

@@ 87-93
**API keys:** a test key starts with `dk_test_`, parses back to its mode and lookup, matches its digest, and a key with one extra character does *not* match. The last line checks that the key's text doesn't appear anywhere inside the stored digest.

@@ 96-98
**Other formats are refused** before any database work: empty text, a whole `Authorization` header pasted by mistake, an unknown prefix, and a key too short to hold a lookup.

@@ 101-104
**Client secrets** start with their session's ID and match their digest.

@@ 107-110
**Policies:** a preset is found by name; an unknown name raises `UnknownPolicyError`.

@@ 113-119
**The real stub manifest** loads, admits it is uncalibrated, serves stub model versions but not others, and has sensible thresholds for every preset policy. If someone adds a preset and forgets its thresholds, this test fails.

@@ 122-126
**`write_manifest`** — a helper that writes a small manifest file with chosen thresholds for age 18.

@@ 129-132
**A policy without thresholds is refused**: the manifest covers only age 18, so asking for the 21+ policy raises `UncalibratedPolicyError`. `tmp_path` is pytest's temporary folder for this test.

@@ 135-137
**Impossible thresholds are refused** at loading time: a fail threshold above the pass threshold.

@@ 140-143
**The three clear cases**: 0.99 passes, 0.01 fails, 0.50 steps up.

@@ 146-149
**Missing or mismatched analyses never pass**: no analysis on the first attempt means retry, and on the last attempt step up; a model the manifest doesn't serve gives the reason `model_mismatch`.

@@ 152-157
**Poor frames get a retry with the main problem.** Two of three frames are too dark, one is also blurry: darkness comes before blur in `ADVICE_ORDER`, so the advice is `too_dark`.

@@ 160-162
**Frames that disagree are not trusted**: estimates of 15 and 40 years in the same burst give `inconsistent_frames`, even with a probability of 0.99.

@@ 165-170
**A broken probability fails closed.** Pydantic models are frozen, so the test makes a *copy* with one change (`model_copy(update=…)`): the probability for 18 becomes NaN. The engine must not pass it.

@@ 173-178
**Property: more evidence of adulthood never makes the outcome worse.** Hypothesis picks two probabilities and an attempt number; `sorted` names the smaller one `low` and the larger `high`. Whatever they are, the outcome for `high` must rank at least as well as the outcome for `low`. A rule like this would catch, for example, a typo that swapped two comparisons.

@@ 181-189
**Property: later attempts never get an easier bar.** For any probability, the threshold on a later attempt is at least the earlier one, and anything that passes later would also have passed earlier. Retrying can only make passing harder, never easier.

@@ 192-197
**Property: every pass clears the calibrated threshold.** Whatever the probability and attempt, if the engine says pass, the probability it used is at least `tau_pass`. This is the safety promise itself, stated as a test.

@@ 200-207
**The state machine allows exactly its listed moves.** Two loops try every status against every status — all 36 pairs. Listed moves must succeed; every other move must raise `IllegalTransitionError`.

@@ 210-215
**Only open sessions expire**: an in-progress session past its time expires; a completed one never does; a session with five minutes left doesn't.

@@ 218-227
**The production guard.** Production settings with the development key are refused, naming `DWARPAL_MASTER_KEY`. With a real key but the default plain-`http` issuer, they are refused naming `DWARPAL_ISSUER`. With a real key and `https` addresses, they are accepted. The "real" key here is simply the bytes 0 to 31 — a test value, never used anywhere else.

@@ 230-238
**Log lines are JSON.** The test builds a log record by hand (`makeLogRecord`) with a request ID and a status, formats it, and parses the result as JSON. The fields must be there, in lowercase where expected — and a field the record didn't carry (`method`) must not appear.
