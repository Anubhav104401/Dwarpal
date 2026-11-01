---
fingerprint: b59c9c5af222f9e4
---
The **accessibility check** every browser test can use: run axe-core on the page and list what it breaks. It moved here from the accessibility test in Phase 6 (§5.6.3), so the age-check test can check the document screens with the very same rules.

@@ 1-2
axe's Playwright helper, and Playwright's `Page` type.

@@ 4-5
The rules to check: those of WCAG 2.2 at levels A and AA, as axe-core tags them (with earlier versions' rules included).

@@ 7-8
**`violations`** — every accessibility rule the page breaks, as one line each; an empty list when it breaks none, which is what every test expects.

@@ 9-18
First let one-off animations finish — a card fading in, say. Colours measured mid-fade are blends, not the page's colours, and would give false contrast failures. Endless animations (a spinner) never finish, so they are left out.

@@ 19-23
Run axe with those rules, and turn each violation into "rule — what it means — where", naming the elements (`target`) it found on the page.
