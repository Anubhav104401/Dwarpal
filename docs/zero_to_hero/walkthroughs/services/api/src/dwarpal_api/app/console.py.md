---
fingerprint: bb4e10a1afe8dbc8
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

@@ 14-16
SQLAlchemy's `select`; `IntegrityError`, raised when the database refuses a row (here, a duplicate); and `AsyncSession`, the type of a unit of work, for a helper's signature.

@@ 18-35
The tenant helper and the account look-up, password hashing, the tables (including sessions and their attempts, for the decision trace), the other use cases this module reuses — analytics, the audit log, policies, verification and webhooks — IDs and one-time codes, the key helpers, the `Policy` type, the roles, and our error class.

@@ 37-39
For type hints only: the master key's type and the toolbox (see `app/webhooks.py` for why such imports are kept apart).

@@ 41
`EMAIL` — a deliberately simple test of an e-mail address: something without spaces or a second `@`, an `@`, and a domain with a dot and a final part of at least two letters. The only real proof of an address is a message reaching it; this just catches typing slips.

@@ 42
`PASSWORD_LENGTHS` — 12 to 256 characters. Length matters far more than odd symbols; the upper limit only keeps hashing time bounded.

@@ 43
`SIGN_IN_REFUSED` — the one refusal for both a wrong password and an unknown address.

@@ 46-49
**`ConsoleSession`** — who is signed in, and their **CSRF token**, a second random value that every change must repeat in a header (`http/console.py`).

@@ 52-53
**`_slot`** — where a session lives in Valkey: the SHA-256 of its token, so a copy of Valkey doesn't hold any usable cookie.

@@ 56-57
**`actor_of`** — how the audit log names a person: `user` and their public ID (`usr_…`).

@@ 60-63
**`_master`** — the master key from the toolbox (it seals one-time-code secrets); missing would be a programming error.

@@ 66-67
**`open_session`** — start a signed-in session.

@@ 68
Two independent 32-byte random tokens: one for the cookie, one against CSRF.

@@ 69-70
Store who it is and the CSRF token, for the session's lifetime (12 hours, renewed on each use).

@@ 71
Return the cookie's token and the session.

@@ 74-79
**`session_of`** — who is signed in with this token, if anyone. Reading renews the session's lifetime (`fetch`).

@@ 82-83
**`close_session`** — sign out: delete the session.

@@ 86-90
**`normalise_email`** — trim spaces, use lower case, and refuse what doesn't look like an address.

@@ 93-96
**`check_password`** — the length rule, and the password must not simply be the e-mail address.

@@ 99-100
**`sign_up`** — a new person, a new organisation they own, and a first project in it.

@@ 101-103
Check the address and the password, and hash the password (`adapters/passwords.py`).

@@ 104
The time and three new IDs.

@@ 105-106
One unit of work that names both the new organisation and the new user as its tenant. Row-level security insists that every new row belongs to the named tenant, so naming them first is what lets these rows be written.

@@ 107-108
If the address already has an account, refuse with `409 email_taken`.

@@ 109-111
Add the user and the organisation, and send them to the database (`flush`), so the membership's foreign keys find them.

@@ 112
Make the person the organisation's **owner**.

@@ 113-116
A first project, with no allowed origins yet.

@@ 117-120
Record the organisation's creation in its new audit log, naming the person and the project.

@@ 121
Save everything at once.

@@ 122-123
Two sign-ups with the same address at the same moment: the unique address lets only one in, and the other gets the same `409`.

@@ 124
Sign the new person in.

@@ 127-128
**`_spend_sign_in`** — each sign-in attempt takes a token from two buckets (`adapters/store.py`): one for the account, one for the network address.

@@ 129-134
For each bucket, take a token; if none is left, refuse with `429` and a `Retry-After` in whole seconds, rounded up (`-(-x // 1000)` divides and rounds up). The account bucket stops someone guessing one person's password from many places; the address bucket stops one place guessing many people's.

@@ 137-139
**`sign_in`** — check an address, a password and, if switched on, a one-time code.

@@ 140-141
Normalise the address and spend an attempt, before any work is done.

@@ 142-143
Find the account through the look-up function, before anyone is named.

@@ 144-146
Check the password — against the decoy when there is no account — and refuse with the same answer either way. Both paths do one Argon2 check, so they take the same time too.

@@ 147-151
The password was right: in a unit of work named for this user, read their row **locked**, so two sign-ins can't both use the same one-time code.

@@ 152-154
If codes are switched on, one must be given.

@@ 155-159
Open the sealed secret, and accept the code only if it is right now and newer than the last one used; remember its step.

@@ 160
Note the time of this sign-in.

@@ 161-164
Record the sign-in in the audit log of every organisation the person belongs to.

@@ 165-166
Save, and open the session.

@@ 169
**`me`** — who is signed in, for the console's pages.

@@ 170-179
Read the user, and their organisations with their role in each, oldest first.

@@ 180-181
An account deleted meanwhile: sign in again.

@@ 182-189
The answer: their ID and address, whether one-time codes are on, the session's CSRF token (the console's pages read it from here and send it back with each change), and their organisations.

@@ 192-193
**`totp_enrol`** — start switching on one-time codes. Nothing changes until a code made from the new secret is confirmed, so a person can't lock themselves out by abandoning the set-up halfway.

@@ 194-200
Make a secret, and keep it **pending**, sealed under the master key with the user's ID as associated data.

@@ 201
Return the secret and its `otpauth://` address, for the console to show as a QR code.

@@ 204-209
**`totp_confirm`** — finish switching codes on. There must be a pending secret.

@@ 210-213
Open it, and check the code the person's app now shows.

@@ 214
Make the pending secret the real one, clear the pending one, and remember the code's step, so it can't be reused.

@@ 215-218
Record it in each of the person's organisations' audit logs.

@@ 219
Save.

@@ 222-223
**`authorise`** — the gate for every organisation action: the person must be a member, and their role must allow the action.

@@ 224-227
A malformed organisation ID is "not found".

@@ 228-231
Read the person's own membership of that organisation (named as the user only: they can see their own memberships).

@@ 232-233
Not a member: `404`, exactly as if the organisation didn't exist — an outsider learns nothing.

@@ 234-235
A member whose role doesn't allow it: `403 forbidden_for_role`.

@@ 236
Allowed: return the organisation and the role.

@@ 239-240
**`list_members`** — any member may see who else belongs.

@@ 241-251
Named as the organisation and the user, read each member's ID, address and role, in the order they joined.

@@ 254-255
**`list_projects`** (Phase 5) — the organisation's projects, oldest first. Any member may read them: the console's keys page needs them to offer a project.

@@ 256-259
Check membership, then, named as the organisation, read its projects.

@@ 260-269
Each project's public ID, name, allowed origins and retention period, as a list.

@@ 272-273
**`add_member`** — give an existing account a role.

@@ 274
Only owners and admins may.

@@ 275-276
The role must be one of the four.

@@ 277-278
Only an owner may make another owner: an admin can't promote anyone above themselves.

@@ 279
The address and the time.

@@ 280-284
Find the account; there must be one (inviting people by e-mail comes with the console's pages).

@@ 285-288
Add the membership, record it in the audit log, and save.

@@ 289-290
Already a member: the membership's key refuses a second one, answered as `409`.

@@ 291
Answer with the new member.

@@ 294-298
**`_member_id`** (Phase 5, §5.5.4) — a member's ID from its public form (`usr_…`); a malformed one is simply "not found".

@@ 301-305
**`_lock_member`** — the membership about to change (to `new_role`) or go (`None`), if the rules allow it.

@@ 306-308
First lock every owner's membership row (`FOR UPDATE`): another request that wants to change an owner must wait until this one has finished. Without it, two owners could each demote the other at the same moment — each would see two owners, both changes would succeed, and the organisation would have none. Everyone takes the locks in the same order (owners first), so two requests can't wait for each other forever.

@@ 309-311
Then lock the member's own row; no such member in this organisation is `404`.

@@ 312-313
If the change involves an owner — making one, or changing or removing one — only an owner may do it. An admin can manage everyone else.

@@ 314-315
The **last owner** can't stop being one, by a role change or by removal: `409`, with what to do instead. Somebody must always be able to manage the organisation.

@@ 316
The locked membership.

@@ 319-322
**`change_role`** — give a member another role.

@@ 323-325
The person must be allowed to manage members, and the role must exist.

@@ 326-328
Read the member's ID and the time, then lock the membership under the rules above.

@@ 329
Remember the old role, and set the new one.

@@ 330-332
Record both roles in the audit log, in the same transaction, and save.

@@ 333
Answer with the member and their new role.

@@ 336-337
**`remove_member`** — take someone out of the organisation. Their account stays; they just lose access to it. People may remove themselves — unless they are the last owner.

@@ 338-341
The same checks and lock.

@@ 342-345
Record the removal (with the role they had), delete the membership, and save.

@@ 348-351
**`create_key`** — a new API key for one of the organisation's projects; owners, admins and developers may.

@@ 352-353
At least one scope, and only real ones.

@@ 354-357
A malformed project ID is "not found".

@@ 358
Make the key.

@@ 359-362
Named as the organisation, read the project; it must exist and belong to this organisation.

@@ 363-374
The key's row: only the **digest** of the secret, the project, the mode, the scopes, and neither expiring nor revoked.

@@ 375-378
Save it, with an audit entry naming the key by its id — never the key itself.

@@ 379-380
Answer with the key, the only time it is ever shown.

@@ 383-385
**`audit_log`** — the organisation's newest audit entries; owners and admins only.

@@ 386-389
Named as the organisation, read the newest entries (up to `limit`), and verify the whole chain.

@@ 390-400
Each entry as the console shows it: its number, who, what, to what, the facts, and when.

@@ 401-402
And the chain's verdict, so the console can show whether it is intact.

@@ 405-408
**`project_in`** (Phase 5) — the gate for every project page: the organisation and one of its projects, if the person's role there allows the action.

@@ 409
First the organisation and the role (`authorise`): not a member → 404, role not allowed → 403.

@@ 410-413
A malformed project ID is "not found".

@@ 414-417
Named as the organisation, read the project; it must exist **and belong to this organisation**. Without that last check, a member of organisation A could name organisation A in the address but a project of organisation B — and row-level security would not stop it, because the console names the organisation, not the project.

@@ 418
Return both.

@@ 421-430
**`project_sessions`** — a project's sessions, a page at a time, for any member.

@@ 431-432
The same list a website reads with its key (`verification.list_sessions`), confined to this project.

@@ 435-439
**`session_trace`** — one session with its **decision trace**: what each attempt decided, why, and the numbers it rested on.

@@ 440-441
Check the project, and read the session's ID from its public form.

@@ 442-445
Named as the project, read the session; another project's session is simply invisible, and gets 404.

@@ 446-451
Its attempts, oldest first.

@@ 452-461
Each attempt's kind, outcome, reasons, scores (the stored numbers: the age probability, the line it was compared with, the liveness evidence) and time.

@@ 462
The session's summary — never a token: reading a trace must not mint one — and the attempts.

@@ 465-469
**`project_analytics`** — the project's daily counts, for roles allowed to read analytics.

@@ 472-474
**`project_policies`** — the presets and the project's own policy versions, for any member.

@@ 477-480
**`add_policy_version`** — the next version of a policy, for roles allowed to manage policies.

@@ 481-485
Check the project and the role, then add the version, with the person (not an API key) named in the audit log.

@@ 488-493
**`project_webhooks`** (Phase 5, §5.5.3) — a project's endpoints in one mode. Only roles that may manage webhooks may even **see** them: an endpoint's address says where the project's events go, which is the kind of thing an attacker would like to know.

@@ 496-505
**`add_webhook`** — a new endpoint, from the console.

@@ 506-508
Check the project and the role, then create it with the website API's own use case — the same allowed events, the same SSRF guard, the same limit of 16, the same secret shown once — with the person named in the audit log.

@@ 511-516
**`remove_webhook`** — the same check, then delete it, the person named.

@@ 519-530
**`switch_webhook`** — the same from the console, for roles that may manage webhooks, naming the person.

@@ 533-537
**`send_test_event`** — queue a test event for one endpoint.

@@ 540-544
**`webhook_deliveries`** — an endpoint's recent deliveries.

@@ 547-551
**`replay_delivery`** — send a delivery again from the start of its retry schedule.
