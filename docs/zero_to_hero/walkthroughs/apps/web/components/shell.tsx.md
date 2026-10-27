---
fingerprint: 91db951d6e5d9b4a
---
The **page frame** shared by every screen of the verify app: the soft saffron glow at the top, the Dwarpal mark and name, an optional label (such as "Amber Cellars · 18+"), the content, and a reassuring footer. It also passes on the verify page's card and buttons, which since §5.5.6 come from the design system, so every screen looks like part of one product.

This is a **server component** (§4.17): it has no interactivity of its own, so React can draw it to HTML ahead of time.

@@ 1
React's `ReactNode` type.

@@ 3
From the design system (§5.5.6): the badge and the button classes.

@@ 5-6
The verify page's `card` now comes from the design system; re-exported here, so the pages import it from `shell` as before.

@@ 7-8
The verify page's two big buttons: **`primaryButton`**, near-black (white in dark mode), for the final action; **`accentButton`**, saffron, for the action that moves the check forward, such as "Start the camera".

@@ 10
The doc comment explains the mark: a temple doorway, where a dwarpal stands.

@@ 11
**`Mark`** — the logo, drawn in SVG (§0.10). Its one input, `className`, has a **default value**: if no size is given, `size-7` (1.75 rem square).

@@ 12-13
An `<svg>` with a 32 × 32 drawing space. `aria-hidden="true"` hides it from screen readers: it is decoration, and the name "Dwarpal" is written beside it.

@@ 14
A rounded square background: near-black, or white in dark mode.

@@ 15-21
The doorway's arch in saffron. The path's instructions read: start at (10, 25), go up to 14, curve over the top as half a circle of radius 6 to x = 22, and go down to 25.

@@ 22-27
The threshold: a horizontal line across the bottom, in the colour that contrasts with the background.

@@ 28-30
The closing tags.

@@ 32
**`Shell`** — the frame. `children` is the screen's content; `label?` is optional text for the top-right corner.

@@ 33-34
The outer box: at least the full screen's height, a **flex column** (children stacked from top to bottom, centred), with side padding. `relative` lets the glow below be positioned against it.

@@ 35-38
**The glow**: an empty `<div>` 20 rem tall across the top, painted with a radial gradient — saffron at 24 % strength at the top centre, fading out by 70 % of the way. The square brackets hold a value Tailwind doesn't have a name for (an **arbitrary value**); underscores stand for spaces. `pointer-events-none` lets clicks pass through it, and `aria-hidden` hides it from screen readers.

@@ 39-41
The header row: the mark and the name, side by side.

@@ 42-46
The optional label. `label === undefined ? null : (…)` — if there is no label, draw nothing (`null`); otherwise a neutral **badge**, pushed to the right by `ml-auto` (an automatic left margin takes up all the free space).

@@ 47
The end of the header.

@@ 48
`<main>` — the screen's content. `flex-1` lets it grow to fill the space, pushing the footer to the bottom of short pages.

@@ 49-53
The footer: two short promises in small grey text, with `<br />` starting the second line. They appear on every screen, so the person sees them at the exact moment they decide whether to turn on the camera.

@@ 54-56
The closing tags.
