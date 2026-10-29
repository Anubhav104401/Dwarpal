---
fingerprint: 7cf5cc9a3b53609e
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

@@ 98-106
**`ModelLine`** — one age's lines on the model page: the age, the risk budget, the pass and fail lines, and the two measured bounds, `null` when nothing was measured.

@@ 108-114
**`FaceSource`** — where a set of faces came from: its name, its licence, how the ages were known, and how many faces (when recorded).

@@ 116-125
**`ModelInfo`** — the model page's contents: the version, whether it may decide live checks, its note and permitted use, the network it started from, the faces it was trained and calibrated on, and its lines.

@@ 134-139
**`Analytics`** — the first day counted, the totals by outcome, the counts day by day (`DailyCount`, from `daily.ts`), which the chart draws, and the face checks' figures.

@@ 141-147
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, and its rules.

@@ 149-150
**`EVENT_TYPES`** (§5.5.3) — the events an endpoint can ask for, as the API lists them. `as const` keeps them as these exact texts, not just "some strings".

@@ 152-158
**`WebhookEndpoint`** — one endpoint: its ID, address, events, whether it is switched on, and when it was made.

@@ 160-163
**`NewWebhook`** — the same, plus its signing secret: only ever in the answer that created it.

@@ 165-173
**`Delivery`** — one delivery of an event to an endpoint: its ID, the event's ID, its status (`pending`, `delivered` or `dead`), how many tries so far, and the receiver's last answer — a status code, or an error such as a timeout — and when it was made.

@@ 175-182
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages it also says who may manage policies and webhooks.

@@ 184-194
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 196
`Json` — a short name for "an object with any keys".

@@ 198-203
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 204
`orNumber` — a number, or `null` when the answer had none.

@@ 206-215
**`asFaceSource`** — read a source of faces, or `null` when there is none. The training section names its dataset `name`, the calibration section `dataset`, so the caller says which key holds the name.

@@ 217-227
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 229-237
**`asEndpoint`** — read one webhook endpoint the same way.

@@ 239-240
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 242-244
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 246-248
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 250-253
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 254-260
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 261
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 262-268
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 269
Otherwise, the answer.

@@ 270
End of `#call`.

@@ 272-273
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 274-284
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 285
End of `#remember`.

@@ 287-295
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 297-301
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 303-305
**`signUp`** — a new account and organisation.

@@ 307-310
**`signOut`** — end the session, and forget the CSRF token.

@@ 312-319
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 321-323
**`addMember`** — give an existing account a role.

@@ 325-329
**`changeRole`** — a member's new role, by their ID, with `PATCH`.

@@ 331-333
**`removeMember`** — take a member out, with `DELETE`.

@@ 335-339
**`totpEnrol`** — ask for a new secret; nothing changes until a code from it is confirmed.

@@ 341-354
**`totpConfirm`** — send a code from the app; if it's right, one-time codes are on, and the answer holds the recovery codes. **`newRecoveryCodes`** — a fresh set. **`totpDisable`** — switch codes off, with the password and a current code.

@@ 356-364
**`projects`** — an organisation's projects.

@@ 366-375
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 377-391
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 393-395
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 397-411
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor, the outcome and the reference are added only when they are set — an empty one means "any", so it is left out.

@@ 413-426
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 428-448
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number, and each of the API's daily rows (one per day, policy and outcome) as a day, an outcome and a number of sessions. The policy is left behind: the chart adds policies together. Then the face checks' figures: each outcome's count, and the median band — `null` stays `null`, and a band without an end (`orNumber`) gets `null` as its end.

@@ 450-458
**`model`** — the age model's details, or `null` when the person isn't signed in (the same 401 handling as `me`).

@@ 459-477
Turn the answer into a `ModelInfo`: the training section, when there is one, gives the starting network and the faces it learnt from; the calibration section gives the faces the lines were set on; and each row of thresholds becomes a `ModelLine`, its bounds kept as `null` where the stub has none.

@@ 479-488
**`policies`** — the presets and the project's own policy versions.

@@ 490-500
**`addPolicy`** — the next version of a policy: its name, minimum age and number of face attempts. Returns the new version's label, such as `shop_18@1`.

@@ 502-505
**`#hooks`** — the address of a project's webhooks, or of one endpoint among them.

@@ 507-510
**`webhooks`** — the endpoints, test or live.

@@ 512-521
**`addWebhook`** — a new endpoint, with its mode in the body. Returns it with its secret.

@@ 523-525
**`removeWebhook`** — delete one; the mode in the address.

@@ 527-537
**`switchWebhook`** — switch an endpoint off or on with `PATCH`, the mode in the address, and read the endpoint back.

@@ 539-543
**`testWebhook`** — queue a test event; returns its ID.

@@ 545-559
**`deliveries`** — an endpoint's recent deliveries. The receiver's last answer is a number only if it is one, and its error a text only if there was one.

@@ 561-565
**`replay`** — send a delivery again.

@@ 566
End of the class.

@@ 127-132
**`FaceStage`** — how the face checks that reached a decision ended: how many were decided, how many had each outcome, and the band of seconds holding the median (with no end for the last band), or `null` before any were decided.
