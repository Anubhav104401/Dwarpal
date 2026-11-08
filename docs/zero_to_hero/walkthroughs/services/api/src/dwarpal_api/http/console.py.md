---
fingerprint: eb0fbf5a59122bcb
---
The **console API** (Phase 4, §5.4.5), under `/console/v1`: what Dwarpal's own web console calls for a signed-in person. Unlike the website API, which uses API keys, it uses a **cookie**, because people sign in with a browser.

Cookies bring a classic danger, **cross-site request forgery** (CSRF). A browser sends a site's cookie with *every* request to that site, even one triggered by a page on another site. A malicious page could make your browser post "add attacker as owner" to the console, and the browser would helpfully attach your cookie. Two defences stop it here:

- every change must also carry the session's **CSRF token** in an `X-CSRF-Token` header. The console's own pages read it from `/me`; another site's page can't read it, because browsers forbid one site reading another's responses;
- every change's `Origin` header, which browsers set and pages can't fake, must be one of the console's own addresses.

| Method and path | Who | What |
| :-- | :-- | :-- |
| `POST /signup`, `POST /login` | anyone | create an account, or sign in; set the cookie |
| `POST /logout` | signed in, CSRF | end the session |
| `GET /me` | signed in | who you are, your organisations, the CSRF token |
| `POST /totp`, `POST /totp/confirm` | signed in, CSRF | switch on one-time codes |
| `GET`/`POST /orgs/{org}/members` | members / owners and admins | list or add members |
| `POST /orgs/{org}/projects/{project}/keys` | owners, admins, developers | create an API key |
| `GET /orgs/{org}/audit` | owners and admins | the audit log, and whether its chain is intact |

@@ 1-2
The docstring.

@@ 4
The project-wide type-hint setting.

@@ 6-7
`hmac` (for its constant-time comparison), and `Annotated` and `Any`.

@@ 9-10
FastAPI's pieces, and Pydantic's model, settings and field limits.

@@ 12-18
The console's and the passkeys' use cases and the session type, the toolbox type and the session filter, the outcome names, the `Policy` type, our error class, and the toolbox dependency.

@@ 19
The body of a new policy version, as the website API defines it (`http/policies.py`): one shape, one set of rules.

@@ 20
The body of a new webhook endpoint, and of a switch, as the website API defines them (`http/webhooks.py`).

@@ 22-23
The router, under `/console/v1`, and a short name for the toolbox parameter.

@@ 26-28
**`cookie_name`** — the cookie is called `__Host-dwarpal_session`. Browsers enforce the **`__Host-` prefix**: such a cookie must be `Secure` (HTTPS only), set for the whole site (`path=/`) and tied to exactly this host, so no other site — not even a sub-domain — can set or overwrite it. Only the tests, over plain HTTP, use the plain name.

@@ 31-34
**`check_origin`** — if the request names an `Origin` (browsers always do for these requests), it must be one of the console's addresses. A program that isn't a browser sends none, and can't carry someone else's cookie anyway.

@@ 37-42
**`signed_in`** — the gate for signed-in requests: read the cookie, look its session up, and refuse with `401` if there is none. It returns the token too, for signing out.

@@ 45-50
**`changing`** — the gate for requests that change something: signed in, and also the CSRF token from the `X-CSRF-Token` header (empty if missing).

@@ 51-52
Its docstring: why the token stops forged requests.

@@ 53
Check the origin.

@@ 54-56
Compare the token with the session's, in constant time; refuse with `403 csrf_failed` if they differ.

@@ 57
Let the change proceed.

@@ 60-61
**`reading`** — the gate for requests that only read: signed in is enough. Reading can't be forged into harm, and another site can't see the answer.

@@ 64-65
Short names for the two kinds of caller, used in every endpoint below.

@@ 68-73
**`give_cookie`** — set the session cookie: for 12 hours; `httponly=True`, so the page's own JavaScript can't read it (a script injected into the page can't steal it); `secure`, so it only travels over HTTPS; `samesite="lax"`, so browsers don't send it with requests that other sites trigger in the background — a third CSRF defence; for the whole site.

@@ 76-81
**`SignUp`** — the body for signing up: an address, a password, and the organisation's name, each with a length limit.

@@ 84-90
**`SignIn`** — an address, a password, and optionally a code: six digits from the phone, or one of the recovery codes (five letters, a dash or space or nothing, five letters; capitals allowed), as the published document states.

@@ 93-105
**`Code`** — a body holding just a six-digit code. **`Reauthentication`** (Phase 5) — the password and a current six-digit code, for turning one-time codes off. Recovery codes aren't accepted there: they are for signing in when the phone is lost, not for removing the protection.

@@ 155-159
**`NewMember`** — an address and a role.

@@ 162-165
**`RoleChange`** — the body of a role change: just the new role.

@@ 168-172
**`NewKey`** — one to eight scopes, and whether the key is live (test by default).

@@ 194-199
**`sign_up`** — check the origin, create the account, give the cookie, and answer with who is now signed in.

@@ 228-233
**`sign_out`** — a change (so it needs the CSRF token); the `_` parameter runs that check, and its value isn't needed.

@@ 234-237
End the session, and tell the browser to delete the cookie.

@@ 240-242
**`me`** — who is signed in.

@@ 245-248
**`model`** — `GET /console/v1/model`: the age model's details. `current` isn't used inside, but asking for it makes the route refuse anyone not signed in.

@@ 251-253
**`totp_enrol`** — start switching on one-time codes.

@@ 317-319
**`list_members`**.

@@ 322-324
**`list_projects`** — `GET /orgs/{org}/projects`, for any signed-in member.

@@ 327-330
**`add_member`** — `201 Created`, for a membership or, for an address without an account, an invitation (`"pending": true`).

@@ 344-348
**`change_role`** — `PATCH …/members/{user}`. `PATCH` is the HTTP method for changing part of something: here, one field of a membership.

@@ 351-354
**`remove_member`** — `DELETE …/members/{user}`: `204`.

@@ 369-371
**`create_key`** — `201 Created`, with the key shown once.

@@ 385-389
**`audit_log`** — up to 500 entries (100 if not asked).

@@ 392-393
The path every project route starts with, written once; and `Live`, the `livemode` query parameter (`?livemode=true`), which chooses test or live data.

@@ 396-409
**`project_sessions`** — `GET …/sessions`: test sessions unless asked for live, 20 a page (at most 100), after the given cursor — and, like the website API, optionally only one outcome or one reference.

@@ 412-416
**`session_trace`** — `GET …/sessions/{id}`: one session's decision trace.

@@ 419-428
**`project_analytics`** — `GET …/analytics`: the last 30 days (1 to 365), test or live.

@@ 431-433
**`project_policies`** — `GET …/policies`.

@@ 436-448
**`add_policy_version`** — `POST …/policies`, a change (so it needs the CSRF token): build the draft from the body — the Age Pass switch included — and add it.

@@ 451-454
**`ConsoleEndpoint`** — that body plus `livemode` (test unless asked). A website's key is already test or live; a person in the console chooses.

@@ 457-461
**`project_webhooks`** — `GET …/webhooks`: the endpoints, test or live.

@@ 464-468
**`add_webhook`** — `POST …/webhooks`, a change: `201`, with the secret.

@@ 471-476
**`remove_webhook`** — `DELETE …/webhooks/{id}`: `204`. The mode comes in the address (`?livemode=true`), like every other webhook route here.

@@ 479-489
**`switch_webhook`** — `PATCH …/webhooks/{id}`, a change: on or off, in the mode the address names.

@@ 492-496
**`send_test_event`** — `POST …/webhooks/{id}/test`: `202 Accepted` — queued, not yet sent.

@@ 499-503
**`webhook_deliveries`** — `GET …/webhooks/{id}/deliveries`.

@@ 506-510
**`replay_delivery`** — `POST …/webhook-deliveries/{id}/replay`: `202`.

@@ 127
**`Base64Url`** (Phase 9) — a field holding base64url text: only its letters, digits, `-` and `_`, and at most 4 KB, so nothing odd or huge reaches the checks.

@@ 130-140
**`NewPasskey`** — a device's answer to `navigator.credentials.create`, with a name for the passkey, the password, and a code if one-time codes are on.

@@ 143-152
**`PasskeySignIn`** — a device's answer to `navigator.credentials.get`: the passkey's ID, the client data, the device's data, the signature, and the account's handle when the device gives one.

@@ 202-208
**`sign_in`** — the same, with the network address the request came from, for the sign-in limit.

@@ 211-214
**`passkey_sign_in_options`** — `POST /passkey-login/options`: a challenge for signing in with a passkey. Nobody is signed in yet, so only the origin is checked.

@@ 217-225
**`passkey_sign_in`** — `POST /passkey-login`: check the device's answer, give the session cookie, and answer with who is now signed in, as a password sign-in does.

@@ 256-270
**`totp_confirm`** — finish it with a code; the answer holds the recovery codes. **`replace_recovery_codes`** — `POST /totp/recovery-codes`: a fresh set. **`totp_disable`** — `POST /totp/disable`, with the network address for the sign-in limits: `204` when codes are off.

@@ 293-295
**`list_passkeys`** — `GET /passkeys`: the person's own passkeys.

@@ 298-300
**`passkey_options`** — `POST /passkeys/options`: the options for adding one. A change, so it needs the CSRF token.

@@ 303-308
**`add_passkey`** — `POST /passkeys`: check the device's answer and the password, and keep the passkey (`201`).

@@ 311-314
**`remove_passkey`** — `DELETE /passkeys/{id}`: `204`.

@@ 108-115
**`PasswordChange`** — the body of a password change (decision D31): the current password, the new one, and a 6-digit code when one-time codes are on.

@@ 118-124
**`AccountDeletion`** — the body of an account deletion (decision D32): the password, and a code when codes are on.

@@ 175
**`Origin`** — one allowed origin as sent: up to 300 characters (the rule itself is checked in `domain/origins.py`).

@@ 178-182
**`NewProject`** — a new project's name (1 to 80 characters) and up to 10 allowed origins.

@@ 185-191
**`ProjectChange`** — a new name, a new list of origins, or both; a field left out is not changed.

@@ 273-277
**`POST /password`** — change the password.

@@ 278-281
The client's address for the sign-in limits; the change; then the new session's cookie, and the person as `/me` shows them — with the new CSRF token the page must use from now on.

@@ 284-290
**`POST /account/delete`** — delete the account (`204`), and the cookie is removed from this browser. (A `POST`, not a `DELETE`, because it carries the password in its body.)

@@ 333-335
**`GET …/invitations`** — the invitations still waiting.

@@ 338-341
**`DELETE …/invitations/{id}`** — cancel one; `204`.

@@ 357-359
**`POST …/projects`** — a new project; `201`.

@@ 362-366
**`PATCH …/projects/{id}`** — rename it, or replace its allowed origins.

@@ 374-376
**`GET …/keys`** — a project's keys, without their secrets.

@@ 379-382
**`DELETE …/keys/{id}`** — stop a key at once; `204`.
