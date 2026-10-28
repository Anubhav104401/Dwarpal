---
fingerprint: 7b95e301b459227f
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

@@ 32-34
Then the verify page, as a visitor first sees it (before the camera): none either.

@@ 35
End of the test.

@@ 37-40
**Test — the console.** The sign-in page.

@@ 42-48
Create an account; the organisations page.

@@ 50-52
The organisation's page, with its audit log.

@@ 54-56
The project's page, down to the webhooks.

@@ 58-61
The *Security* page, with a QR code on show.

@@ 63-65
The *Age model* page.

@@ 66
End of the test.

@@ 68-70
**Test — the design system's specimen** (§5.5.6), in both themes.

@@ 71-72
For the light theme, then the dark: tell the browser to report that colour scheme (`emulateMedia`), as a visitor's system setting would.

@@ 73-75
Open the specimen; once its heading is there, no rule may be broken — the failure message names the theme.

@@ 76-77
End of the loop and the test.
