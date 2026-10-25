---
fingerprint: 0c30f39e36e66c89
---
The low-level side of **webhooks** (Phase 4, §5.4.3): deciding whether an address is safe to send to, signing what is sent, sending it, and when to try again.

A **webhook** turns the usual direction round. Instead of a website asking Dwarpal "is it finished yet?" over and over, Dwarpal calls the website when something happens. The website gives Dwarpal an address on its own server, and Dwarpal sends an HTTP `POST` there.

That makes Dwarpal a program that sends requests to addresses **chosen by its customers**, which is dangerous. An attacker could register `http://169.254.169.254/…` (the cloud's internal metadata service, which hands out credentials), or `http://localhost:8001` (Dwarpal's own inference service), and use Dwarpal to reach places only Dwarpal can reach. This attack is called **server-side request forgery (SSRF)**, and it is one of the OWASP top ten. The first half of this file exists to prevent it.

!!! kid "Explain like I'm six — the trusted messenger"
    Imagine a messenger who can walk into every room of a castle. If anyone may hand him a letter "for the treasure room", the castle has a problem. So before he takes a letter, he checks that the address is *outside* the castle walls — and checks again on the day he delivers it, in case someone moved the sign.

@@ 1
The docstring: safe addresses, signatures, retries.

@@ 3
The project-wide type-hint setting.

@@ 5-11
Standard-library tools: `asyncio` (to look up a host name without blocking), `hashlib` and `hmac` (signatures), `ipaddress` (to classify addresses), `secrets` (new secrets), `socket` (the kind of connection to look up), and `urlsplit` (to take an address apart).

@@ 13
`httpx`, the HTTP client that sends the webhooks.

@@ 15-16
**`RETRY_AFTER_S`** — the retry schedule from the design (§3.7): after each failure, wait 1 minute, then 5, 30, 2 hours, 6, 12, 24. A receiver that is down for a day still gets every event; one gone for good stops costing effort. The spacing grows because a receiver that failed just now will probably still be failing in a few seconds.

@@ 17
`SECRET_PREFIX` — every webhook secret starts with `whsec_`, so a leaked one is easy to recognise for what it is. (The `noqa` tells the linter that this text is a label, not a hidden password.)

@@ 20-21
**`UnsafeUrlError`** — the error for an address Dwarpal won't send to.

@@ 24-25
**`is_public`** — is this address on the public internet?

@@ 26-27
An IPv6 address of the form `::ffff:10.0.0.1` is just the IPv4 address `10.0.0.1` written differently. Unwrapped first, it can't sneak a private address past the checks below.

@@ 28
Python's `ipaddress` knows the official lists: `is_global` is false for private ranges (`10.…`, `192.168.…`), loopback (`127.…`, `::1`), link-local (`169.254.…`), shared and reserved space. Multicast addresses are excluded too.

@@ 31-32
**`check_url`** — refuse an address that could turn Dwarpal against its own network.

@@ 33-35
Take the address apart. Only `http` and `https`, with a host name, are web addresses.

@@ 36-37
Live webhooks must be encrypted (`https`). Test ones may use `http`, for a developer's quick experiments.

@@ 38-39
No user name or password inside the address (`https://user:pass@…`): secrets don't belong in URLs, which end up in logs.

@@ 40-41
On a developer's laptop or in tests, private addresses are allowed and the rest is skipped. Production refuses this setting (`settings.py`).

@@ 42-46
Look the host name up, as a connection would (`getaddrinfo`; the port matters little, but it is the right one). It runs without blocking the API's other requests. A name that doesn't exist is refused.

@@ 47-50
**Every** address the name points to must be public. A name can have several, and an attacker controls their own name: one public address to pass a lazy check, one private address to be connected to. `address[0]` is the address's text form.

@@ 53-54
**`new_secret`** — a fresh signing secret: the prefix and 32 unpredictable bytes.

@@ 57-58
**`signature`** — the `Dwarpal-Signature` header. The receiver shares the secret, so it can recompute the HMAC and compare. A match proves two things: the request came from someone holding the secret (Dwarpal), and the body wasn't changed on the way.

@@ 59
The HMAC-SHA256, keyed with the secret, of the time, a dot, and the exact body. Including the time means an attacker who captured a webhook can't resend it a day later with a fresh time: the signature covers the old one, and receivers refuse signatures older than five minutes.

@@ 60
The header's form: `t=<seconds since 1970>,v1=<hex digest>`. The `v1` label lets a future signature scheme be added alongside without breaking receivers.

@@ 63-67
**`send`** — POST one event. It returns two things: the receiver's status code (`None` if it never answered), and a reason it failed (`None` if it accepted, with any 2xx status).

@@ 68-73
The headers: JSON content, a `User-Agent` naming the sender, the event's ID (so a receiver can ignore a duplicate), and the signature.

@@ 74-76
Send. **No redirects** (`follow_redirects=False`): a public address could otherwise answer "go to `http://localhost/…`", and the request would follow it straight past the address check.

@@ 77-78
If no answer came — the connection failed, or the timeout ran out — the reason is the kind of error, such as `ConnectTimeout`.

@@ 79
Otherwise the status, and a reason only if it wasn't a success.

@@ 82-84
**`retry_delay`** — after `attempts_made` failures, how long to wait: the schedule's entry, or `None` once the schedule is used up, meaning give up. The first failure uses entry 0, hence `- 1`.
