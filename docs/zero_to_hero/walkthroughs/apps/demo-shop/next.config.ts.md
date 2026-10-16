---
fingerprint: 1add9b8c7783bd7f
---
The demo shop's Next.js configuration. A shop isn't Dwarpal's product, so its security headers are a sensible minimum rather than the verify page's strict set (`apps/web/next.config.ts`) — but every real website should send at least these.

@@ 1
The Next.js configuration type.

@@ 3-7
Three security headers:

- a small **Content Security Policy**: no other site may frame the shop (against clickjacking), no plug-ins, and no `<base>` tag may change what relative addresses mean;
- `Referrer-Policy: strict-origin-when-cross-origin` — when a visitor follows a link to another site, send only the shop's *origin*, never the full address. This is the browsers' default today, stated explicitly;
- `X-Content-Type-Options: nosniff` — never guess a file's type.

The shop deliberately has no `form-action` rule: its "Verify my age" button submits a form whose answer *redirects* to the verify page on another origin, and a strict `form-action` would block that redirect.

@@ 9-11
The configuration: no "powered by" header, and React's Strict Mode in development.

@@ 12-14
The headers, on every path.

@@ 15
The end of the object.

@@ 17
Hand the configuration to Next.js.
