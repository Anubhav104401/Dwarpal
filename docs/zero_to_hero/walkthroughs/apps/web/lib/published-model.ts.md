---
fingerprint: 517d569e1a1e36e7
---
**The published model** (§5.5.9): the age model's figures as the API publishes them to anyone (`/v1/model`), read into types the home page can trust.

@@ 1
The adults' outcomes type, shared with the console's model page.

@@ 3-12
**`PublishedLine`** — one age line: its age and risk budget, its two bounds (each explained by its comment), and how adults just over it fared. A bound is `null` for a model never measured.

@@ 14-20
**`PublishedModel`** — the model's version, whether it may decide real checks, what it was measured on, and its lines.

@@ 22-26
Three small readers of untrusted JSON: is it an object; a number or nothing; a list of objects (anything else in it dropped).

@@ 28-31
**`readPublishedModel`** — the API's answer as a model, or null if it has no version. The calibration details, if any.

@@ 32-38
The version, whether it is calibrated (only an explicit `true` counts), and the measured dataset — only if it names one.

@@ 39-51
Each line, its snake_case names turned into the app's camelCase. A missing bound stays `null` ("not measured"); a missing count reads as 0.

@@ 52-53
The end.

@@ 55-59
**`publishedModel`** — ask the API. `ask` is `fetch` unless a test passes its own stand-in.

@@ 60-62
Ask, giving up after 1.5 s so a slow API can't hold up the page; never from a cache, so the figures are those of the model running now. Read the answer only if the API said it succeeded.

@@ 63-66
Anything else — the API down, a timeout, an answer that isn't JSON — means "no figures": the page then says so instead of failing.
