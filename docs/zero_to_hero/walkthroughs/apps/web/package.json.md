---
fingerprint: 44d67adef6b04290
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
`dev` — Next.js's **development server** on port 3000: it rebuilds the page the moment a file is saved.

@@ 9
`build` — make an optimised **production build** into `.next/`.

@@ 10
`start` — serve that production build on port 3000.

@@ 11
`typecheck` — check every TypeScript file without writing anything.

@@ 12
`test` — run the unit tests once with Vitest.

@@ 13
The end of the scripts.

@@ 14-19
What the page needs to run, each pinned exactly:

- `geist` — the **Geist** typeface, as font files inside the package (its licence, the SIL Open Font License, allows exactly this). The page serves the fonts itself, so a visitor's browser never contacts a font service;
- `next` 16.4.0 — the framework;
- `react` and `react-dom` 19.3.0 — the library that draws the page (§4.16), and its part for web browsers.

Each version was at least seven days old when chosen — the workspace's cooldown rule (`pnpm-workspace.yaml`).

@@ 20-29
What's needed only to develop and build it: the shared TypeScript settings; **Tailwind CSS** and its PostCSS plugin (§4.18); type descriptions of Node.js, React and React DOM; the TypeScript compiler; and Vitest.

@@ 30
The closing brace.
