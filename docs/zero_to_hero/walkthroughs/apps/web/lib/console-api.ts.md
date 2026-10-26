---
fingerprint: d52093761277ad51
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

@@ 61-69
**`SessionSummary`** (Phase 5, project pages) — one session as the list shows it: its ID, status, outcome, policy, number of attempts, the website's own reference and when it was made.

@@ 71-74
**`SessionPage`** — one page of sessions, and the cursor for the next page (`null` at the end).

@@ 76-83
**`TracedAttempt`** — one attempt as the decision saw it: kind, outcome, reasons, and its scores — the stored numbers, whatever their shape (`Record<string, unknown>`).

@@ 85-87
**`SessionTrace`** — a session's summary plus its traced attempts. `extends` means it has every field of `SessionSummary`, and one more.

@@ 89-92
**`Analytics`** — the first day counted, and the totals by outcome.

@@ 94-100
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, and its rules.

@@ 102-103
**`EVENT_TYPES`** (§5.5.3) — the events an endpoint can ask for, as the API lists them. `as const` keeps them as these exact texts, not just "some strings".

@@ 105-111
**`WebhookEndpoint`** — one endpoint: its ID, address, events, whether it is switched on, and when it was made.

@@ 113-116
**`NewWebhook`** — the same, plus its signing secret: only ever in the answer that created it.

@@ 118-126
**`Delivery`** — one delivery of an event to an endpoint: its ID, the event's ID, its status (`pending`, `delivered` or `dead`), how many tries so far, and the receiver's last answer — a status code, or an error such as a timeout — and when it was made.

@@ 128-135
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages it also says who may manage policies and webhooks.

@@ 137-147
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 149
`Json` — a short name for "an object with any keys".

@@ 151-156
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 158-168
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 170-178
**`asEndpoint`** — read one webhook endpoint the same way.

@@ 180-181
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 183-185
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 187-189
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 191-194
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 195-201
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 202
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 203-209
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 210
Otherwise, the answer.

@@ 211
End of `#call`.

@@ 213-214
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 215-224
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 225
End of `#remember`.

@@ 227-235
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 237-241
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 243-245
**`signUp`** — a new account and organisation.

@@ 247-250
**`signOut`** — end the session, and forget the CSRF token.

@@ 252-259
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 261-263
**`addMember`** — give an existing account a role.

@@ 265-269
**`changeRole`** — a member's new role, by their ID, with `PATCH`.

@@ 271-273
**`removeMember`** — take a member out, with `DELETE`.

@@ 275-279
**`totpEnrol`** — ask for a new secret; nothing changes until a code from it is confirmed.

@@ 281-283
**`totpConfirm`** — send a code from the app; if it's right, one-time codes are on.

@@ 285-293
**`projects`** — an organisation's projects.

@@ 295-304
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 306-320
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 322-324
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 326-332
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor is added only when there is one.

@@ 334-347
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 349-355
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number.

@@ 357-366
**`policies`** — the presets and the project's own policy versions.

@@ 368-378
**`addPolicy`** — the next version of a policy: its name, minimum age and number of face attempts. Returns the new version's label, such as `shop_18@1`.

@@ 380-383
**`#hooks`** — the address of a project's webhooks, or of one endpoint among them.

@@ 385-388
**`webhooks`** — the endpoints, test or live.

@@ 390-399
**`addWebhook`** — a new endpoint, with its mode in the body. Returns it with its secret.

@@ 401-403
**`removeWebhook`** — delete one; the mode in the address.

@@ 405-409
**`testWebhook`** — queue a test event; returns its ID.

@@ 411-425
**`deliveries`** — an endpoint's recent deliveries. The receiver's last answer is a number only if it is one, and its error a text only if there was one.

@@ 427-431
**`replay`** — send a delivery again.

@@ 432
End of the class.
