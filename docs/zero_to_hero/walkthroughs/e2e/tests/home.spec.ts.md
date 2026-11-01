---
fingerprint: f7adbd8a765982a0
---
**The home page's browser test** (§5.5.9).

@@ 1
Playwright's test tools.

@@ 3-7
Open the home page and find the accuracy section, a *region* named by its heading.

@@ 8-10
A row for each of the model's four lines.

@@ 11-13
The test servers run the stand-in model, whose lines were never measured: the table must say "not measured" rather than show a figure, and the note must say the model decides test checks only.

@@ 15-16
The demo shop's link leads to the shop the tests run (`playwright.config.ts` tells the page where it is).

@@ 17-19
The header's "Console" link leads to the console's sign-in (`exact`, since "Open the console" contains the word too).
