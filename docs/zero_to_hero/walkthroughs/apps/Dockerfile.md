---
fingerprint: 15aa15ca98b21d60
---
The image of the two **Next.js apps** (Phase 8, §5.8.2) — the web app (home page, verify page, console) and the demo shop — one recipe for both, chosen with the `APP` build argument.

@@ 1-4
What this file makes: the image of either Next.js app — the web app or the demo shop — chosen with `APP`; how to build it; and why the API's public address is given at build time: Next.js writes `NEXT_PUBLIC_…` values into the code it builds, so each domain gets its own build.

@@ 6-9
**Stage 1** — Node 24 on slim Debian, at the version CI uses. The two build arguments, and the API's address made available to the build; Next.js's anonymous usage reports switched off.

@@ 10-11
Switch on **Corepack**, Node's own tool that provides pnpm at exactly the version the repository names (`packageManager` in `package.json`).

@@ 12-13
Copy the repository in (`.dockerignore` keeps out installed packages, builds, secrets and data).

@@ 14-15
Install exactly the lockfile's versions, then build the chosen app *and* the workspace packages it depends on (`...` after the name), such as the SDKs.

@@ 16-21
**`pnpm deploy`** copies the app with only its production dependencies into `/out`. It copies the files Git tracks, so the build (`.next`, without its cache) and the public folder — including MediaPipe's files, generated during the build — are copied in after.

@@ 23-26
**Stage 2** — a fresh Node image in production mode, with only `/out` copied in, owned by the `node` user.

@@ 27-30
Run as `node`, the unprivileged user Node's image provides; listen on port 3000; start the app with Next.js's own server.
