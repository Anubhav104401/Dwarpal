---
fingerprint: 77a6424ead41d273
---
A project's page in the console (Phase 5, §5.5.2): its counts for the last 30 days, its sessions with each one's **decision trace** — why it ended as it did, down to the numbers — and its policies, with a form to add a version. A switch chooses test or live data. Everything comes from the console API; the page decides nothing about who may do what — it only hides a form the API would refuse.

@@ 1
`"use client"` — this file runs in the browser: it keeps state and answers clicks.

@@ 3-4
Next.js's `Link`, and React's tools: the type of a form's submit event, and the hooks for remembered functions, side effects and state.

@@ 6-14
The console's shared pieces (§5.5.1): an alert box, the page's frame, a labelled field, and the class names for inputs, panels and buttons.

@@ 15-25
The console client, its error type, the role table `CAN`, and the shapes of the answers this page reads — and of a session search.

@@ 27
The webhooks panel (§5.5.3), in its own file.

@@ 29
One client for the page.

@@ 30
The outcomes a search can ask for.

@@ 32-38
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies.

@@ 40-41
**`ScoreList`** — one attempt's numbers.

@@ 42-44
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 45-54
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 55-62
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 63-65
End of `ScoreList`.

@@ 67
**`ProjectView`** — the page, for one organisation's project.

@@ 68
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 69
The current search: none at first.

@@ 70
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 71-72
The trace being shown, if any; and an error message, if any.

@@ 74-77
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 78-83
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions — matching the search — and the policies. The counts and the sessions are for the chosen mode.

@@ 84
The project's name, or its ID if it isn't listed.

@@ 85
Remember it all.

@@ 86
End of `load`. `useCallback` keeps the same function until the organisation, the project, the mode or the search changes — and a new function makes the page load again.

@@ 88-91
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 93-100
**`more`** — the next page of sessions, after the cursor and matching the same search, added below the ones already shown.

@@ 102-108
**`searchSessions`** — the search form was sent: read its two fields, trimmed, with an empty one meaning any, and make that the search. Changing the search changes `load`, so the list starts again from the newest matching session.

@@ 110-113
**`addPolicy`** — the form was sent: stop the browser's own submission, and read the form's fields.

@@ 114
Clear any old message.

@@ 115-122
Ask the API for the new version: name, minimum age and face attempts — the last two turned from text into numbers.

@@ 123-124
Empty the form and reload, so the new version appears in the table.

@@ 125-127
A refusal shows the API's own words; anything else, a general message.

@@ 128
End of `addPolicy`.

@@ 130-136
While loading, "Loading…" — or the error, if loading failed.

@@ 137-148
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 150-151
The loaded values; and the counts as a list of (outcome, number) pairs.

@@ 152-159
The page, framed by the console, with a link back to the organisation.

@@ 160-164
The project's name as the heading, with its ID beneath.

@@ 165-166
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 167-171
One label each for test and live; the chosen one is drawn dark.

@@ 172-178
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 179-182
Its words, "Test" or "Live"; end of the switch.

@@ 183
End of the heading row.

@@ 184-188
The error, if there is one.

@@ 190-193
**Counts** — a panel headed "Last 30 days".

@@ 194-195
None yet: say so.

@@ 196-205
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 206
End of the panel.

@@ 208
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 209-212
**Sessions** — a panel.

@@ 213-216
**The search form**: in a row on wider screens.

@@ 217-226
The outcome to look for, from a menu that starts with *Any*.

@@ 227-229
The website's reference, up to 200 characters, as the API allows.

@@ 230-233
The button, and the end of the form.

@@ 234-237
Nothing to show: "No sessions match." when searching, "No sessions yet." otherwise.

@@ 238-249
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 250-255
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 256-264
A **Trace** button: fetch this session's trace and show it.

@@ 265-269
End of the row and the table.

@@ 270-274
If there are older sessions, a button to show them.

@@ 275
End of the panel.

@@ 277-280
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 281-282
No session chosen yet: say what the panel is for.

@@ 283-290
Otherwise the session's ID, then its policy, status and outcome.

@@ 291-293
Its attempts, in order, each in a box.

@@ 294-297
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 298
Its numbers.

@@ 299-301
End of the attempt and the list.

@@ 302
A session with no attempts says so.

@@ 303-306
End of the trace, the panel and the side-by-side area.

@@ 308-311
**Policies** — a panel.

@@ 312-320
A table: the policy's label, its minimum age, its risk budget, and its face attempts.

@@ 321-326
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 327-329
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, and its attempts.

@@ 330-333
End of the row and the table.

@@ 334-335
**The add form** — only for roles that may manage policies (`CAN.managePolicies`); the API checks again.

@@ 336-338
The name: lower-case letters, digits and underscores, 3 to 40 characters, starting with a letter — the API's own rule, so the browser can say so before sending (`pattern`).

@@ 339-347
The minimum age, from a short list: 13, 16, 18 (chosen at first) or 21.

@@ 348-356
The face attempts, 1 to 5 (3 at first).

@@ 357-359
The button.

@@ 360-361
End of the form, if shown.

@@ 362
End of the policies panel.

@@ 364-366
**Webhooks** — for roles that may manage them, the panel, given the page's own client (it holds the CSRF token) and the current mode.

@@ 367-369
End of the page and `ProjectView`.
