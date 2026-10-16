---
fingerprint: 5963bddc43874e70
---
The shop's own **"age checked" pass**. After a successful check, the shop shouldn't ask Dwarpal again on every page; instead it gives the visitor's browser a **cookie** saying "this visitor passed, until 10:30". The danger is obvious: a cookie is stored by the visitor, so a visitor could try to *write* one. The pass is therefore **signed** by the shop with a secret only the shop knows, using an **HMAC** — a keyed fingerprint (§4.12). Change one character, and the signature no longer matches.

A pass looks like this: `vs_01JA8XQ2….1792141800.Xk3f9qW…` — the session's ID, the expiry time, and the signature, joined by dots.

@@ 1
The doc comment.

@@ 3
From Node.js's built-in `crypto` module: `createHmac` (make a keyed fingerprint) and `timingSafeEqual` (compare two values in constant time, §4.12). The `node:` prefix makes clear this is Node.js's own module, not a package from the registry.

@@ 5
The pass cookie's name.

@@ 6
A pass lasts 30 minutes (`30 * 60` seconds): long enough to shop, short enough that a shared computer doesn't stay "verified" all day.

@@ 7-8
The name of the second cookie, `amber_pending`. It remembers *which* check this browser started, so the return link only works in that same browser (see `actions.ts` and `route.ts`).

@@ 10-13
**`Pass`** — what a valid pass contains: the session it came from, and when it expires.

@@ 15-17
**`signature`** — the HMAC-SHA256 of a text with the secret, written as URL-safe Base64, so it is safe to put in a cookie.

@@ 19-20
**`issuePass`** — make a pass for a session. `now` defaults to the current time (`Date.now()`, in milliseconds); tests pass a fixed time instead.

@@ 21
The body: the session's ID and the expiry, as whole seconds since 1970, joined by a dot.

@@ 22
Append the body's signature.

@@ 23
The closing brace.

@@ 25-26
**`readPass`** — check a pass from a cookie. It returns the pass, or `null` for anything wrong. It never throws: a strange cookie simply isn't a pass.

@@ 27
Split the cookie's text at the dots. **Array destructuring** names the first three parts, and `...extra` collects any further ones. A missing cookie (`undefined`) is treated as empty text.

@@ 28-30
Exactly three parts are required: fewer, or more, means it isn't a pass.

@@ 31-32
Compute the signature the body *should* have, and take the one that was *given*, both as bytes.

@@ 33-35
They must match, compared in constant time. `timingSafeEqual` only accepts two values of the same length, so the lengths are compared first (the length of a correct signature is no secret).

@@ 36-37
Finally, the pass must not have expired. If all is well, return the session and the expiry.

@@ 38
The closing brace.
