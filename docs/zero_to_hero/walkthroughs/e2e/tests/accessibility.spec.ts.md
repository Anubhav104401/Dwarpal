---
fingerprint: b525f363f01d9059
---
The accessibility checks (Phase 5's exit criterion "axe clean"): **axe** inspects each key page against the rules of WCAG 2.2 at levels A and AA, on every browser engine, and the test fails if any rule is broken — naming the rule and the elements.

@@ 1-2
axe's Playwright helper; Playwright's `expect`, `Page` type and `test`.

@@ 4-5
The shop's address, and the console's.

@@ 6-7
**`STANDARDS`** — which rules to apply, by axe's tags: WCAG 2.0, 2.1 and 2.2, levels A and AA. (**WCAG**, the Web Content Accessibility Guidelines, is the standard most laws point to; AA is the level they usually require.)

@@ 9-10
**`violations`** — every rule the page breaks; an empty list means none.

@@ 11-20
First wait for one-off animations to finish. The verify page's card fades in; measured halfway, its colours are blends of the card and the page behind it, and axe reported a contrast failure that wasn't there. Animations that run forever (a spinner) are left out, or the wait would never end.

@@ 21
Run axe on the page with those rules.

@@ 22-24
Each broken rule as "rule — what it means — where": its ID, its explanation, and the elements that break it.

@@ 25
End of `violations`.

@@ 27-30
**Test — the shop.** Its front page: no broken rule.

@@ 32-36
Then, as the comment says, open the check: since decision D16 it opens in a modal over the shop, the verify page inside a frame. Wait for the verify page's intro inside the frame, and check the whole page again. axe looks inside frames too, so this one check covers the shop under the modal, the modal and its Close button, and the verify page as a visitor first sees it (before the camera): no failures either.

@@ 37
End of the test.

@@ 39-42
**Test — the console.** The sign-in page.

@@ 44-50
Create an account; the organisations page.

@@ 52-54
The organisation's page, with its audit log.

@@ 56-58
The project's page, down to the webhooks.

@@ 60-63
The *Security* page, with a QR code on show.

@@ 65-67
The *Age model* page.

@@ 69-71
The command palette, opened from the sidebar's button, with its search box focused.

@@ 72
End of the test.

@@ 74-76
**Test — the home page** (§5.5.9), in both themes, like the design system's specimen below.

@@ 77-80
For each theme: ask for it, open the home page, and wait for its heading.

@@ 81
Open every question first, so their answers are checked too: a closed `details` hides its answer from axe.

@@ 82-84
No rule broken, in either theme. (This test caught two things while the page was built: grey text too faint on the dark background, and code boxes that scrolled sideways but couldn't be reached by keyboard.)

@@ 86-88
**Test — the design system's specimen** (§5.5.6), in both themes.

@@ 89-90
For the light theme, then the dark: tell the browser to report that colour scheme (`emulateMedia`), as a visitor's system setting would.

@@ 91-93
Open the specimen; once its heading is there, no rule may be broken — the failure message names the theme.

@@ 94-95
End of the loop and the test.
