---
fingerprint: b203eef5df65fa36
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

@@ 5-13
Standard-library tools for building test inputs: Base64, `itertools` (`pairwise`, for neighbouring items), JSON, logging records, `math.nan`, `random` (for reproducible draws), UUIDs, dates and paths.

@@ 14
`Any` — for the made-up scores in the liveness-report test.

@@ 16-19
`pytest`; Hypothesis's `given` decorator and its **strategies** (`st`), which describe what kind of inputs to invent; and Pydantic's `SecretStr` and `ValidationError`.

@@ 21
`liveness_summary` — the report behind the `liveness-report` command (Phase 3).

@@ 22-38
The code under test, from every part of the domain — now including the challenge generator and its limits, and the bands of time — plus the settings, the log formatter and the contracts used to build analyses, liveness results among them.

@@ 40
`REPO` — the repository's top folder, three levels above this file, for finding the stub manifest.

@@ 41-42
A standard policy (UK, 18+) and simple thresholds — pass at 0.95, fail at 0.05 — shared by the decision tests.

@@ 43
`RANK` — the outcomes in order from worst to best for the person: fail (0), step up (1), pass (2). It lets a test say "better" with a simple `<=`.

@@ 46-56
**`frame`** — a helper that builds one frame report: a good, frontal, sharp face by default, with any quality flags the test asks for.

@@ 59
`LIVE` (Phase 3) — a liveness result with nothing wrong: the pose challenge passed, the light couldn't be measured (which never decides anything on its own), and no injection signs. The tests that aren't about liveness use it, so they test exactly what they did before.

@@ 62-70
**`analysis`** — a helper that builds a whole analysis with a chosen probability of being 18 or over, a number of usable frames, optionally the per-frame age estimates (30 for every frame, unless given), and the liveness result (`LIVE` unless given). Helpers like these keep each test down to the one thing it is about.

@@ 73-78
**Property: a UUIDv7 carries its version, variant and time.** For *any* time that fits in 48 bits (from 0 to 2⁴⁸ − 1, the limits Hypothesis explores), the made ID must say version 7, have the standard variant, and give the exact time back from its top bits (`>> 80` drops the 80 lower bits).

@@ 81-82
**IDs sort by time:** one made at 1,000 ms comes before one made at 2,000 ms. UUIDs can be compared with `<` directly.

@@ 85-91
**Property: any UUID survives encoding and decoding.** For any UUID Hypothesis invents, the text starts with `vs_`, is exactly 29 characters long (3 for the prefix and 26 for the body), and decodes back to the same UUID — even when written in lowercase.

@@ 94-97
**Malformed IDs are refused.** `@pytest.mark.parametrize` runs the same test once per value in the list:

- `prj_01ABC` — the wrong prefix, and too short;
- 26 `U`s — `U` isn't in Crockford's alphabet;
- 25 zeros — one symbol short;
- `vs-…` — a hyphen instead of the underscore;
- 26 `Z`s — every symbol at its maximum is a number bigger than 128 bits.

@@ 100-106
**API keys:** a test key starts with `dk_test_`, parses back to its mode and lookup, matches its digest, and a key with one extra character does *not* match. The last line checks that the key's text doesn't appear anywhere inside the stored digest.

@@ 109-111
**Other formats are refused** before any database work: empty text, a whole `Authorization` header pasted by mistake, an unknown prefix, and a key too short to hold a lookup.

@@ 114-117
**Client secrets** start with their session's ID and match their digest.

@@ 120-123
**Policies:** a preset is found by name; an unknown name raises `UnknownPolicyError`.

@@ 126-132
**The real stub manifest** loads, admits it is uncalibrated, serves stub model versions but not others, and has sensible thresholds for every preset policy. If someone adds a preset and forgets its thresholds, this test fails.

@@ 135-139
**`write_manifest`** — a helper that writes a small manifest file with chosen thresholds for age 18.

@@ 142-145
**A policy without thresholds is refused**: the manifest covers only age 18, so asking for the 21+ policy raises `UncalibratedPolicyError`. `tmp_path` is pytest's temporary folder for this test.

@@ 148-150
**Impossible thresholds are refused** at loading time: a fail threshold above the pass threshold.

@@ 153-156
**The three clear cases**: 0.99 passes, 0.01 fails, 0.50 steps up.

@@ 159-162
**Missing or mismatched analyses never pass**: no analysis on the first attempt means retry, and on the last attempt step up; a model the manifest doesn't serve gives the reason `model_mismatch`.

@@ 165-170
**Poor frames get a retry with the main problem.** Two of three frames are too dark, one is also blurry: darkness comes before blur in `ADVICE_ORDER`, so the advice is `too_dark`.

@@ 173-175
**Frames that disagree are not trusted**: estimates of 15 and 40 years in the same burst give `inconsistent_frames`, even with a probability of 0.99.

@@ 178-183
**A broken probability fails closed.** Pydantic models are frozen, so the test makes a *copy* with one change (`model_copy(update=…)`): the probability for 18 becomes NaN. The engine must not pass it.

@@ 186-191
**Property: more evidence of adulthood never makes the outcome worse.** Hypothesis picks two probabilities and an attempt number; `sorted` names the smaller one `low` and the larger `high`. Whatever they are, the outcome for `high` must rank at least as well as the outcome for `low`. A rule like this would catch, for example, a typo that swapped two comparisons.

@@ 194-202
**Property: later attempts never get an easier bar.** For any probability, the threshold on a later attempt is at least the earlier one, and anything that passes later would also have passed earlier. Retrying can only make passing harder, never easier.

@@ 205-210
**Property: every pass clears the calibrated threshold.** Whatever the probability and attempt, if the engine says pass, the probability it used is at least `tau_pass`. This is the safety promise itself, stated as a test.

@@ 213-220
**The state machine allows exactly its listed moves.** Two loops try every status against every status — all 36 pairs. Listed moves must succeed; every other move must raise `IllegalTransitionError`.

@@ 223-228
**Only open sessions expire**: an in-progress session past its time expires; a completed one never does; a session with five minutes left doesn't.

@@ 231-240
**The production guard.** Production settings with the development key are refused, naming `DWARPAL_MASTER_KEY`. With a real key but the default plain-`http` issuer, they are refused naming `DWARPAL_ISSUER`. With a real key and `https` addresses, they are accepted. The "real" key here is simply the bytes 0 to 31 — a test value, never used anywhere else.

@@ 243-251
**Log lines are JSON.** The test builds a log record by hand (`makeLogRecord`) with a request ID and a status, formats it, and parses the result as JSON. The fields must be there, in lowercase where expected — and a field the record didn't carry (`method`) must not appear.

@@ 254-258
**Without liveness evidence, nothing passes.** Even a clear adult (probability 0.999) gets a retry with `liveness_unavailable`, both when the report has no liveness part (`None`) and when it has one without a pose check.

@@ 261-266
**A failed pose challenge gets one retry, then a rejection.** The same failed result twice: the first attempt (no earlier failures) gives a retry; the second, with one earlier failure (`liveness_failures=1`), a rejection.

@@ 269-272
**Signs of injection send even a clear adult to step up** — here, a virtual camera.

@@ 275-284
**Liveness reasons never say which check fired.** Four very different liveness problems — a missing pose, a turned head at the start, automation, identical frames — and collect every reason given (`|=` adds a set's items to another). Only two words ever come out: `liveness_check_failed` and `liveness_uncertain`. An attacker learns nothing about *which* check caught them.

@@ 287-292
**A live session never accepts liveness taken from labels.** The same passing result, marked `evidence="labels"`: a test session passes, a live one gets `liveness_unavailable`.

@@ 295-297
**Challenges are random, never repeat a step, and cover every order.** 2,000 challenges from a seeded random generator — `random.Random(7)` gives the same "random" numbers every run, so a failure can be repeated. The `noqa` comment tells the linter that a predictable generator is intended here: real challenges use `secrets.SystemRandom`, which can't be predicted.

@@ 298-304
Every challenge has 3 or 4 poses, at most one look-up, the right number of colours, only colours from the palette (`<=` between sets means "is contained in"), and **no step equal to the one before** — `itertools.pairwise` gives each pair of neighbours. A repeated step would be a weaker test: holding still would satisfy it.

@@ 305
And all **24** possible pose orders turn up: 10 with three poses and 14 with four, once the two rules are applied. If the generator favoured some orders, an attacker could prepare for those.

@@ 308-321
**The liveness report** — first a small helper that builds the stored scores of one attempt: whether the pose passed, its problems, how far its turn got (0.3 when it passed, 0.05 when it didn't), the injection signs, a skin correlation (or `None` for "not measurable"), and the presentation evidence: a real-face chance of 0.9 when it passed and 0.1 when it didn't, and a screen pattern of 1.1. Each attempt also carries a render detector's chance: 0.2 when it passed, 0.7 when not.

@@ 323-330
Four made-up attempts: two passes with good light measurements, a retry whose head never turned left, and a step-up caused by automation.

@@ 331-361
The report counts them correctly: the outcomes, 3 of 4 pose checks passed (a false-reject rate of 25% *if* these were all genuine people), the one problem, the measurement used, the turn's reach — median 0.30, lowest 0.05 — the one sign, the presentation line (real-face chance median 0.90, lowest 0.10), and the light: shown 4 times, usable 3, median skin correlation 0.6.

Then four decision tests. **The screen light is recorded but decides nothing**: even a correlation of −0.25 lets a clear adult pass — genuine faces in the owner's tests measured that low. **A hand beside the face decides nothing yet**: the hand detector isn't trusted. **A face the anti-spoofing networks doubt goes to step-up**: a real-face chance of 0.95 passes, 0.2 steps up. The presentation line now also gives the render detector's median (0.20) and highest (0.70) chance.

@@ 364-365
**A live session needs the anti-spoofing verdict.** Two passing liveness results, one with the networks' verdict (0.97) and one without.

@@ 366-369
In a live session, the measured one passes and the unmeasured one gets a retry (`liveness_unavailable`).

@@ 370
In a test session, the unmeasured one still passes: tests and local development work without the networks.

@@ 373-374
**Bands of time, and the median band.** Times on and around the edges of bands: below zero and under 5 s go in the first band; exactly 5 s starts the next; anything from 5 minutes on is in the last.

@@ 375-376
A band's end is the next band's start, and the last has none; and every band's own start falls in that band.

@@ 377-380
No checks, no median. Of three checks, the 2nd's band. Of four, two fast and two slow, the slower middle one — a tie never flatters the figure. And a single check in the last band gives a band without an end.
