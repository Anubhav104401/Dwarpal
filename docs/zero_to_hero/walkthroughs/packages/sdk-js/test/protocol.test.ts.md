---
fingerprint: e7e8b9ef6883c8dc
---
Tests of the browser SDK's checks: the link check, the message reader and the origin check. They are plain functions, so they run in Node.js with no browser. The modal itself is tested in a real browser, through the demo shop (`e2e/tests/age-check.spec.ts`).

@@ 1-3
Vitest's tools, and the three functions under test.

@@ 5-6
A session ID, and a verify link for it.

@@ 8-12
**A real link is accepted**, giving back the link, its origin and its session; plain `http:` works on this computer.

@@ 14-24
**Bad links are refused** with a `TypeError`. `it.each` runs the same test once per row, putting the row's first item into the test's name (`%s`): not an address; plain HTTP to another computer; another page; a malformed session; no secret; an empty secret.

@@ 26-32
A well-formed *finished* message, for the next tests.

@@ 34-41
**Both messages are read** as they are.

@@ 43-45
**Extra fields are dropped**: what comes out is exactly the checked message.

@@ 47-58
**Anything else is ignored** — `null`: nothing; text; another sender's message; an unknown type; a malformed session; a `javascript:` address, which would run code; a finished message with no address.

@@ 60-67
**`isOn`**: true for an address on the website's origin; false for a lookalike host (`shop.example.evil`), for the same host without HTTPS (another origin), and for text that isn't an address.
