# Node.js SDK: `@dwarpal/node`

The server side of an integration: create sessions, read their results, verify age tokens and webhooks. It needs Node.js 24.11 or newer. Its one dependency is [jose](https://github.com/panva/jose), for JSON Web Tokens.

See [Integrating Dwarpal](README.md) for the whole flow.

## `DwarpalClient`

```ts
import { DwarpalClient } from "@dwarpal/node";

const dwarpal = new DwarpalClient({
  apiKey: process.env.DWARPAL_API_KEY!, // dk_test_… or dk_live_…
  baseUrl: "https://api.dwarpal.example",
  timeoutMs: 10_000, // the default
});
```

Your API key is a secret: keep it in your server's environment, never in a browser, a repository or a log. A test key (`dk_test_…`) sees only test sessions; a live key only live ones.

### `createSession(params?)`

```ts
const session = await dwarpal.createSession({
  policy: "uk_osa_18", // the default
  returnUrl: "https://shop.example/age-check/complete",
  externalRef: "order-1234", // optional: your own reference, up to 200 characters
});
// session.id        "vs_…"
// session.url       the verify link — hand it to your page; never log or store it
// session.expiresAt when an unfinished session expires (30 minutes)
```

The return address must be on one of your project's allowed origins. Without one, the person stays on Dwarpal's page at the end, and the check can't be opened in a modal.

### `retrieveSession(id)`

```ts
const result = await dwarpal.retrieveSession(sessionId);
// result.status   "created" | "in_progress" | "awaiting_step_up" | "completed" | "expired" | "canceled"
// result.outcome  "pass" | "fail" | "reject" | "step_up" | null
// result.ageToken the signed token once completed, else null
```

`retrieveSession` throws a `TypeError` for an ID that isn't a session ID. Errors from the API arrive as **`DwarpalApiError`**, with its `status`, `code` and `requestId` (quote the request ID when asking for help).

## `verifyAgeToken(token, options)`

```ts
import { verifyAgeToken } from "@dwarpal/node";

const verdict = await verifyAgeToken(result.ageToken!, {
  issuer: "https://api.dwarpal.example",
  audience: "prj_…", // your project's ID
  minAge: 18,
  sessionId, // optional, but recommended: the session this browser started
});
if (verdict.allowed) {
  // verdict.outcome "pass", verdict.policy, verdict.livemode, verdict.expiresAt
}
```

It fetches Dwarpal's public keys (JWKS) from the issuer, caches them, and checks the token's signature (Ed25519), type, issuer, audience, expiry and age claim. Anything wrong throws an **`AgeTokenError`**. `allowed` is true only for a `pass` whose age claim covers `minAge`.

Check `livemode` too before going live: a test token must never open a real door.

## `verifyWebhook(rawBody, signatureHeader, secret, options?)`

Dwarpal can tell your server when a session completes or expires, with a signed **webhook**. Add an endpoint in the console; it shows the endpoint's signing secret once.

```ts
import { verifyWebhook } from "@dwarpal/node";

const raw = await request.text(); // the body exactly as it arrived
const event = verifyWebhook(raw, request.headers.get("Dwarpal-Signature"), process.env.DWARPAL_WEBHOOK_SECRET!);
if (event.type === "verification_session.completed") {
  // event.data holds the session's summary
}
```

- Pass the body **exactly as it arrived**: parsing and re-serialising JSON changes the bytes, and the signature with them.
- Signatures older than five minutes are refused (`toleranceS` changes that), against replays.
- A bad signature throws a **`WebhookSignatureError`**: answer `400` and do nothing else.
- Answer `2xx` quickly; Dwarpal retries failed deliveries with growing waits. The same event may arrive twice: use `event.id` to do its work once.

The events are `verification_session.completed` and `verification_session.expired`.
