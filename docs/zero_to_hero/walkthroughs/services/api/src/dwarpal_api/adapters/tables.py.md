---
fingerprint: b901a295960dc50d
---
The **database tables**, described as Python classes. Each class is one table; each `Mapped[...]` line inside it is one **column**. SQLAlchemy's **ORM** (Object-Relational Mapper, §4.10) translates between the two worlds: code works with ordinary Python objects such as `row.status`, and SQLAlchemy writes the SQL.

| Table | One row is… | Lives for |
| :-- | :-- | :-- |
| `projects` | one website using Dwarpal, with its allowed web addresses | as long as the customer |
| `api_keys` | one secret key of a project (only its digest) | until revoked |
| `verification_sessions` | one person's age check | its retention period (Phase 4) |
| `verification_attempts` | one face attempt within a session: outcome, reasons and numbers | with its session |
| `signing_keys` | one key pair for signing age tokens (the private half sealed) | rotation plus overlap |
| `issued_tokens` | a record that a token was issued — never the token itself | with its session |

!!! key "What is never stored"
    No table has a column that could hold a picture, a face measurement or an estimated age (ADR-0013). An attempt keeps only the outcome, short reason codes, and a few numbers — such as the probability compared with the threshold — that explain the decision.

**Type hints become columns.** SQLAlchemy reads each `Mapped[...]` hint:

- `Mapped[str]` — a column that must always have a value (`NOT NULL` in SQL);
- `Mapped[str | None]` — a column that may be empty (`NULL`);
- `mapped_column(...)` — extra details: an exact SQL type, a length limit, an index.

@@ 1
The docstring, and the privacy promise: no column could hold an image.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`uuid` and `datetime` for the column types, and `Any` for the JSON columns, whose contents vary.

@@ 9
SQL types that work in any database:

- `DateTime` — a point in time;
- `ForeignKey` — a link to a row in another table;
- `LargeBinary` — raw bytes, for digests and sealed keys;
- `String(n)` — text of at most *n* characters;
- `Text` — text of any length.

@@ 10
Types that only PostgreSQL has: `ARRAY` (a list stored in one column) and `JSONB` (JSON stored in a compact binary form that the database can search inside).

@@ 11
`Mapped` and `mapped_column`, explained above.

@@ 13
`Base`, the shared catalogue (`db.py`).

@@ 15
`Timestamp` — one reusable column type: a date and time **with a time zone** (`timestamptz` in PostgreSQL). Every time in this project is stored in UTC, so "10:00" can never be misread as someone else's local time.

@@ 18-19
**`Project`** — `__tablename__` gives the table's name in the database: `projects`.

@@ 21
`id` — the **primary key**: the one column whose value is different in every row, used to point at it. Its values are UUIDv7s (`domain/ids.py`).

@@ 22
`name` — the project's display name (at most 120 characters), shown on the verify page: "*Amber Cellars* asks you to confirm your age".

@@ 23
`allowed_origins` — the website addresses this project may send people back to after a check, such as `https://shop.example`. Storing them as an `ARRAY` of text keeps the list in one place. A session's `return_url` must start with one of them (see `create_session`), so a stolen API key can't be used to send people to a fake site.

@@ 24
`created_at` — when the project was created.

@@ 27-28
**`ApiKey`** — the table `api_keys`.

@@ 30
`id` — the key's primary key.

@@ 31
`project_id` — a **foreign key**: it must hold the `id` of an existing row in `projects`, and the database itself refuses anything else. `ondelete="CASCADE"` means that deleting a project automatically deletes its keys too. `index=True` builds an **index** on this column — like the index at the back of a book — so "all keys of project X" is found without reading the whole table.

@@ 32
`livemode` — is this a live key (`True`) or a test key (`False`)? A plain `Mapped[bool]` needs no `mapped_column` at all.

@@ 33
`lookup` — the key's plain-text label (`domain/keys.py`). `unique=True` makes the database refuse two keys with the same lookup, so a lookup always finds exactly one key.

@@ 34
`secret_digest` — the key's SHA-256 fingerprint: exactly 32 bytes. The key itself is never stored.

@@ 35
`name` — a label chosen by the customer, such as "demo shop".

@@ 36-37
When the key was created, and when it was **revoked** (switched off). Empty means it is still active. Revoking instead of deleting keeps a record of which key did what.

@@ 40-41
**`VerificationSession`** — the table `verification_sessions`: one person's age check.

@@ 43-45
Its ID, its project (a foreign key, indexed), and whether it is a live or a test session.

@@ 46
`policy_id` — which policy it checks, such as `uk_osa_18` (`domain/policy.py`).

@@ 47
`status` — its state in the state machine (`domain/sessions.py`), stored as text such as `in_progress`.

@@ 48
`outcome` — the final answer (`pass`, `fail`, …), or empty while there isn't one.

@@ 49
`client_secret_digest` — the fingerprint of the session's one-time client secret.

@@ 50
`return_url` — where to send the person afterwards. It is optional: a website may handle the end of the check in other ways.

@@ 51
`external_ref` — the website's own label for this check, such as an order number. Dwarpal stores it and gives it back, but never interprets it.

@@ 52
`attempts_count` — how many face attempts have been made.

@@ 53
`model_version` — which age model produced the last analysis. It is recorded so that any decision can be traced to the exact model that informed it.

@@ 54-56
Three moments: when the session was created, when it **expires** if unfinished, and when it was completed (empty until then).

@@ 59-60
**`VerificationAttempt`** — the table `verification_attempts`: one face attempt.

@@ 62-65
Its ID, and its session (a foreign key, indexed, deleted together with the session). The `mapped_column(...)` call is spread over three lines only because it is long.

@@ 66
`kind` — which method the attempt used: `face` in Phase 1; document checks follow in Phase 6.

@@ 67
`outcome` — the decision for this attempt: any of the five outcomes, including `retry`.

@@ 68
`reasons` — the decision's reason codes, as a list of texts.

@@ 69
`scores` — the numbers behind the decision, as JSON: the model version, how many frames were sent and usable, which quality problems occurred, the probability and the threshold used, and how long the analysis took (`attempt_scores` in `app/verification.py`). Storing them as JSON lets later phases add numbers without changing the table.

@@ 70
`created_at` — when the attempt was made.

@@ 73-74
**`SigningKey`** — the table `signing_keys`: the key pairs that sign age tokens (`adapters/signing.py`, §4.12).

@@ 76
`kid` — the **key ID**, such as `sig_20261016_3fa9c2e1`, which is also the primary key. Every token says in its header which `kid` signed it, so a verifier knows which public key to use.

@@ 77
`public_jwk` — the **public** half, in the standard JSON format for keys (JWK). It is safe to publish, and it is published.

@@ 78
`private_key_sealed` — the **private** half, encrypted under the master key before it was stored. The database never sees it in plain form.

@@ 79
`status` — `active` (signs new tokens), `retiring` (still published, so tokens it already signed can still be checked) or retired.

@@ 80
`created_at` — when the key was made. Key **rotation** — a fresh key every 30 days (ADR-0008) — uses it to tell when a key is due for replacement.

@@ 83-84
**`IssuedToken`** — the table `issued_tokens`: a record of every token issued. The token itself is not stored — only facts about it.

@@ 86
`jti` — the token's unique ID, the "JWT ID", which is also written inside the token. Phase 4 uses these records to let a website mark a token as *used*, so one token can't be accepted twice.

@@ 87-89
Which session the token reports on (a foreign key, indexed).

@@ 90
`audience` — which project the token was issued to (`aud`): only that project should accept it.

@@ 91-92
When it was issued, and when it expires.

@@ 95
`METADATA` — a short public name for the catalogue of all these tables. The migration tool and the tests import it from here, which makes sure every table class above has been loaded first.
