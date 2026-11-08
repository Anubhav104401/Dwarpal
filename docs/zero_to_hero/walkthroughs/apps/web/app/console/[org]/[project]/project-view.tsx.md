---
fingerprint: 6fa92b07ca70a702
---
A project's page in the console (Phase 5, §5.5.2): its counts for the last 30 days, its sessions with each one's **decision trace** — why it ended as it did, down to the numbers — and its policies, with a form to add a version. A switch chooses test or live data. Everything comes from the console API; the page decides nothing about who may do what — it only hides a form the API would refuse.

@@ 1
`"use client"` — this file runs in the browser: it keeps state and answers clicks.

@@ 3-4
Next.js's `Link`, and React's tools: the type of a form's submit event, and the hooks for remembered functions, side effects and state.

@@ 6
The console's shared pieces (§5.5.1): an alert box, the page's frame, a labelled field, and the class names for inputs, panels and quiet buttons.

@@ 7-17
The console client, the role table `CAN`, and the shapes of the answers this page reads — and of a session search. Since 8 Nov also the `Project` type, for the settings panel.

@@ 19
From `daily.ts`: `everyDay`, which turns the counts into one entry per day, and the order of the outcomes, shared with the chart.

@@ 22-26
The daily chart (§5.5.2), the policy editor (§5.5.8), the webhooks panel (§5.5.3), and since 8 Nov the keys and settings panels — each in its own file.

@@ 28
One client for the page.

@@ 30-38
**`Loaded`** — everything the page shows, once loaded: the person's role, the project's name, the counts, the first page of sessions, and the policies. Since 8 Nov also the project's own record (`info`), for the settings panel.

@@ 40-41
**`ScoreList`** — one attempt's numbers.

@@ 42-44
Split them in two: plain values (a number, a word) and nested ones (an object, such as the liveness evidence).

@@ 45-54
The plain ones as a description list (`<dl>`): each name (`<dt>`) beside its value (`<dd>`). `contents` lets each pair's wrapper vanish from the layout, so the names and values line up in two columns.

@@ 55-62
Each nested one folded inside `<details>` — a built-in disclosure, opened with a click or the keyboard — showing it as indented JSON.

@@ 99-101
The end of the box and of `FaceFigures`.

@@ 103
**`ProjectView`** — the page, for one organisation's project.

@@ 104
Test or live — test by default, so nobody looks at real people's sessions by accident.

@@ 105
The current search: none at first.

@@ 106
What was loaded, `"unavailable"` (no such project for this person), or `null` while loading.

@@ 107-108
The trace being shown, if any; and an error message, if any.

@@ 110-113
**`load`** — who is signed in, and their membership of this organisation. Not signed in, or not a member: the page says so ("unavailable").

@@ 114-119
Four requests at once (`Promise.all`): the organisation's projects (for this one's name), the counts, the first page of sessions — matching the search — and the policies. The counts and the sessions are for the chosen mode.

@@ 120
The project's own record from the list, if it is there.

@@ 121
Remember it all; the name falls back to the project's ID if it isn't listed.

@@ 122
End of `load`. `useCallback` keeps the same function until the organisation, the project, the mode or the search changes — and a new function makes the page load again.

@@ 124-127
When `load` changes — on arrival, and when the mode switches — close any trace (it may belong to the other mode) and load again. A failure becomes a message.

@@ 129-136
**`more`** — the next page of sessions, after the cursor and matching the same search, added below the ones already shown.

@@ 138-143
**`searchSessions`** — the search form was sent: read its two fields, trimmed, with an empty one meaning any, and make that the search. Changing the search changes `load`, so the list starts again from the newest matching session.

@@ 144
End of `searchSessions`.

@@ 146-152
While loading, "Loading…" — or the error, if loading failed.

@@ 153-164
Not available: say so, with a way back to the console. It doesn't say which of the two reasons it is.

@@ 166-172
The loaded values; and the counts as a list of (outcome, number) pairs, sorted into the chart's order of outcomes, so each total sits where its colour does in the legend. `rank` gives an outcome's place in that order; one it doesn't know (`indexOf` gives −1) goes after all the others.

@@ 173-181
The page, framed by the console with its sidebar (`signedIn`), and a link back to the organisation.

@@ 182-186
The project's name as the heading, with its ID beneath.

@@ 187-188
**The mode switch** — a `fieldset` of two radio buttons, named "Mode" for screen readers (`sr-only`: read aloud, not shown).

@@ 189-193
One label each for test and live; the chosen one is drawn dark.

@@ 194-200
The radio button itself is hidden from sight but not from the keyboard or screen readers; choosing it changes the mode, which reloads the page's data.

@@ 201-204
Its words, "Test" or "Live"; end of the switch.

@@ 205
End of the heading row.

@@ 206-210
The error, if there is one.

@@ 212-215
**Counts** — a panel headed "Last 30 days".

@@ 216-217
None yet: say so.

@@ 218-227
Otherwise, one tile per outcome: the number large, the outcome beneath (`step_up` shown as "step up").

@@ 229
When there are counts, the chart beneath the tiles: the 30 days from the first day counted, each with its numbers.

@@ 230
End of the panel.

@@ 232
Sessions and the trace side by side on wide screens, one above the other on narrow ones.

@@ 233-236
**Sessions** — a panel.

@@ 237-240
**The search form**: in a row on wider screens.

@@ 241-250
The outcome to look for, from a menu that starts with *Any* and then lists the outcomes in the same shared order (`OUTCOME_ORDER`, from `daily.ts`).

@@ 251-253
The website's reference, up to 200 characters, as the API allows.

@@ 254-257
The button, and the end of the form.

@@ 258-261
Nothing to show: "No sessions match." when searching, "No sessions yet." otherwise.

@@ 262-273
Otherwise a table: when it was created, its status, its outcome, and a column for the buttons (named "Trace" for screen readers only).

@@ 274-279
One row per session: its time in the reader's own format, its status, and its outcome (a dash if none yet).

@@ 280-288
A **Trace** button: fetch this session's trace and show it.

@@ 289-293
End of the row and the table.

@@ 294-298
If there are older sessions, a button to show them.

@@ 299
End of the panel.

@@ 301-304
**Decision trace** — a panel. `aria-live="polite"` makes a screen reader read out a new trace when it appears, once it has finished speaking.

@@ 305-306
No session chosen yet: say what the panel is for.

@@ 307-314
Otherwise the session's ID, then its policy, status and outcome.

@@ 315-317
Its attempts, in order, each in a box.

@@ 318-321
"Attempt 1: pass" — with its reasons in brackets, if any.

@@ 322
Its numbers.

@@ 323-325
End of the attempt and the list.

@@ 326
A session with no attempts says so.

@@ 327-330
End of the trace, the panel and the side-by-side area.

@@ 332-335
**Policies** — a panel.

@@ 336-345
A table: the policy's label, its minimum age, its risk budget, its face attempts and (Phase 9) whether it accepts Age Passes.

@@ 346-351
One row per policy: its label, marked "preset" if it's one of Dwarpal's own.

@@ 352-355
Its minimum age ("18+"), its risk budget as a percentage to one decimal place, its attempts, and `accepted` or a dash for the Age Pass.

@@ 356-359
End of the row and the table.

@@ 360-362
**The policy editor** (`policy-editor.tsx`) — only for roles that may manage policies (`CAN.managePolicies`); the API checks again. It is given the page's client and, as `onAdded`, the page's own `load`, so a new version appears in the table at once.

@@ 363
End of the policies panel.

@@ 365-367
**Webhooks** — for roles that may manage them, the panel, given the page's own client (it holds the CSRF token) and the current mode.

@@ 380-382
End of the page and `ProjectView`.

@@ 20
The face checks' figures in words (`lib/figures.ts`).

@@ 63-65
The end of the wrapper and of `ScoreList`.

@@ 67-69
**`FaceFigures`** — the face checks' three headline figures, which the design's dashboard asks for.

@@ 70-81
The median time to a decision, as a band ("10–15 s"), and whether the whole band is within the 15-second target; a dash before anything has been decided.

@@ 82-84
The share of decided checks rejected as a likely attack (a failed liveness check or signs of tampering), and the share sent to a stronger check because the age estimate was unsure.

@@ 85-89
A small heading, with how many face checks the figures are based on — a percentage of 3 means little.

@@ 90-98
The figures as a description list (`dl`): each name (`dt`) with its value and note (`dd`), in a box. On a phone they stack; from the `sm` width, three side by side.

@@ 228
Under the totals, the face checks' figures — once at least one has been decided.

@@ 369
**The keys panel** (decision D30), for the roles that may make keys.

@@ 371-379
**The settings panel** (decisions D28, D29): everyone sees the allowed origins; owners and admins may change them, and the name. After a save the page loads again (`onSaved`), so the heading shows a new name.
