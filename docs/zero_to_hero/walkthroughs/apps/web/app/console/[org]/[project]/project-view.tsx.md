---
fingerprint: 37e7b8b27a029cb4
---
A project's page in the console (Phase 5, §5.5.2): its counts for the last 30 days, its sessions with each one's **decision trace** — why it ended as it did, down to the numbers — and its policies, with a form to add a version. A switch chooses test or live data. Everything comes from the console API; the page decides nothing about who may do what — it only hides a form the API would refuse.

@@ 1
`"use client"` — this file runs in the browser: it keeps state and answers clicks.

@@ 3-4
Next.js's `Link`, and React's tools: the type of a form's submit event, and the hooks for remembered functions, side effects and state.

@@ 6
The console's shared pieces (§5.5.1): an alert box, the page's frame, a labelled field, and the class names for inputs, panels and quiet buttons.

@@ 7-16
The console client, the role table `CAN`, and the shapes of the answers this page reads — and of a session search.

@@ 18
From `daily.ts`: `everyDay`, which turns the counts into one entry per day, and the order of the outcomes, shared with the chart.

@@ 21-23
The daily chart (§5.5.2), the policy editor (§5.5.8) and the webhooks panel (§5.5.3), each in its own file.

@@ 25
One client for the page.

@@ 27-33
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies.

@@ 35-36
**`ScoreList`** — one attempt's numbers.

@@ 37-39
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 40-49
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 50-57
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 94-96
The end of the box and of `FaceFigures`.

@@ 98
**`ProjectView`** — the page, for one organisation's project.

@@ 99
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 100
The current search: none at first.

@@ 101
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 102-103
The trace being shown, if any; and an error message, if any.

@@ 105-108
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 109-114
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions — matching the search — and the policies. The counts and the sessions are for the chosen mode.

@@ 115
The project's name, or its ID if it isn't listed.

@@ 116
Remember it all.

@@ 117
End of `load`. `useCallback` keeps the same function until the organisation, the project, the mode or the search changes — and a new function makes the page load again.

@@ 119-122
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 124-131
**`more`** — the next page of sessions, after the cursor and matching the same search, added below the ones already shown.

@@ 133-138
**`searchSessions`** — the search form was sent: read its two fields, trimmed, with an empty one meaning any, and make that the search. Changing the search changes `load`, so the list starts again from the newest matching session.

@@ 139
End of `searchSessions`.

@@ 141-147
While loading, "Loading…" — or the error, if loading failed.

@@ 148-159
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 161-167
The loaded values; and the counts as a list of (outcome, number) pairs, sorted into the chart's order of outcomes, so each total sits where its colour does in the legend. `rank` gives an outcome's place in that order; one it doesn't know (`indexOf` gives −1) goes after all the others.

@@ 168-176
The page, framed by the console with its sidebar (`signedIn`), and a link back to the organisation.

@@ 177-181
The project's name as the heading, with its ID beneath.

@@ 182-183
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 184-188
One label each for test and live; the chosen one is drawn dark.

@@ 189-195
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 196-199
Its words, "Test" or "Live"; end of the switch.

@@ 200
End of the heading row.

@@ 201-205
The error, if there is one.

@@ 207-210
**Counts** — a panel headed "Last 30 days".

@@ 211-212
None yet: say so.

@@ 213-222
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 224
When there are counts, the chart beneath the tiles: the 30 days from the first day counted, each with its numbers.

@@ 225
End of the panel.

@@ 227
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 228-231
**Sessions** — a panel.

@@ 232-235
**The search form**: in a row on wider screens.

@@ 236-245
The outcome to look for, from a menu that starts with *Any* and then lists the outcomes in the same shared order (`OUTCOME_ORDER`, from `daily.ts`).

@@ 246-248
The website's reference, up to 200 characters, as the API allows.

@@ 249-252
The button, and the end of the form.

@@ 253-256
Nothing to show: "No sessions match." when searching, "No sessions yet." otherwise.

@@ 257-268
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 269-274
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 275-283
A **Trace** button: fetch this session's trace and show it.

@@ 284-288
End of the row and the table.

@@ 289-293
If there are older sessions, a button to show them.

@@ 294
End of the panel.

@@ 296-299
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 300-301
No session chosen yet: say what the panel is for.

@@ 302-309
Otherwise the session's ID, then its policy, status and outcome.

@@ 310-312
Its attempts, in order, each in a box.

@@ 313-316
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 317
Its numbers.

@@ 318-320
End of the attempt and the list.

@@ 321
A session with no attempts says so.

@@ 322-325
End of the trace, the panel and the side-by-side area.

@@ 327-330
**Policies** — a panel.

@@ 331-340
A table: the policy's label, its minimum age, its risk budget, its face attempts and (Phase 9) whether it accepts Age Passes.

@@ 341-346
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 347-350
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, its attempts, and `accepted` or a dash for the Age Pass.

@@ 351-354
End of the row and the table.

@@ 355-357
**The policy editor** (`policy-editor.tsx`) — only for roles that may manage policies (`CAN.managePolicies`); the API checks again. It is given the page's client and, as `onAdded`, the page's own `load`, so a new version appears in the table at once.

@@ 358
End of the policies panel.

@@ 360-362
**Webhooks** — for roles that may manage them, the panel, given the page's own client (it holds the CSRF token) and the current mode.

@@ 363-365
End of the page and `ProjectView`.

@@ 19
The face checks' figures in words (`lib/figures.ts`).

@@ 58-60
The end of the wrapper and of `ScoreList`.

@@ 62-64
**`FaceFigures`** — the face checks' three headline figures, which the design's dashboard asks for.

@@ 65-76
The median time to a decision, as a band ("10–15 s"), and whether the whole band is within the 15-second target; a dash before anything has been decided.

@@ 77-79
The share of decided checks rejected as a likely attack (a failed liveness check or signs of tampering), and the share sent to a stronger check because the age estimate was unsure.

@@ 80-84
A small heading, with how many face checks the figures are based on — a percentage of 3 means little.

@@ 85-93
The figures as a description list (`dl`): each name (`dt`) with its value and note (`dd`), in a box. On a phone they stack; from the `sm` width, three side by side.

@@ 223
Under the totals, the face checks' figures — once at least one has been decided.
