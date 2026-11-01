---
fingerprint: 6de097dfd3f2622f
---
The accessibility checks (Phase 5's exit criterion "axe clean"): **axe** inspects each key page against the rules of WCAG 2.2 at levels A and AA, on every browser engine, and the test fails if any rule is broken — naming the rule and the elements.

@@ 1-3
Playwright's `expect` and `test`, and `violations` — the axe check every test here uses, moved into its own module (`axe.ts`) in Phase 6 so the age-check test can use it too.

@@ 5-6
The shop's address, and the console's.

@@ 8-11
**Test — the shop.** Its front page: no broken rule.

@@ 13-17
Then, as the comment says, open the check: since decision D16 it opens in a modal over the shop, the verify page inside a frame. Wait for the verify page's intro inside the frame, and check the whole page again. axe looks inside frames too, so this one check covers the shop under the modal, the modal and its Close button, and the verify page as a visitor first sees it (before the camera): no failures either.

@@ 18
End of the test.

@@ 20-23
**Test — the console.** The sign-in page.

@@ 25-31
Create an account; the organisations page.

@@ 33-35
The organisation's page, with its audit log.

@@ 37-39
The project's page, down to the webhooks.

@@ 41-44
The *Security* page, with a QR code on show.

@@ 46-48
The *Age model* page.

@@ 50-52
The command palette, opened from the sidebar's button, with its search box focused.

@@ 53
End of the test.

@@ 55-57
**Test — the home page** (§5.5.9), in both themes, like the design system's specimen below.

@@ 58-61
For each theme: ask for it, open the home page, and wait for its heading.

@@ 62
Open every question first, so their answers are checked too: a closed `details` hides its answer from axe.

@@ 63-65
No rule broken, in either theme. (This test caught two things while the page was built: grey text too faint on the dark background, and code boxes that scrolled sideways but couldn't be reached by keyboard.)

@@ 67-69
**Test — the design system's specimen** (§5.5.6), in both themes.

@@ 70-71
For the light theme, then the dark: tell the browser to report that colour scheme (`emulateMedia`), as a visitor's system setting would.

@@ 72-74
Open the specimen; once its heading is there, no rule may be broken — the failure message names the theme.

@@ 75-76
End of the loop and the test.
