---
fingerprint: 7a8bca633e1c3deb
---
**A project's settings** (decisions D28, D29, 8 Nov 2026): its name and allowed origins, on its page.

@@ 1
A component that runs in the browser (it keeps state and answers clicks).

@@ 3-7
React's types and state; the console's shared pieces; the client and its types; `originLines`.

@@ 9-15
What the panel is given: the client, the organisation, the project as listed, whether this person may change it, and what to do after a save.

@@ 17-19
**`SettingsPanel`** (decisions D28, D29) — a project's name and the origins its websites run on.

@@ 20-21
An error to show, and whether to say *Saved.*

@@ 23-27
**`save`** — the form's values, with earlier messages cleared.

@@ 28-32
The new name, trimmed, and the origins, one per line, sent together.

@@ 33-34
The page loads again, then *Saved.* is shown.

@@ 35-38
A refusal — such as an origin that isn't one — is shown in the API's own words.

@@ 40-48
The panel: its heading, and what allowed origins are for and what one looks like.

@@ 49-53
An error, if there is one.

@@ 54-60
For owners and admins, a form. Its `key` is what is stored: after a save, React makes it again, so it shows the origins as the API wrote them (`HTTPS://Shop.Example/` comes back as `https://shop.example`).

@@ 61-70
The name, filled in, required, at most 80 characters.

@@ 71-79
The origins, one per line, in a monospaced box.

@@ 80-89
The button, and *Saved.* — announced to screen readers (`role="status"`).

@@ 90-99
For the other roles, the origins as a list — or a note that there are none.

@@ 100-102
End of the panel and of the component.
