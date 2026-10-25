---
fingerprint: 3905fd0dc2f37717
---
Tests of webhook **safety** that need no database (Phase 4): which addresses the SSRF guard refuses, what a signature is, and the retry schedule. They run in a fraction of a second.

The addresses use numbers instead of names wherever possible, so that no test depends on the internet: an IP address written in full needs no look-up. `93.184.215.14` is a public address belonging to the reserved example domains.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`hashlib` and `hmac`, to compute the expected signature independently, and `ipaddress`.

@@ 9
`pytest`.

@@ 11
The code under test.

@@ 13-23
**`INSIDE`** — addresses that lead **inside** a network, each a classic SSRF target: this computer, by number and by name; two private networks; the cloud's metadata service at `169.254.169.254`, which hands out a server's credentials to anything that asks from inside; IPv6's loopback; a private IPv4 address dressed as IPv6; IPv6's private range; and `0.0.0.0`, which many systems treat as "this computer".

@@ 26-30
**Every one is refused.** `@pytest.mark.parametrize("url", INSIDE)` runs the test once per address — nine tests from one function — and `pytest.raises` passes only if `check_url` raises `UnsafeUrlError`.

@@ 33-44
**Badly formed addresses are refused**, even with private addresses allowed: not a web address, plain `http` for a live webhook, and a user name and password inside the address. Each case is a pair of the address and the mode.

@@ 47-49
**A public address is accepted**, even in live mode with private addresses not allowed. The test passes if nothing is raised.

@@ 52-55
**What counts as public**: a normal internet address yes; a multicast address no; and no for `100.64.0.1`, the space internet providers share among customers, which is not on the public internet either.

@@ 58-63
**The signature** is exactly an HMAC-SHA256 of `"<time>.<body>"`, keyed with the secret, in the `t=…,v1=…` form; and adding a single space to the body changes it.

@@ 66-67
**The retry schedule**: one delay per failure, in order, then `None` — give up. `[*RETRY_AFTER_S, None]` is the schedule's items followed by `None`.
