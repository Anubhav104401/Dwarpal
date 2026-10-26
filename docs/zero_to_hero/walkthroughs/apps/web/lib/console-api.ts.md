---
fingerprint: 13889b2727669cd0
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

@@ 55-60
**`CAN`** — what each role may do, as far as the pages need to know. The API decides (`domain/roles.py`); the pages only use this to **hide** buttons that would fail. Someone who changes the page in their browser still meets the API's refusal.

@@ 62-72
**`ConsoleError`** — a refusal from the API, with its status and stable code, so pages can show the right words.

@@ 74
`Json` — a short name for "an object with any keys".

@@ 76-80
Small, defensive readers for the API's answers. Each takes a value of unknown shape and returns what's expected, or a harmless default: an object, a text, a list of objects, a role. A surprise in an answer becomes an empty field, not a crash.

@@ 82-84
**`ConsoleClient`**. Its two private fields (`#` makes them truly private in JavaScript): the base address, and the CSRF token — empty until someone signs in.

@@ 86-88
The constructor: `/console-api` unless told otherwise (tests may pass another), without a trailing `/`.

@@ 90-93
**`#call`** — every request goes through here. It always asks for JSON; it says it is sending JSON when it is; and for anything but a read (`GET`) it adds the CSRF token.

@@ 94-100
Send the request: the method, headers and body (`null` when there is none). `credentials: "same-origin"` sends the session cookie, which is right because the request stays on this site; `cache: "no-store"` makes sure the browser never answers from a stored copy.

@@ 101
Read the answer as JSON, unless it is `204 No Content`; if it isn't JSON at all, use an empty object.

@@ 102-108
A refusal becomes a `ConsoleError` with the problem's code and sentence (`http/problems.py`).

@@ 109
Otherwise, the answer.

@@ 110
End of `#call`.

@@ 112-113
**`#remember`** — read who is signed in from an answer, and keep the CSRF token it carries.

@@ 114-123
Turn the API's names (`totp_enabled`, …) into the page's (`totpEnabled`, …), reading each field defensively.

@@ 124
End of `#remember`.

@@ 126-134
**`me`** — who is signed in. `401` means nobody is, which isn't an error here: the answer is `null`. Anything else wrong is passed on.

@@ 136-140
**`signIn`** — an address, a password and, if asked for, a one-time code.

@@ 142-144
**`signUp`** — a new account and organisation.

@@ 146-149
**`signOut`** — end the session, and forget the CSRF token.

@@ 151-158
**`members`** — an organisation's members. `encodeURIComponent` makes an ID safe to put in an address.

@@ 160-162
**`addMember`** — give an existing account a role.

@@ 164-172
**`projects`** — an organisation's projects.

@@ 174-183
**`createKey`** — a new API key for a project, with the chosen scopes and mode.

@@ 185-199
**`audit`** — the newest hundred audit entries, and the chain's verdict.

@@ 200
End of the class.
