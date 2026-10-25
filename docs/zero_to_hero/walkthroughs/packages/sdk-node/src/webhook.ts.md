---
fingerprint: 9fbed25a87eebba0
---
**Verifying webhooks** in the Node SDK (Phase 4, §5.4.3) — the receiving side of the signature that `adapters/webhooks.py` makes. A website calls `verifyWebhook` on every webhook it receives, before believing a word of it:

```ts
const event = verifyWebhook(rawBody, request.headers["dwarpal-signature"], process.env.DWARPAL_WEBHOOK_SECRET);
if (event.type === "verification_session.completed") { … }
```

It checks three things: the header is well formed, the signature is recent (five minutes by default, so a captured webhook can't be replayed later), and the HMAC of the time and the exact body matches. If any check fails, it throws `WebhookSignatureError`.

@@ 1
From Node's built-in `crypto`: `createHmac` (compute an HMAC) and `timingSafeEqual` (compare two byte strings in constant time).

@@ 3
The SDK's error for a webhook that fails verification.

@@ 5-6
**`WEBHOOK_TOLERANCE_S`** — how old a signature may be by default: 300 seconds, five minutes.

@@ 8-16
**`DwarpalEvent`** — the shape of what Dwarpal sends, as `event_view` builds it on the server: ID, `object`, type, mode, time and data. `Record<string, unknown>` means "an object with any keys, whose values must be checked before use".

@@ 18-23
**`VerifyWebhookOptions`** — two optional settings: a different tolerance, and a fixed "now" for tests.

@@ 25-28
The function's documentation, with the one mistake that trips people up: verify the body **exactly as it arrived**. A web framework that parses the JSON and gives you an object has already lost the original bytes. Turning the object back into JSON may order or space it differently, and then the signature no longer matches.

@@ 29-34
**`verifyWebhook`** — the raw body (text or bytes), the header's value (perhaps missing), the endpoint's secret, and the options. It returns the event.

@@ 35-37
Split the header into its fields, and read `t` as a number and `v1` as text.

@@ 38-40
Refuse a header without a whole-number time, or without a `v1` of exactly 64 hexadecimal characters (a SHA-256 digest).

@@ 41-44
**Freshness**: refuse a signature more than the tolerance away from now, in either direction (`Math.abs`). An old one may be a captured webhook being replayed; one from the future means a clock is badly wrong.

@@ 45
Turn the body into bytes, whichever form it came in.

@@ 46
Compute the HMAC-SHA256, keyed with the secret, of the time, a dot, and the body — exactly what the server signed.

@@ 47-50
Compare it with the given signature in **constant time**. An ordinary comparison stops at the first different byte, so it answers slightly faster the more wrong a guess is. Measured many times, that difference would let a forger find a valid signature byte by byte. `timingSafeEqual` always takes the same time.

@@ 51
Everything checked: parse the body and return the event.

@@ 52
End of the function.

@@ 54-61
**`parseHeader`** — split `t=…,v1=…` at the commas, and each part at its first `=`, into a map of names to values. Parts without an `=` are ignored.
