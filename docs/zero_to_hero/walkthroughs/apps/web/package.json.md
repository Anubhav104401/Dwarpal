---
fingerprint: 2ac8f4fdc2b20052
---
The package description of **`@dwarpal/web`** — the **hosted verify page**: the website a person is sent to by a shop, where they take the age check with their camera. It is built with **Next.js** (§4.17), the React framework chosen in ADR-0012.

"Hosted" means Dwarpal runs this page itself, on its own address, rather than each shop building its own camera page. That is a deliberate safety choice: the code that handles the camera, the secrets and the upload is written, tested and updated in one place.

@@ 1
The opening brace.

@@ 2-5
Name, version, `private` (it is an app to run, never a library to publish) and a one-line description.

@@ 6
`"type": "module"` — the files are ES modules.

@@ 7
The scripts:

@@ 8
`dev` — first copy MediaPipe's files into `public/` (`scripts/mediapipe.mjs`), then start Next.js's **development server** on port 3000, which rebuilds the page the moment a file is saved. `&&` runs the second command only if the first succeeded.

@@ 9
`build` — the same copying, then an optimised **production build** into `.next/`. (pnpm doesn't run `prebuild` scripts by default, so the copy step is written into the command itself.)

@@ 10
`start` — serve that production build on port 3000.

@@ 11
`typecheck` — check every TypeScript file without writing anything.

@@ 12
`test` — run the unit tests once with Vitest.

@@ 13
The end of the scripts.

@@ 14-22
What the page needs to run, each pinned exactly:

- `geist` — the **Geist** typeface, as font files inside the package (its licence, the SIL Open Font License, allows exactly this). The page serves the fonts itself, so a visitor's browser never contacts a font service;
- `next` 16.4.2 — the framework (upgraded from 16.4.0 on 27 Oct 2026 to fix two critical remote-code-execution flaws and a denial-of-service flaw that `pnpm audit` reported);
- `qrcode` 1.5.4 (Phase 5, approved as D13) — draws the QR code on the console's *Security* page;
- `react` and `react-dom` 19.3.0 — the library that draws the page (§4.16), and its part for web browsers.

Each version was at least seven days old when chosen — the workspace's cooldown rule (`pnpm-workspace.yaml`).

Added in Phase 3: `@mediapipe/tasks-vision` 1.1.0 — Google's **MediaPipe** vision tasks for the browser (Apache-2.0), which includes the face landmarker used for live guidance (`lib/landmarker.ts`). Version 1.1.1 existed, but was less than a week old.

Added with decision D16: `@dwarpal/js`, this repository's own browser SDK (`workspace:*`). The verify page imports its **message protocol** (`protocol.ts`), so the messages it sends to a website that framed it are exactly the ones the SDK reads.

@@ 23-33
What's needed only to develop and build it: the shared TypeScript settings; **Tailwind CSS** and its PostCSS plugin (§4.18); type descriptions of Node.js, `qrcode`, React and React DOM; the TypeScript compiler; and Vitest.

@@ 34
The closing brace.
