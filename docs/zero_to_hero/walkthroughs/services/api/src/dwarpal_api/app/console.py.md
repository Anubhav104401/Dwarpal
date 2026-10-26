---
fingerprint: 7dcbdc002963d93c
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

@@ 17-24
The tenant helper and the account look-up, password hashing, the tables, the audit log, IDs and one-time codes, the key helpers, the roles, and our error class.

@@ 26-28
For type hints only: the master key's type and the toolbox (see `app/webhooks.py` for why such imports are kept apart).

@@ 30
`EMAIL` — a deliberately simple test of an e-mail address: something without spaces or a second `@`, an `@`, and a domain with a dot and a final part of at least two letters. The only real proof of an address is a message reaching it; this just catches typing slips.

@@ 31
`PASSWORD_LENGTHS` — 12 to 256 characters. Length matters far more than odd symbols; the upper limit only keeps hashing time bounded.

@@ 32
`SIGN_IN_REFUSED` — the one refusal for both a wrong password and an unknown address.

@@ 35-38
**`ConsoleSession`** — who is signed in, and their **CSRF token**, a second random value that every change must repeat in a header (`http/console.py`).

@@ 41-42
**`_slot`** — where a session lives in Valkey: the SHA-256 of its token, so a copy of Valkey doesn't hold any usable cookie.

@@ 45-46
**`actor_of`** — how the audit log names a person: `user` and their public ID (`usr_…`).

@@ 49-52
**`_master`** — the master key from the toolbox (it seals one-time-code secrets); missing would be a programming error.

@@ 55-56
**`open_session`** — start a signed-in session.

@@ 57
Two independent 32-byte random tokens: one for the cookie, one against CSRF.

@@ 58-59
Store who it is and the CSRF token, for the session's lifetime (12 hours, renewed on each use).

@@ 60
Return the cookie's token and the session.

@@ 63-68
**`session_of`** — who is signed in with this token, if anyone. Reading renews the session's lifetime (`fetch`).

@@ 71-72
**`close_session`** — sign out: delete the session.

@@ 75-79
**`normalise_email`** — trim spaces, use lower case, and refuse what doesn't look like an address.

@@ 82-85
**`check_password`** — the length rule, and the password must not simply be the e-mail address.

@@ 88-89
**`sign_up`** — a new person, a new organisation they own, and a first project in it.

@@ 90-92
Check the address and the password, and hash the password (`adapters/passwords.py`).

@@ 93
The time and three new IDs.

@@ 94-95
One unit of work that names both the new organisation and the new user as its tenant. Row-level security insists that every new row belongs to the named tenant, so naming them first is what lets these rows be written.

@@ 96-97
If the address already has an account, refuse with `409 email_taken`.

@@ 98-100
Add the user and the organisation, and send them to the database (`flush`), so the membership's foreign keys find them.

@@ 101
Make the person the organisation's **owner**.

@@ 102-105
A first project, with no allowed origins yet.

@@ 106-109
Record the organisation's creation in its new audit log, naming the person and the project.

@@ 110
Save everything at once.

@@ 111-112
Two sign-ups with the same address at the same moment: the unique address lets only one in, and the other gets the same `409`.

@@ 113
Sign the new person in.

@@ 116-117
**`_spend_sign_in`** — each sign-in attempt takes a token from two buckets (`adapters/store.py`): one for the account, one for the network address.

@@ 118-123
For each bucket, take a token; if none is left, refuse with `429` and a `Retry-After` in whole seconds, rounded up (`-(-x // 1000)` divides and rounds up). The account bucket stops someone guessing one person's password from many places; the address bucket stops one place guessing many people's.

@@ 126-128
**`sign_in`** — check an address, a password and, if switched on, a one-time code.

@@ 129-130
Normalise the address and spend an attempt, before any work is done.

@@ 131-132
Find the account through the look-up function, before anyone is named.

@@ 133-135
Check the password — against the decoy when there is no account — and refuse with the same answer either way. Both paths do one Argon2 check, so they take the same time too.

@@ 136-140
The password was right: in a unit of work named for this user, read their row **locked**, so two sign-ins can't both use the same one-time code.

@@ 141-143
If codes are switched on, one must be given.

@@ 144-148
Open the sealed secret, and accept the code only if it is right now and newer than the last one used; remember its step.

@@ 149
Note the time of this sign-in.

@@ 150-153
Record the sign-in in the audit log of every organisation the person belongs to.

@@ 154-155
Save, and open the session.

@@ 158
**`me`** — who is signed in, for the console's pages.

@@ 159-168
Read the user, and their organisations with their role in each, oldest first.

@@ 169-170
An account deleted meanwhile: sign in again.

@@ 171-178
The answer: their ID and address, whether one-time codes are on, the session's CSRF token (the console's pages read it from here and send it back with each change), and their organisations.

@@ 181-182
**`totp_enrol`** — start switching on one-time codes. Nothing changes until a code made from the new secret is confirmed, so a person can't lock themselves out by abandoning the set-up halfway.

@@ 183-189
Make a secret, and keep it **pending**, sealed under the master key with the user's ID as associated data.

@@ 190
Return the secret and its `otpauth://` address, for the console to show as a QR code.

@@ 193-198
**`totp_confirm`** — finish switching codes on. There must be a pending secret.

@@ 199-202
Open it, and check the code the person's app now shows.

@@ 203
Make the pending secret the real one, clear the pending one, and remember the code's step, so it can't be reused.

@@ 204-207
Record it in each of the person's organisations' audit logs.

@@ 208
Save.

@@ 211-212
**`authorise`** — the gate for every organisation action: the person must be a member, and their role must allow the action.

@@ 213-216
A malformed organisation ID is "not found".

@@ 217-220
Read the person's own membership of that organisation (named as the user only: they can see their own memberships).

@@ 221-222
Not a member: `404`, exactly as if the organisation didn't exist — an outsider learns nothing.

@@ 223-224
A member whose role doesn't allow it: `403 forbidden_for_role`.

@@ 225
Allowed: return the organisation and the role.

@@ 228-229
**`list_members`** — any member may see who else belongs.

@@ 230-240
Named as the organisation and the user, read each member's ID, address and role, in the order they joined.

@@ 243-244
**`add_member`** — give an existing account a role.

@@ 245
Only owners and admins may.

@@ 246-247
The role must be one of the four.

@@ 248-249
Only an owner may make another owner: an admin can't promote anyone above themselves.

@@ 250
The address and the time.

@@ 251-255
Find the account; there must be one (inviting people by e-mail comes with the console's pages).

@@ 256-259
Add the membership, record it in the audit log, and save.

@@ 260-261
Already a member: the membership's key refuses a second one, answered as `409`.

@@ 262
Answer with the new member.

@@ 265-268
**`create_key`** — a new API key for one of the organisation's projects; owners, admins and developers may.

@@ 269-270
At least one scope, and only real ones.

@@ 271-274
A malformed project ID is "not found".

@@ 275
Make the key.

@@ 276-279
Named as the organisation, read the project; it must exist and belong to this organisation.

@@ 280-291
The key's row: only the **digest** of the secret, the project, the mode, the scopes, and neither expiring nor revoked.

@@ 292-295
Save it, with an audit entry naming the key by its id — never the key itself.

@@ 296-297
Answer with the key, the only time it is ever shown.

@@ 300-302
**`audit_log`** — the organisation's newest audit entries; owners and admins only.

@@ 303-306
Named as the organisation, read the newest entries (up to `limit`), and verify the whole chain.

@@ 307-317
Each entry as the console shows it: its number, who, what, to what, the facts, and when.

@@ 318-319
And the chain's verdict, so the console can show whether it is intact.
