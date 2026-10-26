---
fingerprint: f6eaee8e3073f2aa
---
The **console's use cases** (Phase 4, §5.4.5) — everything a person at one of Dwarpal's customers does through the web console: signing up and in, switching on one-time codes, managing members, creating API keys, reading the audit log.

Three ideas run through the file:

- **A session is a token in a cookie** — a long random value, meaningful only as a key into Valkey, where the session's facts live. Signing out deletes them, and the cookie becomes worthless.
- **Every organisation action checks the role first** (`authorise`), using the matrix in `domain/roles.py`, and only then names the organisation as the tenant.
- **Nothing leaks through refusals.** A wrong password and an unknown address get the same answer after the same amount of work, and an organisation you don't belong to looks exactly like one that doesn't exist.

@@ 1-2
The docstring.

@@ 4
The project-wide type-hint setting.

@@ 6-12
`hashlib` (to hash session tokens), `json`, `re`, `secrets` (unpredictable tokens), `uuid`, `dataclass`, and `TYPE_CHECKING` and `Any`.

@@ 14-15
SQLAlchemy's `select`, and `IntegrityError`, raised when the database refuses a row (here, a duplicate).

@@ 17-34
The tenant helper and the account look-up, password hashing, the tables (including sessions and their attempts, for the decision trace), the other use cases this module reuses — analytics, the audit log, policies, verification and webhooks — IDs and one-time codes, the key helpers, the `Policy` type, the roles, and our error class.

@@ 36-38
For type hints only: the master key's type and the toolbox (see `app/webhooks.py` for why such imports are kept apart).

@@ 40
`EMAIL` — a deliberately simple test of an e-mail address: something without spaces or a second `@`, an `@`, and a domain with a dot and a final part of at least two letters. The only real proof of an address is a message reaching it; this just catches typing slips.

@@ 41
`PASSWORD_LENGTHS` — 12 to 256 characters. Length matters far more than odd symbols; the upper limit only keeps hashing time bounded.

@@ 42
`SIGN_IN_REFUSED` — the one refusal for both a wrong password and an unknown address.

@@ 45-48
**`ConsoleSession`** — who is signed in, and their **CSRF token**, a second random value that every change must repeat in a header (`http/console.py`).

@@ 51-52
**`_slot`** — where a session lives in Valkey: the SHA-256 of its token, so a copy of Valkey doesn't hold any usable cookie.

@@ 55-56
**`actor_of`** — how the audit log names a person: `user` and their public ID (`usr_…`).

@@ 59-62
**`_master`** — the master key from the toolbox (it seals one-time-code secrets); missing would be a programming error.

@@ 65-66
**`open_session`** — start a signed-in session.

@@ 67
Two independent 32-byte random tokens: one for the cookie, one against CSRF.

@@ 68-69
Store who it is and the CSRF token, for the session's lifetime (12 hours, renewed on each use).

@@ 70
Return the cookie's token and the session.

@@ 73-78
**`session_of`** — who is signed in with this token, if anyone. Reading renews the session's lifetime (`fetch`).

@@ 81-82
**`close_session`** — sign out: delete the session.

@@ 85-89
**`normalise_email`** — trim spaces, use lower case, and refuse what doesn't look like an address.

@@ 92-95
**`check_password`** — the length rule, and the password must not simply be the e-mail address.

@@ 98-99
**`sign_up`** — a new person, a new organisation they own, and a first project in it.

@@ 100-102
Check the address and the password, and hash the password (`adapters/passwords.py`).

@@ 103
The time and three new IDs.

@@ 104-105
One unit of work that names both the new organisation and the new user as its tenant. Row-level security insists that every new row belongs to the named tenant, so naming them first is what lets these rows be written.

@@ 106-107
If the address already has an account, refuse with `409 email_taken`.

@@ 108-110
Add the user and the organisation, and send them to the database (`flush`), so the membership's foreign keys find them.

@@ 111
Make the person the organisation's **owner**.

@@ 112-115
A first project, with no allowed origins yet.

@@ 116-119
Record the organisation's creation in its new audit log, naming the person and the project.

@@ 120
Save everything at once.

@@ 121-122
Two sign-ups with the same address at the same moment: the unique address lets only one in, and the other gets the same `409`.

@@ 123
Sign the new person in.

@@ 126-127
**`_spend_sign_in`** — each sign-in attempt takes a token from two buckets (`adapters/store.py`): one for the account, one for the network address.

@@ 128-133
For each bucket, take a token; if none is left, refuse with `429` and a `Retry-After` in whole seconds, rounded up (`-(-x // 1000)` divides and rounds up). The account bucket stops someone guessing one person's password from many places; the address bucket stops one place guessing many people's.

@@ 136-138
**`sign_in`** — check an address, a password and, if switched on, a one-time code.

@@ 139-140
Normalise the address and spend an attempt, before any work is done.

@@ 141-142
Find the account through the look-up function, before anyone is named.

@@ 143-145
Check the password — against the decoy when there is no account — and refuse with the same answer either way. Both paths do one Argon2 check, so they take the same time too.

@@ 146-150
The password was right: in a unit of work named for this user, read their row **locked**, so two sign-ins can't both use the same one-time code.

@@ 151-153
If codes are switched on, one must be given.

@@ 154-158
Open the sealed secret, and accept the code only if it is right now and newer than the last one used; remember its step.

@@ 159
Note the time of this sign-in.

@@ 160-163
Record the sign-in in the audit log of every organisation the person belongs to.

@@ 164-165
Save, and open the session.

@@ 168
**`me`** — who is signed in, for the console's pages.

@@ 169-178
Read the user, and their organisations with their role in each, oldest first.

@@ 179-180
An account deleted meanwhile: sign in again.

@@ 181-188
The answer: their ID and address, whether one-time codes are on, the session's CSRF token (the console's pages read it from here and send it back with each change), and their organisations.

@@ 191-192
**`totp_enrol`** — start switching on one-time codes. Nothing changes until a code made from the new secret is confirmed, so a person can't lock themselves out by abandoning the set-up halfway.

@@ 193-199
Make a secret, and keep it **pending**, sealed under the master key with the user's ID as associated data.

@@ 200
Return the secret and its `otpauth://` address, for the console to show as a QR code.

@@ 203-208
**`totp_confirm`** — finish switching codes on. There must be a pending secret.

@@ 209-212
Open it, and check the code the person's app now shows.

@@ 213
Make the pending secret the real one, clear the pending one, and remember the code's step, so it can't be reused.

@@ 214-217
Record it in each of the person's organisations' audit logs.

@@ 218
Save.

@@ 221-222
**`authorise`** — the gate for every organisation action: the person must be a member, and their role must allow the action.

@@ 223-226
A malformed organisation ID is "not found".

@@ 227-230
Read the person's own membership of that organisation (named as the user only: they can see their own memberships).

@@ 231-232
Not a member: `404`, exactly as if the organisation didn't exist — an outsider learns nothing.

@@ 233-234
A member whose role doesn't allow it: `403 forbidden_for_role`.

@@ 235
Allowed: return the organisation and the role.

@@ 238-239
**`list_members`** — any member may see who else belongs.

@@ 240-250
Named as the organisation and the user, read each member's ID, address and role, in the order they joined.

@@ 253-254
**`list_projects`** (Phase 5) — the organisation's projects, oldest first. Any member may read them: the console's keys page needs them to offer a project.

@@ 255-258
Check membership, then, named as the organisation, read its projects.

@@ 259-268
Each project's public ID, name, allowed origins and retention period, as a list.

@@ 271-272
**`add_member`** — give an existing account a role.

@@ 273
Only owners and admins may.

@@ 274-275
The role must be one of the four.

@@ 276-277
Only an owner may make another owner: an admin can't promote anyone above themselves.

@@ 278
The address and the time.

@@ 279-283
Find the account; there must be one (inviting people by e-mail comes with the console's pages).

@@ 284-287
Add the membership, record it in the audit log, and save.

@@ 288-289
Already a member: the membership's key refuses a second one, answered as `409`.

@@ 290
Answer with the new member.

@@ 293-296
**`create_key`** — a new API key for one of the organisation's projects; owners, admins and developers may.

@@ 297-298
At least one scope, and only real ones.

@@ 299-302
A malformed project ID is "not found".

@@ 303
Make the key.

@@ 304-307
Named as the organisation, read the project; it must exist and belong to this organisation.

@@ 308-319
The key's row: only the **digest** of the secret, the project, the mode, the scopes, and neither expiring nor revoked.

@@ 320-323
Save it, with an audit entry naming the key by its id — never the key itself.

@@ 324-325
Answer with the key, the only time it is ever shown.

@@ 328-330
**`audit_log`** — the organisation's newest audit entries; owners and admins only.

@@ 331-334
Named as the organisation, read the newest entries (up to `limit`), and verify the whole chain.

@@ 335-345
Each entry as the console shows it: its number, who, what, to what, the facts, and when.

@@ 346-347
And the chain's verdict, so the console can show whether it is intact.

@@ 350-353
**`project_in`** (Phase 5) — the gate for every project page: the organisation and one of its projects, if the person's role there allows the action.

@@ 354
First the organisation and the role (`authorise`): not a member → 404, role not allowed → 403.

@@ 355-358
A malformed project ID is "not found".

@@ 359-362
Named as the organisation, read the project; it must exist **and belong to this organisation**. Without that last check, a member of organisation A could name organisation A in the address but a project of organisation B — and row-level security would not stop it, because the console names the organisation, not the project.

@@ 363
Return both.

@@ 366-375
**`project_sessions`** — a project's sessions, a page at a time, for any member.

@@ 376-377
The same list a website reads with its key (`verification.list_sessions`), confined to this project.

@@ 380-384
**`session_trace`** — one session with its **decision trace**: what each attempt decided, why, and the numbers it rested on.

@@ 385-386
Check the project, and read the session's ID from its public form.

@@ 387-390
Named as the project, read the session; another project's session is simply invisible, and gets 404.

@@ 391-396
Its attempts, oldest first.

@@ 397-406
Each attempt's kind, outcome, reasons, scores (the stored numbers: the age probability, the line it was compared with, the liveness evidence) and time.

@@ 407
The session's summary — never a token: reading a trace must not mint one — and the attempts.

@@ 410-414
**`project_analytics`** — the project's daily counts, for roles allowed to read analytics.

@@ 417-419
**`project_policies`** — the presets and the project's own policy versions, for any member.

@@ 422-425
**`add_policy_version`** — the next version of a policy, for roles allowed to manage policies.

@@ 426-430
Check the project and the role, then add the version, with the person (not an API key) named in the audit log.

@@ 433-438
**`project_webhooks`** (Phase 5, §5.5.3) — a project's endpoints in one mode. Only roles that may manage webhooks may even **see** them: an endpoint's address says where the project's events go, which is the kind of thing an attacker would like to know.

@@ 441-450
**`add_webhook`** — a new endpoint, from the console.

@@ 451-453
Check the project and the role, then create it with the website API's own use case — the same allowed events, the same SSRF guard, the same limit of 16, the same secret shown once — with the person named in the audit log.

@@ 456-461
**`remove_webhook`** — the same check, then delete it, the person named.

@@ 464-468
**`send_test_event`** — queue a test event for one endpoint.

@@ 471-475
**`webhook_deliveries`** — an endpoint's recent deliveries.

@@ 478-482
**`replay_delivery`** — send a delivery again from the start of its retry schedule.
