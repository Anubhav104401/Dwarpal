---
fingerprint: ae13f04fea9dfed2
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

@@ 44-49
**`Project`** — one project, with its allowed origins and retention period.

@@ 83-89
**`AuditEntry`** — one line of the audit log.

@@ 91-95
**`AuditLog`** — the entries, and whether the chain is intact (and where it broke).

@@ 97-111
**`SessionSummary`** (Phase 5, project pages) — one session as the list shows it: its ID, status, outcome, policy, number of attempts, the website's own reference and when it was made.

**`SessionSearch`** — what to search for: an outcome, the website's reference, or both; a field left out (or empty) means any. `| undefined` lets a field be present but empty, which the project's strict settings would otherwise forbid.

@@ 113-116
**`SessionPage`** — one page of sessions, and the cursor for the next page (`null` at the end).

@@ 118-125
**`TracedAttempt`** — one attempt as the decision saw it: kind, outcome, reasons, and its scores — the stored numbers, whatever their shape (`Record<string, unknown>`).

@@ 127-129
**`SessionTrace`** — a session's summary plus its traced attempts. `extends` means it has every field of `SessionSummary`, and one more.

@@ 131-139
**`AdultOutcome`** (§5.5.8) — how adults in one age band above a line fared when the model was measured: the band ("18-20", "30+"), how many faces, and the shares that passed, were sent to a stronger check, and failed.

@@ 141-151
**`ModelLine`** — one age's lines on the model page: the age, the risk budget, the pass and fail lines, the two measured bounds, `null` when nothing was measured, and the adults' outcomes — the policy editor's projection, empty when the model in use hasn't been measured.

@@ 153-159
**`FaceSource`** — where a set of faces came from: its name, its licence, how the ages were known, and how many faces (when recorded).

@@ 161-170
**`ModelInfo`** — the model page's contents: the version, whether it may decide live checks, its note and permitted use, the network it started from, the faces it was trained and calibrated on, and its lines.

@@ 185-191
**`Analytics`** — the first day counted, the totals by outcome, the counts day by day (`DailyCount`, from `daily.ts`), which the chart draws, and the face checks' figures. Since 9 Nov also the ID-document checks' counts (`documentStage`).

@@ 193-201
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, its rules, and (Phase 9) whether it accepts Age Passes.

@@ 203-204
**`EVENT_TYPES`** (§5.5.3) — the events an endpoint can ask for, as the API lists them. `as const` keeps them as these exact texts, not just "some strings".

@@ 206-212
**`WebhookEndpoint`** — one endpoint: its ID, address, events, whether it is switched on, and when it was made.

@@ 214-217
**`NewWebhook`** — the same, plus its signing secret: only ever in the answer that created it.

@@ 219-227
**`Delivery`** — one delivery of an event to an endpoint: its ID, the event's ID, its status (`pending`, `delivered` or `dead`), how many tries so far, and the receiver's last answer — a status code, or an error such as a timeout — and when it was made.

@@ 229-237
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages it also says who may manage policies and webhooks. Since 8 Nov also who may make projects and change their origins: owners and admins (`manageProjects`).

@@ 270
`Json` — a short name for "an object with any keys".

@@ 272-277
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 278
`orNumber` — a number, or `null` when the answer had none.

@@ 280-289
**`asFaceSource`** — read a source of faces, or `null` when there is none. The training section names its dataset `name`, the calibration section `dataset`, so the caller says which key holds the name.

@@ 291-301
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 303-311
**`asEndpoint`** — read one webhook endpoint the same way.

@@ 313-314
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 337-339
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 341-343
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 345-348
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 349-355
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 356
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 357-364
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`). Since 9 Nov it also keeps the answer's `Retry-After`, in seconds.

@@ 365
Otherwise, the answer.

@@ 366
End of `#call`.

@@ 368-369
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 370-380
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 381
End of `#remember`.

@@ 383-391
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 393-397
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 399-401
**`signUp`** — a new account and organisation.

@@ 403-406
**`signOut`** — end the session, and forget the CSRF token.

@@ 408-415
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 453-457
**`changeRole`** — a member's new role, by their ID, with `PATCH`.

@@ 459-461
**`removeMember`** — take a member out, with `DELETE`.

@@ 463-467
**`totpEnrol`** — ask for a new secret; nothing changes until a code from it is confirmed.

@@ 469-482
**`totpConfirm`** — send a code from the app; if it's right, one-time codes are on, and the answer holds the recovery codes. **`newRecoveryCodes`** — a fresh set. **`totpDisable`** — switch codes off, with the password and a current code.

@@ 553-562
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 564-578
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 580-582
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 584-598
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor, the outcome and the reference are added only when they are set — an empty one means "any", so it is left out.

@@ 600-613
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 615-639
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number, and each of the API's daily rows (one per day, policy and outcome) as a day, an outcome and a number of sessions. The policy is left behind: the chart adds policies together. Then the face checks' figures: each outcome's count, and the median band — `null` stays `null`, and a band without an end (`orNumber`) gets `null` as its end. Since 9 Nov also the ID-document checks: how many reached one, and each ending's count, read as numbers the same way.

@@ 641-649
**`model`** — the age model's details, or `null` when the person isn't signed in (the same 401 handling as `me`).

@@ 650-675
Turn the answer into a `ModelInfo`: the training section, when there is one, gives the starting network and the faces it learnt from; the calibration section gives the faces the lines were set on; and each row of thresholds becomes a `ModelLine`, its bounds kept as `null` where the stub has none, and each of its adult bands read field by field (snake_case `step_up` becomes `stepUp`).

@@ 677-687
**`policies`** — the presets and the project's own policy versions, each with its Age Pass switch (`true` only if the API says so).

@@ 689-707
**`addPolicy`** — the next version of a policy: its name, minimum age, number of face attempts and risk budget — the age and budget together name one of the model's lines (§5.5.8). Returns the new version's label, such as `shop_18@1`. Since Phase 9 also the Age Pass switch, off unless asked for.

@@ 709-712
**`#hooks`** — the address of a project's webhooks, or of one endpoint among them.

@@ 714-717
**`webhooks`** — the endpoints, test or live.

@@ 719-728
**`addWebhook`** — a new endpoint, with its mode in the body. Returns it with its secret.

@@ 730-732
**`removeWebhook`** — delete one; the mode in the address.

@@ 734-744
**`switchWebhook`** — switch an endpoint off or on with `PATCH`, the mode in the address, and read the endpoint back.

@@ 746-750
**`testWebhook`** — queue a test event; returns its ID.

@@ 752-766
**`deliveries`** — an endpoint's recent deliveries. The receiver's last answer is a number only if it is one, and its error a text only if there was one.

@@ 768-772
**`replay`** — send a delivery again.

@@ 773
End of the class.

@@ 172-177
**`FaceStage`** — how the face checks that reached a decision ended: how many were decided, how many had each outcome, and the band of seconds holding the median (with no end for the last band), or `null` before any were decided.

@@ 30-34
**`TotpOffer`** (§5.5.4) — a new authenticator secret, not yet in force: the text to type into an app, and the `otpauth://` address an app on the same device can open.

@@ 36-42
**`PasskeyInfo`** (Phase 9) — a passkey as the account page lists it: its ID, the person's name for it, and when it was added and last used.

@@ 484-491
**`passkeys`** — the person's passkeys.

@@ 493-496
**`passkeyOptions`** — the options for adding a passkey, as the API sends them; `lib/passkeys.ts` turns them into what the browser takes.

@@ 498-508
**`addPasskey`** — send the device's answer with the name and the password, and the code only when there is one.

@@ 510-512
**`removePasskey`**.

@@ 514-517
**`passkeySignInOptions`** — a challenge for signing in, naming no account.

@@ 519-521
**`passkeySignIn`** — send the device's answer; like `signIn`, remember the new session's CSRF token and return who is signed in.

@@ 51-56
**`NewKey`** — a key just created: its id, the key itself (shown once), its scopes and mode.

@@ 58-67
**`ApiKeyInfo`** (decision D30) — a key as the console lists it: its public ID, mode, scopes, dates and state — never its secret, which Dwarpal doesn't keep.

@@ 69-75
**`Invitation`** (decision D44) — an address invited but not signed up yet, with its role.

@@ 77-81
**`ProjectChange`** — a project's new name, the full new list of its allowed origins, or both (each optional, `?`).

@@ 316-323
**`asProject`** — a project as the API sends it, turned into a `Project`.

@@ 325-335
**`asKey`** — a key as the API sends it; a state it doesn't recognise reads as `active`.

@@ 417-421
**`addMember`** — give an account a role; for an address without one the API invites instead, and the answer says so (`pending`, decision D44).

@@ 423-431
**`invitations`** — the organisation's invitations still waiting.

@@ 433-436
**`cancelInvitation`** — withdraw one.

@@ 438-443
**`changePassword`** (decision D31) — the old password, the new one, and a code if given. The answer is the person again, with the new session's CSRF token, which `#remember` keeps for the next changes.

@@ 445-451
**`deleteAccount`** (decision D32) — erase the account; the CSRF token is forgotten, as on signing out.

@@ 523-526
**`projects`** — an organisation's projects.

@@ 528-532
**`createProject`** (decisions D28, D29) — a new project with its name and allowed origins.

@@ 534-540
**`updateProject`** — sends only what changes: a field not given is left out of the body.

@@ 542-545
**`keys`** — a project's keys.

@@ 547-551
**`revokeKey`** (decision D30) — stop a key at once.

@@ 179-183
**`DocumentStage`** (9 Nov) — how many sessions reached the ID-document check, and how many of those checks ended each way: the counts behind the dashboard's step-up conversion (`figures.ts`).

@@ 239-252
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words; and since 9 Nov how many seconds to wait before trying again, when the answer said (`retryAfter`, else `null`).

@@ 254-258
**`retryAfterOf`** (9 Nov) — the answer's `Retry-After` as whole seconds. The header may also hold a date, which the API never sends: anything but digits gives `null`, rather than a wrong number.

@@ 260-268
**`waitInWords`** (9 Nov) — how long a refused sign-in must wait, as people say it: seconds under a minute, then minutes rounded up (61 seconds is "2 minutes", never too early), then hours — "in an hour" for one. Nothing known: "in a moment".
