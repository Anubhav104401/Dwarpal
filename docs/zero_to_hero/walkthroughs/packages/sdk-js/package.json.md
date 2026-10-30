---
fingerprint: f4c0fec36794e427
---
The package description of **`@dwarpal/js`**, the **browser SDK** (decision D16). Where `@dwarpal/node` runs on a website's *server* — creating sessions with the secret key and checking tokens — this one runs in the person's *browser*, on the website's page: it opens the age check in a modal over the page and listens for its end. It never sees a key or a token.

Its lines are those of `@dwarpal/node`'s `package.json`, explained there; only the differences are noted.

@@ 1
The opening brace.

@@ 2-4
Its name (in the `@dwarpal` scope), its version — 0.1.0, early — and a one-line description.

@@ 5
`"private": true` — never published by accident: publishing, and the licence, are the owner's decisions for later.

@@ 6
ES modules (`import … from …`).

@@ 7-12
The one thing it exports, the package itself: the type descriptions and the JavaScript, both built into `dist/`.

@@ 13-15
Only `dist/` would be packed for publishing.

@@ 16-20
The three scripts: build (`tsconfig.build.json`), check every file including the tests (`tsconfig.json`), and run the tests once with Vitest.

@@ 21-25
**No `dependencies` at all**: it runs on other people's pages, so it brings nothing of its own — only the browser's built-ins. Development needs the shared TypeScript settings (from this repository), the compiler and the test runner. There's no `engines` field: it runs in browsers, not Node.js.

@@ 26
The closing brace.
