---
fingerprint: c37b871a774b47fe
---
**Caddy's settings** (Phase 8, §5.8.2): which address goes to which service, and HTTPS for all of them. A Caddyfile lists *sites* — an address, then in braces what to do with its requests.

@@ 1-3
What Caddy does here: it gets HTTPS certificates from **Let's Encrypt** and renews them by itself, and passes each address's requests to the right service. The domain comes from the environment, so the file is the same for any domain.

@@ 5-8
The global options block: the e-mail address Let's Encrypt writes to about certificates that are about to expire.

@@ 10-16
**`(common)`** — a *snippet* every site imports: compress answers (zstd or gzip); **HSTS** — browsers that have seen it refuse plain HTTP to the domain for two years, even if a link asks for it; and no `Server` header saying what software answers.

@@ 18-22
The domain itself: the home page, the verify page and the console, all from the web app.

@@ 24-27
`www.` sends visitors to the plain domain, permanently (`301`), keeping the rest of the address: one true address.

@@ 29-33
`api.` — the API, for websites and the verify page.

@@ 35-39
`shop.` — the demo shop.
