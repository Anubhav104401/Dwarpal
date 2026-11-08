---
fingerprint: a26fcb897d31888c
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
`uuid`, and `date` and `datetime` for the column types, and `Any` for the JSON columns, whose contents vary.

@@ 9-24
SQL types and table parts that work in any database:

- `BigInteger` — a whole number up to about 9 × 10¹⁸, for audit sequence numbers that must never run out;
- `Boolean` — true or false (since Phase 9, for a policy's Age Pass switch);
- `CheckConstraint` — a rule every row must obey, checked by the database;
- `DateTime` — a point in time;
- `Float` — a decimal number, for a policy's risk budget;
- `ForeignKey` — a link to a row in another table;
- `Index` — a look-up list over chosen columns;
- `SmallInteger` — a whole number up to 32,767, enough for a band of seconds;
- `LargeBinary` — raw bytes, for digests, hashes and sealed keys;
- `String(n)` — text of at most *n* characters; `Text` — text of any length;
- `UniqueConstraint` — no two rows may share these values;
- `text` — a small piece of raw SQL, here inside an index definition.

The brackets let one `import` span several lines.

And `false()`, SQL's own `false`, as a column's default inside the database (Phase 9).

@@ 25
Types that only PostgreSQL has: `ARRAY` (a list stored in one column) and `JSONB` (JSON stored in a compact binary form that the database can search inside).

@@ 26
`Mapped` and `mapped_column`, explained above.

@@ 28
`Base`, the shared catalogue (`db.py`).

@@ 30
`Timestamp` — one reusable column type: a date and time **with a time zone** (`timestamptz` in PostgreSQL). Every time in this project is stored in UTC, so "10:00" can never be misread as someone else's local time.

@@ 33-34
**`Organization`** — a customer of Dwarpal: the company or person that signs up (Phase 4). The table's name in the database is `organizations`. An organisation owns one or more **projects**, so a business with a shop *and* a forum can keep their age checks, keys and settings apart while being one customer.

@@ 36
`id` — the primary key, a UUIDv7 like every other ID.

@@ 37
`name` — the organisation's display name, at most 120 characters.

@@ 38
`slug` — a short, unique, address-friendly name, such as `amber-cellars`, for console web addresses later. `unique=True` makes the database refuse a second organisation with the same slug.

@@ 39
`created_at` — when the organisation was created.

@@ 42-43
**`Project`** — `__tablename__` gives the table's name in the database: `projects`.

@@ 44
A **check constraint**: the database refuses any project whose retention isn't between 1 and 365 days (Phase 4, step 5).

@@ 46
`id` — the **primary key**: the one column whose value is different in every row, used to point at it. Its values are UUIDv7s (`domain/ids.py`).

@@ 47
`org_id` — the organisation that owns this project. `ForeignKey("organizations.id", ondelete="CASCADE")` makes the database refuse a project whose organisation doesn't exist, and delete an organisation's projects with it. `index=True` builds an **index** on the column — a sorted look-up list, like the index at the back of a book — so "every project of organisation X" is found without reading the whole table. The row-level security policy for projects asks exactly that question.

@@ 48
`name` — the project's display name (at most 120 characters), shown on the verify page: "*Amber Cellars* asks you to confirm your age".

@@ 49
`allowed_origins` — the website addresses this project may send people back to after a check, such as `https://shop.example`. Storing them as an `ARRAY` of text keeps the list in one place. A session's `return_url` must start with one of them (see `create_session`), so a stolen API key can't be used to send people to a fake site.

@@ 50-51
`retention_days` — how many days a session's metadata is kept before the purge removes it (`app/maintenance.py`). `default=90` is filled in by Python when a project is made without one.

@@ 52
`created_at` — when the project was created.

@@ 55-56
**`ApiKey`** — the table `api_keys`.

@@ 58
`id` — the key's primary key.

@@ 59
`project_id` — a **foreign key**: it must hold the `id` of an existing row in `projects`, and the database itself refuses anything else. `ondelete="CASCADE"` means that deleting a project automatically deletes its keys too. `index=True` builds an **index** on this column — like the index at the back of a book — so "all keys of project X" is found without reading the whole table.

@@ 60
`livemode` — is this a live key (`True`) or a test key (`False`)? A plain `Mapped[bool]` needs no `mapped_column` at all.

@@ 61
`lookup` — the key's plain-text label (`domain/keys.py`). `unique=True` makes the database refuse two keys with the same lookup, so a lookup always finds exactly one key.

@@ 62
`secret_digest` — the key's SHA-256 fingerprint: exactly 32 bytes. The key itself is never stored.

@@ 63
`name` — a label chosen by the customer, such as "demo shop".

@@ 64-65
`scopes` — what the key may do: a list such as `sessions:read`, `sessions:write`, `policies:write` (`domain/keys.py`). A key for a server that only reads results can be given just `sessions:read`.

@@ 66
`created_at` — when the key was created.

@@ 67-68
`expires_at` — when a **rotated** key stops working (`cli.py`, `rotate-key`); empty for a key that hasn't been rotated.

@@ 69
`revoked_at` — when the key was **revoked** (switched off at once). Empty means it hasn't been. Revoking instead of deleting keeps a record of which key did what.

@@ 72-73
**`VerificationSession`** — the table `verification_sessions`: one person's age check.

@@ 74-79
`__table_args__` adds things to the table beyond its columns: two indexes. One over `(project_id, id)` answers the paginated list, "this project's sessions, newest first, older than this one", by reading only the rows it returns; it works because UUIDv7s sort by the time they were made. One over `created_at` lets the retention purge find old sessions across every project without reading them all.

@@ 81-83
Its ID, its project (a foreign key, indexed), and whether it is a live or a test session.

@@ 84
`policy_id` — which policy it checks, such as `uk_osa_18` (`domain/policy.py`).

@@ 85-86
`policy_version` — which version of the policy the session follows: `0` for a built-in preset, or the version number of the project's own policy (Phase 4).

@@ 87
`status` — its state in the state machine (`domain/sessions.py`), stored as text such as `in_progress`.

@@ 88
`outcome` — the final answer (`pass`, `fail`, …), or empty while there isn't one.

@@ 89
`client_secret_digest` — the fingerprint of the session's one-time client secret.

@@ 90
`return_url` — where to send the person afterwards. It is optional: a website may handle the end of the check in other ways.

@@ 91
`external_ref` — the website's own label for this check, such as an order number. Dwarpal stores it and gives it back, but never interprets it.

@@ 92
`attempts_count` — how many face attempts have been made.

@@ 93
`model_version` — which age model produced the last analysis. It is recorded so that any decision can be traced to the exact model that informed it.

@@ 94-97
Four moments: when the session was created; when the person first opened the verify page (empty until then — the face check's time is counted from it); when it **expires** if unfinished; and when it was completed (empty until then).

@@ 101-102
**`PolicyVersion`** — one version of a project's own policy, in the table `policies`. A version is never changed once made; editing a policy adds its next version.

@@ 104-105
The table's name, and a unique constraint: a project can't have two versions with the same number for the same name.

@@ 107-115
The ID, the project that owns it, the policy's name (such as `shop_18`), its version number, the rules — the age, the risk budget, how many face attempts, how long a token lasts — and when it was made.

@@ 120-121
**`VerificationAttempt`** — the table `verification_attempts`: one face attempt.

@@ 123-126
Its ID, and its session (a foreign key, indexed, deleted together with the session). The `mapped_column(...)` call is spread over three lines only because it is long.

@@ 127
`kind` — which method the attempt used: `face` in Phase 1; document checks follow in Phase 6.

@@ 128
`outcome` — the decision for this attempt: any of the five outcomes, including `retry`.

@@ 129
`reasons` — the decision's reason codes, as a list of texts.

@@ 130
`scores` — the numbers behind the decision, as JSON: the model version, how many frames were sent and usable, which quality problems occurred, the probability and the threshold used, and how long the analysis took (`attempt_scores` in `app/verification.py`). Storing them as JSON lets later phases add numbers without changing the table.

@@ 131
`created_at` — when the attempt was made.

@@ 134-135
**`SigningKey`** — the table `signing_keys`: the key pairs that sign age tokens (`adapters/signing.py`, §4.12).

@@ 137
`kid` — the **key ID**, such as `sig_20261016_3fa9c2e1`, which is also the primary key. Every token says in its header which `kid` signed it, so a verifier knows which public key to use.

@@ 138
`public_jwk` — the **public** half, in the standard JSON format for keys (JWK). It is safe to publish, and it is published.

@@ 139
`private_key_sealed` — the **private** half, encrypted under the master key before it was stored. The database never sees it in plain form.

@@ 140
`status` — `active` (signs new tokens), `retiring` (still published, so tokens it already signed can still be checked) or retired.

@@ 141
`created_at` — when the key was made. Key **rotation** — a fresh key every 30 days (ADR-0008) — uses it to tell when a key is due for replacement.

@@ 144-145
**`IssuedToken`** — the table `issued_tokens`: a record of every token issued. The token itself is not stored — only facts about it.

@@ 147
`jti` — the token's unique ID, the "JWT ID", which is also written inside the token. Phase 4 uses these records to let a website mark a token as *used*, so one token can't be accepted twice.

@@ 148-150
Which session the token reports on (a foreign key, indexed).

@@ 151
`audience` — which project the token was issued to (`aud`): only that project should accept it.

@@ 152-153
When it was issued, and when it expires.

@@ 154-155
`introspected_at` — when a website asked Dwarpal to check this token (`/v1/tokens/introspect`, Phase 4). A token is answered as genuine only once: the second time, this column is already filled.

@@ 158-159
**`WebhookEndpoint`** — an address on a website's server that Dwarpal notifies when something happens (Phase 4, §5.4.3), with the secret that signs each notification.

@@ 161
Its table: `webhook_endpoints`.

@@ 163-165
The ID; the project it belongs to (indexed, so a project's endpoints are found quickly); and its mode — a test endpoint hears only about test sessions.

@@ 166
`url` — where to send.

@@ 167
`secret_sealed` — the endpoint's signing secret, **sealed** (encrypted) under the master key. The website is shown the secret once; the database holds only this sealed form.

@@ 168
`events` — which kinds of event it wants, such as `verification_session.completed`.

@@ 169-170
Whether it is switched on, and when it was made.

@@ 173-174
**`Event`** — something that happened to a project's sessions, recorded as it was at that moment. Events are history: once written, they are never changed (the API's role may only read and add them).

@@ 176-177
Its table, `events`, with an index over `(project_id, id)` for reading a project's events in time order.

@@ 179-184
The ID; the project and mode; the event's `type`; its `data` — a JSON snapshot of the session, never a token; and when it happened.

@@ 187-188
**`WebhookDelivery`** — one event on its way to one endpoint. Together these rows are the **outbox**: the worker's to-do list (`app/delivery.py`).

@@ 190-193
Its table, with a **partial index**: an index over `next_attempt_at` that includes only rows whose status is `pending` (`postgresql_where`). The worker's question is always "which pending deliveries are due?", and delivered rows — soon the vast majority — never enter this index at all, so it stays small and fast.

@@ 195-197
The ID, the endpoint it goes to, and the event it carries. Deleting either deletes the delivery.

@@ 198-199
`status` — `pending`, `delivered` or `dead` (given up); `attempt` — how many times it has been sent.

@@ 200
`next_attempt_at` — when it is next due.

@@ 201-202
What happened last time: the receiver's HTTP status if it answered, and a short reason if it failed.

@@ 203-204
When the delivery was created, and when it succeeded.

@@ 207-208
**`AuditHead`** — the newest link of one organisation's audit chain (Phase 4, step 5): `app/audit.py` locks this row while it appends, so one organisation's appends happen one at a time, without slowing anyone else's.

@@ 210
Its table: `audit_heads`.

@@ 212-214
One row per organisation (deleted with it): the number of its last entry, and that entry's hash.

@@ 217-218
**`AuditEntry`** — one thing someone did. Each entry holds the hash of the one before it, which is what makes the log **tamper-evident**.

@@ 220
Its table: `audit_log`.

@@ 222-223
The key is two columns: the organisation, and the entry's number within it (`seq`, 1, 2, 3, …).

@@ 224-225
Who did it: an API key (named by its public ID) or an operator's tool.

@@ 226-228
What was done (`action`, such as `policy.version_added`), to what (`target`), and the facts (`data`) — never a secret.

@@ 229-230
The previous entry's hash, and this entry's own.

@@ 231
When.

@@ 234-235
**`SessionStat`** — a count: how many sessions of one project ended one way, on one day, under one policy. These counts are kept after the sessions themselves are purged.

@@ 237
Its table: `session_stats`.

@@ 239-243
The key is five columns together: project, mode (test and live are counted apart), day, policy and outcome.

@@ 244
The count.

@@ 261-262
**`User`** — a person at one of Dwarpal's customers, who signs in to the console (Phase 4, step 2). The docstring repeats the privacy promise: the people whose age is checked are **never** stored as users.

@@ 264
Its table: `users`.

@@ 266-267
The ID, and the e-mail address — unique, and always stored in lower case, so `Ana@Shop.example` and `ana@shop.example` are one account.

@@ 268
`password_hash` — never the password: its **Argon2id hash**, a long text that also carries the random salt and the settings it was made with (`adapters/passwords.py`).

@@ 269-271
One-time codes (`domain/totp.py`): the secret, sealed under the master key, once they are switched on; a secret that has been offered but not yet confirmed; and the 30-second step of the last code used, so no code works twice.

@@ 272
`recovery_digests` (Phase 5) — the HMACs of the person's unused recovery codes; never the codes themselves.

@@ 273-274
When the account was made, and when it last signed in.

@@ 277-278
**`Membership`** — a user's role in one organisation. A person can belong to several organisations, with a different role in each.

@@ 280-283
Its table, `memberships`, with a **check constraint**: the database refuses any role but the four in `domain/roles.py`.

@@ 285-286
The key is the pair: the organisation and the user (each deleted with its parent). The user column is indexed, for "which organisations does this person belong to?".

@@ 287-288
The role, and when it was given.

@@ 324
`METADATA` — a short public name for the catalogue of all these tables. The migration tool and the tests import it from here, which makes sure every table class above has been loaded first.

@@ 247-249
**`FaceStageStat`** — how many of a project's face checks reached one decision on one day, within one band of time (`from_s` seconds or more, up to the next band, as `domain/timing.py` defines). Like `SessionStat`, it is kept after the purge, and no row is about any one person.

@@ 251
The table's name.

@@ 253-258
Its key — the project, test or live, the day, the decision and the band (a small integer) — and the count.

@@ 309-321
**`Passkey`** (Phase 9, migration `0010`) — a console user's passkey: its ID, its owner, the device's ID for it (unique), the public key as the device sent it, the device's signature counter, the person's name for it, and when it was added and last used. Never a private key: that stays on the device.

@@ 98-100
`age_pass_issued_at` (Phase 9, migration `0011`) — when the session gave out its one batch of Age Passes (§5.9.3); empty until then. Only the time: never the passes, their keys or their salts.

@@ 116-119
`accept_age_pass` (Phase 9, migration `0011`) — whether sessions under this version accept Age Passes, and give them out after a pass. `server_default=false()` fills it in the database itself for versions made before the column existed; `default=False` for new rows made in Python.

@@ 291-293
**`Invitation`** (decision D44) — someone without an account yet, invited to an organisation by e-mail address: they join, with this role, when they sign up with that address. No e-mail is sent (D25).

@@ 295-299
Its table, with the same check on roles as memberships, and one invitation per address in an organisation.

@@ 301-306
Its ID, organisation, the address (in lower case, and indexed: sign-up looks it up), the role, who invited, and when.
