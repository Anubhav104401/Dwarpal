---
fingerprint: f43dfb397eed70e8
---
The webhooks panel of a project's page (Phase 5, §5.5.3): the endpoints for the chosen mode, a form to add one — whose signing secret is shown **once** — and, for each, buttons to send a test event, see its recent deliveries (and replay a finished one), or remove it.

@@ 1
`"use client"` — it runs in the browser.

@@ 3
React's tools: the form event's type, and the hooks.

@@ 5
The console's shared pieces: the alert, a labelled field, and class names.

@@ 6-12
The client's type, its error, and the shapes and event types this panel uses.

@@ 14
**`Props`** — what the page passes in: its client (the one holding the CSRF token — a second client would have none), the organisation, the project, and the mode.

@@ 16-17
**`WebhooksPanel`**.

@@ 18-21
Its state: the endpoints (`null` while loading), a just-shown secret, the deliveries being shown (and whose), and an error.

@@ 23-25
**`load`** — read the endpoints for this mode.

@@ 27-31
On arrival and whenever the mode changes: forget any shown secret and deliveries, and load. A failure becomes a message.

@@ 33-40
**`attempt`** — run one piece of work, clearing the old error first; a refusal shows the API's own words, anything else a general message. Every button goes through it.

@@ 42-44
**`showDeliveries`** — fetch and show one endpoint's deliveries.

@@ 46-49
**`add`** — the form was sent: stop the browser's own submission, and read the fields.

@@ 50-53
Collect the ticked events (`getAll`: a checkbox group sends one value per ticked box), create the endpoint, and empty the form.

@@ 54-57
Show its secret, and reload the list.

@@ 59-63
**`sendTest`** — queue a test event, then show the endpoint's deliveries, where it now waits.

@@ 65-70
**`remove`** — delete the endpoint; if its deliveries were showing, hide them; reload.

@@ 72-76
**`replay`** — send a delivery again, and show the deliveries afresh.

@@ 78-82
The panel, named by its heading "Webhooks".

@@ 83-86
What webhooks are for, in this mode, and that every request is signed.

@@ 87-91
The error, if any.

@@ 92-101
**The secret**, if one was just made, announced (`role="status"`), with a warning that it won't be shown again. Like a new key, after a reload only its sealed form exists — on the server.

@@ 103-106
Loading, or none yet.

@@ 107-114
Otherwise a list: each endpoint's address and its events.

@@ 115-129
Its three buttons: Send test, Deliveries, Remove.

@@ 130-133
End of the endpoint and the list.

@@ 135-137
**Deliveries**, when asked for, under a small heading. `aria-live` announces them when they change.

@@ 138-139
None yet: say so.

@@ 140-152
Otherwise a table, named "Recent deliveries" (`aria-label`): when it was made, its status, its tries, the receiver's last answer, and a column for the buttons.

@@ 153-159
One row per delivery: its time, status, tries, and the last answer — the status code, or the error, or a dash.

@@ 160-170
A **Replay** button — except for a pending delivery, which is going to be tried anyway.

@@ 171-177
End of the row, the table and the deliveries.

@@ 179-189
**The add form**: the address, with `type="url"` so the browser checks its shape first; the API checks again, and refuses an unsafe one (§5.4.3).

@@ 190-198
The events, one checkbox each, all ticked at first, inside a `fieldset` named "Events". Each row is at least 32 pixels tall (`min-h-8`), so the two boxes sit far enough apart for a finger: WCAG 2.2 asks that small targets have room around them, and the accessibility test (§5.5.5) found they didn't.

@@ 199-202
The button, and the end of the form.

@@ 203-205
End of the panel.
