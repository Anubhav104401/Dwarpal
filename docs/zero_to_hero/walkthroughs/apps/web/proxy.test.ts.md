---
fingerprint: 3af4432114019827
---
Tests of the per-page content security policy (Phase 7): only scripts with this page's nonce may run, never inline ones; and every page gets a fresh nonce.

@@ 1-2
Next.js's request type, to make requests for the proxy; and Vitest's tools.

@@ 4
The code under test.

@@ 6
The group.

@@ 7-11
**Test — only this page's scripts.** The policy for the nonce `abc123`, and its script rule.

@@ 12-14
It names the nonce and trusts what nonce'd scripts add, and it does not allow inline scripts.

@@ 15
End of the test.

@@ 17-19
**Test — a fresh nonce each time.** Two requests for the same page, through the proxy.

@@ 20
A small helper: the nonce inside a policy, if there is one.

@@ 21-24
The first answer has a nonce, and the second a different one.

@@ 25-28
And the request Next.js will render carries the same policy as the answer — that's how it finds the nonce. (`NextResponse.next` passes changed request headers on under names starting `x-middleware-request-`.)

@@ 29-30
End of the test and the group.
