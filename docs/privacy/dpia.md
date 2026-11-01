# Data Protection Impact Assessment (DPIA) — reference deployment

> **Draft — not legally reviewed.** The owner has not yet arranged a legal review (O5, 1 Nov 2026); nothing here should be relied on or published as final until one is done. Prepared from the system as built (26 Oct 2026) for the reference deployment: Dwarpal operated as a hosted service, with a website (the *relying party*) sending its visitors to Dwarpal's verify page. A website using Dwarpal needs its own DPIA for its own processing; this one covers Dwarpal's part. It follows the structure of the UK ICO's DPIA template and the GDPR's Article 35. Every factual statement points at the code that makes it true.

## 1. The processing

| | |
| :-- | :-- |
| **Purpose** | Estimate whether a person meets a website's minimum age, so that the website can restrict age-restricted content or goods, as laws such as the UK Online Safety Act and Australia's social-media minimum age require (problem analysis §2) |
| **Controller / processor** | The website is the controller of its decision to check age. Dwarpal processes on its behalf (processor) for the check itself; for its own accounts, security logs and service operation, Dwarpal is the controller |
| **Data subjects** | (a) visitors whose age is checked, **who may be children**; (b) people at customer organisations who use the console |
| **Scale** | per check: a few seconds of camera frames, processed once |
| **Nature** | automated estimation from facial images; liveness checks; an automated decision with legal or similarly significant effect only to the extent of access to a website |

## 2. Data, and how long it is kept

| Data | From | Kept | Where in the code |
| :-- | :-- | :-- | :-- |
| **Camera frames (face images)** | visitor | **never stored**: in memory for one request (≈ 1–2 s), then discarded; no table can hold an image | ADR-0013; `adapters/tables.py`; inference service |
| Derived numbers per attempt (age probability, quality and liveness scores, timings) | derived | until the session's retention ends (default 90 days, project-configurable 1–365) | `verification_attempts.scores`; `app/maintenance.py` |
| Session facts (status, outcome, policy, times, the website's own reference, return address) | website / derived | until retention ends | `verification_sessions` |
| Events and webhook deliveries | derived | until retention ends | `events`, `webhook_deliveries` |
| Daily counts (no person, no session) | derived | indefinitely — anonymous | `session_stats` |
| Device budget counters (a random ID the page keeps; the network address) | visitor's browser | **one hour**, and only as SHA-256 digests in Valkey | `adapters/store.py` (`spend_budget`) |
| Request logs | — | per the operator's log retention | method, path, status, duration and request ID only — **no IP addresses, no bodies** (`logs.py`) |
| Console users: e-mail, Argon2id password hash, sealed TOTP secret, HMACs of unused recovery codes (never the codes) | console user | while the account exists; recovery codes until used, replaced, or codes switched off | `users` |
| Audit log | console users' and keys' actions | design: one year (purge not yet built) | `audit_log` |
| Document step-up (planned): year and month of birth only | visitor | as session facts | `domain/mrz.py` (`birth_year_month`) |

## 3. Necessity and proportionality

- **Why faces at all?** The law requires *effective* age assurance; self-declaration fails (problem analysis §2). Facial age estimation is the least intrusive effective method: it identifies no one, needs no document, and its result is a yes/no for one age line.
- **Data minimisation:** the website learns only a signed yes/no for its age line (ADR-0020); Dwarpal never learns who the visitor is; frames are never stored; only numbers about an attempt are kept, and only for the retention period.
- **Alternatives considered:** documents (more intrusive, offered only as step-up), credit cards (excludes people, not proof of age), third-party identity (identifies the person) — see options analysis (solution options §2).
- **Accuracy:** thresholds are risk-controlled with stated error bounds (ADR-0006); uncertain results step up to another method instead of failing the person (ADR-0003).

## 4. Risks to individuals

| Risk | Likelihood / severity | Measures | Residual |
| :-- | :-- | :-- | :-- |
| Face images leaked or reused | low / high | never stored; memory only; never logged; tests assert logs carry no secrets | low |
| A child wrongly passes | medium / high | risk-controlled thresholds; liveness; attempt and device budgets; step-up | medium — estimation error and untested attacks remain (Phase 3 open items) |
| An adult wrongly refused, or a group refused more often (bias) | medium / medium | step-up instead of fail; fairness measured per group (model card) | medium — fairness measured on public datasets, not yet on field data |
| Re-identification from kept numbers | low / medium | numbers only; no identifiers of the visitor; retention purge | low |
| One website seeing another's data | low / high | row-level security with isolation tests | low |
| Tracking across websites | low / medium | no cross-site identifier; device counters hashed and kept one hour | low |
| Console account takeover | low / high | Argon2id, TOTP, rate limits, CSRF protection, audit log | low |
| Children's data handled without appropriate care | medium / high | no storage of images; plain-language notice on the verify page; no profiling | medium — requires the website's own age-appropriate design assessment |

## 5. Rights of individuals

- **Information:** the verify page states, before the camera starts, that photos are checked once and never stored, and that the website learns only whether the person passed.
- **Access and erasure:** Dwarpal holds no identifier of a visitor, so it can't find "their" records unless the website supplies its session reference; requests go through the website. Records are purged at the end of retention anyway.
- **Not to be subject to a solely automated decision:** the person can always use another method (step-up), and the website remains responsible for offering an alternative route.

## 6. Open items before production

1. Legal review of this DPIA, the roles (controller/processor) and the lawful basis, for each launch market (UK, EU, India, Australia, US states).
2. Fairness measured on field data; the anti-spoofing model's fairness (Phase 3 open item).
3. Audit-log retention and purge (one year) — not yet built.
4. A data-processing agreement template for websites.
5. Age-appropriate design review of the verify page's wording with children in mind.

**Sign-off:** _(owner / DPO, after legal review)_
