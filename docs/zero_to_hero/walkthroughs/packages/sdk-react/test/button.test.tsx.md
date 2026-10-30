---
fingerprint: c467981e877fb95a
---
A test of the React SDK's button. With no browser in the test, the button is drawn as HTML text by React DOM's server renderer, and that text is compared.

@@ 1-4
The renderer, Vitest's tools, and the button.

@@ 6
`never` — a "create the session" function whose promise never settles; the test only draws the button, so it is never called.

@@ 8-12
**The button with its default words**: a plain `button` — `type="button"`, so it never submits a form around it — not busy, and not marked unusable.

@@ 13-23
**With a class and words of its own**: both reach the HTML.
