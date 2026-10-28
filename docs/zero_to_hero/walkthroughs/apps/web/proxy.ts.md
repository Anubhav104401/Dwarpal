---
fingerprint: 05306acfc4687fa1
---
**The content security policy, made per page** (Phase 7, §5.7.5). Next.js runs a file named `proxy.ts` before every request it matches. This one makes a random **nonce** — a number used once — and a policy that lets only scripts carrying that nonce run. Next.js finds the nonce in the request and puts it on its own scripts as it renders the page; an attacker's injected script can't know it, so it doesn't run.

@@ 1
Next.js's request and response types for a proxy.

@@ 3-8
What this file does, and why: the policy it replaces allowed every inline script (`'unsafe-inline'`), which OWASP ZAP's scan flagged — so an injected one would have run too.

@@ 10-11
The API's address, as in `next.config.ts`; and whether this is the development server.

@@ 13-14
**`policy`** — the policy for one page, given its nonce: a list of rules, joined into one header value.

@@ 15-19
Everything not named below only from this site (`'self'`); connections only to this site and the API — even injected code couldn't send a picture anywhere else; images from this site or made in memory; video from this site or memory (the camera's stream); fonts from this site.

@@ 20-22
**Styles**: from this site, and inline ones. A few elements set a colour or a width in a `style` attribute — the light challenge's colours, the progress bar — and a nonce can't be put on an attribute. Injected styles can change how a page looks, but can't run code.

@@ 23-24
**Scripts**: only those carrying this page's nonce (`'nonce-…'`), and those *they* add (`'strict-dynamic'` — MediaPipe's WebAssembly loader is added that way); WebAssembly may be compiled (`'wasm-unsafe-eval'`), but no JavaScript text may be turned into code — except on the development server, where React's live reloading needs it. `'self'` stays for old browsers that don't understand `'strict-dynamic'`; new ones ignore it when it is there.

@@ 25-28
No plug-ins ever; no `<base>` tag may change what relative addresses mean; forms only to this site; and no other site may show this page in a frame (that blocks **clickjacking**).

@@ 29-30
Join the rules with `; `.

@@ 32-34
**`proxy`** — for each request: a fresh nonce — 16 random bytes (a random UUID) as Base64 — and the policy with it.

@@ 35-38
Next.js renders the page with the request's headers, so the policy goes into a copy of them; `NextResponse.next` lets the request carry on to the page, with those headers.

@@ 39-40
And the browser reads the policy from the answer.

@@ 41
End of `proxy`.

@@ 43-44
**`config`** — which requests the proxy handles: pages only.

@@ 45-53
Every path except the built files (`_next/static`, `_next/image`), the console's passage to the API, MediaPipe's files and the icon — none of them pages — and except **prefetches**, which `next/link` makes in the background to speed up the next page: they would each spend a nonce for nothing.

@@ 54
End.
