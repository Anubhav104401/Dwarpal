---
fingerprint: 905588c59afb2a65
---
The verify page's **Next.js configuration**, and above all its **security headers**: instructions sent with every page that tell the browser what this page may and may not do. The verify page handles a camera, a one-time secret and a flow token, so it gets the strictest rules the app can work with.

!!! kid "Explain like I'm six — house rules on the door"
    A sign on a door says "no shoes, no dogs, no strangers upstairs". The browser is the strict babysitter who reads the sign and enforces it — even against code that somehow got into the house. Security headers are that sign.

@@ 1
The type of a Next.js configuration, so mistakes in it are caught by the type checker. `import type` brings in only the type, nothing that runs.

@@ 3
`apiUrl` — the API's address, from `NEXT_PUBLIC_DWARPAL_API_URL`, or the local one. In Next.js, variables starting with `NEXT_PUBLIC_` are built into the page's code, so the browser knows where the API is.

@@ 4-10
The **security headers** that are the same for every answer, as a list of name and value pairs. (The **content security policy** used to be here too; since Phase 7 it changes with every page — it carries a fresh nonce — so `proxy.ts` makes it.)

- `Permissions-Policy` — which powerful browser features the page may use: the camera, for this page itself only (`camera=(self)`), and never the microphone, location or payments (`()` means "nobody");
- `Referrer-Policy: no-referrer` — when the person leaves, don't tell the next site which address they came from. The address contains the session's ID;
- `X-Content-Type-Options: nosniff` — the browser must trust the declared type of each file, and never guess. Guessing has let attackers disguise scripts as images;
- `Cross-Origin-Opener-Policy: same-origin` — a window opened by another site can't hold a handle on this page.

@@ 12
The configuration object, checked against `NextConfig`.

@@ 13
`poweredByHeader: false` — don't announce "X-Powered-By: Next.js" in every response. Telling strangers exactly which software runs a site helps no one but attackers.

@@ 14
`reactStrictMode: true` — in development, React runs certain parts twice on purpose, to bring hidden bugs to the surface (see `verify-flow.tsx`).

@@ 15-17
`headers()` — Next.js asks this function which headers to add. The answer: on every path (`/:path*` matches all of them), the security headers above.

@@ 18-22
**`rewrites`** (Phase 5) — a request to `/console-api/…` on this site is passed on, by the Next.js server, to the API's `/console/v1/…`. The console's pages therefore only ever talk to their own origin. The session cookie belongs to one site, `SameSite` and the `__Host-` prefix work as intended, and the API's `Origin` check sees the console's own address. In production, Caddy does the same job, serving both from one address (§3.8). Requests passed on this way carry the browser's address in `X-Forwarded-For`, which the API's server (uvicorn) trusts from the local machine, so sign-in limits still count each person's own address.

@@ 23
The end of the object.

@@ 25
Hand the configuration to Next.js.
