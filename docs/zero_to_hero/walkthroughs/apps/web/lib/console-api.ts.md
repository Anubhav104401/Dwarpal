---
fingerprint: 9430b80ccbab6c68
---
The console's **client** (Phase 5, §5.5.1): the one place in the web app that talks to the console API, in the same way as `flow-api.ts` talks to the flow API for the verify page. Every page calls these methods and never `fetch` directly.

Two rules shape it. Requests go to **`/console-api` on the same site**, which Next.js passes on to the API (`next.config.ts`), so the session cookie stays with one origin. And every request that changes something repeats the **CSRF token**, which the client learns from the API's answers to sign-in and `/me` and keeps only in memory.

@@ 1-4
The file's comment: where requests go, and the CSRF rule.

@@ 6
`Role` — the four roles, as a TypeScript type: only these four texts are allowed.

@@ 8-12
**`Organisation`** — one of the signed-in person's organisations, with their role in it.

@@ 14-20
**`Me`** — who is signed in: their ID and address, whether one-time codes are on, how many recovery codes they have left, and their organisations.

@@ 22-26
**`Member`** — one member of an organisation.

@@ 28-32
**`TotpOffer`** (§5.5.4) — a new authenticator secret, not yet in force: the text to type into an app, and the `otpauth://` address an app on the same device can open.

@@ 34-39
**`Project`** — one project, with its allowed origins and retention period.

@@ 41-46
**`NewKey`** — a key just created: its id, the key itself (shown once), its scopes and mode.

@@ 48-54
**`AuditEntry`** — one line of the audit log.

@@ 56-60
**`AuditLog`** — the entries, and whether the chain is intact (and where it broke).

@@ 62-76
**`SessionSummary`** (Phase 5, project pages) — one session as the list shows it: its ID, status, outcome, policy, number of attempts, the website's own reference and when it was made.

**`SessionSearch`** — what to search for: an outcome, the website's reference, or both; a field left out (or empty) means any. `| undefined` lets a field be present but empty, which the project's strict settings would otherwise forbid.

@@ 78-81
**`SessionPage`** — one page of sessions, and the cursor for the next page (`null` at the end).

@@ 83-90
**`TracedAttempt`** — one attempt as the decision saw it: kind, outcome, reasons, and its scores — the stored numbers, whatever their shape (`Record<string, unknown>`).

@@ 92-94
**`SessionTrace`** — a session's summary plus its traced attempts. `extends` means it has every field of `SessionSummary`, and one more.

@@ 96-99
**`Analytics`** — the first day counted, and the totals by outcome.

@@ 101-107
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, and its rules.

@@ 109-110
**`EVENT_TYPES`** (§5.5.3) — the events an endpoint can ask for, as the API lists them. `as const` keeps them as these exact texts, not just "some strings".

@@ 112-118
**`WebhookEndpoint`** — one endpoint: its ID, address, events, whether it is switched on, and when it was made.

@@ 120-123
**`NewWebhook`** — the same, plus its signing secret: only ever in the answer that created it.

@@ 125-133
**`Delivery`** — one delivery of an event to an endpoint: its ID, the event's ID, its status (`pending`, `delivered` or `dead`), how many tries so far, and the receiver's last answer — a status code, or an error such as a timeout — and when it was made.

@@ 135-142
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages it also says who may manage policies and webhooks.

@@ 144-154
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 156
`Json` — a short name for "an object with any keys".

@@ 158-163
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 165-175
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 177-185
**`asEndpoint`** — read one webhook endpoint the same way.

@@ 187-188
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 190-192
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 194-196
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 198-201
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 202-208
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 209
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 210-216
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 217
Otherwise, the answer.

@@ 218
End of `#call`.

@@ 220-221
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 222-232
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 233
End of `#remember`.

@@ 235-243
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 245-249
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 251-253
**`signUp`** — a new account and organisation.

@@ 255-258
**`signOut`** — end the session, and forget the CSRF token.

@@ 260-267
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 269-271
**`addMember`** — give an existing account a role.

@@ 273-277
**`changeRole`** — a member's new role, by their ID, with `PATCH`.

@@ 279-281
**`removeMember`** — take a member out, with `DELETE`.

@@ 283-287
**`totpEnrol`** — ask for a new secret; nothing changes until a code from it is confirmed.

@@ 289-302
**`totpConfirm`** — send a code from the app; if it's right, one-time codes are on, and the answer holds the recovery codes. **`newRecoveryCodes`** — a fresh set. **`totpDisable`** — switch codes off, with the password and a current code.

@@ 304-312
**`projects`** — an organisation's projects.

@@ 314-323
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 325-339
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 341-343
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 345-359
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor, the outcome and the reference are added only when they are set — an empty one means "any", so it is left out.

@@ 361-374
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 376-382
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number.

@@ 384-393
**`policies`** — the presets and the project's own policy versions.

@@ 395-405
**`addPolicy`** — the next version of a policy: its name, minimum age and number of face attempts. Returns the new version's label, such as `shop_18@1`.

@@ 407-410
**`#hooks`** — the address of a project's webhooks, or of one endpoint among them.

@@ 412-415
**`webhooks`** — the endpoints, test or live.

@@ 417-426
**`addWebhook`** — a new endpoint, with its mode in the body. Returns it with its secret.

@@ 428-430
**`removeWebhook`** — delete one; the mode in the address.

@@ 432-442
**`switchWebhook`** — switch an endpoint off or on with `PATCH`, the mode in the address, and read the endpoint back.

@@ 444-448
**`testWebhook`** — queue a test event; returns its ID.

@@ 450-464
**`deliveries`** — an endpoint's recent deliveries. The receiver's last answer is a number only if it is one, and its error a text only if there was one.

@@ 466-470
**`replay`** — send a delivery again.

@@ 471
End of the class.
