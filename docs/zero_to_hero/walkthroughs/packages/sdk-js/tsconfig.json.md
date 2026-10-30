---
fingerprint: 0a0a6c8a9eb3370e
---
The browser SDK's **TypeScript settings** for checking. The same as `@dwarpal/node`'s (explained there), but for a browser.

@@ 1-3
The opening brace; start from the shared strict settings; the changes follow.

@@ 4
`"lib": ["ES2024", "DOM"]` — the modern language, **and the DOM**: the browser's own objects (`window`, `document`, `HTMLElement`, `MessageEvent`), which the modal is built from.

@@ 5-6
Node.js's own module rules, so each import of our own files carries its `.js` ending, as in the Node SDK — the strictest rules, which any bundler also accepts.

@@ 7
`"types": []` — load no extra type descriptions: in particular not Node.js's, which would let `Buffer` or `process` slip in, though no browser has them.

@@ 8-9
Only check; never write files. The end of the options.

@@ 10-11
Check the sources and the tests. The closing brace.
