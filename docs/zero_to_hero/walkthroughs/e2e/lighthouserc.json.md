---
fingerprint: 8c0bcaeba5f97a3c
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

@@ 18-23
The **home page** (port 3000, the address `/` and nothing after it, §5.5.9): search engines at least 0.9. It is the one page of the web app that asks to be found; the rules below hold it to the other three categories too, since its address matches theirs as well.

@@ 24-31
The **verify page and console** (port 3000): the same, except search engines. These pages ask search engines not to index them (`layout.tsx`), so that score can't reach 90 — by design. The test checks instead that they keep asking.

@@ 32-33
End of the rules.

@@ 34
**Uploading**: no server, just files — the reports are saved in `test-results/lighthouse`.

@@ 35-36
End.
