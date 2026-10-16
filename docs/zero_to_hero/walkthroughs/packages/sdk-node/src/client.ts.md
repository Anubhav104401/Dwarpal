---
fingerprint: bfaec3d5ed813c75
---
**`DwarpalClient`** — the SDK's way for a website's server to talk to the API: create a session, and read its result. It wraps the two relying-party endpoints (§5.1.3) in ordinary functions with typed inputs and outputs, so a website writes `await client.createSession({ policy: "uk_osa_18" })` instead of building HTTP requests by hand.

It is careful in both directions:

- **what it sends** — the key's shape is checked once, when the client is made; session IDs are checked before any request goes out;
- **what it receives** — every field of every answer is checked against its expected type before the website sees it. If the API ever answered something unexpected, the SDK says so clearly instead of handing over a half-broken object.

@@ 1
The SDK's error class for refusals from the API.

@@ 3-10
`STATUSES` — the six session statuses, as a list. `as const` tells TypeScript that this list will never change, so it may remember the *exact* texts (`"created"`, `"in_progress"`, …) rather than just "some strings".

@@ 11
`OUTCOMES` — the outcomes a session can end with, in the same way. (`step_up` appears here, though not in tokens: a session waiting for a stronger check has that outcome, but no token.)

@@ 12-13
Two **types made from the lists**. `(typeof STATUSES)[number]` reads: "the type of any element of `STATUSES`" — which, thanks to `as const`, is exactly `"created" | "in_progress" | …`. Writing each status once, in the list, gives both the runtime check (below) and the type, so the two can never disagree.

@@ 15
`DwarpalClientOptions` — how to make a client.

@@ 16-17
`apiKey` — the secret key. The doc comment repeats the most important rule: servers only, never a browser.

@@ 18-19
`baseUrl` — the API's address.

@@ 20-21
`timeoutMs?` — optional: how long to wait for an answer before giving up. Default 10 seconds.

@@ 22-23
`fetch?` — optional: the function used to send HTTP requests. `typeof fetch` means "anything shaped exactly like the built-in `fetch`". Tests pass a fake one that answers instantly, without a network (`client.test.ts`).

@@ 24
The interface ends.

@@ 26-30
`CreateSessionParams` — the three optional settings for a new session, in JavaScript's usual **camelCase** (`returnUrl`), although the API itself uses Python's **snake_case** (`return_url`). The SDK translates, so each side keeps its own conventions.

@@ 32-40
`CreatedSession` — the useful parts of the API's answer: the ID, status, mode, policy, the **link** to send the person to, and the expiry as a `Date`. The client secret is deliberately *not* included: a website only needs to pass the link on, and the less it holds, the less it can leak. The doc comment on `url` warns that the link itself carries the secret.

@@ 42-54
`SessionResult` — a session's result, with every field typed: `SessionOutcome | null` because a session in progress has no outcome yet; `Date | null` because an unfinished session has no completion time; and the token, with a reminder that a token must be *verified* before it is trusted.

@@ 56
`Json` — a short name for "an object with text keys and values of unknown type": what parsed JSON looks like before it is checked. `unknown` is TypeScript's safest type: nothing can be done with an `unknown` value until its type has been checked.

@@ 58-59
Two **regular expressions** (as in Python's `re`, §5.1.3), between slashes: the shape of an API key — `dk_test_` or `dk_live_` followed by at least 20 key characters — and of a session ID.

@@ 61
**`field`** — read one field from an answer, and check it. `<T>` makes it a **generic** function: `T` stands for whatever type the check is about, so `field(data, "id", isText)` returns a `string`, and `field(data, "attempts", isCount)` a `number`.

The third parameter, `accept`, is a **type guard**: a function returning `value is T`, which tells TypeScript "if I return true, this value *is* a `T`".

@@ 62-67
Look the field up. If the check fails, throw an error naming the field; otherwise return the value — now known to be a `T`.

@@ 69-71
Three simple type guards: text, a true-or-false flag, and a whole number. `=>` defines a short **arrow function**.

@@ 72-75
**`oneOf`** — makes a type guard that accepts only the values in a given list. It is a function that *returns* a function: `oneOf(STATUSES)` is a guard for statuses. `as T` is needed only because `includes` expects a value of the list's own type; the check itself is exact.

@@ 76-79
**`orNull`** — turns any guard into one that also accepts `null`: `orNull(isText)` accepts text or `null`.

@@ 80
**`dateOrNull`** — turns a timestamp text into a `Date`, and `null` into `null`.

@@ 82
**`DwarpalClient`** — the class.

@@ 83-86
Four **private fields**. A name that starts with `#` is truly private in JavaScript: no code outside the class can read it, at all. Nobody can accidentally log `client.#apiKey`, or read it in a debugger's autocomplete list.

@@ 88-91
The constructor checks the key's *shape* first. A key pasted with a missing character, or a key from another service, fails right here, when the website starts — not later, when the first visitor arrives.

@@ 92-96
Store the settings: the key; the address without a trailing slash; the timeout (`??` picks 10 seconds if none was given — the underscore in `10_000` only helps reading); and the `fetch` to use, by default the one built into Node.js (`globalThis` is the object that holds every built-in).

@@ 98-99
**`createSession`** — with all settings optional, `= {}` lets it be called with no argument at all.

@@ 100-103
Build the request body, including only the settings that were given, under the API's own names. `!== undefined` means "was provided".

@@ 104
Send it: `POST /v1/verification-sessions`.

@@ 105-113
Build the result, checking each field. `expires_at` arrives as text, and becomes a `Date`.

@@ 115-116
**`retrieveSession`** — read a session's result by its ID.

@@ 117-119
Check the ID's shape *before* using it in an address. An ID from the visitor's browser is untrusted text; without this check, a crafted value such as `../something` could change which address is called.

@@ 120
Send `GET /v1/verification-sessions/<id>`.

@@ 121-133
Build the result, with the right guard for each field — including the nullable ones.

@@ 135
**`#request`** — the one private method that every call goes through. Its `method` can only be `"GET"` or `"POST"`.

@@ 136-142
The headers: the key as a bearer token, and a request for JSON. Only a request with a body says what kind of body it is (`Content-Type`).

@@ 143-148
Send the request with the chosen `fetch`:

- `body` — the JSON text, or `null` for no body;
- `signal: AbortSignal.timeout(…)` — a **signal** that cancels the request if it isn't finished in time. Without a timeout, one stuck connection could make a visitor wait for ever.

@@ 149-150
Parse the answer as JSON. If the body isn't JSON at all, `.catch(() => null)` turns the error into `null`. Then keep it only if it really is an object; otherwise use an empty one. From here on, `data` is safe to look into.

@@ 151-155
`response.ok` is true for statuses 200–299. Anything else becomes a `DwarpalApiError`, built from the problem details (§4.13): the stable code, the sentence, the status, and the request ID from the headers — or generic values if the answer wasn't problem details at all.

@@ 156-158
Success: return the parsed answer. The closing braces end the method and the class.
