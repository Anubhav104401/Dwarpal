---
fingerprint: ef5c4141083a1648
---
The **organisation page** (Phase 5, §5.5.1): its members, its projects and API keys, and — for owners and admins — its audit log, with whether the chain is intact. Forms appear only for roles that may use them (`CAN`); the API refuses anyway if someone forces them.

@@ 1
`"use client"`: this runs in the browser.

@@ 3-4
Next.js's `Link`, and React's form-event type and three hooks: `useCallback` (keep one copy of a function between showings), `useEffect` and `useState`.

@@ 6-14
The console's building blocks.

@@ 15
The design system's badge, for the audit chain's verdict.

@@ 16-26
The client, the role checks, the error, and the types of everything this page shows.

@@ 28
One client for the page.

@@ 29
The roles a member may be given, least powerful first.

@@ 30
The four scopes a key may have.

@@ 32-39
**`Loaded`** — everything the page shows once loaded: who is signed in, their role here, the organisation's name, its members and projects, and the audit log (or `null` for roles that may not read it).

@@ 41-44
**`OrganisationView`**, and what it remembers: what was loaded — or `"signed-out"`, `"not-found"`, or `null` while loading — the current error, and a newly created key.

@@ 46-48
**`load`** — read everything. Nobody signed in: say so.

@@ 49-50
Find this organisation among the person's own. Not there: the same message as an organisation that doesn't exist.

@@ 51-55
Ask for the members, the projects and (if the role allows) the audit log **at the same time** (`Promise.all`), rather than one after another.

@@ 56
Remember it all.

@@ 57
`useCallback` keeps the same `load` unless the organisation changes, so the effect below runs once per organisation.

@@ 59-61
When the page appears, load; if anything fails, say so in plain words.

@@ 63-66
**`addMember`** — the add-member form was sent: read its fields.

@@ 67-71
Add the member, empty the form, and load again to show them.

@@ 72-74
A refusal shows the API's sentence; anything else a general one.

@@ 75
End of `addMember`.

@@ 77-86
**`changeMember`** (§5.5.4) — change a member's role, or remove them (`null`), then reload: the change may have been to one's own membership, which changes what the page may show — or whether it can show anything.

@@ 88-91
**`createKey`** — the key form was sent.

@@ 92-95
Read every ticked scope (`getAll`), create the key, keep it to show **once**, and load again (the audit log now has a new line). The key lives only in this page's memory: a reload forgets it, and it is never stored in the browser.

@@ 96-98
A refusal shows the API's sentence.

@@ 99
End of `createKey`.

@@ 101-107
Still loading: *Loading…*, or the error if loading failed.

@@ 108-121
Signed out, or not a member: say which, with a link back to the console.

@@ 123
Everything was loaded: take its parts.

@@ 124-134
The frame, with a link back to all organisations and the person's address.

@@ 135-138
The organisation's name, and the person's role here.

@@ 139-143
The error, if any, announced to screen readers.

@@ 145
Two panels side by side on wide screens, one above the other on narrow ones.

@@ 146-149
**Members.** `aria-labelledby` names the section by its heading, so screen readers (and the tests) can find the region called "Members".

@@ 150-153
The list of members: each one's address.

@@ 154
For people who may manage members, controls — except on an owner's row, unless they are an owner themselves (the API's rule, mirrored).

@@ 155-167
A role menu, named for screen readers after the member ("Role of ann@…"), showing their role; choosing another changes it at once. Only owners are offered "owner".

@@ 168-175
A *Remove* button, also named after the member, so a screen reader doesn't hear a list of identical "Remove" buttons.

@@ 176-179
Otherwise, just the role.

@@ 180-182
End of the row and the list.

@@ 183-201
For owners and admins, the form to add a member: an address and a role. Only an owner is offered *owner*, as only an owner may give it.

@@ 202
End of the members panel.

@@ 204-207
**Projects and API keys.**

@@ 208-220
Each project's name — since the project pages (§5.5.2), a link to its page — and its public ID.

@@ 221-231
A key just created, in a highlighted box: the warning that it won't be shown again, and the key itself. `role="status"` makes screen readers announce it.

@@ 232-242
For roles that may manage keys, and when there is a project: the form, starting with which project.

@@ 243-258
The scopes, as tick-boxes in a `fieldset` whose `legend` names the group; the two session scopes start ticked.

@@ 259-261
Whether the key is live — useful only once the age model is calibrated, which the API also enforces.

@@ 262-266
The button, and the end of the form.

@@ 267-268
End of the panel and of the two-column grid.

@@ 270-275
**The audit log**, for owners and admins.

@@ 276-278
The chain's verdict as a **badge** from the design system (§5.5.6): *Chain intact* in the success tone, or *Chain broken at entry N* in the danger tone — the console's view of `cli verify-audit`.

@@ 279
End of the heading row.

@@ 280-288
A table with four columns: the entry's number, when, what, and who.

@@ 289-300
One row per entry, newest first; the time in the reader's own format and time zone (`toLocaleString`).

@@ 301-303
End of the table, the section, and the condition.

@@ 304-306
End of the frame and the component.
