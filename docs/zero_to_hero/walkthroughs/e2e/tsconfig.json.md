---
fingerprint: 231b33ef9fd81ebc
---
The end-to-end test's TypeScript settings: the shared strict ones, following Node.js's own module rules (like the SDK), because Playwright runs the test files directly in Node.js.

@@ 1
The opening brace.

@@ 2
Start from the shared settings (which include the browser's `DOM` types — useful here, since tests talk about pages).

@@ 3
The changes:

@@ 4-5
Node.js's module rules.

@@ 6
Load Node.js's types: the configuration uses its built-in modules.

@@ 7
Only check; Playwright runs the TypeScript itself.

@@ 8
The end of the options.

@@ 9
Check the Playwright configuration and the tests.

@@ 10
The closing brace.
