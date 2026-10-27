---
fingerprint: 82e36d5a494f066b
---
**Dwarpal's components** (Phase 5, §5.5.6): the few pieces every page is built from — buttons, surfaces, inputs, fields, messages and badges — styled only with the design tokens. The console's and the verify page's shells re-export them under their old names.

@@ 1
React's `ReactNode` type: anything React can draw.

@@ 3-4
Most pieces are **class names**, not components: a link and a button can then look alike while staying what they are — a `<Link>` for going somewhere, a `<button>` for doing something — which matters to screen readers and keyboards.

@@ 6
**`focusRing`** — a saffron outline, 2 pixels wide and 2 away, shown when the control is focused *from the keyboard* (`focus-visible:`), so keyboard users always see where they are and mouse users aren't distracted.

@@ 7
**`motion`** — colour changes ease over the *quick* duration with the *settle* curve, only for people who haven't asked for reduced motion.

@@ 9-13
**`TONES`** — how loud a button is: **primary**, near-black (white in dark mode); **accent**, saffron with a soft saffron shadow, for the action that moves things forward; **quiet**, no background until hovered. Each brightens or darkens on hover. `as const` keeps the names exact, so only these three can be asked for.

@@ 15-19
**`SIZES`** — **large**, full width with generous padding (the verify page); **small**, the console's main buttons; **compact**, the quietest.

@@ 21-25
**`button`** — a button's classes: a centred row, dimmed and with a "not allowed" pointer when disabled, plus its size, tone, motion and focus ring. `keyof typeof TONES` means "one of the names in `TONES`": TypeScript refuses any other.

@@ 27-29
**`panel`** — a white surface with a soft border and shadow (translucent midnight in dark mode), for a group of things on a console page.

@@ 30-31
**`card`** — the verify page's larger surface: more rounded, more padding, a deeper shadow, and slightly see-through with the background blurred behind it (`backdrop-blur`). It rises into view (`motion-safe:animate-rise`).

@@ 33
**`input`** — text boxes and menus: rounded, with a saffron border and ring when focused (`focus:`), and the same motion as buttons.

@@ 35-45
**`Field`** — a label and its control. The label's `htmlFor` names the control's `id`, so clicking the label focuses the control, and screen readers read the label when the control is reached.

@@ 47-57
**`Alert`** — a red message with `role="alert"`: screen readers announce it the moment it appears, so someone who can't see the page still learns that, say, sign-in failed.

@@ 59-69
**`Notice`** — good news in teal, with `role="status"`: announced *politely*, once the screen reader has finished what it was saying.

@@ 71-76
**`BADGES`** — four tones for small labels: **brand** (the *Console* mark), **success** and **danger** (an audit chain's verdict), **neutral** (an outline, for plain facts such as *Test mode*). Each tone's text colour was chosen to keep 4.5:1 on its own tint, in both themes; the specimen page's accessibility test proves it.

@@ 78-83
**`Badge`** — a short label in a pill, in one of those tones.
