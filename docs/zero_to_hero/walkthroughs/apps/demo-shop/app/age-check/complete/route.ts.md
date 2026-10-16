---
fingerprint: d440b72b1be06739
---
**The moment of truth for the shop**: the address the verify page sends the visitor back to, `…/age-check/complete?session_id=vs_…`. This is a **route handler** (§4.17) — server code that answers a request directly, with no page to draw.

The address itself proves nothing: anyone can type `?session_id=` followed by anything. So the shop checks, in order:

1. this browser started this session (the `amber_pending` cookie);
2. the API, asked *by the shop's server with its secret key*, reports the session as completed, with a token;
3. the token's signature and claims check out, for exactly 18+ and exactly this session.

Only then does the visitor get the shop's signed pass. Any failure leads to a polite refusal page — never to the cellar.

@@ 1
The SDK's token checker.

@@ 2
From Next.js: the request type, and `NextResponse` for building answers.

@@ 4-5
The shop's settings helpers, and the pass functions and names.

@@ 7-11
The doc comment, explaining the rule.

@@ 12
`GET` — a function named after an HTTP method answers that method at this file's address. It receives the request, and returns the response.

@@ 13
Read the settings.

@@ 14
The session's ID from the address — or empty text if there is none.

@@ 15-19
**`go`** — a small helper for every possible answer: a redirect to a page of the shop, with the status `303 See Other` (the standard "now go and *get* this page"). Every answer also **deletes the pending cookie**: whatever happens, a return link can be used only once.

@@ 20-22
**Check 1: was this check started in this browser?** If there's no session ID, or the cookie doesn't hold exactly this ID, refuse — before even asking the API.

@@ 23-24
**Check 2:** ask the API for the session, with the shop's key. `retrieveSession` also rejects malformed IDs (§ the SDK's `client.ts`).

@@ 25-27
Too close to call from photos: the visitor would need a stronger check. Explain that on the refusal page.

@@ 28-30
Not finished, or no token: refuse.

@@ 31-36
**Check 3: verify the token** — its signature, issuer, audience (this shop's project), age (18) and session.

@@ 37-39
The token is genuine, but doesn't allow entry: refuse, kindly.

@@ 40
**All checks passed**: prepare the redirect into the cellar…

@@ 41-47
…and give the browser the signed pass, in a cookie that the page's scripts can't read (`httpOnly`), sent back on normal navigation (`sameSite: "lax"`), over HTTPS when available (`secure`), for every page of the shop (`path: "/"`), for 30 minutes.

@@ 48
Send it.

@@ 49-52
**Any error** — the API unreachable, a forged or expired token, a malformed ID — is logged on the shop's server for its developers, and the visitor is sent to a polite "something went wrong" page. Errors can never lead into the cellar.

@@ 53
The closing brace.
