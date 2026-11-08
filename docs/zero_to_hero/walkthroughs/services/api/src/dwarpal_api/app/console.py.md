---
fingerprint: db377cb527bd2ee3
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

@@ 7-15
`hashlib` (to hash session tokens) and `hmac` (for recovery codes' fingerprints), `json`, `re`, `secrets` (unpredictable tokens), `uuid`, `dataclass`, `datetime` (the type of a moment), and `TYPE_CHECKING` and `Any`.

@@ 17-19
SQLAlchemy's `select`, `func` (for counting), and `update` and `delete` (to change or remove many rows in one statement); `IntegrityError`, raised when the database refuses a row (here, a duplicate); and `AsyncSession`, the type of a unit of work, for a helper's signature.

@@ 21-40
The tenant helpers — `tenant`, and `name_tenant` to name another organisation within the same transaction — the account look-up and the function that takes a new address's invitations (`TAKE_INVITATIONS`), password hashing, the tables (including invitations and passkeys, and sessions and their attempts, for the decision trace), the other use cases this module reuses — analytics, the audit log, policies, verification and webhooks — IDs, origins and one-time codes, the key helpers, the `Policy` type, the roles, and our error class.

@@ 42-44
For type hints only: the master key's type and the toolbox (see `app/webhooks.py` for why such imports are kept apart).

@@ 46
`EMAIL` — a deliberately simple test of an e-mail address: something without spaces or a second `@`, an `@`, and a domain with a dot and a final part of at least two letters. The only real proof of an address is a message reaching it; this just catches typing slips.

@@ 47
`PASSWORD_LENGTHS` — 12 to 256 characters. Length matters far more than odd symbols; the upper limit only keeps hashing time bounded.

@@ 50
`SIGN_IN_REFUSED` — the one refusal for both a wrong password and an unknown address.

@@ 53-56
**`ConsoleSession`** — who is signed in, and their **CSRF token**, a second random value that every change must repeat in a header (`http/console.py`).

@@ 59-60
**`_slot`** — where a session lives in Valkey: the SHA-256 of its token, so a copy of Valkey doesn't hold any usable cookie.

@@ 63-64
**`actor_of`** — how the audit log names a person: `user` and their public ID (`usr_…`).

@@ 67-70
**`_master`** — the master key from the toolbox (it seals one-time-code secrets); missing would be a programming error.

@@ 79-80
**`open_session`** — start a signed-in session.

@@ 81
Two independent 32-byte random tokens: one for the cookie, one against CSRF.

@@ 82-84
Store who it is, the CSRF token and the generation the session begins in, for the session's lifetime (12 hours, renewed on each use).

@@ 85
Return the cookie's token and the session.

@@ 105-106
**`close_session`** — sign out: delete the session.

@@ 109-113
**`normalise_email`** — trim spaces, use lower case, and refuse what doesn't look like an address.

@@ 116-119
**`check_password`** — the length rule, and the password must not simply be the e-mail address.

@@ 122-123
**`sign_up`** — a new person, a new organisation they own, and a first project in it.

@@ 124-126
Check the address and the password, and hash the password (`adapters/passwords.py`).

@@ 127
The time and three new IDs.

@@ 128-129
One unit of work that names both the new organisation and the new user as its tenant. Row-level security insists that every new row belongs to the named tenant, so naming them first is what lets these rows be written.

@@ 130-131
If the address already has an account, refuse with `409 email_taken`.

@@ 132-134
Add the user and the organisation, and send them to the database (`flush`), so the membership's foreign keys find them.

@@ 135
Make the person the organisation's **owner**.

@@ 136-139
A first project, with no allowed origins yet.

@@ 140-143
Record the organisation's creation in its new audit log, naming the person and the project.

@@ 145
Save everything at once.

@@ 146-147
Two sign-ups with the same address at the same moment: the unique address lets only one in, and the other gets the same `409`.

@@ 148
Sign the new person in.

@@ 161-162
**`_spend_sign_in`** — each sign-in attempt takes a token from two buckets (`adapters/store.py`): one for the account, one for the network address.

@@ 163-168
For each bucket, take a token; if none is left, refuse with `429` and a `Retry-After` in whole seconds, rounded up (`-(-x // 1000)` divides and rounds up). The account bucket stops someone guessing one person's password from many places; the address bucket stops one place guessing many people's.

@@ 171-173
**`sign_in`** — check an address, a password and, if switched on, a one-time code.

@@ 174-175
Normalise the address and spend an attempt, before any work is done.

@@ 176-177
Find the account through the look-up function, before anyone is named.

@@ 178-180
Check the password — against the decoy when there is no account — and refuse with the same answer either way. Both paths do one Argon2 check, so they take the same time too.

@@ 181-185
The password was right: in a unit of work named for this user, read their row **locked**, so two sign-ins can't both use the same one-time code.

@@ 186-188
If codes are switched on, one must be given.

@@ 189-197
Open the sealed secret, and accept the code if it is right now and newer than the last one used; remember its step. If it isn't, it may be a **recovery code**: if it is one of the person's unused ones, it signs them in — and is used up, and the audit log records it, with how many are left. Otherwise, refused.

@@ 198
Note the time of this sign-in.

@@ 199-202
Record the sign-in in the audit log of every organisation the person belongs to.

@@ 203-204
Save, and open the session.

@@ 207
**`me`** — who is signed in, for the console's pages.

@@ 208-217
Read the user, and their organisations with their role in each, oldest first.

@@ 218-219
An account deleted meanwhile: sign in again.

@@ 220-228
The answer: their ID and address, whether one-time codes are on, how many recovery codes they have left, the session's CSRF token (the console's pages read it from here and send it back with each change), and their organisations.

@@ 231-234
**`_recovery_key`** — the key for recovery codes' fingerprints, made from the master key with HMAC and a label of its own: a key for this purpose alone, as the idempotency key is for its. Someone with a copy of the database but not the master key can't test guesses against the digests.

@@ 237-242
**`_new_recovery_codes`** — make ten fresh codes, keep only their digests (replacing any old ones, used or not), and return the codes: the one moment they exist in plain text.

@@ 245-251
**`_use_recovery_code`** — is this one of the person's unused codes? Its digest is compared with each kept one by `hmac.compare_digest`, which takes the same time whether the first character differs or the last, so timing can't reveal how close a guess came. If found, it is removed: each code works once.

@@ 254-258
**`_record_for_all`** — record something a person did to their own account (switching codes on or off, using a recovery code) in every organisation they belong to, since each organisation's administrators may need to know.

@@ 261-262
**`totp_enrol`** — start switching on one-time codes. Nothing changes until a code made from the new secret is confirmed, so a person can't lock themselves out by abandoning the set-up halfway.

@@ 263-269
Make a secret, and keep it **pending**, sealed under the master key with the user's ID as associated data.

@@ 270
Return the secret and its `otpauth://` address, for the console to show as a QR code.

@@ 273-278
**`totp_confirm`** — finish switching codes on. There must be a pending secret.

@@ 279-282
Open the pending secret and check the code against it; a wrong code is refused with a hint about the phone's clock.

@@ 283
The pending secret becomes the real one, and the code's step is remembered, so it can't be used again.

@@ 284-287
Make the ten **recovery codes**, record it in each of the person's organisations' audit logs, save, and answer with the codes — the only time they are shown.

@@ 290-300
**`replace_recovery_codes`** — a fresh set, for someone who lost theirs or used most of them. Only with one-time codes on; every old code stops working, used or not; the audit log records it.

@@ 303-305
**`totp_disable`** — switch one-time codes off. Only with the **password and a current code**: someone who has merely found a signed-in browser left open knows neither, so can't remove the protection.

@@ 306-311
Codes must be on. The attempt counts against the same limits as signing in (`_spend_sign_in`), so guessing the password here is as slow as guessing it at the sign-in page.

@@ 312-315
Check the code (without using it up yet) and the password; if either is wrong, one answer for both — `403 reauthentication_failed` — so the reply doesn't say which part was right.

@@ 316-319
Forget the secret, any pending one, the last step and every recovery code; record it in each organisation's audit log; save.

@@ 404-405
**`authorise`** — the gate for every organisation action: the person must be a member, and their role must allow the action.

@@ 406-409
A malformed organisation ID is "not found".

@@ 410-413
Read the person's own membership of that organisation (named as the user only: they can see their own memberships).

@@ 414-415
Not a member: `404`, exactly as if the organisation didn't exist — an outsider learns nothing.

@@ 416-417
A member whose role doesn't allow it: `403 forbidden_for_role`.

@@ 418
Allowed: return the organisation and the role.

@@ 421-422
**`list_members`** — any member may see who else belongs.

@@ 423-433
Named as the organisation and the user, read each member's ID, address and role, in the order they joined.

@@ 445-446
**`list_projects`** (Phase 5) — the organisation's projects, oldest first. Any member may read them: the console's keys page needs them to offer a project.

@@ 447-450
Check membership, then, named as the organisation, read its projects.

@@ 523-525
**`add_member`** — give an account a role; an address without an account is **invited** instead (decision D44). Only an owner may make — or invite — another owner.

@@ 526
Only owners and admins may.

@@ 527-528
The role must be one of the four.

@@ 529-530
Only an owner may make another owner: an admin can't promote anyone above themselves.

@@ 531
The address and the time.

@@ 546-549
Otherwise, add the membership, record it in the audit log, and save.

@@ 550-551
A second membership — or a second invitation for the same address — breaks one of the database's keys (the membership's own, or `uq_invitations_org_id_email`), answered as `409`.

@@ 592-596
**`_member_id`** (Phase 5, §5.5.4) — a member's ID from its public form (`usr_…`); a malformed one is simply "not found".

@@ 599-603
**`_lock_member`** — the membership about to change (to `new_role`) or go (`None`), if the rules allow it.

@@ 604-606
First lock every owner's membership row (`FOR UPDATE`): another request that wants to change an owner must wait until this one has finished. Without it, two owners could each demote the other at the same moment — each would see two owners, both changes would succeed, and the organisation would have none. Everyone takes the locks in the same order (owners first), so two requests can't wait for each other forever.

@@ 607-609
Then lock the member's own row; no such member in this organisation is `404`.

@@ 610-611
If the change involves an owner — making one, or changing or removing one — only an owner may do it. An admin can manage everyone else.

@@ 612-613
The **last owner** can't stop being one, by a role change or by removal: `409`, with what to do instead. Somebody must always be able to manage the organisation.

@@ 614
The locked membership.

@@ 617-620
**`change_role`** — give a member another role.

@@ 621-623
The person must be allowed to manage members, and the role must exist.

@@ 624-626
Read the member's ID and the time, then lock the membership under the rules above.

@@ 627
Remember the old role, and set the new one.

@@ 628-630
Record both roles in the audit log, in the same transaction, and save.

@@ 631
Answer with the member and their new role.

@@ 634-635
**`remove_member`** — take someone out of the organisation. Their account stays; they just lose access to it. People may remove themselves — unless they are the last owner.

@@ 636-639
The same checks and lock.

@@ 640-643
Record the removal (with the role they had), delete the membership, and save.

@@ 646-649
**`create_key`** — a new API key for one of the organisation's projects; owners, admins and developers may.

@@ 650-651
At least one scope, and only real ones.

@@ 652-655
A malformed project ID is "not found".

@@ 656
Make the key.

@@ 657-660
Named as the organisation, read the project; it must exist and belong to this organisation.

@@ 661-672
The key's row: only the **digest** of the secret, the project, the mode, the scopes, and neither expiring nor revoked.

@@ 673-676
Save it, with an audit entry naming the key by its id — never the key itself.

@@ 677-678
Answer with the key, the only time it is ever shown.

@@ 723-725
**`audit_log`** — the organisation's newest audit entries; owners and admins only.

@@ 726-729
Named as the organisation, read the newest entries (up to `limit`), and verify the whole chain.

@@ 730-740
Each entry as the console shows it: its number, who, what, to what, the facts, and when.

@@ 741-742
And the chain's verdict, so the console can show whether it is intact.

@@ 745-748
**`project_in`** (Phase 5) — the gate for every project page: the organisation and one of its projects, if the person's role there allows the action.

@@ 749
First the organisation and the role (`authorise`): not a member → 404, role not allowed → 403.

@@ 750-753
A malformed project ID is "not found".

@@ 754-757
Named as the organisation, read the project; it must exist **and belong to this organisation**. Without that last check, a member of organisation A could name organisation A in the address but a project of organisation B — and row-level security would not stop it, because the console names the organisation, not the project.

@@ 758
Return both.

@@ 761-771
**`project_sessions`** — a project's sessions, a page at a time, for any member, optionally filtered.

@@ 772-773
The same list a website reads with its key (`verification.list_sessions`), with the same filter, confined to this project.

@@ 776-780
**`session_trace`** — one session with its **decision trace**: what each attempt decided, why, and the numbers it rested on.

@@ 781-782
Check the project, and read the session's ID from its public form.

@@ 783-786
Named as the project, read the session; another project's session is simply invisible, and gets 404.

@@ 787-792
Its attempts, oldest first.

@@ 793-802
Each attempt's kind, outcome, reasons, scores (the stored numbers: the age probability, the line it was compared with, the liveness evidence) and time.

@@ 803
The session's summary — never a token: reading a trace must not mint one — and the attempts.

@@ 806-810
**`project_analytics`** — the project's daily counts, for roles allowed to read analytics.

@@ 813-815
**`model_information`** — the age model now deciding, for any signed-in person: it is the same for every organisation, so it needs no tenant and no role. It is not `async`: it reads only what the manifest loaded at start-up.

@@ 816-818
The manifest's whole file, its training section (or an empty dictionary, for the stub, which has none), and its calibration section if there is one.

@@ 819-824
The answer: the version; whether it may decide live sessions; its note and permitted use as written in the manifest; and only the backbone and dataset of its training — not the run's name, the pretrained file's checksum or the commit it was built from.

@@ 825
Where its lines were measured, as the manifest records it: which faces, under what licence, how their ages were known, and how many.

@@ 826-842
For each age and risk budget, the two lines and the two **measured bounds** — the worst plausible share of people under the age who would pass, and of people comfortably over it who would fail. `row.get(...)` gives `None` for the stub, which measured nothing.

And, as the comment says, **how adults fared** in each age band above the line on the test split — the shares that passed, were sent to a stronger check, or failed, and how many faces each share is of. The console's policy editor shows them as its projection (§5.5.8). Each band is copied field by field, so nothing else in the file can slip into the answer; the stub has none, and gets an empty list.

@@ 845-848
**`published_model`** (§5.5.9) — the model's description for anyone, signed in or not (`GET /v1/model`): everything `model_information` says but the scores at which each line passes and fails. The bounds and the adults' outcomes say how well a line works; the exact scores would only help someone tuning an attack.

@@ 849-854
Take the console's description, and copy each line without its two scores (`tau_pass`, `tau_fail`). `{**information, …}` copies the description with its lines replaced.

@@ 857-859
**`project_policies`** — the presets and the project's own policy versions, for any member.

@@ 862-865
**`add_policy_version`** — the next version of a policy, for roles allowed to manage policies.

@@ 866-870
Check the project and the role, then add the version, with the person (not an API key) named in the audit log.

@@ 873-878
**`project_webhooks`** (Phase 5, §5.5.3) — a project's endpoints in one mode. Only roles that may manage webhooks may even **see** them: an endpoint's address says where the project's events go, which is the kind of thing an attacker would like to know.

@@ 881-890
**`add_webhook`** — a new endpoint, from the console.

@@ 891-893
Check the project and the role, then create it with the website API's own use case — the same allowed events, the same SSRF guard, the same limit of 16, the same secret shown once — with the person named in the audit log.

@@ 896-901
**`remove_webhook`** — the same check, then delete it, the person named.

@@ 904-915
**`switch_webhook`** — the same from the console, for roles that may manage webhooks, naming the person.

@@ 918-922
**`send_test_event`** — queue a test event for one endpoint.

@@ 925-929
**`webhook_deliveries`** — an endpoint's recent deliveries.

@@ 932-936
**`replay_delivery`** — send a delivery again from the start of its retry schedule.

@@ 48-49
**Limits for projects** (decision D28): at most 20 in an organisation, and a name of 1 to 80 characters.

@@ 73-76
**`_generation`** — the Valkey key of a person's session **generation** (decisions D31, D32): a counter, 0 until it is first moved on. Every session remembers the generation it began in; changing the password or deleting the account moves it on, and every session begun before stops counting.

@@ 88-92
**`session_of`** — who is signed in with this token, if anyone. Reading renews the session's lifetime (`fetch`). The record holds who it is, the CSRF token and the session's generation.

@@ 93-96
A session begun in an older generation — before a password change, or the account's deletion — no longer counts: it is deleted, and nobody is signed in with it. (A session kept from before 8 Nov has no generation; it counts as 0, which matches until the person's first change.)

@@ 97
Otherwise: this person, with this session's CSRF token.

@@ 100-102
**`end_sessions`** — move the person's generation on: every session they have, in any browser, ends at its next request. (There is no list of a person's sessions to go through: this one number does it.)

@@ 144
Then the new account joins every organisation that invited its address (decision D44).

@@ 151-153
**`_join_invited`** — a new account joins every organisation that invited its address, with the role each named. The invitations are *taken* — deleted and returned at once, by a database function the policies don't bind (signing up happens before any organisation is named) — so none can be used twice.

@@ 154-156
For each: that organisation is named as the tenant, within the same transaction, and the membership is added…

@@ 157-158
…and recorded in its audit log: who joined, with which role, and who invited them.

@@ 322-323
**`_reauthenticate`** — proof that the person, not just their signed-in browser, is asking: the password, and a current one-time code if they have switched codes on.

@@ 324
The password is checked first, always.

@@ 325-330
With one-time codes on, a current code is needed too, and both must be right; the code is then used up (`totp_last_step`), as when signing in, so it can't be used again.

@@ 331-332
Without codes, the password alone.

@@ 335-339
**`change_password`** (decision D31): a new password, given with the old one (and a code, if codes are on). It returns a new session for this browser.

@@ 340-346
In one transaction on the person's own row, locked: the attempt counts against the same limits as signing in (so guessing the old password stays slow), and the person is checked again.

@@ 347-349
The new password must be long enough and not the e-mail address; it is hashed (Argon2id), and the change is recorded in every organisation the person belongs to.

@@ 350
Saved.

@@ 351-352
Then every session of the person ends — this browser's too — and this browser is given a fresh one, so it carries on signed in while every other browser must sign in again with the new password.

@@ 355-361
**`delete_account`** (decision D32): erase the person's account. The docstring states the rules: refused while they are an organisation's only owner and others remain; an organisation where they are alone closes with them; their personal data is erased; their ID stays in the audit chains, so the chains still verify.

@@ 362-368
The same start as a password change: the person's row locked, the sign-in limits, the password (and code) again.

@@ 369-370
Their memberships, and a note of which organisations will close.

@@ 371-373
Each organisation in turn is named as the tenant within this one transaction — so either everything below happens, or nothing does.

@@ 374-377
The organisation's other members, locked.

@@ 378-380
If there are others and none of them is an owner while this person is, the deletion is refused, naming the organisation: someone else must be made an owner first.

@@ 381
Otherwise, the organisation closes if nobody else is in it.

@@ 382
The person's public ID, for the audit log.

@@ 383-385
Then each organisation again, named as the tenant:

@@ 386-391
one where they were alone is closed — every key of every project in it stops at once (one `UPDATE` for them all) — and the closing is recorded;

@@ 392-393
in each, the deletion is recorded and the membership removed.

@@ 394
The person alone is named again, for their own row.

@@ 395-398
**The erasing.** The e-mail address becomes one nobody has (`.invalid` is a name reserved never to exist) — still unique, as the column requires — so the real address is free to sign up again; the password becomes `!`, which looks like no Argon2 hash, so no password can ever match it; the one-time-code secrets, recovery codes and last sign-in go.

@@ 399
Their passkeys are deleted.

@@ 400
All of it, at once.

@@ 401
And every session of theirs ends.

@@ 436-442
**`project_view`** — what the console shows of a project: its public ID, name, allowed origins and retention period.

@@ 451
Each project as `project_view` writes it.

@@ 454-458
**`_project_name`** — a project's name, trimmed, of 1 to 80 characters (decision D28).

@@ 461-465
**`_allowed_origins`** — the list of origins, checked and written the standard way by `domain/origins.py` (decision D29): `https://` in production, and `http://` too for `localhost` while developing. A refusal is answered `422 invalid_origin`, with the rule's own words.

@@ 468-471
**`create_project`** — a new project in the organisation, with its name and allowed origins.

@@ 472-473
Owners and admins only (`projects.manage`); the name and origins are checked before anything is written.

@@ 474-479
In the organisation's tenant: its row is locked — two new projects at the same moment would otherwise both be counted under the limit — then its projects are counted; at 20, `409 too_many_projects`.

@@ 480-483
The project, kept for the default 90 days.

@@ 484-486
Recorded in the audit log with its name and origins, and saved.

@@ 487
Answered as the list shows projects.

@@ 490-498
**`update_project`** — rename a project, or replace its whole list of allowed origins, or both.

@@ 499-500
Asking to change nothing is a mistake: `422`.

@@ 501-504
The role (owners and admins) and the project, then the new values checked before anything is written.

@@ 505-508
The project's row, locked while it changes.

@@ 509-515
Only what really changes is changed — and noted, from and to.

@@ 516-519
If anything changed, it is recorded in the audit log; then saved.

@@ 520
The project as it now is.

@@ 532
Who is acting, for the audit log.

@@ 533-535
In the organisation's tenant, look the address up.

@@ 536-540
No account: an **invitation** waits instead — the address, the role, who invited, and when.

@@ 541-545
The audit log names the invitation, not the address: its chain can't be edited later, and an address is personal. The answer says the member is `pending`.

@@ 552
Answer with the new member, not pending.

@@ 555-560
**`list_invitations`** — the invitations still waiting, oldest first, for the roles that manage members.

@@ 561-570
Each with its public ID, address, role and when it was made.

@@ 573-578
**`cancel_invitation`** — withdraw one, by its public ID (a malformed one is simply not found).

@@ 579-583
In the organisation's tenant. It isn't locked: an invitation is never changed, only made and deleted — the app's role may not update one at all, and `SELECT … FOR UPDATE` would need that right. One from another organisation is not found.

@@ 584-589
Recorded, with its role; then deleted, and saved.

@@ 681-693
**`key_view`** (decision D30) — what the console shows of a key: its public ID (the lookup part), mode, scopes and dates, and a state worked out from them: `revoked`, `expired` (a rotated key past its grace) or `active`. Never the secret: Dwarpal keeps only its digest.

@@ 696-703
**`project_keys`** — a project's keys, newest first, for the roles that may make keys (owners, admins and developers).

@@ 706-708
**`revoke_key`** — stop a key at once. Nothing caches keys: every request looks its key up afresh, so the next request with this one is refused.

@@ 709-713
The role and the project; the key, found by its public ID within that project, locked.

@@ 714-715
Not there: `404 key_not_found`.

@@ 716-719
Revoked only if it wasn't already — so revoking twice records it once — with the time, and an audit entry naming the project.

@@ 720
Saved.
