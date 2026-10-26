---
fingerprint: 02a8423f9a4094b9
---
The **organisation page** (Phase 5, §5.5.1): its members, its projects and API keys, and — for owners and admins — its audit log, with whether the chain is intact. Forms appear only for roles that may use them (`CAN`); the API refuses anyway if someone forces them.

@@ 1
`"use client"`: this runs in the browser.

@@ 3-4
Next.js's `Link`, and React's form-event type and three hooks: `useCallback` (keep one copy of a function between showings), `useEffect` and `useState`.

@@ 6-14
The console's building blocks.

@@ 15-25
The client, the role checks, the error, and the types of everything this page shows.

@@ 27
One client for the page.

@@ 28
The roles a member may be given, least powerful first.

@@ 29
The four scopes a key may have.

@@ 31-38
**`Loaded`** — everything the page shows once loaded: who is signed in, their role here, the organisation's name, its members and projects, and the audit log (or `null` for roles that may not read it).

@@ 40-43
**`OrganisationView`**, and what it remembers: what was loaded — or `"signed-out"`, `"not-found"`, or `null` while loading — the current error, and a newly created key.

@@ 45-47
**`load`** — read everything. Nobody signed in: say so.

@@ 48-49
Find this organisation among the person's own. Not there: the same message as an organisation that doesn't exist.

@@ 50-54
Ask for the members, the projects and (if the role allows) the audit log **at the same time** (`Promise.all`), rather than one after another.

@@ 55
Remember it all.

@@ 56
`useCallback` keeps the same `load` unless the organisation changes, so the effect below runs once per organisation.

@@ 58-60
When the page appears, load; if anything fails, say so in plain words.

@@ 62-65
**`addMember`** — the add-member form was sent: read its fields.

@@ 66-70
Add the member, empty the form, and load again to show them.

@@ 71-73
A refusal shows the API's sentence; anything else a general one.

@@ 74
End of `addMember`.

@@ 76-79
**`createKey`** — the key form was sent.

@@ 80-83
Read every ticked scope (`getAll`), create the key, keep it to show **once**, and load again (the audit log now has a new line). The key lives only in this page's memory: a reload forgets it, and it is never stored in the browser.

@@ 84-86
A refusal shows the API's sentence.

@@ 87
End of `createKey`.

@@ 89-95
Still loading: *Loading…*, or the error if loading failed.

@@ 96-109
Signed out, or not a member: say which, with a link back to the console.

@@ 111
Everything was loaded: take its parts.

@@ 112-122
The frame, with a link back to all organisations and the person's address.

@@ 123-126
The organisation's name, and the person's role here.

@@ 127-131
The error, if any, announced to screen readers.

@@ 133
Two panels side by side on wide screens, one above the other on narrow ones.

@@ 134-137
**Members.** `aria-labelledby` names the section by its heading, so screen readers (and the tests) can find the region called "Members".

@@ 138-145
Each member's address and role.

@@ 146-164
For owners and admins, the form to add a member: an address and a role. Only an owner is offered *owner*, as only an owner may give it.

@@ 165
End of the members panel.

@@ 167-170
**Projects and API keys.**

@@ 171-183
Each project's name — since the project pages (§5.5.2), a link to its page — and its public ID.

@@ 184-194
A key just created, in a highlighted box: the warning that it won't be shown again, and the key itself. `role="status"` makes screen readers announce it.

@@ 195-205
For roles that may manage keys, and when there is a project: the form, starting with which project.

@@ 206-223
The scopes, as tick-boxes in a `fieldset` whose `legend` names the group; the two session scopes start ticked.

@@ 224-226
Whether the key is live — useful only once the age model is calibrated, which the API also enforces.

@@ 227-231
The button, and the end of the form.

@@ 232-233
End of the panel and of the two-column grid.

@@ 235-240
**The audit log**, for owners and admins.

@@ 241-249
The chain's verdict as a badge: teal *Chain intact*, or red *Chain broken at entry N* — the console's view of `cli verify-audit`.

@@ 250
End of the heading row.

@@ 251-259
A table with four columns: the entry's number, when, what, and who.

@@ 260-271
One row per entry, newest first; the time in the reader's own format and time zone (`toLocaleString`).

@@ 272-274
End of the table, the section, and the condition.

@@ 275-277
End of the frame and the component.
