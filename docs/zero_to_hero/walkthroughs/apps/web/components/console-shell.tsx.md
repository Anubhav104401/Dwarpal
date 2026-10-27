---
fingerprint: e36c5993a58195dd
---
The console's **frame and building blocks** (Phase 5): the page frame with the Dwarpal mark, a "Console" badge, and room for who is signed in; and the console's pieces — buttons, panel, input, field, alert — which since §5.5.6 come from the design system (`components/ui.tsx`) and are passed on from here under their old names.

@@ 1
React's `ReactNode` type.

@@ 3-4
Dwarpal's mark, from the verify page's shell; and from the design system (§5.5.6) the badge and the button classes.

@@ 6-7
The console's pieces now come from the design system (`components/ui.tsx`). Re-exporting them here (`export { … } from`) means every console page keeps importing from `console-shell` — nothing else had to change.

@@ 8-9
The console's two buttons, named as before: `smallButton`, the main one, and `quietButton`, a secondary one with no background until hovered.

@@ 11-12
**`ConsoleShell`** — the frame of every console page: the content, and an optional `aside` for the header's right-hand side.

@@ 13-23
A centred column up to 5xl wide: the header (mark, name, the *Console* badge in the brand tone, then the aside pushed right by `ml-auto`), and the page's `main` content.

@@ 24
End of the component.
