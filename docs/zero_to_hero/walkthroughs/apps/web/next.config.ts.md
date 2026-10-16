---
fingerprint: bb0dac69938d8e82
---
The verify page's **Next.js configuration**, and above all its **security headers**: instructions sent with every page that tell the browser what this page may and may not do. The verify page handles a camera, a one-time secret and a flow token, so it gets the strictest rules the app can work with.

!!! kid "Explain like I'm six — house rules on the door"
    A sign on a door says "no shoes, no dogs, no strangers upstairs". The browser is the strict babysitter who reads the sign and enforces it — even against code that somehow got into the house. Security headers are that sign.

@@ 1
The type of a Next.js configuration, so mistakes in it are caught by the type checker. `import type` brings in only the type, nothing that runs.

@@ 3
`apiUrl` — the API's address, from `NEXT_PUBLIC_DWARPAL_API_URL`, or the local one. In Next.js, variables starting with `NEXT_PUBLIC_` are built into the page's code, so the browser knows where the API is.

@@ 4
`development` — true when running the development server.

@@ 6-18
The **Content Security Policy** (CSP): a list of rules about where the page may load things from and send things to. Each rule is one text, and `.join("; ")` puts them into one header value. `'self'` means "this page's own origin".

| Rule | Means |
| :-- | :-- |
| `default-src 'self'` | anything not covered below: only from this origin |
| `connect-src 'self' <API>` | the page's code may talk only to itself and the API. Even injected code couldn't send a picture anywhere else |
| `img-src 'self' data: blob:` | images from this origin, or made in memory |
| `media-src 'self' blob:` | video only from this origin or from memory — the camera's stream is in memory |
| `font-src 'self'` | fonts only from this origin |
| `style-src 'self' 'unsafe-inline'` | styles from this origin, plus inline ones, which Next.js uses |
| `script-src 'self' 'unsafe-inline'` | scripts from this origin, plus the inline ones Next.js writes into each page to start React |
| `object-src 'none'` | no plug-ins, ever |
| `base-uri 'none'` | no `<base>` tag may change what relative addresses mean |
| `form-action 'self'` | forms may only send to this origin |
| `frame-ancestors 'none'` | no other website may show this page inside a frame. That blocks **clickjacking**: a hostile site hiding this page under its own buttons |

Line 13 adds `'unsafe-eval'` only in development, where React's live reloading needs it. A production build never gets it.

!!! warn "Careful — honest about a gap"
    `'unsafe-inline'` for scripts weakens the policy: if an attacker ever managed to inject a `<script>` into the page, the browser would run it. The strict fix is a **nonce** — a fresh random value per page, which every allowed script must carry. It needs per-request rendering, and it is scheduled for the security-hardening phase (Phase 7). The other rules, especially `connect-src`, already limit what any injected code could do.

@@ 20-26
The **security headers**, as a list of name and value pairs:

- the CSP from above;
- `Permissions-Policy` — which powerful browser features the page may use: the camera, for this page itself only (`camera=(self)`), and never the microphone, location or payments (`()` means "nobody");
- `Referrer-Policy: no-referrer` — when the person leaves, don't tell the next site which address they came from. The address contains the session's ID;
- `X-Content-Type-Options: nosniff` — the browser must trust the declared type of each file, and never guess. Guessing has let attackers disguise scripts as images;
- `Cross-Origin-Opener-Policy: same-origin` — a window opened by another site can't hold a handle on this page.

@@ 28
The configuration object, checked against `NextConfig`.

@@ 29
`poweredByHeader: false` — don't announce "X-Powered-By: Next.js" in every response. Telling strangers exactly which software runs a site helps no one but attackers.

@@ 30
`reactStrictMode: true` — in development, React runs certain parts twice on purpose, to bring hidden bugs to the surface (see `verify-flow.tsx`).

@@ 31-33
`headers()` — Next.js asks this function which headers to add. The answer: on every path (`/:path*` matches all of them), the security headers above.

@@ 34
The end of the object.

@@ 36
Hand the configuration to Next.js.
