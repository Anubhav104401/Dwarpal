---
fingerprint: 70a6214031be3575
---
**The content security policy, made per page** (Phase 7, §5.7.5). Next.js runs a file named `proxy.ts` before every request it matches. This one makes a random **nonce** — a number used once — and a policy that lets only scripts carrying that nonce run. Next.js finds the nonce in the request and puts it on its own scripts as it renders the page; an attacker's injected script can't know it, so it doesn't run.

@@ 1
Next.js's request and response types for a proxy.

@@ 3-8
What this file does, and why: the policy it replaces allowed every inline script (`'unsafe-inline'`), which OWASP ZAP's scan flagged — so an injected one would have run too.

@@ 10
The API's address, as in `next.config.ts`.

@@ 11-12
How *this server* reaches the API, to ask who may frame a page. In production the web server may reach the API inside a private network, by another address than the public one; without that setting, the public address is used.

@@ 13
Whether this is the development server.

@@ 15
The path of a verify page: `/v/` and a session's public ID, which the brackets capture.

@@ 16-17
**`ORIGIN`** — an origin and nothing else: `http` or `https`, `://`, a host of letters, digits, dots and dashes, and perhaps a port. Whatever the API answers is checked against it before it goes into a header, so even a broken or tampered answer can't add rules of its own (a `;` would start a new one).

@@ 19-29
**`frameAncestorFor`** (decision D16) — which website may show this page inside a frame. The design embeds the verify page in a modal on the website's own page (`@dwarpal/js`); the browser allows that only if the page's policy names the website. Each session names exactly one: the website it returns to, which the API knows (`frame_ancestor`). `ask` is how the API is asked — `fetch`, or a stand-in in tests. Since 9 Nov it also takes **`forwardedFor`**, the visitor's address: the API limits the verify page's calls per address, and this server asks on behalf of every visitor from its own one address — counted against that, a busy hour could use up the server's allowance and leave verify pages that no website may frame.

@@ 30-33
Not a verify page: no website at all.

@@ 34-39
Ask the API — giving up after 1.5 seconds (`AbortSignal.timeout`), so a slow API can't hold the page back for long — and never from a cache: the answer belongs to this moment. The visitor's address goes with it as `X-Forwarded-For`, the header Caddy itself sets, so the API counts the lookup against the visitor.

@@ 40-41
A successful answer's `origin`, if it is text shaped like an origin; otherwise nothing.

@@ 42-45
Anything that goes wrong — the API down, the time up, an answer that isn't JSON — means no website. Failing *closed*: the page still works on its own, just not inside a frame.

@@ 47-48
**`policy`** — the policy for one page, given its nonce and the website that may frame it (none by default): a list of rules, joined into one header value.

@@ 49-53
Everything not named below only from this site (`'self'`); connections only to this site and the API — even injected code couldn't send a picture anywhere else; images from this site or made in memory; video from this site or memory (the camera's stream); fonts from this site.

@@ 54-56
**Styles**: from this site, and inline ones. A few elements set a colour or a width in a `style` attribute — the light challenge's colours, the progress bar — and a nonce can't be put on an attribute. Injected styles can change how a page looks, but can't run code.

@@ 57-58
**Scripts**: only those carrying this page's nonce (`'nonce-…'`), and those *they* add (`'strict-dynamic'` — MediaPipe's WebAssembly loader is added that way); WebAssembly may be compiled (`'wasm-unsafe-eval'`), but no JavaScript text may be turned into code — except on the development server, where React's live reloading needs it. `'self'` stays for old browsers that don't understand `'strict-dynamic'`; new ones ignore it when it is there.

@@ 59-61
No plug-ins ever; no `<base>` tag may change what relative addresses mean; forms only to this site.

@@ 62
**`frame-ancestors`** — which pages may show this one in a frame: the session's own website, if there is one, otherwise `'none'` — no page at all. Every other page of this site, and every verify page whose session has no website, can't be framed, which blocks **clickjacking** (a page that hides a real button under a decoy of its own). And the website that may frame a verify page is the one the person is about to go back to anyway.

@@ 63-64
Join the rules with `; `.

@@ 66-68
**`proxy`** — the function Next.js calls for each request. It hands the work to `secure`, with the real `fetch`. (Next.js passes `proxy` a second argument of its own, so a stand-in for `fetch` couldn't be a second argument here.)

@@ 70-74
**`secure`** — for each request: a fresh nonce — 16 random bytes (a random UUID) as Base64 — and the policy with it, naming the website that may frame this page, if any. The visitor's address is read from the request's `X-Forwarded-For`, which Caddy sets in production; without Caddy (on a laptop) there is none, and nothing is sent.

@@ 75-78
Next.js renders the page with the request's headers, so the policy goes into a copy of them; `NextResponse.next` lets the request carry on to the page, with those headers.

@@ 79-80
And the browser reads the policy from the answer.

@@ 81
End of `secure`.

@@ 83-84
**`config`** — which requests the proxy handles: pages only.

@@ 85-93
Every path except the built files (`_next/static`, `_next/image`), the console's passage to the API, MediaPipe's files and the icon — none of them pages — and except **prefetches**, which `next/link` makes in the background to speed up the next page: they would each spend a nonce for nothing.

@@ 94
End.
