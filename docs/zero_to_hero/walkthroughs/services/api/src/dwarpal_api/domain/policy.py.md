---
fingerprint: 734b2d5429ad8021
---
A **policy** is a website's rule for one age check: *how old* a person must be, and *how strict* the check is. A UK site under the Online Safety Act needs 18+; an Australian social network needs 16+. Each policy also carries a **risk budget**: the largest share of under-age people the system may let through, at 95 % confidence (§1.7, ADR-0006). Every preset here uses 2 %.

The second half of the file is about the **age model's manifest**. A model can't simply be "used" for a policy: it must first be **calibrated** for it — tested on labelled photos to find the exact score thresholds that keep under-age passes within the budget (Phase 2). The manifest is the model's certificate: which versions it covers, and the thresholds it earned for each (age, risk budget) pair.

@@ 1
The docstring: policies, and the calibrated thresholds that go with them.

@@ 3
The project-wide type-hint setting.

@@ 5-8
The tools: `json` (reading the manifest file), `dataclass`, `fnmatchcase` (simple wildcard matching, explained below) and `Path`.

@@ 11-12
`UnknownPolicyError` — asked for a policy name that doesn't exist. It is a kind of `LookupError`, Python's family of "I looked for it and it isn't there" errors (`KeyError` belongs to the same family).

@@ 15-16
`UncalibratedPolicyError` — the policy exists, but the active model has **no thresholds** for it. That is a refusal, never a guess: using thresholds made for a different age would break the safety promise.

@@ 19-25
**`Policy`** — one rule, read-only once made (`frozen=True`):

- `id` — its name, such as `uk_osa_18`;
- `min_age` — the minimum age, such as 18;
- `risk_budget` — the largest allowed share of under-age passes, as a fraction: `0.02` means 2 %;
- `max_face_attempts` — how many face captures a person may try before being sent to a stronger check: 3;
- `token_ttl_s` — how long a signed result stays valid: 600 seconds (10 minutes). A token is meant to be checked *right away*, not kept.

The last two have **default values** (`= 3`, `= 600`), so a policy only needs to say them when it differs.

@@ 28-38
**`PRESETS`** — the six ready-made policies, stored in a dict from name to policy:

| Name | Minimum age | Where it comes from (§1.2, §1.4) |
| :-- | :-: | :-- |
| `uk_osa_18` | 18 | UK Online Safety Act |
| `eu_dsa_18` | 18 | EU Digital Services Act |
| `in_dpdp_18` | 18 | India's Digital Personal Data Protection Act |
| `au_smma_16` | 16 | Australia's social-media minimum age |
| `us_21` | 21 | alcohol, tobacco and some gambling in the US |
| `teen_13` | 13 | social media accounts in many places |

The dict is built by a **dict comprehension** (lines 29–30): "for each policy in this list, use `policy.id` as its key". Writing each name only once — inside its `Policy` — means a key can never disagree with the policy it points to.

In Phase 4, websites get their own versioned policies stored in the database. Presets keep Phase 1 simple.

@@ 41-45
**`get_policy`** — find a preset by name. A missing name raises Python's `KeyError`, which is turned into our own `UnknownPolicyError`. `from None` hides the original `KeyError` from the error report, because it adds nothing.

@@ 48-51
**`Thresholds`** — the two numbers the decision engine compares against `p`, the model's probability that the person is at least the policy's age:

- `tau_pass` (τ, the Greek letter "tau") — at or above it, **pass**;
- `tau_fail` — at or below it, **fail**;
- anything in between is too uncertain to call: **step up** to a stronger check.

@@ 54-60
**`ModelManifest`** — the age model's certificate:

- `name` and `version` — which model this is;
- `serves` — a **pattern** of model versions this manifest covers, such as `stub-age-*`;
- `calibrated` — whether these thresholds really came from risk calibration. Only calibrated models may decide **live** sessions;
- `thresholds` — one `Thresholds` for each `(min_age, risk_budget)` pair. A **tuple** of two values works as a dict key, so a lookup asks one precise question: "the thresholds for age 18 at 2 %".

@@ 62-63
**`serves_model`** — does a model version reported by the inference service belong to this manifest? `fnmatchcase` matches **shell-style wildcards**: `*` means "any characters", so `stub-age-*` matches `stub-age-1` and `stub-age-30`. The `case` in its name means capital letters matter (`Stub-age-1` doesn't match).

The decision engine uses it as a safety catch: if the inference service ever ran a different model than the one these thresholds were made for, no decision is taken.

@@ 65-70
**`thresholds_for`** — the thresholds for a policy, or `UncalibratedPolicyError` with a message that names the model, the age and the budget. `message = …` builds the text on its own line first, so the `raise` stays short and readable.

@@ 73
**`load_manifest`** — read a manifest file into a `ModelManifest`. It runs once, when the API starts.

@@ 74
Read the file as UTF-8 text and parse the JSON.

@@ 75-78
Build the thresholds dict with a dict comprehension: for each row of the file's `thresholds` list, the key is `(min_age, risk_budget)` and the value a `Thresholds`. `int(...)` and `float(...)` turn the file's values into exact Python numbers, so `18` and `18.0` can't end up as two different keys.

@@ 79-81
**Sanity check.** Every pair must satisfy 0 ≤ τ_fail < τ_pass ≤ 1. Python allows **chained comparisons**, so this reads exactly like the maths. A broken file — say, with the two thresholds swapped — stops the API at start-up with a clear message, instead of producing nonsense decisions later.

@@ 82
Build and return the manifest. `bool(...)` makes sure `calibrated` is a true `True` or `False`.
