---
fingerprint: ff088d0bbee35958
---
**The policy editor** (§5.5.8) — the form that adds a version of one of a project's own policies, and the **projection** the design asks for: what the chosen age line means for adults, measured.

@@ 1
It runs in the browser.

@@ 3
From React: the form event's type, and two hooks.

@@ 5-7
The console's alert, labelled field and class names; the client, its error and the model's description; and the projection's words (`lib/projection.ts`).

@@ 9
Its inputs: the page's client, the organisation and project, and `onAdded` — what to do once a version is added (the page reloads its table).

@@ 11-15
What it does, and why it offers only the model's own lines: a policy's age and risk budget must match one of the lines the model in use was calibrated for, or the API refuses it. Before, the form offered four ages at a fixed 2 % budget — which the trained model has no line for, so every version would have been refused.

@@ 16-19
The component: the model's description (none yet), the chosen line's key, and an error, if any.

@@ 21-30
When it first appears, ask for the model's description (the same as the model page's, `/console/v1/model`). With it, choose the line to offer first; if it can't be loaded, say so.

@@ 32
The chosen line itself, found by its key.

@@ 34-39
**`add`** — the form was sent. Keep the page from reloading; stop if no line is chosen; read the form's fields; clear any old error.

@@ 40-48
Ask the API for a new version: the name typed, the chosen line's age and risk budget, and the face attempts.

@@ 49-50
Clear the form, and let the page reload its policies, so the new version appears at once.

@@ 51-54
On failure, show the API's message (such as a name already used by a preset), or a general one.

@@ 56-58
Until the model's lines are known — or if it has none — show nothing but an error, if there is one.

@@ 60-62
The editor: any error first.

@@ 63-66
The form, in a grid that puts the fields side by side from the `sm` width. The name: lower-case letters, digits and underscores, 3 to 40, starting with a letter — the API's own rule, so the browser can say so before sending (`pattern`).

@@ 67-80
**The age line**, from the model's own lines, labelled like "18+ · risk budget 7.5 %". It is a **controlled** menu: its value comes from `chosen`, and choosing another line sets `chosen` — which redraws the projection below.

@@ 81-89
The face attempts, 1 to 5 (3 at first).

@@ 90-93
The button, and the end of the form.

@@ 95-98
**The projection** — a section named by its heading, "What the 18+ line means for adults", so screen readers (and the browser tests) can find it.

@@ 99-102
A model that was never measured — the stand-in the tests use — has no adult outcomes: say so, naming the model, rather than show nothing.

@@ 103-113
Otherwise a table: for each band of adults, the share **sent to a stronger check** (the design's "projected adult step-up rate", in bold), the share that passes, and the share turned away.

@@ 114-124
One row per band, in the bands' own order, each share written by `percent`.

@@ 125-130
And underneath, what the numbers rest on, honestly: how many photos of adults (`reduce` adds up the bands' faces), from which dataset, with estimated rather than documented ages — and that a projection isn't a promise: real visitors, cameras and light differ from a dataset's photos.

@@ 131-136
The closing tags.
