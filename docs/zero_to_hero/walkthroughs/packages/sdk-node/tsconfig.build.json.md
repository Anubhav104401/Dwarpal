---
fingerprint: efd9a83d40e3f3db
---
The settings for **building** the SDK: turning its TypeScript into the JavaScript and type files that other code uses. They extend the checking settings (`tsconfig.json`) and change four things.

@@ 1
The opening brace.

@@ 2
`"extends": "./tsconfig.json"` — start from the checking settings, so the build is held to exactly the same rules.

@@ 3
The changes.

@@ 4
`"noEmit": false` — this time, *do* write files.

@@ 5
`"rootDir": "src"` — the source files live in `src/`…

@@ 6
`"outDir": "dist"` — …and the results go to `dist/`, with the same folder layout: `src/token.ts` becomes `dist/token.js`.

@@ 7
`"declaration": true` — also write a **declaration file** (`.d.ts`) beside each JavaScript file. It contains only the types — no code — so that TypeScript users of the SDK get the same checking and autocomplete as if they had the source.

@@ 8
The closing brace of the options.

@@ 9
`"include": ["src"]` — build only the source. The tests are checked, but never shipped.

@@ 10
The closing brace.
