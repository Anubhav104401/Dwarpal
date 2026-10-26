---
fingerprint: f457d60845e681b6
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

@@ 12-17
The console use cases and session type, the toolbox type, the `Policy` type, our error class, and the toolbox dependency.

@@ 18
The body of a new policy version, as the website API defines it (`http/policies.py`): one shape, one set of rules.

@@ 19
The body of a new webhook endpoint, as the website API defines it (`http/webhooks.py`).

@@ 21-22
The router, under `/console/v1`, and a short name for the toolbox parameter.

@@ 25-27
**`cookie_name`** — the cookie is called `__Host-dwarpal_session`. Browsers enforce the **`__Host-` prefix**: such a cookie must be `Secure` (HTTPS only), set for the whole site (`path=/`) and tied to exactly this host, so no other site — not even a sub-domain — can set or overwrite it. Only the tests, over plain HTTP, use the plain name.

@@ 30-33
**`check_origin`** — if the request names an `Origin` (browsers always do for these requests), it must be one of the console's addresses. A program that isn't a browser sends none, and can't carry someone else's cookie anyway.

@@ 36-41
**`signed_in`** — the gate for signed-in requests: read the cookie, look its session up, and refuse with `401` if there is none. It returns the token too, for signing out.

@@ 44-49
**`changing`** — the gate for requests that change something: signed in, and also the CSRF token from the `X-CSRF-Token` header (empty if missing).

@@ 50-51
Its docstring: why the token stops forged requests.

@@ 52
Check the origin.

@@ 53-55
Compare the token with the session's, in constant time; refuse with `403 csrf_failed` if they differ.

@@ 56
Let the change proceed.

@@ 59-60
**`reading`** — the gate for requests that only read: signed in is enough. Reading can't be forged into harm, and another site can't see the answer.

@@ 63-64
Short names for the two kinds of caller, used in every endpoint below.

@@ 67-72
**`give_cookie`** — set the session cookie: for 12 hours; `httponly=True`, so the page's own JavaScript can't read it (a script injected into the page can't steal it); `secure`, so it only travels over HTTPS; `samesite="lax"`, so browsers don't send it with requests that other sites trigger in the background — a third CSRF defence; for the whole site.

@@ 75-80
**`SignUp`** — the body for signing up: an address, a password, and the organisation's name, each with a length limit.

@@ 83-88
**`SignIn`** — an address, a password, and optionally a one-time code: exactly six digits, as the published document states.

@@ 91-94
**`Code`** — a body holding just a six-digit code.

@@ 97-101
**`NewMember`** — an address and a role.

@@ 104-107
**`RoleChange`** — the body of a role change: just the new role.

@@ 110-114
**`NewKey`** — one to eight scopes, and whether the key is live (test by default).

@@ 117-122
**`sign_up`** — check the origin, create the account, give the cookie, and answer with who is now signed in.

@@ 125-131
**`sign_in`** — the same, with the network address the request came from, for the sign-in limit.

@@ 134-139
**`sign_out`** — a change (so it needs the CSRF token); the `_` parameter runs that check, and its value isn't needed.

@@ 140-143
End the session, and tell the browser to delete the cookie.

@@ 146-148
**`me`** — who is signed in.

@@ 151-153
**`totp_enrol`** — start switching on one-time codes.

@@ 156-159
**`totp_confirm`** — finish it with a code; `204` means done, nothing to show.

@@ 162-164
**`list_members`**.

@@ 167-169
**`list_projects`** — `GET /orgs/{org}/projects`, for any signed-in member.

@@ 172-174
**`add_member`** — `201 Created`.

@@ 177-181
**`change_role`** — `PATCH …/members/{user}`. `PATCH` is the HTTP method for changing part of something: here, one field of a membership.

@@ 184-187
**`remove_member`** — `DELETE …/members/{user}`: `204`.

@@ 190-192
**`create_key`** — `201 Created`, with the key shown once.

@@ 195-199
**`audit_log`** — up to 500 entries (100 if not asked).

@@ 202-203
The path every project route starts with, written once; and `Live`, the `livemode` query parameter (`?livemode=true`), which chooses test or live data.

@@ 206-216
**`project_sessions`** — `GET …/sessions`: test sessions unless asked for live, 20 a page (at most 100), after the given cursor.

@@ 219-223
**`session_trace`** — `GET …/sessions/{id}`: one session's decision trace.

@@ 226-235
**`project_analytics`** — `GET …/analytics`: the last 30 days (1 to 365), test or live.

@@ 238-240
**`project_policies`** — `GET …/policies`.

@@ 243-248
**`add_policy_version`** — `POST …/policies`, a change (so it needs the CSRF token): build the draft from the body, and add it.

@@ 251-254
**`ConsoleEndpoint`** — that body plus `livemode` (test unless asked). A website's key is already test or live; a person in the console chooses.

@@ 257-261
**`project_webhooks`** — `GET …/webhooks`: the endpoints, test or live.

@@ 264-268
**`add_webhook`** — `POST …/webhooks`, a change: `201`, with the secret.

@@ 271-276
**`remove_webhook`** — `DELETE …/webhooks/{id}`: `204`. The mode comes in the address (`?livemode=true`), like every other webhook route here.

@@ 279-283
**`send_test_event`** — `POST …/webhooks/{id}/test`: `202 Accepted` — queued, not yet sent.

@@ 286-290
**`webhook_deliveries`** — `GET …/webhooks/{id}/deliveries`.

@@ 293-297
**`replay_delivery`** — `POST …/webhook-deliveries/{id}/replay`: `202`.
