---
fingerprint: 548c9652e27d1ae1
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

@@ 16-27
The client, the role checks, the error, and the types of everything this page shows — since 8 Nov including invitations.

@@ 30
One client for the page.

@@ 31
The roles a member may be given, least powerful first.

@@ 32
The four scopes a key may have.

@@ 34-43
**`Loaded`** — everything the page shows once loaded: who is signed in, their role here, the organisation's name, its members and projects, and the audit log (or `null` for roles that may not read it). Since 8 Nov also the invitations still waiting (decision D44), for those who manage members — an empty list for the others.

@@ 45-48
**`OrganisationView`**, and what it remembers: what was loaded — or `"signed-out"`, `"not-found"`, or `null` while loading — the current error, and a newly created key.

@@ 51-53
**`load`** — read everything. Nobody signed in: say so.

@@ 54-55
Find this organisation among the person's own. Not there: the same message as an organisation that doesn't exist.

@@ 56-61
Ask for the members, the invitations (for roles that manage members), the projects and (if the role allows) the audit log **at the same time** (`Promise.all`), rather than one after another.

@@ 62
Remember it all.

@@ 63
`useCallback` keeps the same `load` unless the organisation changes, so the effect below runs once per organisation.

@@ 65-67
When the page appears, load; if anything fails, say so in plain words.

@@ 69-72
**`addMember`** — the add-member form was sent: read its fields.

@@ 124-127
**`createKey`** — the key form was sent.

@@ 128-131
Read every ticked scope (`getAll`), create the key, keep it to show **once**, and load again (the audit log now has a new line). The key lives only in this page's memory: a reload forgets it, and it is never stored in the browser.

@@ 132-134
A refusal shows the API's sentence.

@@ 135
End of `createKey`.

@@ 137-143
Still loading: *Loading…*, or the error if loading failed.

@@ 144-157
Signed out, or not a member: say which, with a link back to the console.

@@ 159
Everything was loaded: take its parts.

@@ 160-171
The frame, with its sidebar (`signedIn`), a link back to all organisations and the person's address.

@@ 172-175
The organisation's name, and the person's role here.

@@ 176-180
The error, if any, announced to screen readers.

@@ 182
Two panels side by side on wide screens, one above the other on narrow ones.

@@ 183-186
**Members.** `aria-labelledby` names the section by its heading, so screen readers (and the tests) can find the region called "Members".

@@ 187-190
The list of members: each one's address.

@@ 191
For people who may manage members, controls — except on an owner's row, unless they are an owner themselves (the API's rule, mirrored).

@@ 192-204
A role menu, named for screen readers after the member ("Role of ann@…"), showing their role; choosing another changes it at once. Only owners are offered "owner".

@@ 205-212
A *Remove* button, also named after the member, so a screen reader doesn't hear a list of identical "Remove" buttons.

@@ 213-216
Otherwise, just the role.

@@ 217-219
End of the row and the list.

@@ 248-266
For owners and admins, the form to add a member: an address and a role. Only an owner is offered *owner*, as only an owner may give it.

@@ 267
End of the members panel.

@@ 269-272
**Projects and API keys.**

@@ 273-290
Each project's name — since the project pages (§5.5.2), a link to its page — its public ID, and its allowed origins, or (with none yet) where to add them: until it has some, a check can't return to the website (decision D29).

@@ 312-322
A key just created, in a highlighted box: the warning that it won't be shown again, and the key itself. `role="status"` makes screen readers announce it.

@@ 323-333
For roles that may manage keys, and when there is a project: the form, starting with which project.

@@ 334-349
The scopes, as tick-boxes in a `fieldset` whose `legend` names the group; the two session scopes start ticked.

@@ 350-353
Whether the key is live. Until an age model is certified, live checks are decided by an ID document (D24), and the label says so.

@@ 354-358
The button, and the end of the form.

@@ 359-360
End of the panel and of the two-column grid.

@@ 362-367
**The audit log**, for owners and admins.

@@ 368-370
The chain's verdict as a **badge** from the design system (§5.5.6): *Chain intact* in the success tone, or *Chain broken at entry N* in the danger tone — the console's view of `cli verify-audit`.

@@ 371
End of the heading row.

@@ 372-380
A table with four columns: the entry's number, when, what, and who.

@@ 381-392
One row per entry, newest first; the time in the reader's own format and time zone (`toLocaleString`).

@@ 393-395
End of the table, the section, and the condition.

@@ 396-398
End of the frame and the component.

@@ 28
**`originLines`** (`lib/origins.ts`) — the allowed-origins box's lines, as the API takes them.

@@ 49
**`invited`** — the address the last *Add* invited, if it invited someone: the page says so.

@@ 73-81
Clear any earlier error or notice. Then add the member — or, for an address without an account, the API invites them instead (decision D44), and the page notes the address to say so — empty the form, and load again.

@@ 82-85
A refusal is shown in words.

@@ 87-95
**`cancelInvitation`** — withdraw an invitation, then load again.

@@ 97-106
**`changeMember`** (§5.5.4) — change a member's role, or remove them (`null`), then reload: the change may have been to one's own membership, which changes what the page may show — or whether it can show anything.

@@ 108-122
**`createProject`** (decisions D28, D29) — a new project: its name, and its allowed origins typed one per line (`originLines`), checked by the API; then the form is emptied and the page loads again.

@@ 220-241
**Invitations still waiting** (decision D44): each address with its role, and a button to cancel it (its label names the address, for screen readers).

@@ 242-247
After an invitation, the notice: no account yet, so they are invited, and join on signing up with that address — and since no e-mail is sent (D25), the person adding them should tell them.

@@ 291-311
**A new project**, for owners and admins: folded away (`<details>`) until wanted — its name, and its allowed origins, one per line.
