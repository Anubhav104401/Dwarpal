---
fingerprint: 8a8403559295f6dd
---
**The home page's browser test** (§5.5.9).

@@ 1
Playwright's test tools.

@@ 5-9
Open the home page and find the accuracy section, a *region* named by its heading.

@@ 10-12
A row for each of the model's four lines.

@@ 13-15
The test servers run the stand-in model, whose lines were never measured: the table must say "not measured" rather than show a figure, and the note must say the model decides test checks only.

@@ 17-18
The demo shop's link leads to the shop the tests run (`playwright.config.ts` tells the page where it is).

@@ 19-21
The header's "Console" link leads to the console's sign-in (`exact`, since "Open the console" contains the word too).

@@ 23-26
**Test — the hero's face turns 3D where the browser can draw it, and stays still for anyone who asks for less motion** (§5.5.10). It uses the page, and the browser to open a second page.

@@ 27-29
Open the home page, and ask the browser whether it can draw WebGL 2; if not (a machine without graphics), the test is skipped rather than failed.

@@ 30-32
Once the page is idle, the 3D canvas appears and the doorway's points are gone.

@@ 34-39
A second page, in a browser set to **reduced motion**: after three seconds there is still no canvas, and all 168 of the still face's points are drawn. Then close it.

@@ 40
The end of the test.

@@ 3
The shared axe check (`axe.ts`).

@@ 42-48
**Test — the home page speaks Hindi to anyone who chooses it** (§5.5.11). It starts in English (`lang="en"`); pressing "हिन्दी" brings the heading, the page's language and its title in Hindi.

@@ 49-52
Open every question, and check the Hindi page with axe: no rule broken.

@@ 54-59
Reload: the choice is remembered (the Hindi button is pressed). And pressing "English" brings English back.

@@ 61-68
**Test — a browser that asks for Hindi gets it without choosing**: a browser set to Hindi (`hi-IN`, which Playwright turns into its `Accept-Language` header) is answered in Hindi at once.

@@ 69-73
And the console, written in English only, says so in its content (`lang="en"`), whatever the page's language.
