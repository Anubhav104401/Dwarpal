---
fingerprint: 10d76de7eb84f759
---
Tests of webhook **safety** that need no database (Phase 4): which addresses the SSRF guard refuses, what a signature is, and the retry schedule. They run in a fraction of a second.

The addresses use numbers instead of names wherever possible, so that no test depends on the internet: an IP address written in full needs no look-up. `93.184.215.14` is a public address belonging to the reserved example domains.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 6-8
`hashlib` and `hmac`, to compute the expected signature independently, and `ipaddress`.

@@ 13
`pytest`.

@@ 28-38
**`INSIDE`** — addresses that lead **inside** a network, each a classic SSRF target: this computer, by number and by name; two private networks; the cloud's metadata service at `169.254.169.254`, which hands out a server's credentials to anything that asks from inside; IPv6's loopback; a private IPv4 address dressed as IPv6; IPv6's private range; and `0.0.0.0`, which many systems treat as "this computer".

@@ 41-45
**Every one is refused.** `@pytest.mark.parametrize("url", INSIDE)` runs the test once per address — nine tests from one function — and `pytest.raises` passes only if `check_url` raises `UnsafeUrlError`.

@@ 48-59
**Badly formed addresses are refused**, even with private addresses allowed: not a web address, plain `http` for a live webhook, and a user name and password inside the address. Each case is a pair of the address and the mode.

@@ 143-146
**What counts as public**: a normal internet address yes; a multicast address no; and no for `100.64.0.1`, the space internet providers share among customers, which is not on the public internet either.

@@ 149-154
**The signature** is exactly an HMAC-SHA256 of `"<time>.<body>"`, keyed with the secret, in the `t=…,v1=…` form; and adding a single space to the body changes it.

@@ 157-158
**The retry schedule**: one delay per failure, in order, then `None` — give up. `[*RETRY_AFTER_S, None]` is the schedule's items followed by `None`.

@@ 5
`asyncio`, to reach the running event loop and stand in for its address lookup (9 Nov).

@@ 9-10
`socket`, for the kinds of address a lookup answers with, and `Any`, for the stand-in's loose types (9 Nov).

@@ 12
`httpx`, to make the requests a webhook sends, answered by a stand-in receiver (9 Nov).

@@ 15-24
The code under test — since 9 Nov also `send` and `MAX_ADDRESSES`.

@@ 26
Two public addresses (example.com's, IPv4 and IPv6), for the tests to use.

@@ 62-65
**A public address is accepted and handed back to connect to**, even in live mode with private addresses not allowed; with them allowed (development), nothing is looked up and no addresses come back.

@@ 68-71
**Test — every address a name gives is checked and handed back, once each, in order** (9 Nov). `monkeypatch` undoes the stand-in afterwards.

@@ 72-76
A stand-in for the address lookup, so the test needs no internet: it checks it was asked about the right name and port, and answers with an IPv6 address and an IPv4 address — the second twice, as a real lookup can.

@@ 78-80
Put the stand-in in place of the running loop's own lookup, check a name, and expect both addresses — in the order given, the repeat dropped.

@@ 83-87
**Test — a webhook goes to the address that was checked, still naming the website** (9 Nov): the DNS rebinding gap is closed by never asking for the name a second time.

@@ 88-92
A stand-in receiver that keeps every request it gets, and accepts each (`204`).

@@ 94-95
Send to a name with capitals, a port and a query, with one checked address.

@@ 96-101
Accepted; one request, to the checked address with the port, path and query unchanged; the name — lower-cased — in `Host` with its port, and as the TLS name (`sni_hostname`); and `Connection: close`.

@@ 104-117
**Test — only an address that can't be reached is passed over for the next** (9 Nov), three ways: a refused connection and a connection that timed out move on, up to three addresses; no answer after connecting stops at the first, since the event may have arrived.

@@ 118-122
A receiver that notes the address of each request, then fails it in the given way.

@@ 124-128
Four checked addresses; the outcome is the failure's name, and the addresses tried are the first three — or just the first.

@@ 131-140
**Test — the next address answers when the first can't be reached** (9 Nov), as on a server without IPv6: the IPv6 address is refused, the IPv4 one accepts, and that is the outcome.
