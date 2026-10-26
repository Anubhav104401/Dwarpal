---
fingerprint: 4b70e6e1ff60190d
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
The webhooks panel (§5.5.3), in its own file.

@@ 28
One client for the page.

@@ 30-36
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies.

@@ 38-39
**`ScoreList`** — one attempt's numbers.

@@ 40-42
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 43-52
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 53-60
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 61-63
End of `ScoreList`.

@@ 65
**`ProjectView`** — the page, for one organisation's project.

@@ 66
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 67
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 68-69
The trace being shown, if any; and an error message, if any.

@@ 71-74
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 75-80
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions and the policies. The counts and the sessions are for the chosen mode.

@@ 81
The project's name, or its ID if it isn't listed.

@@ 82
Remember it all.

@@ 83
End of `load`. `useCallback` keeps the same function until the organisation, the project or the mode changes.

@@ 85-88
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 90-97
**`more`** — the next page of sessions, after the cursor, added below the ones already shown.

@@ 99-102
**`addPolicy`** — the form was sent: stop the browser's own submission, and read the form's fields.

@@ 103
Clear any old message.

@@ 104-111
Ask the API for the new version: name, minimum age and face attempts — the last two turned from text into numbers.

@@ 112-113
Empty the form and reload, so the new version appears in the table.

@@ 114-116
A refusal shows the API's own words; anything else, a general message.

@@ 117
End of `addPolicy`.

@@ 119-125
While loading, "Loading…" — or the error, if loading failed.

@@ 126-137
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 139-140
The loaded values; and the counts as a list of (outcome, number) pairs.

@@ 141-148
The page, framed by the console, with a link back to the organisation.

@@ 149-153
The project's name as the heading, with its ID beneath.

@@ 154-155
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 156-160
One label each for test and live; the chosen one is drawn dark.

@@ 161-167
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 168-171
Its words, "Test" or "Live"; end of the switch.

@@ 172
End of the heading row.

@@ 173-177
The error, if there is one.

@@ 179-182
**Counts** — a panel headed "Last 30 days".

@@ 183-184
None yet: say so.

@@ 185-194
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 195
End of the panel.

@@ 197
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 198-201
**Sessions** — a panel.

@@ 202-203
None yet: say so.

@@ 204-215
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 216-221
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 222-230
A **Trace** button: fetch this session's trace and show it.

@@ 231-235
End of the row and the table.

@@ 236-240
If there are older sessions, a button to show them.

@@ 241
End of the panel.

@@ 243-246
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 247-248
No session chosen yet: say what the panel is for.

@@ 249-256
Otherwise the session's ID, then its policy, status and outcome.

@@ 257-262
Its attempts, in order, each in a box.

@@ 263-266
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 267
Its numbers.

@@ 268-270
End of the attempt and the list.

@@ 271
A session with no attempts says so.

@@ 272-275
End of the trace, the panel and the side-by-side area.

@@ 277-280
**Policies** — a panel.

@@ 281-289
A table: the policy's label, its minimum age, its risk budget, and its face attempts.

@@ 290-296
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 297-299
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, and its attempts.

@@ 300-303
End of the row and the table.

@@ 304-305
**The add form** — only for roles that may manage policies (`CAN.managePolicies`); the API checks again.

@@ 306-308
The name: lower-case letters, digits and underscores, 3 to 40 characters, starting with a letter — the API's own rule, so the browser can say so before sending (`pattern`).

@@ 309-317
The minimum age, from a short list: 13, 16, 18 (chosen at first) or 21.

@@ 318-326
The face attempts, 1 to 5 (3 at first).

@@ 327-329
The button.

@@ 330-331
End of the form, if shown.

@@ 332
End of the policies panel.

@@ 334-336
**Webhooks** — for roles that may manage them, the panel, given the page's own client (it holds the CSRF token) and the current mode.

@@ 337-339
End of the page and `ProjectView`.
