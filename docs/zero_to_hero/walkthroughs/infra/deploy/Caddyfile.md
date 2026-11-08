---
fingerprint: be84c6a1552221bf
---
**Caddy's settings** (Phase 8, §5.8.2): which address goes to which service, and HTTPS for all of them. A Caddyfile lists *sites* — an address, then in braces what to do with its requests.

@@ 1-4
What Caddy does here: it gets HTTPS certificates from **Let's Encrypt** and renews them by itself, and passes each address's requests to the right service. The domain comes from the environment, so the file is the same for any domain — a free **DuckDNS** name too (decision D40): DuckDNS answers every name under one with the same address, so `www.`, `api.` and `shop.` need nothing more.

@@ 6-9
The global options block: the e-mail address Let's Encrypt writes to about certificates that are about to expire.

@@ 11-17
**`(common)`** — a *snippet* every site imports: compress answers (zstd or gzip); **HSTS** — browsers that have seen it refuse plain HTTP to the domain for two years, even if a link asks for it; and no `Server` header saying what software answers.

@@ 19-23
The domain itself: the home page, the verify page and the console, all from the web app.

@@ 25-28
`www.` sends visitors to the plain domain, permanently (`301`), keeping the rest of the address: one true address.

@@ 30-34
`api.` — the API, for websites and the verify page.

@@ 36-40
`shop.` — the demo shop.
