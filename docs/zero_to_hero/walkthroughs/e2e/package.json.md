---
fingerprint: fd26e3e5d95eb956
---
The package of the **end-to-end test** (§4.20): the whole system, in a real browser, from the shop's front door to its cellar. It is a workspace package of its own, so its tools — Playwright, above all — stay out of every other package.

@@ 1
The opening brace.

@@ 2-5
Name, a version that will never be published (`0.0.0`), `private`, and a description.

@@ 6
ES modules.

@@ 7-10
Two scripts: `e2e` runs Playwright's tests, and `typecheck` checks the test code. (The root's `pnpm e2e` runs `e2e` through Turborepo, which builds everything it needs first.)

@@ 11-20
Development tools only — nothing here ships anywhere:

- `@axe-core/playwright` 4.14.0 (Phase 5, D4) — **axe**, which checks a page against the accessibility rules of WCAG;
- the shared TypeScript settings;
- the **demo shop** and the **verify page**, from this workspace. The test never imports their code; listing them tells Turborepo that they must be *built* before the test runs;
- `@lhci/cli` 0.15.1 (Phase 5, D5) — **Lighthouse CI**, which scores pages for speed, accessibility, good practice and search engines;
- `@playwright/test` 1.64.0 — the browser-testing framework;
- Node.js's types, and the TypeScript compiler.

@@ 21
The closing brace.
