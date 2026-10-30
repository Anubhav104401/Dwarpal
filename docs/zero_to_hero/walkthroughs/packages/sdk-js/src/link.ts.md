---
fingerprint: a8e205053be06bdd
---
Checking a **verify link** — the session's `url` that the website's server got from Dwarpal — before the SDK opens it. A link that came from somewhere else is refused before anything is shown.

@@ 1
The shape of a session's ID, from the protocol.

@@ 3-8
**`VerifyLink`** — a link, checked: the whole link, the verify page's **origin** (scheme, host and port — `https://verify.example`), which every message must then come from, and the session's ID, which every message must name.

@@ 10
The names of *this* computer. Only there may a link be plain `http:` — for development.

@@ 12-16
**`readVerifyLink`** — check the link, or throw a `TypeError` saying what is wrong with it.

@@ 17-22
Read it as an address; if it isn't one, say so.

@@ 23-25
It must be `https:` — or `http:` on this computer only. A verify page sent over plain HTTP could be changed on its way by anyone on the network.

@@ 26-29
Its path must be `/v/` and a session ID: the verify page, and nothing else on that website. `?.[1]` takes the ID from the match, if there was one; `?? ""` gives empty text otherwise, which then fails the check.

@@ 30-32
Its **fragment** (after `#`) must carry the one-time secret, `cs=…`. `slice(1)` drops the `#`; `URLSearchParams` reads the `name=value` pairs. Without the secret, the page could only say "this link doesn't work".

@@ 33-34
The checked link, in its standard written form (`href`), its origin and its session.

@@ 36-43
**`isOn`** — whether an address is on a given origin. The SDK uses it on the address a *finished* message asks to go to: only the website's own addresses are accepted, so even a message from the real verify page could never send the person to another website.
