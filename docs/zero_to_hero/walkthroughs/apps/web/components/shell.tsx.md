---
fingerprint: 6aa0c6b9f0c6ad8b
---
The **page frame** shared by every screen of the verify app: the soft saffron glow at the top, the Dwarpal mark and name, an optional label (such as "Amber Cellars · 18+"), the content, and a reassuring footer. It also passes on the verify page's card and buttons, which since §5.5.6 come from the design system, so every screen looks like part of one product.

This is a **server component** (§4.17): it has no interactivity of its own, so React can draw it to HTML ahead of time.

@@ 2
React's `ReactNode` type.

@@ 6
From the design system (§5.5.6): the badge and the button classes.

@@ 8-9
The verify page's `card` now comes from the design system; re-exported here, so the pages import it from `shell` as before.

@@ 10-11
The verify page's two big buttons: **`primaryButton`**, near-black (white in dark mode), for the final action; **`accentButton`**, saffron, for the action that moves the check forward, such as "Start the camera".

@@ 14
The doc comment explains the mark: a temple doorway, where a dwarpal stands.

@@ 15
**`Mark`** — the logo, drawn in SVG (§0.10). Its one input, `className`, has a **default value**: if no size is given, `size-7` (1.75 rem square).

@@ 16-17
An `<svg>` with a 32 × 32 drawing space. `aria-hidden="true"` hides it from screen readers: it is decoration, and the name "Dwarpal" is written beside it.

@@ 18
A rounded square background: near-black, or white in dark mode.

@@ 19-25
The doorway's arch in saffron. The path's instructions read: start at (10, 25), go up to 14, curve over the top as half a circle of radius 6 to x = 22, and go down to 25.

@@ 26-31
The threshold: a horizontal line across the bottom, in the colour that contrasts with the background.

@@ 32-34
The closing tags.

@@ 36
**`Shell`** — the frame. `children` is the screen's content; `label?` is optional text for the top-right corner.

@@ 38-39
The outer box: at least the full screen's height, a **flex column** (children stacked from top to bottom, centred), with side padding. `relative` lets the glow below be positioned against it.

@@ 40-43
**The glow**: an empty `<div>` 20 rem tall across the top, painted with a radial gradient — saffron at 24 % strength at the top centre, fading out by 70 % of the way. The square brackets hold a value Tailwind doesn't have a name for (an **arbitrary value**); underscores stand for spaces. `pointer-events-none` lets clicks pass through it, and `aria-hidden` hides it from screen readers.

@@ 44-46
The header row: the mark and the name, side by side.

@@ 47-51
The optional label. `label === undefined ? null : (…)` — if there is no label, draw nothing (`null`); otherwise a neutral **badge**, pushed to the right by `ml-auto` (an automatic left margin takes up all the free space).

@@ 52
The end of the header.

@@ 53
`<main>` — the screen's content. `flex-1` lets it grow to fill the space, pushing the footer to the bottom of short pages.

@@ 54-61
The footer: two short promises in small grey text (a darker grey, and a lighter one in the dark theme, since Firefox's accessibility check on GitHub found the old one too faint — §5.6.2), with `<br />` starting the second line, and below them the language switch (§5.5.11). They appear on every screen, so the person sees them at the exact moment they decide whether to turn on the camera.

@@ 62-64
The closing tags.

@@ 12
`quietButton` (§5.6.3) — the quiet, large button: for the second choice under a loud one, such as "Not now" under "Use a passport or ID card".

@@ 1
`useTranslations` — next-intl's way for a component to get its words, in the page's language (§5.5.11).

@@ 4
The language switch.

@@ 37
The page frame's words (`Shell` in `messages/`).
