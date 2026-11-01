---
fingerprint: c789d814d6de69ff
---
The API speaks in short **codes** such as `too_dark` or `session_not_open` — stable and precise, but not words to show a person. This file turns them into friendly sentences, in two kinds:

- a **tip** after a "retry", saying how to take better photos;
- a **problem** — a title and an explanation — when something stops the check.

Keeping every sentence in one file has two benefits: the wording can be improved without touching any logic, and when the page is translated into other languages (a later phase), this is the one file to translate.

@@ 1
The doc comment.

@@ 3-29
**`TIPS`** — one tip per reason code the decision engine can give (§5.1.2, `ADVICE_ORDER`), plus the two extra ones that come from the decision rules: `inconsistent_frames` and `analysis_unavailable`. Phase 3 added the liveness tips; as their comment says, they use the same words whichever check failed, so nobody can learn which one to fool.

Phase 6 (§5.6.3) added the document check's: the zone not found, unreadable, or failing its check digits; no photo on the document; no face in the selfie; and a selfie that doesn't match the document's photo — each telling the person what to do differently.

@@ 31
`DEFAULT_TIP` — for any reason this file doesn't know yet, such as a code added to the API later. The page never shows a raw code.

@@ 33
**`tipFor`** — the tip for a list of reasons.

@@ 34-39
Go through the reasons in order, and return the tip for the first one known. Looking a key up in a `Record` may find nothing — and the project's strict settings make TypeScript insist on the `!== undefined` check before the tip is used.

@@ 40-41
None known: the general tip.

@@ 43-46
**`Problem`** — a title and a longer explanation.

@@ 48
**`PROBLEMS`** — the message for each code that can stop a check:

@@ 49-52
`invalid_client_secret` — the link's secret is wrong or missing. Usually the link was copied incompletely.

@@ 53-56
`session_not_found` — no such session: also a broken link, as far as the person is concerned.

@@ 57-60
`session_not_open` — the check expired (after 30 minutes) or was cancelled.

@@ 61-64
`too_many_attempts` (added for the per-device budgets) — this device has used up its hourly allowance of checks. The advice is to wait: the budget starts afresh within the hour.

@@ 65
The end of the entry.

@@ 66-69
`too_many_challenges` — the session used up its challenge budget (§5.1.3).

@@ 70-73
`camera_blocked` — the person refused camera access, or the browser blocks it. This code doesn't come from the API: the verify page makes it up itself when the browser refuses (see `verify-flow.tsx`).

@@ 74-77
`camera_missing` — the device has no camera at all. Also the page's own code.

@@ 78-81
`network_error` — the API couldn't be reached at all (`flow-api.ts`).

@@ 82
The end of the list.

@@ 84-87
`DEFAULT_PROBLEM` — for anything else, including server errors: apologise, and say what to try.

@@ 89-91
**`problemFor`** — the message for a code. `??` falls back to the default when the code isn't in the list.
