---
fingerprint: ef4104862c5c1a81
---
The demo shop's stylesheet: Tailwind, plus the shop's own tokens — two typefaces and three colours. The shop has a look of its own (a dark wine bar), quite unlike the verify page, which makes the hand-over between the two websites easy to see.

@@ 1
Load Tailwind.

@@ 3
The shop's design tokens.

@@ 4
The main typeface: Geist, with fallbacks.

@@ 5
`--font-serif` — a **serif** typeface for headings (letters with small finishing strokes, as in books and wine labels): the system's own serif — Iowan Old Style on Apple devices, Georgia or Cambria on others. Using fonts every system already has means no font files to download.

@@ 7-8
Two wine colours, as OKLCH (see the verify page's `globals.css`): a soft rosé (`wine-300`) for small text, and a deep red (`wine-500`) for the glow behind the page.

@@ 9
`amber-glow` — a warm golden amber, the shop's accent: its name, its buttons and its prices.

@@ 10
The end of the tokens.

@@ 12-14
The shop has only a dark design, and says so: browser-drawn parts such as scrollbars are dark too.
