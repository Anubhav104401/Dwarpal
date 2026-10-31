# Integration checklist

Go through this before switching from a test key to a live key. Each item is something the [demo shop](../../apps/demo-shop) does and its tests prove.

## Keys and settings

- [ ] The API key lives only in your server's environment: not in browser code, a repository, or logs.
- [ ] Live and test keys are kept apart, and the live key is used only in production.
- [ ] Your project's **allowed origins** list exactly your website's origins, and nothing else.
- [ ] The `audience` you verify against is your project's ID, and the `issuer` is Dwarpal's.

## Creating the session

- [ ] Sessions are created only on your server, with your key.
- [ ] The session's verify link is handed only to the browser that asked, never logged or stored: it carries a one-time secret.
- [ ] Your server remembers which session **this browser** started (an `HttpOnly`, `SameSite=Lax` cookie, limited to your return route, lasting as long as a session). Without it, someone could finish a check and send the return link to someone else.

## The result

- [ ] Your return route accepts a `session_id` only if it is the one this browser started.
- [ ] It fetches the result from Dwarpal with your key; it never trusts the address, a query string, a callback or a message from the browser.
- [ ] It lets someone in only when the session is `completed` **and** `verifyAgeToken` says `allowed`, with the session's ID checked.
- [ ] It checks `livemode` is `true` in production.
- [ ] `awaiting_step_up`, `expired`, `fail` and `reject` all keep the door closed, with a kind message and a way to try again. Never tell the person *why* a check was rejected.
- [ ] What you keep afterwards is your own short-lived pass (a signed cookie, for example), not the age token.

## The page

- [ ] The check is opened from a page on the same origin as your return address (the verify page allows framing only by that origin).
- [ ] If your page sends a `Permissions-Policy` header, it allows the camera for Dwarpal's verify origin. If it has a content security policy, `frame-src` allows that origin.
- [ ] A person can open the check, close it, and use your page again, with a keyboard alone.

## Webhooks (if you use them)

- [ ] Each delivery's signature is verified on the raw body before anything else.
- [ ] Your endpoint answers quickly and handles the same event twice safely (by `event.id`).
- [ ] The webhook secret is stored like the API key.

## Privacy

- [ ] Your privacy notice says you use Dwarpal for age checks, and that Dwarpal keeps no images.
- [ ] You keep no more about the check than you need: the outcome and when, if anything.
