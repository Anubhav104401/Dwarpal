---
fingerprint: 46fc2c7761e78b51
---
The console's **client** (Phase 5, §5.5.1): the one place in the web app that talks to the console API, in the same way as `flow-api.ts` talks to the flow API for the verify page. Every page calls these methods and never `fetch` directly.

Two rules shape it. Requests go to **`/console-api` on the same site**, which Next.js passes on to the API (`next.config.ts`), so the session cookie stays with one origin. And every request that changes something repeats the **CSRF token**, which the client learns from the API's answers to sign-in and `/me` and keeps only in memory.

@@ 1-4
The file's comment: where requests go, and the CSRF rule.

@@ 6
`Role` — the four roles, as a TypeScript type: only these four texts are allowed.

@@ 8-12
**`Organisation`** — one of the signed-in person's organisations, with their role in it.

@@ 14-19
**`Me`** — who is signed in: their ID and address, whether one-time codes are on, and their organisations.

@@ 21-25
**`Member`** — one member of an organisation.

@@ 27-31
**`TotpOffer`** (§5.5.4) — a new authenticator secret, not yet in force: the text to type into an app, and the `otpauth://` address an app on the same device can open.

@@ 33-38
**`Project`** — one project, with its allowed origins and retention period.

@@ 40-45
**`NewKey`** — a key just created: its id, the key itself (shown once), its scopes and mode.

@@ 47-53
**`AuditEntry`** — one line of the audit log.

@@ 55-59
**`AuditLog`** — the entries, and whether the chain is intact (and where it broke).

@@ 61-75
**`SessionSummary`** (Phase 5, project pages) — one session as the list shows it: its ID, status, outcome, policy, number of attempts, the website's own reference and when it was made.

**`SessionSearch`** — what to search for: an outcome, the website's reference, or both; a field left out (or empty) means any. `| undefined` lets a field be present but empty, which the project's strict settings would otherwise forbid.

@@ 77-80
**`SessionPage`** — one page of sessions, and the cursor for the next page (`null` at the end).

@@ 82-89
**`TracedAttempt`** — one attempt as the decision saw it: kind, outcome, reasons, and its scores — the stored numbers, whatever their shape (`Record<string, unknown>`).

@@ 91-93
**`SessionTrace`** — a session's summary plus its traced attempts. `extends` means it has every field of `SessionSummary`, and one more.

@@ 95-98
**`Analytics`** — the first day counted, and the totals by outcome.

@@ 100-106
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, and its rules.

@@ 108-109
**`EVENT_TYPES`** (§5.5.3) — the events an endpoint can ask for, as the API lists them. `as const` keeps them as these exact texts, not just "some strings".

@@ 111-117
**`WebhookEndpoint`** — one endpoint: its ID, address, events, whether it is switched on, and when it was made.

@@ 119-122
**`NewWebhook`** — the same, plus its signing secret: only ever in the answer that created it.

@@ 124-132
**`Delivery`** — one delivery of an event to an endpoint: its ID, the event's ID, its status (`pending`, `delivered` or `dead`), how many tries so far, and the receiver's last answer — a status code, or an error such as a timeout — and when it was made.

@@ 134-141
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages it also says who may manage policies and webhooks.

@@ 143-153
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 155
`Json` — a short name for "an object with any keys".

@@ 157-162
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 164-174
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 176-184
**`asEndpoint`** — read one webhook endpoint the same way.

@@ 186-187
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 189-191
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 193-195
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 197-200
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 201-207
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 208
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 209-215
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 216
Otherwise, the answer.

@@ 217
End of `#call`.

@@ 219-220
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 221-230
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 231
End of `#remember`.

@@ 233-241
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 243-247
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 249-251
**`signUp`** — a new account and organisation.

@@ 253-256
**`signOut`** — end the session, and forget the CSRF token.

@@ 258-265
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 267-269
**`addMember`** — give an existing account a role.

@@ 271-275
**`changeRole`** — a member's new role, by their ID, with `PATCH`.

@@ 277-279
**`removeMember`** — take a member out, with `DELETE`.

@@ 281-285
**`totpEnrol`** — ask for a new secret; nothing changes until a code from it is confirmed.

@@ 287-289
**`totpConfirm`** — send a code from the app; if it's right, one-time codes are on.

@@ 291-299
**`projects`** — an organisation's projects.

@@ 301-310
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 312-326
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 328-330
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 332-346
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor, the outcome and the reference are added only when they are set — an empty one means "any", so it is left out.

@@ 348-361
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 363-369
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number.

@@ 371-380
**`policies`** — the presets and the project's own policy versions.

@@ 382-392
**`addPolicy`** — the next version of a policy: its name, minimum age and number of face attempts. Returns the new version's label, such as `shop_18@1`.

@@ 394-397
**`#hooks`** — the address of a project's webhooks, or of one endpoint among them.

@@ 399-402
**`webhooks`** — the endpoints, test or live.

@@ 404-413
**`addWebhook`** — a new endpoint, with its mode in the body. Returns it with its secret.

@@ 415-417
**`removeWebhook`** — delete one; the mode in the address.

@@ 419-429
**`switchWebhook`** — switch an endpoint off or on with `PATCH`, the mode in the address, and read the endpoint back.

@@ 431-435
**`testWebhook`** — queue a test event; returns its ID.

@@ 437-451
**`deliveries`** — an endpoint's recent deliveries. The receiver's last answer is a number only if it is one, and its error a text only if there was one.

@@ 453-457
**`replay`** — send a delivery again.

@@ 458
End of the class.
