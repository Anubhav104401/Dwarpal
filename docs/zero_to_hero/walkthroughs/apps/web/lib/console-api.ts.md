---
fingerprint: a1dbe36af6a77d91
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

@@ 27-32
**`Project`** — one project, with its allowed origins and retention period.

@@ 34-39
**`NewKey`** — a key just created: its id, the key itself (shown once), its scopes and mode.

@@ 41-47
**`AuditEntry`** — one line of the audit log.

@@ 49-53
**`AuditLog`** — the entries, and whether the chain is intact (and where it broke).

@@ 55-63
**`SessionSummary`** (Phase 5, project pages) — one session as the list shows it: its ID, status, outcome, policy, number of attempts, the website's own reference and when it was made.

@@ 65-68
**`SessionPage`** — one page of sessions, and the cursor for the next page (`null` at the end).

@@ 70-77
**`TracedAttempt`** — one attempt as the decision saw it: kind, outcome, reasons, and its scores — the stored numbers, whatever their shape (`Record<string, unknown>`).

@@ 79-81
**`SessionTrace`** — a session's summary plus its traced attempts. `extends` means it has every field of `SessionSummary`, and one more.

@@ 83-86
**`Analytics`** — the first day counted, and the totals by outcome.

@@ 88-94
**`PolicyVersion`** — one policy as the page shows it: its label, whether it is a preset, and its rules.

@@ 96-102
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal. Since the project pages, it also says who may manage policies.

@@ 104-114
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 116
`Json` — a short name for "an object with any keys".

@@ 118-123
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a number, a list of texts, or a text that may be absent (`null`). A surprise in an answer becomes an empty field, not a crash.

@@ 125-135
**`asSession`** — read one session summary, turning the API's names (`external_ref`, `created_at`) into the page's.

@@ 137-138
**`asRole`** — a role, or `analyst` — the least powerful — for anything unexpected: failing closed, in the page too.

@@ 140-142
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 144-146
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 148-151
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 152-158
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 159
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 160-166
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 167
Otherwise, the answer.

@@ 168
End of `#call`.

@@ 170-171
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 172-181
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 182
End of `#remember`.

@@ 184-192
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 194-198
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 200-202
**`signUp`** — a new account and organisation.

@@ 204-207
**`signOut`** — end the session, and forget the CSRF token.

@@ 209-216
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 218-220
**`addMember`** — give an existing account a role.

@@ 222-230
**`projects`** — an organisation's projects.

@@ 232-241
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 243-257
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 259-261
**`#project`** — the start of every project address, with both IDs made safe for an address.

@@ 263-269
**`sessions`** — one page of a project's sessions, test or live. `URLSearchParams` builds the `?livemode=…&limit=20` part of the address safely; the cursor is added only when there is one.

@@ 271-284
**`trace`** — one session's decision trace: its summary, plus each attempt's kind, outcome, reasons and scores.

@@ 286-292
**`analytics`** — the project's counts for the last 30 days (or another number), test or live; each total is read as a number.

@@ 294-303
**`policies`** — the presets and the project's own policy versions.

@@ 305-315
**`addPolicy`** — the next version of a policy: its name, minimum age and number of face attempts. Returns the new version's label, such as `shop_18@1`.

@@ 316
End of the class.
