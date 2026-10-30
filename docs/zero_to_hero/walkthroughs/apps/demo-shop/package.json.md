---
fingerprint: bb1c93d68061a085
---
The package description of **Amber Cellars**, the **demo shop**: a pretend wine shop that plays the part of a real customer — a **relying party** — so the whole journey can be seen and tested end to end. Its code is written exactly as a real website should integrate Dwarpal, so it doubles as a working example for developers.

Its setup mirrors the verify page's (`apps/web/package.json`), with two differences: it runs on port **3100**, and it depends on the **SDK**.

@@ 1
The opening brace.

@@ 2-5
Name, version, `private`, and a description.

@@ 6
ES modules.

@@ 7-13
The scripts — the same as the verify page's, on port 3100.

@@ 14-21
What the shop needs to run:

- `@dwarpal/node` — the server SDK, from this repository (`workspace:*`). A real shop would install it from a package registry instead; the code that uses it would be identical;
- `@dwarpal/react` — the React SDK (decision D16), likewise: the button that opens the check in a modal (`app/age-check-button.tsx`). It brings the browser SDK, `@dwarpal/js`, with it;
- the Geist typeface, Next.js, React and React DOM, at the same versions as the verify page.

@@ 22-31
Development tools — the same set as the verify page's.

@@ 32
The closing brace.
