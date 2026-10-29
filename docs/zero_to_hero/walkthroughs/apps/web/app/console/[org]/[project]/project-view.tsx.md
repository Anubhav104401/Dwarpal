---
fingerprint: 88e3e5ea1a6d500c
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

@@ 30-31
The daily chart (§5.5.2) and the webhooks panel (§5.5.3), each in its own file.

@@ 33
One client for the page.

@@ 35-41
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies.

@@ 43-44
**`ScoreList`** — one attempt's numbers.

@@ 45-47
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 48-57
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 58-65
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 102-104
The end of the box and of `FaceFigures`.

@@ 106
**`ProjectView`** — the page, for one organisation's project.

@@ 107
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 108
The current search: none at first.

@@ 109
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 110-111
The trace being shown, if any; and an error message, if any.

@@ 113-116
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 117-122
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions — matching the search — and the policies. The counts and the sessions are for the chosen mode.

@@ 123
The project's name, or its ID if it isn't listed.

@@ 124
Remember it all.

@@ 125
End of `load`. `useCallback` keeps the same function until the organisation, the project, the mode or the search changes — and a new function makes the page load again.

@@ 127-130
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 132-139
**`more`** — the next page of sessions, after the cursor and matching the same search, added below the ones already shown.

@@ 141-147
**`searchSessions`** — the search form was sent: read its two fields, trimmed, with an empty one meaning any, and make that the search. Changing the search changes `load`, so the list starts again from the newest matching session.

@@ 149-152
**`addPolicy`** — the form was sent: stop the browser's own submission, and read the form's fields.

@@ 153
Clear any old message.

@@ 154-161
Ask the API for the new version: name, minimum age and face attempts — the last two turned from text into numbers.

@@ 162-163
Empty the form and reload, so the new version appears in the table.

@@ 164-166
A refusal shows the API's own words; anything else, a general message.

@@ 167
End of `addPolicy`.

@@ 169-175
While loading, "Loading…" — or the error, if loading failed.

@@ 176-187
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 189-195
The loaded values; and the counts as a list of (outcome, number) pairs, sorted into the chart's order of outcomes, so each total sits where its colour does in the legend. `rank` gives an outcome's place in that order; one it doesn't know (`indexOf` gives −1) goes after all the others.

@@ 196-204
The page, framed by the console with its sidebar (`signedIn`), and a link back to the organisation.

@@ 205-209
The project's name as the heading, with its ID beneath.

@@ 210-211
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 212-216
One label each for test and live; the chosen one is drawn dark.

@@ 217-223
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 224-227
Its words, "Test" or "Live"; end of the switch.

@@ 228
End of the heading row.

@@ 229-233
The error, if there is one.

@@ 235-238
**Counts** — a panel headed "Last 30 days".

@@ 239-240
None yet: say so.

@@ 241-250
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 252
When there are counts, the chart beneath the tiles: the 30 days from the first day counted, each with its numbers.

@@ 253
End of the panel.

@@ 255
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 256-259
**Sessions** — a panel.

@@ 260-263
**The search form**: in a row on wider screens.

@@ 264-273
The outcome to look for, from a menu that starts with *Any* and then lists the outcomes in the same shared order (`OUTCOME_ORDER`, from `daily.ts`).

@@ 274-276
The website's reference, up to 200 characters, as the API allows.

@@ 277-280
The button, and the end of the form.

@@ 281-284
Nothing to show: "No sessions match." when searching, "No sessions yet." otherwise.

@@ 285-296
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 297-302
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 303-311
A **Trace** button: fetch this session's trace and show it.

@@ 312-316
End of the row and the table.

@@ 317-321
If there are older sessions, a button to show them.

@@ 322
End of the panel.

@@ 324-327
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 328-329
No session chosen yet: say what the panel is for.

@@ 330-337
Otherwise the session's ID, then its policy, status and outcome.

@@ 338-340
Its attempts, in order, each in a box.

@@ 341-344
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 345
Its numbers.

@@ 346-348
End of the attempt and the list.

@@ 349
A session with no attempts says so.

@@ 350-353
End of the trace, the panel and the side-by-side area.

@@ 355-358
**Policies** — a panel.

@@ 359-367
A table: the policy's label, its minimum age, its risk budget, and its face attempts.

@@ 368-373
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 374-376
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, and its attempts.

@@ 377-380
End of the row and the table.

@@ 381-382
**The add form** — only for roles that may manage policies (`CAN.managePolicies`); the API checks again.

@@ 383-385
The name: lower-case letters, digits and underscores, 3 to 40 characters, starting with a letter — the API's own rule, so the browser can say so before sending (`pattern`).

@@ 386-394
The minimum age, from a short list: 13, 16, 18 (chosen at first) or 21.

@@ 395-403
The face attempts, 1 to 5 (3 at first).

@@ 404-406
The button.

@@ 407-408
End of the form, if shown.

@@ 409
End of the policies panel.

@@ 411-413
**Webhooks** — for roles that may manage them, the panel, given the page's own client (it holds the CSRF token) and the current mode.

@@ 414-416
End of the page and `ProjectView`.

@@ 28
The face checks' figures in words (`lib/figures.ts`).

@@ 66-68
The end of the wrapper and of `ScoreList`.

@@ 70-72
**`FaceFigures`** — the face checks' three headline figures, which the design's dashboard asks for.

@@ 73-84
The median time to a decision, as a band ("10–15 s"), and whether the whole band is within the 15-second target; a dash before anything has been decided.

@@ 85-87
The share of decided checks rejected as a likely attack (a failed liveness check or signs of tampering), and the share sent to a stronger check because the age estimate was unsure.

@@ 88-92
A small heading, with how many face checks the figures are based on — a percentage of 3 means little.

@@ 93-101
The figures as a description list (`dl`): each name (`dt`) with its value and note (`dd`), in a box. On a phone they stack; from the `sm` width, three side by side.

@@ 251
Under the totals, the face checks' figures — once at least one has been decided.
