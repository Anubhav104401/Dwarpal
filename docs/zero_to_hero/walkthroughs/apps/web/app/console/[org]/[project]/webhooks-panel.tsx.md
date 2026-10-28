---
fingerprint: f183fc51a168f55e
---
The webhooks panel of a project's page (Phase 5, §5.5.3): the endpoints for the chosen mode, a form to add one — whose signing secret is shown **once** — and, for each, buttons to send a test event, see its recent deliveries (and replay a finished one), or remove it.

@@ 1
`"use client"` — it runs in the browser.

@@ 3
React's tools: the form event's type, and the hooks.

@@ 5
The console's shared pieces: the alert, a labelled field, and class names.

@@ 6
The design system's badge, to mark an endpoint that is off.

@@ 7-13
The client's type, its error, and the shapes and event types this panel uses.

@@ 15
**`Props`** — what the page passes in: its client (the one holding the CSRF token — a second client would have none), the organisation, the project, and the mode.

@@ 17-18
**`WebhooksPanel`**.

@@ 19-22
Its state: the endpoints (`null` while loading), a just-shown secret, the deliveries being shown (and whose), and an error.

@@ 24-26
**`load`** — read the endpoints for this mode.

@@ 28-32
On arrival and whenever the mode changes: forget any shown secret and deliveries, and load. A failure becomes a message.

@@ 34-41
**`attempt`** — run one piece of work, clearing the old error first; a refusal shows the API's own words, anything else a general message. Every button goes through it.

@@ 43-45
**`showDeliveries`** — fetch and show one endpoint's deliveries.

@@ 47-50
**`add`** — the form was sent: stop the browser's own submission, and read the fields.

@@ 51-54
Collect the ticked events (`getAll`: a checkbox group sends one value per ticked box), create the endpoint, and empty the form.

@@ 55-58
Show its secret, and reload the list.

@@ 60-64
**`sendTest`** — queue a test event, then show the endpoint's deliveries, where it now waits.

@@ 66-70
**`switchTo`** — switch an endpoint on or off, then reload the list.

@@ 72-77
**`remove`** — delete the endpoint; if its deliveries were showing, hide them; reload.

@@ 79-83
**`replay`** — send a delivery again, and show the deliveries afresh.

@@ 85-89
The panel, named by its heading "Webhooks".

@@ 90-93
What webhooks are for, in this mode, and that every request is signed.

@@ 94-98
The error, if any.

@@ 99-108
**The secret**, if one was just made, announced (`role="status"`), with a warning that it won't be shown again. Like a new key, after a reload only its sealed form exists — on the server.

@@ 110-114
Loading, or none yet.

@@ 115-123
Otherwise a list: each endpoint's address — with an *Off* badge if it is switched off — and its events.

@@ 124-141
Its four buttons: Send test, Deliveries, *Switch off* or *Switch on* (whichever it isn't), and Remove.

@@ 142-145
End of the endpoint and the list.

@@ 147-149
**Deliveries**, when asked for, under a small heading. `aria-live` announces them when they change.

@@ 150-151
None yet: say so.

@@ 152-164
Otherwise a table, named "Recent deliveries" (`aria-label`): when it was made, its status, its tries, the receiver's last answer, and a column for the buttons.

@@ 165-171
One row per delivery: its time, status, tries, and the last answer — the status code, or the error, or a dash.

@@ 172-182
A **Replay** button — except for a pending delivery, which is going to be tried anyway.

@@ 183-189
End of the row, the table and the deliveries.

@@ 191-201
**The add form**: the address, with `type="url"` so the browser checks its shape first; the API checks again, and refuses an unsafe one (§5.4.3).

@@ 202-210
The events, one checkbox each, all ticked at first, inside a `fieldset` named "Events". Each row is at least 32 pixels tall (`min-h-8`), so the two boxes sit far enough apart for a finger: WCAG 2.2 asks that small targets have room around them, and the accessibility test (§5.5.5) found they didn't.

@@ 211-214
The button, and the end of the form.

@@ 215-217
End of the panel.
