---
fingerprint: d336119962853f94
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

@@ 21-24
**Test — the hero's face turns 3D where the browser can draw it, and stays still for anyone who asks for less motion** (§5.5.10). It uses the page, and the browser to open a second page.

@@ 25-27
Open the home page, and ask the browser whether it can draw WebGL 2; if not (a machine without graphics), the test is skipped rather than failed.

@@ 28-30
Once the page is idle, the 3D canvas appears and the doorway's points are gone.

@@ 32-37
A second page, in a browser set to **reduced motion**: after three seconds there is still no canvas, and all 168 of the still face's points are drawn. Then close it.

@@ 38
The end of the test.
