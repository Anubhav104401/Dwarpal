---
fingerprint: aeb984f35df4bc13
---
The console's **client** (Phase 5, §5.5.1): the one place in the web app that talks to the console API, in the same way as `flow-api.ts` talks to the flow API for the verify page. Every page calls these methods and never `fetch` directly.

Two rules shape it. Requests go to **`/console-api` on the same site**, which Next.js passes on to the API (`next.config.ts`), so the session cookie stays with one origin. And every request that changes something repeats the **CSRF token**, which the client learns from the API's answers to sign-in and `/me` and keeps only in memory.

@@ 1-4
The file's comment: where requests go, and the CSRF rule.

@@ 6
`DailyCount`'s type, from the module that shapes the daily counts. `import type` brings in only the type, which disappears when TypeScript is compiled.

@@ 8
`Role` — the four roles, as a TypeScript type: only these four texts are allowed.

@@ 10-14
**`Organisation`** — one of the signed-in person's organisations, with their role in it.

@@ 16-22
**`Me`** — who is signed in: their ID and address, whether one-time codes are on, how many recovery codes they have left, and their organisations.

@@ 24-28
**`Member`** — one member of an organisation.

@@ 30-34
**`TotpOffer`** (§5.5.4) — a new authenticator secret, not yet in force: the text to type into an app, and the `otpauth://` address an app on the same device can open.

@@ 36-41
**`Project`** — one project, with its allowed origins and retention period.

@@ 43-48
**`NewKey`** — a key just created: its id, the key itself (shown once), its scopes and mode.

@@ 50-56
**`AuditEntry`** — one line of the audit log.

@@ 58-62
**`AuditLog`** — the entries, and whether the chain is intact (and where it broke).

@@ 64-78
**`SessionSummary`** (Phase 5, project pages) — one session as the list shows it: its ID, status, outcome, policy, number of attempts, the website's own reference and when it was made.

**`SessionSearch`** — what to search for: an outcome, the website's reference, or both; a field left out (or empty) means any. `| undefined` lets a field be present but empty, which the project's strict settings would otherwise forbid.

@@ 80-83
**`SessionPage`** — one page of sessions, and the cursor for the next page (`null` at the end).

@@ 85-92
**`TracedAttempt`** — one attempt as the decision saw it: kind, outcome, reasons, and its scores — the stored numbers, whatever their shape (`Record<string, unknown>`).

@@ 94-96
**`SessionTrace`** — a session's summary plus its traced attempts. `extends` means it has every field of `SessionSummary`, and one more.

@@ 98-102
**`Analytics`** — the first day counted, the totals by outcome, and the counts day by day (`DailyCount`, from `daily.ts`), which the chart draws.

@@ 104-110
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, and its rules.

@@ 112-113
**`EVENT_TYPES`** (§5.5.3) — the events an endpoint can ask for, as the API lists them. `as const` keeps them as these exact texts, not just "some strings".

@@ 115-121
**`WebhookEndpoint`** — one endpoint: its ID, address, events, whether it is switched on, and when it was made.

@@ 123-126
**`NewWebhook`** — the same, plus its signing secret: only ever in the answer that created it.

@@ 128-136
**`Delivery`** — one delivery of an event to an endpoint: its ID, the event's ID, its status (`pending`, `delivered` or `dead`), how many tries so far, and the receiver's last answer — a status code, or an error such as a timeout — and when it was made.

@@ 138-145
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages it also says who may manage policies and webhooks.

@@ 147-157
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 159
`Json` — a short name for "an object with any keys".

@@ 161-166
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 168-178
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 180-188
**`asEndpoint`** — read one webhook endpoint the same way.

@@ 190-191
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 193-195
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 197-199
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 201-204
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 205-211
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 212
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 213-219
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 220
Otherwise, the answer.

@@ 221
End of `#call`.

@@ 223-224
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 225-235
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 236
End of `#remember`.

@@ 238-246
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 248-252
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 254-256
**`signUp`** — a new account and organisation.

@@ 258-261
**`signOut`** — end the session, and forget the CSRF token.

@@ 263-270
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 272-274
**`addMember`** — give an existing account a role.

@@ 276-280
**`changeRole`** — a member's new role, by their ID, with `PATCH`.

@@ 282-284
**`removeMember`** — take a member out, with `DELETE`.

@@ 286-290
**`totpEnrol`** — ask for a new secret; nothing changes until a code from it is confirmed.

@@ 292-305
**`totpConfirm`** — send a code from the app; if it's right, one-time codes are on, and the answer holds the recovery codes. **`newRecoveryCodes`** — a fresh set. **`totpDisable`** — switch codes off, with the password and a current code.

@@ 307-315
**`projects`** — an organisation's projects.

@@ 317-326
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 328-342
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 344-346
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 348-362
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor, the outcome and the reference are added only when they are set — an empty one means "any", so it is left out.

@@ 364-377
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 379-390
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number, and each of the API's daily rows (one per day, policy and outcome) as a day, an outcome and a number of sessions. The policy is left behind: the chart adds policies together.

@@ 392-401
**`policies`** — the presets and the project's own policy versions.

@@ 403-413
**`addPolicy`** — the next version of a policy: its name, minimum age and number of face attempts. Returns the new version's label, such as `shop_18@1`.

@@ 415-418
**`#hooks`** — the address of a project's webhooks, or of one endpoint among them.

@@ 420-423
**`webhooks`** — the endpoints, test or live.

@@ 425-434
**`addWebhook`** — a new endpoint, with its mode in the body. Returns it with its secret.

@@ 436-438
**`removeWebhook`** — delete one; the mode in the address.

@@ 440-450
**`switchWebhook`** — switch an endpoint off or on with `PATCH`, the mode in the address, and read the endpoint back.

@@ 452-456
**`testWebhook`** — queue a test event; returns its ID.

@@ 458-472
**`deliveries`** — an endpoint's recent deliveries. The receiver's last answer is a number only if it is one, and its error a text only if there was one.

@@ 474-478
**`replay`** — send a delivery again.

@@ 479
End of the class.
