---
fingerprint: 8327dd21cf708044
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

@@ 54-57
**`ConsoleSession`** — who is signed in, and their **CSRF token**, a second random value that every change must repeat in a header (`http/console.py`).

@@ 60-61
**`_slot`** — where a session lives in Valkey: the SHA-256 of its token, so a copy of Valkey doesn't hold any usable cookie.

@@ 64-65
**`actor_of`** — how the audit log names a person: `user` and their public ID (`usr_…`).

@@ 68-71
**`_master`** — the master key from the toolbox (it seals one-time-code secrets); missing would be a programming error.

@@ 80-81
**`open_session`** — start a signed-in session.

@@ 82
Two independent 32-byte random tokens: one for the cookie, one against CSRF.

@@ 83-85
Store who it is, the CSRF token and the generation the session begins in, for the session's lifetime (12 hours, renewed on each use).

@@ 86
Return the cookie's token and the session.

@@ 106-107
**`close_session`** — sign out: delete the session.

@@ 110-114
**`normalise_email`** — trim spaces, use lower case, and refuse what doesn't look like an address.

@@ 117-120
**`check_password`** — the length rule, and the password must not simply be the e-mail address.

@@ 123-124
**`sign_up`** — a new person, a new organisation they own, and a first project in it.

@@ 125-127
Check the address and the password, and hash the password (`adapters/passwords.py`).

@@ 128
The time and three new IDs.

@@ 129-130
One unit of work that names both the new organisation and the new user as its tenant. Row-level security insists that every new row belongs to the named tenant, so naming them first is what lets these rows be written.

@@ 131-132
If the address already has an account, refuse with `409 email_taken`.

@@ 133-135
Add the user and the organisation, and send them to the database (`flush`), so the membership's foreign keys find them.

@@ 136
Make the person the organisation's **owner**.

@@ 137-140
A first project, with no allowed origins yet.

@@ 141-144
Record the organisation's creation in its new audit log, naming the person and the project.

@@ 146
Save everything at once.

@@ 147-148
Two sign-ups with the same address at the same moment: the unique address lets only one in, and the other gets the same `409`.

@@ 149
Sign the new person in.

@@ 197-199
**`sign_in`** — check an address, a password and, if switched on, a one-time code.

@@ 200-201
Normalise the address and spend an attempt, before any work is done.

@@ 202-203
Find the account through the look-up function, before anyone is named.

@@ 204-208
Check the password — against the decoy when there is no account — and refuse with the same answer either way. Both paths do one Argon2 check, so they take the same time too; and since 9 Nov both count as a wrong try (`_wrong`), so an account that doesn't exist locks just like one that does, and a lock doesn't tell anyone that an address has an account.

@@ 209-213
The password was right: in a unit of work named for this user, read their row **locked**, so two sign-ins can't both use the same one-time code.

@@ 214-216
If codes are switched on, one must be given.

@@ 217-226
Open the sealed secret, and accept the code if it is right now and newer than the last one used; remember its step. If it isn't, it may be a **recovery code**: if it is one of the person's unused ones, it signs them in — and is used up, and the audit log records it, with how many are left. Otherwise, refused. Since 9 Nov a wrong code counts as a wrong try too (`_wrong`): six digits are as guessable as a short password.

@@ 227
Note the time of this sign-in.

@@ 228-231
Record the sign-in in the audit log of every organisation the person belongs to.

@@ 232-234
Save. Signed in: the wrong tries before this one are forgotten, and any lock on this address with them (`forget`). Then open the session.

@@ 237
**`me`** — who is signed in, for the console's pages.

@@ 238-247
Read the user, and their organisations with their role in each, oldest first.

@@ 248-249
An account deleted meanwhile: sign in again.

@@ 250-258
The answer: their ID and address, whether one-time codes are on, how many recovery codes they have left, the session's CSRF token (the console's pages read it from here and send it back with each change), and their organisations.

@@ 261-264
**`_recovery_key`** — the key for recovery codes' fingerprints, made from the master key with HMAC and a label of its own: a key for this purpose alone, as the idempotency key is for its. Someone with a copy of the database but not the master key can't test guesses against the digests.

@@ 267-272
**`_new_recovery_codes`** — make ten fresh codes, keep only their digests (replacing any old ones, used or not), and return the codes: the one moment they exist in plain text.

@@ 275-281
**`_use_recovery_code`** — is this one of the person's unused codes? Its digest is compared with each kept one by `hmac.compare_digest`, which takes the same time whether the first character differs or the last, so timing can't reveal how close a guess came. If found, it is removed: each code works once.

@@ 284-288
**`_record_for_all`** — record something a person did to their own account (switching codes on or off, using a recovery code) in every organisation they belong to, since each organisation's administrators may need to know.

@@ 291-292
**`totp_enrol`** — start switching on one-time codes. Nothing changes until a code made from the new secret is confirmed, so a person can't lock themselves out by abandoning the set-up halfway.

@@ 293-299
Make a secret, and keep it **pending**, sealed under the master key with the user's ID as associated data.

@@ 300
Return the secret and its `otpauth://` address, for the console to show as a QR code.

@@ 303-308
**`totp_confirm`** — finish switching codes on. There must be a pending secret.

@@ 309-312
Open the pending secret and check the code against it; a wrong code is refused with a hint about the phone's clock.

@@ 313
The pending secret becomes the real one, and the code's step is remembered, so it can't be used again.

@@ 314-317
Make the ten **recovery codes**, record it in each of the person's organisations' audit logs, save, and answer with the codes — the only time they are shown.

@@ 320-330
**`replace_recovery_codes`** — a fresh set, for someone who lost theirs or used most of them. Only with one-time codes on; every old code stops working, used or not; the audit log records it.

@@ 333-335
**`totp_disable`** — switch one-time codes off. Only with the **password and a current code**: someone who has merely found a signed-in browser left open knows neither, so can't remove the protection.

@@ 336-341
Codes must be on. The attempt counts against the same limits as signing in (`_spend_sign_in`), so guessing the password here is as slow as guessing it at the sign-in page.

@@ 342-346
Check the code (without using it up yet) and the password; if either is wrong, it counts as a wrong try (`_wrong`, 9 Nov), and one answer covers both — `403 reauthentication_failed` — so it doesn't say which part was right.

@@ 347-350
Forget the secret, any pending one, the last step and every recovery code; record it in each organisation's audit log; save.

@@ 439-440
**`authorise`** — the gate for every organisation action: the person must be a member, and their role must allow the action.

@@ 441-444
A malformed organisation ID is "not found".

@@ 445-448
Read the person's own membership of that organisation (named as the user only: they can see their own memberships).

@@ 449-450
Not a member: `404`, exactly as if the organisation didn't exist — an outsider learns nothing.

@@ 451-452
A member whose role doesn't allow it: `403 forbidden_for_role`.

@@ 453
Allowed: return the organisation and the role.

@@ 456-457
**`list_members`** — any member may see who else belongs.

@@ 458-468
Named as the organisation and the user, read each member's ID, address and role, in the order they joined.

@@ 480-481
**`list_projects`** (Phase 5) — the organisation's projects, oldest first. Any member may read them: the console's keys page needs them to offer a project.

@@ 482-485
Check membership, then, named as the organisation, read its projects.

@@ 558-560
**`add_member`** — give an account a role; an address without an account is **invited** instead (decision D44). Only an owner may make — or invite — another owner.

@@ 561
Only owners and admins may.

@@ 562-563
The role must be one of the four.

@@ 564-565
Only an owner may make another owner: an admin can't promote anyone above themselves.

@@ 566
The address and the time.

@@ 581-584
Otherwise, add the membership, record it in the audit log, and save.

@@ 585-586
A second membership — or a second invitation for the same address — breaks one of the database's keys (the membership's own, or `uq_invitations_org_id_email`), answered as `409`.

@@ 627-631
**`_member_id`** (Phase 5, §5.5.4) — a member's ID from its public form (`usr_…`); a malformed one is simply "not found".

@@ 634-638
**`_lock_member`** — the membership about to change (to `new_role`) or go (`None`), if the rules allow it.

@@ 639-641
First lock every owner's membership row (`FOR UPDATE`): another request that wants to change an owner must wait until this one has finished. Without it, two owners could each demote the other at the same moment — each would see two owners, both changes would succeed, and the organisation would have none. Everyone takes the locks in the same order (owners first), so two requests can't wait for each other forever.

@@ 642-644
Then lock the member's own row; no such member in this organisation is `404`.

@@ 645-646
If the change involves an owner — making one, or changing or removing one — only an owner may do it. An admin can manage everyone else.

@@ 647-648
The **last owner** can't stop being one, by a role change or by removal: `409`, with what to do instead. Somebody must always be able to manage the organisation.

@@ 649
The locked membership.

@@ 652-655
**`change_role`** — give a member another role.

@@ 656-658
The person must be allowed to manage members, and the role must exist.

@@ 659-661
Read the member's ID and the time, then lock the membership under the rules above.

@@ 662
Remember the old role, and set the new one.

@@ 663-665
Record both roles in the audit log, in the same transaction, and save.

@@ 666
Answer with the member and their new role.

@@ 669-670
**`remove_member`** — take someone out of the organisation. Their account stays; they just lose access to it. People may remove themselves — unless they are the last owner.

@@ 671-674
The same checks and lock.

@@ 675-678
Record the removal (with the role they had), delete the membership, and save.

@@ 681-684
**`create_key`** — a new API key for one of the organisation's projects; owners, admins and developers may.

@@ 685-686
At least one scope, and only real ones.

@@ 687-690
A malformed project ID is "not found".

@@ 691
Make the key.

@@ 692-695
Named as the organisation, read the project; it must exist and belong to this organisation.

@@ 696-707
The key's row: only the **digest** of the secret, the project, the mode, the scopes, and neither expiring nor revoked.

@@ 708-711
Save it, with an audit entry naming the key by its id — never the key itself.

@@ 712-713
Answer with the key, the only time it is ever shown.

@@ 758-760
**`audit_log`** — the organisation's newest audit entries; owners and admins only.

@@ 761-764
Named as the organisation, read the newest entries (up to `limit`), and verify the whole chain.

@@ 765-775
Each entry as the console shows it: its number, who, what, to what, the facts, and when.

@@ 776-777
And the chain's verdict, so the console can show whether it is intact.

@@ 780-783
**`project_in`** (Phase 5) — the gate for every project page: the organisation and one of its projects, if the person's role there allows the action.

@@ 784
First the organisation and the role (`authorise`): not a member → 404, role not allowed → 403.

@@ 785-788
A malformed project ID is "not found".

@@ 789-792
Named as the organisation, read the project; it must exist **and belong to this organisation**. Without that last check, a member of organisation A could name organisation A in the address but a project of organisation B — and row-level security would not stop it, because the console names the organisation, not the project.

@@ 793
Return both.

@@ 796-806
**`project_sessions`** — a project's sessions, a page at a time, for any member, optionally filtered.

@@ 807-808
The same list a website reads with its key (`verification.list_sessions`), with the same filter, confined to this project.

@@ 811-815
**`session_trace`** — one session with its **decision trace**: what each attempt decided, why, and the numbers it rested on.

@@ 816-817
Check the project, and read the session's ID from its public form.

@@ 818-821
Named as the project, read the session; another project's session is simply invisible, and gets 404.

@@ 822-827
Its attempts, oldest first.

@@ 828-837
Each attempt's kind, outcome, reasons, scores (the stored numbers: the age probability, the line it was compared with, the liveness evidence) and time.

@@ 838
The session's summary — never a token: reading a trace must not mint one — and the attempts.

@@ 841-845
**`project_analytics`** — the project's daily counts, for roles allowed to read analytics.

@@ 848-850
**`model_information`** — the age model now deciding, for any signed-in person: it is the same for every organisation, so it needs no tenant and no role. It is not `async`: it reads only what the manifest loaded at start-up.

@@ 851-853
The manifest's whole file, its training section (or an empty dictionary, for the stub, which has none), and its calibration section if there is one.

@@ 854-859
The answer: the version; whether it may decide live sessions; its note and permitted use as written in the manifest; and only the backbone and dataset of its training — not the run's name, the pretrained file's checksum or the commit it was built from.

@@ 860
Where its lines were measured, as the manifest records it: which faces, under what licence, how their ages were known, and how many.

@@ 861-877
For each age and risk budget, the two lines and the two **measured bounds** — the worst plausible share of people under the age who would pass, and of people comfortably over it who would fail. `row.get(...)` gives `None` for the stub, which measured nothing.

And, as the comment says, **how adults fared** in each age band above the line on the test split — the shares that passed, were sent to a stronger check, or failed, and how many faces each share is of. The console's policy editor shows them as its projection (§5.5.8). Each band is copied field by field, so nothing else in the file can slip into the answer; the stub has none, and gets an empty list.

@@ 880-883
**`published_model`** (§5.5.9) — the model's description for anyone, signed in or not (`GET /v1/model`): everything `model_information` says but the scores at which each line passes and fails. The bounds and the adults' outcomes say how well a line works; the exact scores would only help someone tuning an attack.

@@ 884-889
Take the console's description, and copy each line without its two scores (`tau_pass`, `tau_fail`). `{**information, …}` copies the description with its lines replaced.

@@ 892-894
**`project_policies`** — the presets and the project's own policy versions, for any member.

@@ 897-900
**`add_policy_version`** — the next version of a policy, for roles allowed to manage policies.

@@ 901-905
Check the project and the role, then add the version, with the person (not an API key) named in the audit log.

@@ 908-913
**`project_webhooks`** (Phase 5, §5.5.3) — a project's endpoints in one mode. Only roles that may manage webhooks may even **see** them: an endpoint's address says where the project's events go, which is the kind of thing an attacker would like to know.

@@ 916-925
**`add_webhook`** — a new endpoint, from the console.

@@ 926-928
Check the project and the role, then create it with the website API's own use case — the same allowed events, the same SSRF guard, the same limit of 16, the same secret shown once — with the person named in the audit log.

@@ 931-936
**`remove_webhook`** — the same check, then delete it, the person named.

@@ 939-950
**`switch_webhook`** — the same from the console, for roles that may manage webhooks, naming the person.

@@ 953-957
**`send_test_event`** — queue a test event for one endpoint.

@@ 960-964
**`webhook_deliveries`** — an endpoint's recent deliveries.

@@ 967-971
**`replay_delivery`** — send a delivery again from the start of its retry schedule.

@@ 48-49
**Limits for projects** (decision D28): at most 20 in an organisation, and a name of 1 to 80 characters.

@@ 74-77
**`_generation`** — the Valkey key of a person's session **generation** (decisions D31, D32): a counter, 0 until it is first moved on. Every session remembers the generation it began in; changing the password or deleting the account moves it on, and every session begun before stops counting.

@@ 89-93
**`session_of`** — who is signed in with this token, if anyone. Reading renews the session's lifetime (`fetch`). The record holds who it is, the CSRF token and the session's generation.

@@ 94-97
A session begun in an older generation — before a password change, or the account's deletion — no longer counts: it is deleted, and nobody is signed in with it. (A session kept from before 8 Nov has no generation; it counts as 0, which matches until the person's first change.)

@@ 98
Otherwise: this person, with this session's CSRF token.

@@ 101-103
**`end_sessions`** — move the person's generation on: every session they have, in any browser, ends at its next request. (There is no list of a person's sessions to go through: this one number does it.)

@@ 145
Then the new account joins every organisation that invited its address (decision D44).

@@ 152-154
**`_join_invited`** — a new account joins every organisation that invited its address, with the role each named. The invitations are *taken* — deleted and returned at once, by a database function the policies don't bind (signing up happens before any organisation is named) — so none can be used twice.

@@ 155-157
For each: that organisation is named as the tenant, within the same transaction, and the membership is added…

@@ 158-159
…and recorded in its audit log: who joined, with which role, and who invited them.

@@ 372-376
**`change_password`** (decision D31): a new password, given with the old one (and a code, if codes are on). It returns a new session for this browser.

@@ 377-382
In one transaction on the person's own row, locked: the person is checked again (`_reauthenticate`), which also spends a sign-in attempt, so guessing the old password stays slow.

@@ 383-385
The new password must be long enough and not the e-mail address; it is hashed (Argon2id), and the change is recorded in every organisation the person belongs to.

@@ 386
Saved.

@@ 387-388
Then every session of the person ends — this browser's too — and this browser is given a fresh one, so it carries on signed in while every other browser must sign in again with the new password.

@@ 391-397
**`delete_account`** (decision D32): erase the person's account. The docstring states the rules: refused while they are an organisation's only owner and others remain; an organisation where they are alone closes with them; their personal data is erased; their ID stays in the audit chains, so the chains still verify.

@@ 398-403
The same start as a password change: the person's row locked, then the sign-in limits and the password (and code) again, in `_reauthenticate`.

@@ 404-405
Their memberships, and a note of which organisations will close.

@@ 406-408
Each organisation in turn is named as the tenant within this one transaction — so either everything below happens, or nothing does.

@@ 409-412
The organisation's other members, locked.

@@ 413-415
If there are others and none of them is an owner while this person is, the deletion is refused, naming the organisation: someone else must be made an owner first.

@@ 416
Otherwise, the organisation closes if nobody else is in it.

@@ 417
The person's public ID, for the audit log.

@@ 418-420
Then each organisation again, named as the tenant:

@@ 421-426
one where they were alone is closed — every key of every project in it stops at once (one `UPDATE` for them all) — and the closing is recorded;

@@ 427-428
in each, the deletion is recorded and the membership removed.

@@ 429
The person alone is named again, for their own row.

@@ 430-433
**The erasing.** The e-mail address becomes one nobody has (`.invalid` is a name reserved never to exist) — still unique, as the column requires — so the real address is free to sign up again; the password becomes `!`, which looks like no Argon2 hash, so no password can ever match it; the one-time-code secrets, recovery codes and last sign-in go.

@@ 434
Their passkeys are deleted.

@@ 435
All of it, at once.

@@ 436
And every session of theirs ends.

@@ 471-477
**`project_view`** — what the console shows of a project: its public ID, name, allowed origins and retention period.

@@ 486
Each project as `project_view` writes it.

@@ 489-493
**`_project_name`** — a project's name, trimmed, of 1 to 80 characters (decision D28).

@@ 496-500
**`_allowed_origins`** — the list of origins, checked and written the standard way by `domain/origins.py` (decision D29): `https://` in production, and `http://` too for `localhost` while developing. A refusal is answered `422 invalid_origin`, with the rule's own words.

@@ 503-506
**`create_project`** — a new project in the organisation, with its name and allowed origins.

@@ 507-508
Owners and admins only (`projects.manage`); the name and origins are checked before anything is written.

@@ 509-514
In the organisation's tenant: its row is locked — two new projects at the same moment would otherwise both be counted under the limit — then its projects are counted; at 20, `409 too_many_projects`.

@@ 515-518
The project, kept for the default 90 days.

@@ 519-521
Recorded in the audit log with its name and origins, and saved.

@@ 522
Answered as the list shows projects.

@@ 525-533
**`update_project`** — rename a project, or replace its whole list of allowed origins, or both.

@@ 534-535
Asking to change nothing is a mistake: `422`.

@@ 536-539
The role (owners and admins) and the project, then the new values checked before anything is written.

@@ 540-543
The project's row, locked while it changes.

@@ 544-550
Only what really changes is changed — and noted, from and to.

@@ 551-554
If anything changed, it is recorded in the audit log; then saved.

@@ 555
The project as it now is.

@@ 567
Who is acting, for the audit log.

@@ 568-570
In the organisation's tenant, look the address up.

@@ 571-575
No account: an **invitation** waits instead — the address, the role, who invited, and when.

@@ 576-580
The audit log names the invitation, not the address: its chain can't be edited later, and an address is personal. The answer says the member is `pending`.

@@ 587
Answer with the new member, not pending.

@@ 590-595
**`list_invitations`** — the invitations still waiting, oldest first, for the roles that manage members.

@@ 596-605
Each with its public ID, address, role and when it was made.

@@ 608-613
**`cancel_invitation`** — withdraw one, by its public ID (a malformed one is simply not found).

@@ 614-618
In the organisation's tenant. It isn't locked: an invitation is never changed, only made and deleted — the app's role may not update one at all, and `SELECT … FOR UPDATE` would need that right. One from another organisation is not found.

@@ 619-624
Recorded, with its role; then deleted, and saved.

@@ 716-728
**`key_view`** (decision D30) — what the console shows of a key: its public ID (the lookup part), mode, scopes and dates, and a state worked out from them: `revoked`, `expired` (a rotated key past its grace) or `active`. Never the secret: Dwarpal keeps only its digest.

@@ 731-738
**`project_keys`** — a project's keys, newest first, for the roles that may make keys (owners, admins and developers).

@@ 741-743
**`revoke_key`** — stop a key at once. Nothing caches keys: every request looks its key up afresh, so the next request with this one is refused.

@@ 744-748
The role and the project; the key, found by its public ID within that project, locked.

@@ 749-750
Not there: `404 key_not_found`.

@@ 751-754
Revoked only if it wasn't already — so revoking twice records it once — with the time, and an audit entry naming the project.

@@ 755
Saved.

@@ 51
**`FAILURES_FORGOTTEN_S`** (9 Nov) — wrong sign-in tries count towards a lock until a day has passed since the latest one.

@@ 162-165
**`lock_s`** (9 Nov) — the design's **lock-out back-off** as a rule: how long an account stays locked to one network address after a run of wrong tries from it. A pure function — numbers in, a number out — so a test checks the whole schedule without a database (`test_console_rules.py`).

@@ 166-167
`over` is how many wrong tries came after the free ones. None yet: no lock. Otherwise the first lock, doubled for each try after the first one over (`2 ** (over - 1)`), but never longer than the longest. With the settings' numbers: five free, then 1 minute, 2, 4, 8, 16, 32 — and an hour from then on. (`min(over - 1, 30)` keeps the power small: a billion wrong tries still give an hour, at once.)

@@ 170-172
**`_too_many`** — the one refusal for too many sign-in attempts, whichever limit said so: `429 too_many_sign_ins`, with `Retry-After` in whole seconds, rounded up (`-(-x // 1000)` divides and rounds up), so the page can say how long to wait.

@@ 175-177
**`_spend_sign_in`** — every sign-in attempt, and every request that asks for the password again, starts here.

@@ 178-181
First the lock (9 Nov): while wrong tries have locked this account to this address, refuse at once — before the password is even looked at, so the right password doesn't open a lock early. The key names the pair: the account's e-mail address and the network address.

@@ 182-185
Then the steady limits: a token from two buckets, one for the account and one for the network address. The account bucket keeps guesses at one person's password slow from however many addresses; the address bucket stops one place guessing many accounts.

@@ 188-189
**`_wrong`** (9 Nov) — a wrong password or code for this account from this address.

@@ 190-194
Count it (forgotten a day after the latest), work out the lock for that many (`lock_s`, with the settings' numbers) and, if there is one, set it on the pair. Only the address the wrong tries came from is locked: someone guessing a stranger's password can't lock the owner out, who signs in from their own address — or with a passkey, which never asks for the password.

@@ 353-357
**`_reauthenticate`** — proof that the person, not just their signed-in browser, is asking: the password, and a current one-time code if they have switched codes on. Since 9 Nov it also takes the network address, and applies the sign-in limits itself.

@@ 358
The same limits as signing in, and the same lock (`_spend_sign_in`): guessing the password through a borrowed signed-in browser is no faster than through the sign-in page.

@@ 359
Check the password first, and keep the answer.

@@ 360-366
With one-time codes on, a current code is needed too, and both must be right — otherwise a wrong try is counted (`_wrong`) and one answer covers both. The code is then used up (`totp_last_step`), as when signing in, so it can't be used again.

@@ 367-369
Without codes, the password alone; a wrong one is counted the same way.
