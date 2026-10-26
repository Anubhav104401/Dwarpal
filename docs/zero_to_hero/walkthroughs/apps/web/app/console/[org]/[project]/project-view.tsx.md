---
fingerprint: 2e3a90384292affb
---
A project's page in the console (Phase 5, §5.5.2): its counts for the last 30 days, its sessions with each one's **decision trace** — why it ended as it did, down to the numbers — and its policies, with a form to add a version. A switch chooses test or live data. Everything comes from the console API; the page decides nothing about who may do what — it only hides a form the API would refuse.

@@ 1
`"use client"` — this file runs in the browser: it keeps state and answers clicks.

@@ 3-4
Next.js's `Link`, and React's tools: the type of a form's submit event, and the hooks for remembered functions, side effects and state.

@@ 6-14
The console's shared pieces (§5.5.1): an alert box, the page's frame, a labelled field, and the class names for inputs, panels and buttons.

@@ 15-24
The console client, its error type, the role table `CAN`, and the shapes of the answers this page reads.

@@ 26
One client for the page.

@@ 28-34
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies.

@@ 36-37
**`ScoreList`** — one attempt's numbers.

@@ 38-40
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 41-50
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 51-58
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 59-61
End of `ScoreList`.

@@ 63
**`ProjectView`** — the page, for one organisation's project.

@@ 64
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 65
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 66-67
The trace being shown, if any; and an error message, if any.

@@ 69-72
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 73-78
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions and the policies. The counts and the sessions are for the chosen mode.

@@ 79
The project's name, or its ID if it isn't listed.

@@ 80
Remember it all.

@@ 81
End of `load`. `useCallback` keeps the same function until the organisation, the project or the mode changes.

@@ 83-86
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 88-95
**`more`** — the next page of sessions, after the cursor, added below the ones already shown.

@@ 97-100
**`addPolicy`** — the form was sent: stop the browser's own submission, and read the form's fields.

@@ 101
Clear any old message.

@@ 102-109
Ask the API for the new version: name, minimum age and face attempts — the last two turned from text into numbers.

@@ 110-111
Empty the form and reload, so the new version appears in the table.

@@ 112-114
A refusal shows the API's own words; anything else, a general message.

@@ 115
End of `addPolicy`.

@@ 117-123
While loading, "Loading…" — or the error, if loading failed.

@@ 124-135
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 137-138
The loaded values; and the counts as a list of (outcome, number) pairs.

@@ 139-146
The page, framed by the console, with a link back to the organisation.

@@ 147-151
The project's name as the heading, with its ID beneath.

@@ 152-153
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 154-158
One label each for test and live; the chosen one is drawn dark.

@@ 159-165
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 166-169
Its words, "Test" or "Live"; end of the switch.

@@ 170
End of the heading row.

@@ 171-175
The error, if there is one.

@@ 177-180
**Counts** — a panel headed "Last 30 days".

@@ 181-182
None yet: say so.

@@ 183-192
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 193
End of the panel.

@@ 195
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 196-199
**Sessions** — a panel.

@@ 200-201
None yet: say so.

@@ 202-213
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 214-219
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 220-228
A **Trace** button: fetch this session's trace and show it.

@@ 229-233
End of the row and the table.

@@ 234-238
If there are older sessions, a button to show them.

@@ 239
End of the panel.

@@ 241-244
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 245-246
No session chosen yet: say what the panel is for.

@@ 247-254
Otherwise the session's ID, then its policy, status and outcome.

@@ 255-260
Its attempts, in order, each in a box.

@@ 261-264
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 265
Its numbers.

@@ 266-268
End of the attempt and the list.

@@ 269
A session with no attempts says so.

@@ 270-273
End of the trace, the panel and the side-by-side area.

@@ 275-278
**Policies** — a panel.

@@ 279-287
A table: the policy's label, its minimum age, its risk budget, and its face attempts.

@@ 288-294
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 295-297
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, and its attempts.

@@ 298-301
End of the row and the table.

@@ 302-303
**The add form** — only for roles that may manage policies (`CAN.managePolicies`); the API checks again.

@@ 304-306
The name: lower-case letters, digits and underscores, 3 to 40 characters, starting with a letter — the API's own rule, so the browser can say so before sending (`pattern`).

@@ 307-315
The minimum age, from a short list: 13, 16, 18 (chosen at first) or 21.

@@ 316-324
The face attempts, 1 to 5 (3 at first).

@@ 325-327
The button.

@@ 328-329
End of the form, if shown.

@@ 330-333
End of the panel, the page and `ProjectView`.
