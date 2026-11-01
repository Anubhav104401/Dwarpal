---
fingerprint: c1b565f9d6f96bec
---
**The front door** (§5.8.3): which public address reaches which service, over HTTPS — Caddy's job on the single server.

@@ 1
The way in from the internet.

@@ 2-11
An **Ingress** — the cluster's rules for which address goes where — named and labelled, with any annotations the cluster's controller needs (`with` writes the block only if there are some).

@@ 12-16
Which ingress controller handles it, and HTTPS for the three addresses, with certificates from the named Secret.

@@ 17-19
The rules: `range` over three pairs — the bare domain to the web app, `api.` to the API, `shop.` to the shop — one rule per address.

@@ 20-29
Every path (`/` and everything under it) to that component's Service, on its port.
