# ADR-0020: State the age result as a boolean claim named after its age — `age_over_18: true`

- **Status:** Accepted — 2026-10-16
- **Refines:** [ADR-0008](0008-signed-age-tokens.md) (only the age claim; everything else stands)

## Context
ADR-0008 listed two separate claims: `age_over`, a number (the policy's age), and `outcome`. A code review in Phase 1 found a dangerous way to misread this. A token for a **failed** check carried `"age_over": 18` next to `"outcome": "fail"`. A relying party that looked only at `age_over` — or a developer skimming a decoded token — would read "over 18" and let a child in. A security token must not have a careless reading that is the opposite of the truth.

There was a second, quieter problem. A token minted under one policy (say `teen_13`) carried a number that relying parties were expected to *compare* with their own requirement. One careless comparison could treat a 13+ result as good enough for an 18+ site.

## Decision
- The age result is **one boolean claim whose name carries the age**: `age_over_18: true` for a pass, and `age_over_18: false` for every other completed outcome. The same `age_over_NN` booleans are used by ISO/IEC 18013-5 mobile driving licences and by the EU age-verification blueprint, so integrators may already know the pattern.
- `outcome` stays as the detailed result (`pass`, `fail`, later `reject`).
- Verifiers — our SDKs included — take the relying party's *own* required age as an input, read exactly `age_over_<required>`, and accept only the literal value `true`. A token minted for a different age doesn't contain that claim at all, so it fails closed.

## Consequences
- **Good:** the careless reading and the correct reading now agree. Confusing one age policy with another is impossible by construction. The claim matches wallet and mdoc age attributes.
- **Cost:** the claim's name depends on the policy, so a JSON schema has to describe it as a pattern (`^age_over_[0-9]{2}$`) instead of a fixed field.

## Alternatives considered
- Keep `age_over` as a number but mint tokens only for passes: a failed check would then have no signed record, and relying parties would lose a tamper-evident "no".
- A nested object such as `{"age": {"over": 18, "verified": false}}`: it still contains the number 18 next to a negative answer, so it can still be misread.
