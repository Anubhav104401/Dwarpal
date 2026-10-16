---
fingerprint: caf3c31661a061c6
---
The API speaks in short **codes** such as `too_dark` or `session_not_open` — stable and precise, but not words to show a person. This file turns them into friendly sentences, in two kinds:

- a **tip** after a "retry", saying how to take better photos;
- a **problem** — a title and an explanation — when something stops the check.

Keeping every sentence in one file has two benefits: the wording can be improved without touching any logic, and when the page is translated into other languages (a later phase), this is the one file to translate.

@@ 1
The doc comment.

@@ 3-15
**`TIPS`** — one tip per reason code the decision engine can give (§5.1.2, `ADVICE_ORDER`), plus the two extra ones that come from the decision rules: `inconsistent_frames` and `analysis_unavailable`. Each says what to *do*, in plain words: "Face a window or a lamp", not "insufficient illumination".

`Record<string, string>` is TypeScript's type for "an object whose keys and values are all text".

@@ 17
`DEFAULT_TIP` — for any reason this file doesn't know yet, such as a code added to the API later. The page never shows a raw code.

@@ 19
**`tipFor`** — the tip for a list of reasons.

@@ 20-25
Go through the reasons in order, and return the tip for the first one known. Looking a key up in a `Record` may find nothing — and the project's strict settings make TypeScript insist on the `!== undefined` check before the tip is used.

@@ 26-27
None known: the general tip.

@@ 29-32
**`Problem`** — a title and a longer explanation.

@@ 34
**`PROBLEMS`** — the message for each code that can stop a check:

@@ 35-38
`invalid_client_secret` — the link's secret is wrong or missing. Usually the link was copied incompletely.

@@ 39-42
`session_not_found` — no such session: also a broken link, as far as the person is concerned.

@@ 43-46
`session_not_open` — the check expired (after 30 minutes) or was cancelled.

@@ 47-50
`too_many_challenges` — the session used up its challenge budget (§5.1.3).

@@ 51-54
`camera_blocked` — the person refused camera access, or the browser blocks it. This code doesn't come from the API: the verify page makes it up itself when the browser refuses (see `verify-flow.tsx`).

@@ 55-58
`camera_missing` — the device has no camera at all. Also the page's own code.

@@ 59-62
`network_error` — the API couldn't be reached at all (`flow-api.ts`).

@@ 63
The end of the list.

@@ 65-68
`DEFAULT_PROBLEM` — for anything else, including server errors: apologise, and say what to try.

@@ 70-72
**`problemFor`** — the message for a code. `??` falls back to the default when the code isn't in the list.
