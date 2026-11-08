---
fingerprint: 18cd8b725c32050a
---
**A project's API keys** (decision D30, 8 Nov 2026): listed without their secrets, and stopped at once.

@@ 1
A component that runs in the browser.

@@ 3-7
React's state and effects; the console's shared pieces and a badge; the client and its types.

@@ 9
What the panel is given: the client, the organisation and the project.

@@ 11
The badge's look for each state a key may end in.

@@ 13-15
**`KeysPanel`** (decision D30) — a project's keys, and a button to stop one.

@@ 16-17
The keys (`null` until loaded), and an error to show.

@@ 19-25
Load the keys when the panel appears; if that fails, say so.

@@ 27-28
**`revoke`** — asks first (`window.confirm`): stopping a key can't be undone, and anything using it will be refused.

@@ 29-36
Then stop it and load the keys again; a refusal is shown in words.

@@ 38-46
The panel: its heading, and that a key's secret is shown only once — so a key that may have leaked is stopped here and replaced.

@@ 47-51
An error, if there is one.

@@ 52-55
Loading, or no keys yet…

@@ 56-68
…or a table: the key's public ID, its mode, scopes, when it was made, and (for screen readers only) a heading for its state.

@@ 69-77
One row a key: the public ID, *Live* or *Test*, the scopes, and the date it was made.

@@ 78-90
An active key gets a *Stop* button, whose label names the key; a stopped or expired one, a badge.

@@ 91-99
Ends of the row, the table, the panel and the component.
