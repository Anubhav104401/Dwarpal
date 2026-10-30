---
fingerprint: 8c95b528873b1698
---
Tests of the per-page content security policy (Phase 7): only scripts with this page's nonce may run, never inline ones; every page gets a fresh nonce; and only a session's own website may frame its verify page (decision D16).

@@ 1-2
Next.js's request type, to make requests for the proxy; and Vitest's tools.

@@ 4
The code under test.

@@ 6
A session's public ID, for the verify page's address.

@@ 8-14
**`api`** — a stand-in for the API, in place of `fetch`: whatever it is asked, it answers with the given status and body, and notes the address asked in `asked`, so a test can check what was asked — and that nothing was, for other pages.

@@ 16-17
**`ancestors`** — the `frame-ancestors` rule inside a policy.

@@ 19
The group.

@@ 20-24
**Test — only this page's scripts.** The policy for the nonce `abc123`, and its script rule.

@@ 25-27
It names the nonce and trusts what nonce'd scripts add, and it does not allow inline scripts.

@@ 28
End of the test.

@@ 30-32
**Test — a fresh nonce each time.** Two requests for the same page, through the proxy itself (which now answers asynchronously, so each is awaited).

@@ 33
A small helper: the nonce inside a policy, if there is one.

@@ 34-37
The first answer has a nonce, and the second a different one.

@@ 38-41
And the request Next.js will render carries the same policy as the answer — that's how it finds the nonce. (`NextResponse.next` passes changed request headers on under names starting `x-middleware-request-`.)

@@ 42-43
End of the test and the group.

@@ 45
**Framing** (decision D16).

@@ 46-55
**Test — the session's own website, and only on its verify page.** A verify page, and the console, each with a stand-in API that names a shop.

@@ 56-59
The verify page may be framed by the shop; the console by no one.

@@ 60-61
The API was asked once — for the verify page's session, at the right address — and never for the console.

@@ 63-74
**Test — no one, whenever in doubt.** `frameAncestorFor` gives `null` when the API names no website; when it answers with an error; when its answer is text that would add a rule of its own (`; script-src *`); when it is an address with a path rather than an origin; and when the API can't be reached at all (a stand-in whose promise fails, as `fetch` does).

@@ 75
End of the group.
