---
fingerprint: f4e34175abdf0ff0
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

@@ 11-18
Development tools only — nothing here ships anywhere:

- the shared TypeScript settings;
- the **demo shop** and the **verify page**, from this workspace. The test never imports their code; listing them tells Turborepo that they must be *built* before the test runs;
- `@playwright/test` 1.64.0 — the browser-testing framework;
- Node.js's types, and the TypeScript compiler.

@@ 19
The closing brace.
