---
fingerprint: c4f01e7287da02e1
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

@@ 6
`base64`, to read the master key's text form.

@@ 7-14
`hashlib` (to hash session tokens) and `hmac` (for recovery codes' fingerprints), `json`, `re`, `secrets` (unpredictable tokens), `uuid`, `dataclass`, and `TYPE_CHECKING` and `Any`.

@@ 16-18
SQLAlchemy's `select`; `IntegrityError`, raised when the database refuses a row (here, a duplicate); and `AsyncSession`, the type of a unit of work, for a helper's signature.

@@ 20-37
The tenant helper and the account look-up, password hashing, the tables (including sessions and their attempts, for the decision trace), the other use cases this module reuses — analytics, the audit log, policies, verification and webhooks — IDs and one-time codes, the key helpers, the `Policy` type, the roles, and our error class.

@@ 39-41
For type hints only: the master key's type and the toolbox (see `app/webhooks.py` for why such imports are kept apart).

@@ 43
`EMAIL` — a deliberately simple test of an e-mail address: something without spaces or a second `@`, an `@`, and a domain with a dot and a final part of at least two letters. The only real proof of an address is a message reaching it; this just catches typing slips.

@@ 44
`PASSWORD_LENGTHS` — 12 to 256 characters. Length matters far more than odd symbols; the upper limit only keeps hashing time bounded.

@@ 45
`SIGN_IN_REFUSED` — the one refusal for both a wrong password and an unknown address.

@@ 48-51
**`ConsoleSession`** — who is signed in, and their **CSRF token**, a second random value that every change must repeat in a header (`http/console.py`).

@@ 54-55
**`_slot`** — where a session lives in Valkey: the SHA-256 of its token, so a copy of Valkey doesn't hold any usable cookie.

@@ 58-59
**`actor_of`** — how the audit log names a person: `user` and their public ID (`usr_…`).

@@ 62-65
**`_master`** — the master key from the toolbox (it seals one-time-code secrets); missing would be a programming error.

@@ 68-69
**`open_session`** — start a signed-in session.

@@ 70
Two independent 32-byte random tokens: one for the cookie, one against CSRF.

@@ 71-72
Store who it is and the CSRF token, for the session's lifetime (12 hours, renewed on each use).

@@ 73
Return the cookie's token and the session.

@@ 76-81
**`session_of`** — who is signed in with this token, if anyone. Reading renews the session's lifetime (`fetch`).

@@ 84-85
**`close_session`** — sign out: delete the session.

@@ 88-92
**`normalise_email`** — trim spaces, use lower case, and refuse what doesn't look like an address.

@@ 95-98
**`check_password`** — the length rule, and the password must not simply be the e-mail address.

@@ 101-102
**`sign_up`** — a new person, a new organisation they own, and a first project in it.

@@ 103-105
Check the address and the password, and hash the password (`adapters/passwords.py`).

@@ 106
The time and three new IDs.

@@ 107-108
One unit of work that names both the new organisation and the new user as its tenant. Row-level security insists that every new row belongs to the named tenant, so naming them first is what lets these rows be written.

@@ 109-110
If the address already has an account, refuse with `409 email_taken`.

@@ 111-113
Add the user and the organisation, and send them to the database (`flush`), so the membership's foreign keys find them.

@@ 114
Make the person the organisation's **owner**.

@@ 115-118
A first project, with no allowed origins yet.

@@ 119-122
Record the organisation's creation in its new audit log, naming the person and the project.

@@ 123
Save everything at once.

@@ 124-125
Two sign-ups with the same address at the same moment: the unique address lets only one in, and the other gets the same `409`.

@@ 126
Sign the new person in.

@@ 129-130
**`_spend_sign_in`** — each sign-in attempt takes a token from two buckets (`adapters/store.py`): one for the account, one for the network address.

@@ 131-136
For each bucket, take a token; if none is left, refuse with `429` and a `Retry-After` in whole seconds, rounded up (`-(-x // 1000)` divides and rounds up). The account bucket stops someone guessing one person's password from many places; the address bucket stops one place guessing many people's.

@@ 139-141
**`sign_in`** — check an address, a password and, if switched on, a one-time code.

@@ 142-143
Normalise the address and spend an attempt, before any work is done.

@@ 144-145
Find the account through the look-up function, before anyone is named.

@@ 146-148
Check the password — against the decoy when there is no account — and refuse with the same answer either way. Both paths do one Argon2 check, so they take the same time too.

@@ 149-153
The password was right: in a unit of work named for this user, read their row **locked**, so two sign-ins can't both use the same one-time code.

@@ 154-156
If codes are switched on, one must be given.

@@ 157-165
Open the sealed secret, and accept the code if it is right now and newer than the last one used; remember its step. If it isn't, it may be a **recovery code**: if it is one of the person's unused ones, it signs them in — and is used up, and the audit log records it, with how many are left. Otherwise, refused.

@@ 166
Note the time of this sign-in.

@@ 167-170
Record the sign-in in the audit log of every organisation the person belongs to.

@@ 171-172
Save, and open the session.

@@ 175
**`me`** — who is signed in, for the console's pages.

@@ 176-185
Read the user, and their organisations with their role in each, oldest first.

@@ 186-187
An account deleted meanwhile: sign in again.

@@ 188-196
The answer: their ID and address, whether one-time codes are on, how many recovery codes they have left, the session's CSRF token (the console's pages read it from here and send it back with each change), and their organisations.

@@ 199-202
**`_recovery_key`** — the key for recovery codes' fingerprints, made from the master key with HMAC and a label of its own: a key for this purpose alone, as the idempotency key is for its. Someone with a copy of the database but not the master key can't test guesses against the digests.

@@ 205-210
**`_new_recovery_codes`** — make ten fresh codes, keep only their digests (replacing any old ones, used or not), and return the codes: the one moment they exist in plain text.

@@ 213-219
**`_use_recovery_code`** — is this one of the person's unused codes? Its digest is compared with each kept one by `hmac.compare_digest`, which takes the same time whether the first character differs or the last, so timing can't reveal how close a guess came. If found, it is removed: each code works once.

@@ 222-226
**`_record_for_all`** — record something a person did to their own account (switching codes on or off, using a recovery code) in every organisation they belong to, since each organisation's administrators may need to know.

@@ 229-230
**`totp_enrol`** — start switching on one-time codes. Nothing changes until a code made from the new secret is confirmed, so a person can't lock themselves out by abandoning the set-up halfway.

@@ 231-237
Make a secret, and keep it **pending**, sealed under the master key with the user's ID as associated data.

@@ 238
Return the secret and its `otpauth://` address, for the console to show as a QR code.

@@ 241-246
**`totp_confirm`** — finish switching codes on. There must be a pending secret.

@@ 247-250
Open the pending secret and check the code against it; a wrong code is refused with a hint about the phone's clock.

@@ 251
The pending secret becomes the real one, and the code's step is remembered, so it can't be used again.

@@ 252-255
Make the ten **recovery codes**, record it in each of the person's organisations' audit logs, save, and answer with the codes — the only time they are shown.

@@ 258-268
**`replace_recovery_codes`** — a fresh set, for someone who lost theirs or used most of them. Only with one-time codes on; every old code stops working, used or not; the audit log records it.

@@ 271-273
**`totp_disable`** — switch one-time codes off. Only with the **password and a current code**: someone who has merely found a signed-in browser left open knows neither, so can't remove the protection.

@@ 274-279
Codes must be on. The attempt counts against the same limits as signing in (`_spend_sign_in`), so guessing the password here is as slow as guessing it at the sign-in page.

@@ 280-283
Check the code (without using it up yet) and the password; if either is wrong, one answer for both — `403 reauthentication_failed` — so the reply doesn't say which part was right.

@@ 284-287
Forget the secret, any pending one, the last step and every recovery code; record it in each organisation's audit log; save.

@@ 290-291
**`authorise`** — the gate for every organisation action: the person must be a member, and their role must allow the action.

@@ 292-295
A malformed organisation ID is "not found".

@@ 296-299
Read the person's own membership of that organisation (named as the user only: they can see their own memberships).

@@ 300-301
Not a member: `404`, exactly as if the organisation didn't exist — an outsider learns nothing.

@@ 302-303
A member whose role doesn't allow it: `403 forbidden_for_role`.

@@ 304
Allowed: return the organisation and the role.

@@ 307-308
**`list_members`** — any member may see who else belongs.

@@ 309-319
Named as the organisation and the user, read each member's ID, address and role, in the order they joined.

@@ 322-323
**`list_projects`** (Phase 5) — the organisation's projects, oldest first. Any member may read them: the console's keys page needs them to offer a project.

@@ 324-327
Check membership, then, named as the organisation, read its projects.

@@ 328-337
Each project's public ID, name, allowed origins and retention period, as a list.

@@ 340-341
**`add_member`** — give an existing account a role.

@@ 342
Only owners and admins may.

@@ 343-344
The role must be one of the four.

@@ 345-346
Only an owner may make another owner: an admin can't promote anyone above themselves.

@@ 347
The address and the time.

@@ 348-352
Find the account; there must be one (inviting people by e-mail comes with the console's pages).

@@ 353-356
Add the membership, record it in the audit log, and save.

@@ 357-358
Already a member: the membership's key refuses a second one, answered as `409`.

@@ 359
Answer with the new member.

@@ 362-366
**`_member_id`** (Phase 5, §5.5.4) — a member's ID from its public form (`usr_…`); a malformed one is simply "not found".

@@ 369-373
**`_lock_member`** — the membership about to change (to `new_role`) or go (`None`), if the rules allow it.

@@ 374-376
First lock every owner's membership row (`FOR UPDATE`): another request that wants to change an owner must wait until this one has finished. Without it, two owners could each demote the other at the same moment — each would see two owners, both changes would succeed, and the organisation would have none. Everyone takes the locks in the same order (owners first), so two requests can't wait for each other forever.

@@ 377-379
Then lock the member's own row; no such member in this organisation is `404`.

@@ 380-381
If the change involves an owner — making one, or changing or removing one — only an owner may do it. An admin can manage everyone else.

@@ 382-383
The **last owner** can't stop being one, by a role change or by removal: `409`, with what to do instead. Somebody must always be able to manage the organisation.

@@ 384
The locked membership.

@@ 387-390
**`change_role`** — give a member another role.

@@ 391-393
The person must be allowed to manage members, and the role must exist.

@@ 394-396
Read the member's ID and the time, then lock the membership under the rules above.

@@ 397
Remember the old role, and set the new one.

@@ 398-400
Record both roles in the audit log, in the same transaction, and save.

@@ 401
Answer with the member and their new role.

@@ 404-405
**`remove_member`** — take someone out of the organisation. Their account stays; they just lose access to it. People may remove themselves — unless they are the last owner.

@@ 406-409
The same checks and lock.

@@ 410-413
Record the removal (with the role they had), delete the membership, and save.

@@ 416-419
**`create_key`** — a new API key for one of the organisation's projects; owners, admins and developers may.

@@ 420-421
At least one scope, and only real ones.

@@ 422-425
A malformed project ID is "not found".

@@ 426
Make the key.

@@ 427-430
Named as the organisation, read the project; it must exist and belong to this organisation.

@@ 431-442
The key's row: only the **digest** of the secret, the project, the mode, the scopes, and neither expiring nor revoked.

@@ 443-446
Save it, with an audit entry naming the key by its id — never the key itself.

@@ 447-448
Answer with the key, the only time it is ever shown.

@@ 451-453
**`audit_log`** — the organisation's newest audit entries; owners and admins only.

@@ 454-457
Named as the organisation, read the newest entries (up to `limit`), and verify the whole chain.

@@ 458-468
Each entry as the console shows it: its number, who, what, to what, the facts, and when.

@@ 469-470
And the chain's verdict, so the console can show whether it is intact.

@@ 473-476
**`project_in`** (Phase 5) — the gate for every project page: the organisation and one of its projects, if the person's role there allows the action.

@@ 477
First the organisation and the role (`authorise`): not a member → 404, role not allowed → 403.

@@ 478-481
A malformed project ID is "not found".

@@ 482-485
Named as the organisation, read the project; it must exist **and belong to this organisation**. Without that last check, a member of organisation A could name organisation A in the address but a project of organisation B — and row-level security would not stop it, because the console names the organisation, not the project.

@@ 486
Return both.

@@ 489-499
**`project_sessions`** — a project's sessions, a page at a time, for any member, optionally filtered.

@@ 500-501
The same list a website reads with its key (`verification.list_sessions`), with the same filter, confined to this project.

@@ 504-508
**`session_trace`** — one session with its **decision trace**: what each attempt decided, why, and the numbers it rested on.

@@ 509-510
Check the project, and read the session's ID from its public form.

@@ 511-514
Named as the project, read the session; another project's session is simply invisible, and gets 404.

@@ 515-520
Its attempts, oldest first.

@@ 521-530
Each attempt's kind, outcome, reasons, scores (the stored numbers: the age probability, the line it was compared with, the liveness evidence) and time.

@@ 531
The session's summary — never a token: reading a trace must not mint one — and the attempts.

@@ 534-538
**`project_analytics`** — the project's daily counts, for roles allowed to read analytics.

@@ 541-543
**`model_information`** — the age model now deciding, for any signed-in person: it is the same for every organisation, so it needs no tenant and no role. It is not `async`: it reads only what the manifest loaded at start-up.

@@ 544-546
The manifest's whole file, its training section (or an empty dictionary, for the stub, which has none), and its calibration section if there is one.

@@ 547-552
The answer: the version; whether it may decide live sessions; its note and permitted use as written in the manifest; and only the backbone and dataset of its training — not the run's name, the pretrained file's checksum or the commit it was built from.

@@ 553
Where its lines were measured, as the manifest records it: which faces, under what licence, how their ages were known, and how many.

@@ 554-570
For each age and risk budget, the two lines and the two **measured bounds** — the worst plausible share of people under the age who would pass, and of people comfortably over it who would fail. `row.get(...)` gives `None` for the stub, which measured nothing.

And, as the comment says, **how adults fared** in each age band above the line on the test split — the shares that passed, were sent to a stronger check, or failed, and how many faces each share is of. The console's policy editor shows them as its projection (§5.5.8). Each band is copied field by field, so nothing else in the file can slip into the answer; the stub has none, and gets an empty list.

@@ 573-575
**`project_policies`** — the presets and the project's own policy versions, for any member.

@@ 578-581
**`add_policy_version`** — the next version of a policy, for roles allowed to manage policies.

@@ 582-586
Check the project and the role, then add the version, with the person (not an API key) named in the audit log.

@@ 589-594
**`project_webhooks`** (Phase 5, §5.5.3) — a project's endpoints in one mode. Only roles that may manage webhooks may even **see** them: an endpoint's address says where the project's events go, which is the kind of thing an attacker would like to know.

@@ 597-606
**`add_webhook`** — a new endpoint, from the console.

@@ 607-609
Check the project and the role, then create it with the website API's own use case — the same allowed events, the same SSRF guard, the same limit of 16, the same secret shown once — with the person named in the audit log.

@@ 612-617
**`remove_webhook`** — the same check, then delete it, the person named.

@@ 620-631
**`switch_webhook`** — the same from the console, for roles that may manage webhooks, naming the person.

@@ 634-638
**`send_test_event`** — queue a test event for one endpoint.

@@ 641-645
**`webhook_deliveries`** — an endpoint's recent deliveries.

@@ 648-652
**`replay_delivery`** — send a delivery again from the start of its retry schedule.
