---
fingerprint: 2cf3006d7f1e5aa5
---
The console's **frame and building blocks** (Phase 5): the page frame with the Dwarpal mark, a "Console" badge, and room for who is signed in; for a signed-in person, the sidebar of places and the command palette (§5.5.6); and the console's pieces — buttons, panel, input, field, alert — which come from the design system (`components/ui.tsx`) and are passed on from here under their old names.

@@ 1
The frame now runs in the browser: it knows the current address, listens for a key and opens the palette.

@@ 3-5
Links between pages; `usePathname`, which gives the current address; React's `ReactNode` type and its state and effect hooks.

@@ 7
The console's fixed places, shared with the palette (`lib/places.ts`).

@@ 9
The command palette.

@@ 10-11
Dwarpal's mark, from the verify page's shell; and from the design system (§5.5.6) the badge and the button classes.

@@ 13-14
The console's pieces now come from the design system (`components/ui.tsx`). Re-exporting them here (`export { … } from`) means every console page keeps importing from `console-shell` — nothing else had to change.

@@ 15-16
The console's two buttons, named as before: `smallButton`, the main one, and `quietButton`, a secondary one with no background until hovered.

@@ 18-28
**`ConsoleShell`** — the frame of every console page: the content, an optional `aside` for the header's right-hand side, and `signedIn`, which pages set once they know someone is signed in. Signed out, there is nowhere to go, so no sidebar or palette.

@@ 29-31
The current address, for marking the current place; whether the palette is open; and the shortcut's name to show, "Ctrl K" to begin with.

@@ 33-35
Once the page is in the browser, a Mac (or iPhone or iPad) gets "⌘K" instead. It is set after the page starts, not while it is drawn, so the server's version and the browser's first one agree — otherwise React would warn of a *hydration mismatch*.

@@ 37-47
**The shortcut**, only when signed in: listen for keys on the whole window; ⌘K or Ctrl+K (`metaKey` is the ⌘ key) opens the palette, and `preventDefault` stops the browser's own use of the combination (in some browsers, its search bar). The function returned stops listening when the page goes away.

@@ 49-50
A centred column up to 6xl wide — a little wider than before, to make room for the sidebar.

@@ 51-56
The header: mark, name, the *Console* badge in the brand tone, then the aside pushed right by `ml-auto`.

@@ 57
Signed in, the area below becomes, on large screens (`lg:`), a grid of two columns: a 12rem sidebar and the page. On smaller screens it stays one column, so the sidebar sits above the page.

@@ 58-59
**The sidebar**, a `nav` named "Console" for screen readers.

@@ 60-67
At its top, a button that opens the palette, showing the shortcut in a `kbd` element (HTML's element for keys to press).

@@ 68-80
The places, one link each. The current one is marked `aria-current="page"`, which tells screen readers "you are here", and the same attribute styles it (`aria-[current=page]:`), so the look and the meaning can't drift apart. On small screens the list is a row that scrolls sideways if needed; on large ones, a column.

@@ 81-82
The end of the list and the sidebar.

@@ 83
The page's own content. `min-w-0` lets a wide table inside scroll in its own box instead of stretching the grid.

@@ 84
The end of the area.

@@ 85
Signed in, the palette, closed until asked for.

@@ 86-88
The end of the frame and the component.
