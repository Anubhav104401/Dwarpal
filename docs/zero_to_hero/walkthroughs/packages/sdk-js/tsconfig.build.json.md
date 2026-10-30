---
fingerprint: efd9a83d40e3f3db
---
The settings for **building** the browser SDK — word for word those of `@dwarpal/node` (explained there).

@@ 1-3
The opening brace; the checking settings, so the build follows the same rules; the changes:

@@ 4-7
Write files this time: from `src/` into `dist/`, with a declaration file (`.d.ts`, the types only) beside each.

@@ 8-10
The end of the options; build only the sources, never the tests; the closing brace.
