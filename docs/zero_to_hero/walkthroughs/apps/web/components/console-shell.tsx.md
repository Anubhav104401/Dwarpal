---
fingerprint: b1b15ab8dae1bc4c
---
The console's **frame and building blocks** (Phase 5): shared styles, a labelled form field, an alert, and the page frame with the Dwarpal mark, a "Console" badge, and room for who is signed in. The styles reuse the verify page's palette (`globals.css`): the warm brand colour for focus and highlights, zinc greys, and a dark version of everything.

@@ 1
The type of anything React can show.

@@ 3
The Dwarpal mark, from the verify page's shell.

@@ 5-6
`panel` — a white card with a soft border and shadow (a dark one in dark mode).

@@ 8-9
`input` — text boxes and menus: rounded, with a brand-coloured ring when focused, so keyboard users always see where they are.

@@ 11-12
`smallButton` — the main button: dark on light, light on dark, with a visible focus outline.

@@ 14-15
`quietButton` — a secondary button, with no background until hovered.

@@ 17-27
**`Field`** — a label and its control. The label's `htmlFor` names the control's `id`, so clicking the label focuses the control, and screen readers read the label when the control is reached.

@@ 29-39
**`Alert`** — a message with `role="alert"`: screen readers announce it the moment it appears, so someone who can't see the page still learns that sign-in failed.

@@ 41-42
**`ConsoleShell`** — the frame of every console page: the content, and an optional `aside` for the header's right-hand side.

@@ 43-55
A centred column up to 5xl wide: the header (mark, name, the *Console* badge — dark saffron text, light in dark mode, for contrast — then the aside pushed right by `ml-auto`), and the page's `main` content.

@@ 56
End of the component.
