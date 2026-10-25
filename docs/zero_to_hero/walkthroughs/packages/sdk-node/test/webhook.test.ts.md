---
fingerprint: 0809fcc897bb744e
---
Tests of `verifyWebhook` (Phase 4). Each one builds a header exactly as the server would, then checks that the SDK accepts the genuine webhook and refuses each kind of tampering.

@@ 1
Node's `createHmac`, to sign test webhooks the way the server does.

@@ 3
Vitest's `describe`, `expect` and `it`.

@@ 5
The code under test, through the SDK's public entry point.

@@ 7-11
A test secret, a fixed "now", that moment in seconds (`T`), and a small event body as raw JSON text.

@@ 13-16
**`header`** — sign a body as the server does (`t=…,v1=…`), at a chosen time and with a chosen secret: by default, now and the right secret.

@@ 18
The group of tests.

@@ 19-23
A **genuine webhook** passes, and its event comes back parsed.

@@ 25-28
A **changed body**, with `pass` turned into `fail`, is refused, though the header is genuine.

@@ 30-34
**Another secret**: a header signed with the wrong secret does not match.

@@ 36-39
**Freshness**: 301 seconds old is refused as a possible replay; 299 seconds is still accepted.

@@ 41-45
**Malformed headers** — none at all, empty, a time that isn't a number, a time with no signature, a signature with no time — are all refused as malformed.

@@ 46
End of the group.
