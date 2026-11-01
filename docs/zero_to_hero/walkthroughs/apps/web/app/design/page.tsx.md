---
fingerprint: a0680bfaaa211702
---
The design system's **specimen** (`/design`, Phase 5, §5.5.6): every token and component on one page. People can see the system at a glance; and the accessibility test checks this page in the light *and* the dark theme, so a change that breaks contrast anywhere in the system fails here first. Like every page of this app, it asks search engines not to index it.

@@ 1
Next.js's type for a page's title.

@@ 3-4
Dwarpal's mark, and every piece of the design system.

@@ 6
The browser tab's title.

@@ 8-16
**`SCALES`** — the colour scales to show: each one's name, what it's for, and its steps.

@@ 18-25
**`TYPE`** — the type styles to show, each with its classes: display, title, heading, body, small and code.

@@ 27-29
**`DesignPage`** — the page itself, drawn on the server (no `"use client"`): it needs no JavaScript in the browser.

@@ 31-36
…so its column says so (`lang="en"`), for screen readers. A centred column; the mark and the title, in the display size.

@@ 37-40
What the page is.

@@ 42-45
**Colours** — a panel.

@@ 46-50
For each scale, its name and purpose.

@@ 51-61
A grid of swatches — 4 across on phones, 6 on tablets, all 11 on wide screens. Each swatch is painted with the token's own CSS variable (`var(--color-ink-500)`, built from the scale's name and the step), so it shows exactly what the pages use; beneath it, the step's number.

@@ 62-64
End of the scales and the panel.

@@ 66-69
**Type** — a panel.

@@ 70-77
A description list: each style's name (`<dt>`), then the brand's motto set in it (`<dd>`). On wider screens they sit side by side, aligned on the text's baseline.

@@ 78
End of the panel.

@@ 80
Two panels side by side on wide screens.

@@ 81-85
**Buttons** — a panel.

@@ 86-91
The two large buttons: accent and primary.

@@ 92-102
The small ones: primary, quiet, and a disabled one, to show how it dims.

@@ 103-104
End of the panel.

@@ 106-110
**Fields and messages** — a panel.

@@ 111-113
A labelled e-mail field.

@@ 114-115
An alert and a notice. Both are announced to screen readers as the page loads — fine on a specimen.

@@ 116-121
One badge in each tone.

@@ 122-124
End of the panel and the pair.

@@ 126-134
**Motion** — a *card*, which rises into view as the page loads, with a sentence describing what just happened (or, with reduced motion, didn't).

@@ 135-137
End of the page.

@@ 30
The design system's page is written in English only, whatever language the page as a whole is in (§5.5.11)…
