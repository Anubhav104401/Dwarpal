---
fingerprint: a5e1c5f7bcce1187
---
**The command palette** (§5.5.6): a search box, opened with ⌘K or Ctrl+K or the sidebar's *Go to…* button, that finds any organisation, project or page by typing a few letters. It is deliberately simple for assistive technology: a search box and a list of ordinary links, inside the browser's own modal dialog.

@@ 1
It runs in the browser.

@@ 3-5
Links; Next.js's router, to change page from code; and React's keyboard-event type and hooks — including `useRef`, which holds a reference to an element on the page.

@@ 7-8
The console client, and the places with their search.

@@ 10
The design system's input style.

@@ 12
One client for the palette.

@@ 14-15
**`everyPlace`** — everything there is to search.

@@ 16-17
Who is signed in; if no one is, just the fixed places.

@@ 18-20
For each organisation, at the same time (`Promise.all`), ask for its projects. If one organisation's projects can't be read, it just contributes none, rather than spoiling the whole search.

@@ 21-28
The organisation itself, then each project, with an address and a hint naming the organisation it belongs to.

@@ 29-32
The fixed places first, then all the organisations and projects in one flat list.

@@ 34-36
**`CommandPalette`** — told whether to be `open`, and what to do when it closes.

@@ 37-38
References to the dialog element and the list of results.

@@ 39-40
The places to search (the fixed ones until the rest arrive) and what has been typed.

@@ 41-42
The router; and the places that match, worked out afresh each time something is typed.

@@ 44-46
Whenever `open` changes, act on the dialog element.

@@ 47-52
Opening: clear the box, show the dialog as **modal** — the rest of the page can't be clicked or tabbed to, focus moves into the dialog (onto the search box, its first control), and Escape closes it — then load every place, falling back to the fixed ones if that fails. It is loaded on each opening, so a new project shows up without reloading the page.

@@ 53-56
Closing from outside: close the dialog.

@@ 58-62
**`go`** — close the palette and go to a place, if there is one.

@@ 64-67
In the search box, Enter goes to the first result.

@@ 68-72
The down arrow moves the focus onto the first result's link.

@@ 74-76
In the list, only the up and down arrows matter; they don't scroll the page.

@@ 77-79
Find which link has the focus and which comes next. `[...]` turns the browser's list of elements into an ordinary array.

@@ 80-82
Above the first link, back to the search box; otherwise the next link, stopping at the last.

@@ 84-90
**The dialog**, named "Go to" for screen readers. When it closes — by Escape, or otherwise — the page is told (`onClose`). It sits 15 % down the screen, at most 36rem wide (and always 1rem clear of a phone's edges), with the page behind dimmed by its `backdrop`.

@@ 91-101
The search box, named for screen readers, with a placeholder saying what it searches. Each keystroke updates `typed`; Enter and the down arrow are handled above.

@@ 102-104
No match: say so.

@@ 105
Otherwise the results, as a list named "Results", with the arrow keys handled.

@@ 106-112
One link per place. Clicking it closes the palette while the link changes the page. Hovering or focusing a link shades it, and focus from the keyboard also draws a brand-coloured outline just inside its edge (`focus-visible`, which leaves mouse clicks alone).

@@ 113-114
The place's name, and its hint in smaller, quieter text, cut short with "…" if it is too long (`truncate`).

@@ 115-122
The end of the link, the list, the dialog and the function.
