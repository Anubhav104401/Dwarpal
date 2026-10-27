---
fingerprint: 87d3ea8667c21638
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

@@ 30-35
A centred column; the mark and the title, in the display size.

@@ 36-39
What the page is.

@@ 41-44
**Colours** — a panel.

@@ 45-49
For each scale, its name and purpose.

@@ 50-60
A grid of swatches — 4 across on phones, 6 on tablets, all 11 on wide screens. Each swatch is painted with the token's own CSS variable (`var(--color-ink-500)`, built from the scale's name and the step), so it shows exactly what the pages use; beneath it, the step's number.

@@ 61-63
End of the scales and the panel.

@@ 65-68
**Type** — a panel.

@@ 69-76
A description list: each style's name (`<dt>`), then the brand's motto set in it (`<dd>`). On wider screens they sit side by side, aligned on the text's baseline.

@@ 77
End of the panel.

@@ 79
Two panels side by side on wide screens.

@@ 80-84
**Buttons** — a panel.

@@ 85-90
The two large buttons: accent and primary.

@@ 91-101
The small ones: primary, quiet, and a disabled one, to show how it dims.

@@ 102-103
End of the panel.

@@ 105-109
**Fields and messages** — a panel.

@@ 110-112
A labelled e-mail field.

@@ 113-114
An alert and a notice. Both are announced to screen readers as the page loads — fine on a specimen.

@@ 115-120
One badge in each tone.

@@ 121-123
End of the panel and the pair.

@@ 125-133
**Motion** — a *card*, which rises into view as the page loads, with a sentence describing what just happened (or, with reduced motion, didn't).

@@ 134-136
End of the page.
