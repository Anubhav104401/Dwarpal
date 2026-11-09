---
fingerprint: 05695a1725250e4d
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

@@ 5-12
Standard-library tools: `asyncio` (to look up a host name without blocking), `hashlib` and `hmac` (signatures), `ipaddress` (to classify addresses), `secrets` (new secrets), `socket` (the kind of connection to look up), `Sequence` (the type of a list of addresses, since 9 Nov) and `urlsplit` (to take an address apart).

@@ 14
`httpx`, the HTTP client that sends the webhooks.

@@ 16-17
**`RETRY_AFTER_S`** — the retry schedule from the design (§3.7): after each failure, wait 1 minute, then 5, 30, 2 hours, 6, 12, 24. A receiver that is down for a day still gets every event; one gone for good stops costing effort. The spacing grows because a receiver that failed just now will probably still be failing in a few seconds.

@@ 18
`SECRET_PREFIX` — every webhook secret starts with `whsec_`, so a leaked one is easy to recognise for what it is. (The `noqa` tells the linter that this text is a label, not a hidden password.)

@@ 25-26
**`UnsafeUrlError`** — the error for an address Dwarpal won't send to.

@@ 29-30
**`is_public`** — is this address on the public internet?

@@ 31-32
An IPv6 address of the form `::ffff:10.0.0.1` is just the IPv4 address `10.0.0.1` written differently. Unwrapped first, it can't sneak a private address past the checks below.

@@ 33
Python's `ipaddress` knows the official lists: `is_global` is false for private ranges (`10.…`, `192.168.…`), loopback (`127.…`, `::1`), link-local (`169.254.…`), shared and reserved space. Multicast addresses are excluded too.

@@ 36-41
**`check_url`** — refuse an address that could turn Dwarpal against its own network. Since 9 Nov it also hands back the addresses it checked, so that `send` connects to one of them: looking the name up again would give its owner a second chance to answer — with a private address this time (**DNS rebinding**). In development, where private addresses are allowed, nothing is looked up and the list is empty.

@@ 42-44
Take the address apart. Only `http` and `https`, with a host name, are web addresses.

@@ 45-46
Live webhooks must be encrypted (`https`). Test ones may use `http`, for a developer's quick experiments.

@@ 47-48
No user name or password inside the address (`https://user:pass@…`): secrets don't belong in URLs, which end up in logs.

@@ 49-50
On a developer's laptop or in tests, private addresses are allowed and the rest is skipped: no addresses come back, and the request looks the name up itself. Production refuses this setting (`settings.py`).

@@ 51-55
Look the host name up, as a connection would (`getaddrinfo`; the port matters little, but it is the right one). It runs without blocking the API's other requests. A name that doesn't exist is refused.

@@ 57-60
**Every** address the name points to must be public. A name can have several, and an attacker controls their own name: one public address to pass a lazy check, one private address to be connected to.

@@ 64-65
**`new_secret`** — a fresh signing secret: the prefix and 32 unpredictable bytes.

@@ 68-69
**`signature`** — the `Dwarpal-Signature` header. The receiver shares the secret, so it can recompute the HMAC and compare. A match proves two things: the request came from someone holding the secret (Dwarpal), and the body wasn't changed on the way.

@@ 70
The HMAC-SHA256, keyed with the secret, of the time, a dot, and the exact body. Including the time means an attacker who captured a webhook can't resend it a day later with a fresh time: the signature covers the old one, and receivers refuse signatures older than five minutes.

@@ 71
The header's form: `t=<seconds since 1970>,v1=<hex digest>`. The `v1` label lets a future signature scheme be added alongside without breaking receivers.

@@ 74-84
**`send`** — POST one event. Since 9 Nov it takes the addresses `check_url` checked (`addresses`; none in development). It returns two things: the receiver's status code (`None` if it never answered), and a reason it failed (`None` if it accepted, with any 2xx status).

@@ 85-90
The headers: JSON content, a `User-Agent` naming the sender, the event's ID (so a receiver can ignore a duplicate), and the signature.

@@ 115-117
**`retry_delay`** — after `attempts_made` failures, how long to wait: the schedule's entry, or `None` once the schedule is used up, meaning give up. The first failure uses entry 0, hence `- 1`.

@@ 19-22
**`MAX_ADDRESSES`** and **`UNREACHED`** (9 Nov) — a name can point to several addresses: a request tries at most three, in turn, and only while none could be reached. Those are the failures named in `UNREACHED` — no connection made, or none made in time — after which nothing was sent, so another address may safely be tried. Any later failure (no answer to the request, say) may come after the event arrived, so it waits for the retry schedule rather than being sent twice at once.

@@ 56
The addresses found, as text, each once and in the order the system gave them — its order of preference. (`dict.fromkeys` keeps the first of each and drops repeats: one address can come back once per kind of socket.)

@@ 61
Hand back the checked addresses — the only ones the request may go to.

@@ 91-92
The address as `httpx` reads it, and the list of tries: by default just one — to the address as written, so the connection looks its name up (development, where no addresses were checked).

@@ 93-98
With checked addresses, one try per address, at most three: the same address with its host replaced by the checked address (`copy_with`), so no new lookup happens. The website is still named: in the `Host` header — how one server tells its websites apart — and to TLS as the **SNI** name (`sni_hostname`), so the server presents that website's certificate and the connection insists the certificate is for that name, exactly as if the name had been looked up. `Connection: close` ends the connection after this one request: `httpx` keeps connections open by the address they reach, and one opened for one name must never carry another name's event.

@@ 99-100
No reason yet; then each try in turn.

@@ 101-105
Send. **No redirects** (`follow_redirects=False`): a public address could otherwise answer "go to `http://localhost/…`", and the request would follow it straight past the address check.

@@ 106-108
Couldn't connect to this address: nothing was sent, so remember why, and try the next one.

@@ 109-110
Any other failure — no answer in time, a broken reply — and the event may have arrived: stop, and let the retry schedule send it again later. The reason is the kind of error, such as `ReadTimeout`.

@@ 111
It answered: the status, and a reason only if it wasn't a success.

@@ 112
No address could be reached: no status, and why the last one failed.
