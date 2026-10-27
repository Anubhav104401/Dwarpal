---
fingerprint: 82e3ac23629c01ac
---
The verify page's one stylesheet. Almost all styling happens through **Tailwind** classes written directly on the elements (§4.18); this file only brings Tailwind in and adds the project's own **design tokens** — named values such as the brand colour, which every class can then use.

@@ 1
`@import "tailwindcss";` — load Tailwind: its reset of browser defaults, its theme (colours, sizes, fonts) and its system of utility classes.

@@ 3
`@theme { … }` — a Tailwind instruction: every `--name: value` inside becomes a **design token**, available both as a CSS variable and as classes. A token named `--color-brand-500` creates classes such as `bg-brand-500` and `text-brand-500`.

@@ 4
`--font-sans` — the page's main typeface: Geist (provided by `layout.tsx` as the variable `--font-geist-sans`), then three fallbacks in case it can't load, ending with the system's own sans-serif font.

@@ 6-9
**The brand colour** — a warm saffron, in four strengths from light (300) to deep (600). They are written in **OKLCH**, a modern way to describe colour with three numbers: **L**ightness (0 to 1), **C**hroma (how vivid) and **H**ue (an angle on the colour wheel; 60–75 is orange-gold). Unlike the older RGB numbers, equal steps in OKLCH *look* equally different to human eyes, which makes harmonious shades easy to choose.

Saffron is the colour of marigolds and temple doorways — the place where a *dwarpal*, a doorkeeper, stands.

@@ 10-11
**`brand-700`** (Phase 5) — a darker saffron for **text** on light backgrounds. The accessibility test found `brand-600` text on a pale saffron badge at 2.8:1; WCAG AA asks for 4.5:1. This shade measures at least 5.3:1 there.

@@ 13
`--animate-march` — an animation token, used as `animate-march`: the "marching ants" movement of the face guide's dotted outline while photos are taken. It runs the `march` keyframes over 0.9 seconds, at even speed (`linear`), for ever (`infinite`).

@@ 14
`--animate-rise` — cards fade in while rising 8 pixels, in 0.45 seconds. `cubic-bezier(0.2, 0.8, 0.2, 1)` describes the speed curve: fast at first, then gently slowing to a stop, which feels natural. `both` keeps the starting state before the animation begins and the end state after it.

@@ 16-20
`@keyframes march` — the animation's steps. It only says the end state: the outline's dash pattern shifted by 32 units. Repeating that endlessly makes the dashes appear to travel around the oval.

@@ 22-31
`@keyframes rise` — from invisible and 8 pixels lower, to fully visible in its place.

@@ 32
The end of the theme.

@@ 34-36
`color-scheme: light dark` — tells the browser that the page supports both light and dark modes, so its own parts — scrollbars, form controls — follow the visitor's system setting too.

!!! key "Respecting reduced motion"
    Some people get dizzy or unwell from movement on screen, and ask their system to reduce it. Every animation in this app is written as `motion-safe:animate-…`: Tailwind applies it only when the visitor has *not* asked for reduced motion. Nothing needs to be switched off afterwards.
