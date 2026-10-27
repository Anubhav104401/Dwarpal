---
fingerprint: d40e33487be06f72
---
**Lighthouse CI's settings** (Phase 5): run Lighthouse once per page, and fail if a page scores under 90 in a category the roadmap names (performance, accessibility, best practices, search engines). JSON allows no comments, so the reasons are here.

@@ 1-2
Everything sits under `ci`.

@@ 3-6
**Collecting**: one run per page, in a headless browser that skips its first-run screens.

@@ 7-8
**Asserting**: one set of rules per group of addresses (`assertMatrix`).

@@ 9-17
The **demo shop** (port 3100), a public page: at least 0.9 — Lighthouse's 90 — in all four categories.

@@ 18-25
The **verify page and console** (port 3000): the same, except search engines. These pages ask search engines not to index them (`layout.tsx`), so that score can't reach 90 — by design. The test checks instead that they keep asking.

@@ 26-27
End of the rules.

@@ 28
**Uploading**: no server, just files — the reports are saved in `test-results/lighthouse`.

@@ 29-30
End.
