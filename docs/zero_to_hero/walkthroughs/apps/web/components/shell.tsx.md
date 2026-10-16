---
fingerprint: 4e060cc24dd2f85c
---
The **page frame** shared by every screen of the verify app: the soft saffron glow at the top, the Dwarpal mark and name, an optional label (such as "Amber Cellars · 18+"), the content, and a reassuring footer. It also holds the shared styles for cards and buttons, so every screen looks like part of one product.

This is a **server component** (§4.17): it has no interactivity of its own, so React can draw it to HTML ahead of time.

@@ 1
The `ReactNode` type, for the `children` input.

@@ 3-4
**`card`** — the classes of every card, as one shared text:

- `motion-safe:animate-rise` — fade in while rising, unless the visitor asked for reduced motion;
- `rounded-3xl` — strongly rounded corners;
- `border border-zinc-200/80` — a thin border, at 80 % strength (`/80` sets a colour's opacity);
- `bg-white/85` and `backdrop-blur` — white at 85 %, blurring whatever is behind it, which gives a frosted-glass look over the glow;
- `p-6`, and `sm:p-8` on screens at least 640 pixels wide — the padding (Tailwind's spacing unit is 0.25 rem, so `p-6` is 1.5 rem);
- `shadow-xl shadow-zinc-900/5` — a large, very faint shadow, lifting the card off the page;
- the `dark:` versions for dark mode.

@@ 6-7
**`button`** — classes shared by every button: full width, content centred, rounded, generous padding, semibold text, a smooth `transition` when its colour changes, a clearly visible **focus outline** for keyboard users (`focus-visible:` applies only when focus came from the keyboard, not a mouse click), and a faded, "not-allowed" look while disabled. It isn't exported: screens use the two finished styles below.

@@ 9
**`primaryButton`** — near-black (or white in dark mode): for the final "Continue" action. `` `${button} …` `` joins the shared classes with its own.

@@ 11
**`accentButton`** — saffron, with a soft saffron shadow: for the action that moves the check forward, such as "Start the camera".

@@ 13
The doc comment explains the mark: a temple doorway, where a dwarpal stands.

@@ 14
**`Mark`** — the logo, drawn in SVG (§0.10). Its one input, `className`, has a **default value**: if no size is given, `size-7` (1.75 rem square).

@@ 15-16
An `<svg>` with a 32 × 32 drawing space. `aria-hidden="true"` hides it from screen readers: it is decoration, and the name "Dwarpal" is written beside it.

@@ 17
A rounded square background: near-black, or white in dark mode.

@@ 18-24
The doorway's arch in saffron. The path's instructions read: start at (10, 25), go up to 14, curve over the top as half a circle of radius 6 to x = 22, and go down to 25.

@@ 25-30
The threshold: a horizontal line across the bottom, in the colour that contrasts with the background.

@@ 31-33
The closing tags.

@@ 35
**`Shell`** — the frame. `children` is the screen's content; `label?` is optional text for the top-right corner.

@@ 36-37
The outer box: at least the full screen's height, a **flex column** (children stacked from top to bottom, centred), with side padding. `relative` lets the glow below be positioned against it.

@@ 38-41
**The glow**: an empty `<div>` 20 rem tall across the top, painted with a radial gradient — saffron at 24 % strength at the top centre, fading out by 70 % of the way. The square brackets hold a value Tailwind doesn't have a name for (an **arbitrary value**); underscores stand for spaces. `pointer-events-none` lets clicks pass through it, and `aria-hidden` hides it from screen readers.

@@ 42-44
The header row: the mark and the name, side by side.

@@ 45-49
The optional label. `label === undefined ? null : (…)` — if there is no label, draw nothing (`null`); otherwise draw it as a small rounded **pill**, pushed to the right by `ml-auto` (an automatic left margin takes up all the free space).

@@ 50
The end of the header.

@@ 51
`<main>` — the screen's content. `flex-1` lets it grow to fill the space, pushing the footer to the bottom of short pages.

@@ 52-56
The footer: two short promises in small grey text, with `<br />` starting the second line. They appear on every screen, so the person sees them at the exact moment they decide whether to turn on the camera.

@@ 57-59
The closing tags.
