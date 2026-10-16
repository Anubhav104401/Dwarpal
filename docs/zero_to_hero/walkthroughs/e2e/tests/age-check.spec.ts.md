---
fingerprint: 6f81b68dac3a8709
---
**The end-to-end tests**: four short stories, acted out by **Playwright** in a real Chromium browser (§4.20). The first one is the whole Phase 1 slice working together — the shop, the SDK, the verify page, the camera, the API, the inference service, the decision engine, the signed token and the shop's pass:

```
shop: "Verify my age"  →  verify page: intro  →  camera (fake)  →  "You're all set"  →  shop: the cellar
```

Playwright finds things on the page the way a person would — by their **role** and **name**: "the button called *Take photos*", "the heading *You're all set*". Tests written that way keep working when the page's design changes, and they quietly check accessibility too: an element a screen reader couldn't name, the test couldn't find either.

@@ 1
From Playwright: `test` (one story) and `expect` (a check that *waits* for the page: `toBeVisible()` keeps looking for up to 5 seconds before failing).

@@ 3-4
The two websites' addresses.

@@ 6
**Test 1: an adult passes and is let into the cellar.** Playwright passes each test a fresh browser `page`, and `info` — information about the running test, used here to choose where screenshots go.

@@ 7-8
Open the shop, and press "Verify my age to enter".

@@ 10
The verify page's intro must appear, naming the age.

@@ 11
**The secret is gone from the address.** The address must be exactly the verify page, `/v/`, and the session's ID — nothing after it. The `$` at the end of the pattern means "and then the address ends", so a leftover `#cs=…` would fail the test.

@@ 12
A screenshot of the intro, for people to look at. `animations: "disabled"` finishes any animation first, so the picture is never caught halfway through a fade.

@@ 14-16
Start the camera, wait until "Take photos" is **enabled** — which happens when the fake camera's first picture has arrived — and take a screenshot of the camera screen.

@@ 17-18
Take the photos, and wait up to 20 seconds for "You're all set". In those seconds, five frames travel to the API, then to the inference service, where the real face detector finds the face, the stand-in model reports 30, and the decision engine says pass.

@@ 19
A screenshot of the result.

@@ 21
Press "Continue to …". The `/^Continue to /` pattern matches any website's name.

@@ 22
The shop's return route has done all its checks — the browser binding, the API's result, the token's signature — and the browser is now in the cellar.

@@ 23
The cellar shows its "Age verified" badge.

@@ 24
A full-page screenshot of the cellar. The end of the story.

@@ 25
The end of test 1.

@@ 27-31
**Test 2: the cellar stays closed without a pass.** Going straight to `/cellar` must land back at the entrance, with the "Verify my age" button.

@@ 33-36
**Test 3: a verify link without its secret explains what to do.** A link with a valid-looking session ID but no `#cs=` part must say "This link doesn't work" — politely, and without asking the API anything.

@@ 38-44
**Test 4: a return link only works in the browser that started the check.** Opening the shop's return address directly — as someone would with a link sent by a friend — must lead to the "Please finish the check where you started it" page, because this browser never started that check.
