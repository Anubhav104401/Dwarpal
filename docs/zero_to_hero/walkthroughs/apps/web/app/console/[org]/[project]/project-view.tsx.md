---
fingerprint: 093a9ccff245a00f
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
From `daily.ts`: `everyDay`, which turns the counts into one entry per day, and the order of the outcomes, shared with the chart.

@@ 29-30
The daily chart (§5.5.2) and the webhooks panel (§5.5.3), each in its own file.

@@ 32
One client for the page.

@@ 34-40
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies.

@@ 42-43
**`ScoreList`** — one attempt's numbers.

@@ 44-46
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 47-56
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 57-64
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 65-67
End of `ScoreList`.

@@ 69
**`ProjectView`** — the page, for one organisation's project.

@@ 70
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 71
The current search: none at first.

@@ 72
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 73-74
The trace being shown, if any; and an error message, if any.

@@ 76-79
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 80-85
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions — matching the search — and the policies. The counts and the sessions are for the chosen mode.

@@ 86
The project's name, or its ID if it isn't listed.

@@ 87
Remember it all.

@@ 88
End of `load`. `useCallback` keeps the same function until the organisation, the project, the mode or the search changes — and a new function makes the page load again.

@@ 90-93
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 95-102
**`more`** — the next page of sessions, after the cursor and matching the same search, added below the ones already shown.

@@ 104-110
**`searchSessions`** — the search form was sent: read its two fields, trimmed, with an empty one meaning any, and make that the search. Changing the search changes `load`, so the list starts again from the newest matching session.

@@ 112-115
**`addPolicy`** — the form was sent: stop the browser's own submission, and read the form's fields.

@@ 116
Clear any old message.

@@ 117-124
Ask the API for the new version: name, minimum age and face attempts — the last two turned from text into numbers.

@@ 125-126
Empty the form and reload, so the new version appears in the table.

@@ 127-129
A refusal shows the API's own words; anything else, a general message.

@@ 130
End of `addPolicy`.

@@ 132-138
While loading, "Loading…" — or the error, if loading failed.

@@ 139-150
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 152-158
The loaded values; and the counts as a list of (outcome, number) pairs, sorted into the chart's order of outcomes, so each total sits where its colour does in the legend. `rank` gives an outcome's place in that order; one it doesn't know (`indexOf` gives −1) goes after all the others.

@@ 159-166
The page, framed by the console, with a link back to the organisation.

@@ 167-171
The project's name as the heading, with its ID beneath.

@@ 172-173
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 174-178
One label each for test and live; the chosen one is drawn dark.

@@ 179-185
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 186-189
Its words, "Test" or "Live"; end of the switch.

@@ 190
End of the heading row.

@@ 191-195
The error, if there is one.

@@ 197-200
**Counts** — a panel headed "Last 30 days".

@@ 201-202
None yet: say so.

@@ 203-212
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 213
When there are counts, the chart beneath the tiles: the 30 days from the first day counted, each with its numbers.

@@ 214
End of the panel.

@@ 216
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 217-220
**Sessions** — a panel.

@@ 221-224
**The search form**: in a row on wider screens.

@@ 225-234
The outcome to look for, from a menu that starts with *Any* and then lists the outcomes in the same shared order (`OUTCOME_ORDER`, from `daily.ts`).

@@ 235-237
The website's reference, up to 200 characters, as the API allows.

@@ 238-241
The button, and the end of the form.

@@ 242-245
Nothing to show: "No sessions match." when searching, "No sessions yet." otherwise.

@@ 246-257
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 258-263
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 264-272
A **Trace** button: fetch this session's trace and show it.

@@ 273-277
End of the row and the table.

@@ 278-282
If there are older sessions, a button to show them.

@@ 283
End of the panel.

@@ 285-288
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 289-290
No session chosen yet: say what the panel is for.

@@ 291-298
Otherwise the session's ID, then its policy, status and outcome.

@@ 299-301
Its attempts, in order, each in a box.

@@ 302-305
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 306
Its numbers.

@@ 307-309
End of the attempt and the list.

@@ 310
A session with no attempts says so.

@@ 311-314
End of the trace, the panel and the side-by-side area.

@@ 316-319
**Policies** — a panel.

@@ 320-328
A table: the policy's label, its minimum age, its risk budget, and its face attempts.

@@ 329-334
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 335-337
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, and its attempts.

@@ 338-341
End of the row and the table.

@@ 342-343
**The add form** — only for roles that may manage policies (`CAN.managePolicies`); the API checks again.

@@ 344-346
The name: lower-case letters, digits and underscores, 3 to 40 characters, starting with a letter — the API's own rule, so the browser can say so before sending (`pattern`).

@@ 347-355
The minimum age, from a short list: 13, 16, 18 (chosen at first) or 21.

@@ 356-364
The face attempts, 1 to 5 (3 at first).

@@ 365-367
The button.

@@ 368-369
End of the form, if shown.

@@ 370
End of the policies panel.

@@ 372-374
**Webhooks** — for roles that may manage them, the panel, given the page's own client (it holds the CSRF token) and the current mode.

@@ 375-377
End of the page and `ProjectView`.
