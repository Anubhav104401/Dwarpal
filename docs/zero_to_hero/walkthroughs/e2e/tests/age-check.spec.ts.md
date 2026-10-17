---
fingerprint: 7133feeb0e7cebde
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

@@ 14-17
Start the camera, wait until the **Start** button is enabled, and take a screenshot of the camera screen. `exact: true` matters: without it, "Start" would also match "Start the camera".

As the comment says, the button is enabled once the live guidance sees a well-placed face — or after a grace period, because the guidance only *advises*: it must never lock out someone whose face it can't read. 15 seconds allows for MediaPipe loading.

@@ 18-19
Press Start. The comment explains the long waits that follow: the fake camera plays a still portrait that never turns, so the page waits the full 5 seconds at each pose before moving on.

@@ 20-27
Follow the check as it happens, with a screenshot at each stage:

- the colour phase, recognised by its instruction "Keep looking at the screen." (`.first()`: the text may appear in more than one place);
- a pose prompt, up to 10 seconds later. `/^(Slowly turn your head|Tilt your head up)/` is a **regular expression**: text that *starts with* (`^`) either phrase (`|` means "or") — the poses are random, so the test can't know which comes first;
- the result, "You're all set", within 45 seconds. Meanwhile seven photos travel to the API, then to the inference service: the real face detector finds the face, liveness (in the labels test mode) accepts the poses, the stand-in model reports 30, and the decision engine says pass.

@@ 29
Press "Continue to …". The `/^Continue to /` pattern matches any website's name.

@@ 30
The shop's return route has done all its checks — the browser binding, the API's result, the token's signature — and the browser is now in the cellar.

@@ 31
The cellar shows its "Age verified" badge.

@@ 32
A full-page screenshot of the cellar. The end of the story.

@@ 33
The end of test 1.

@@ 35-39
**Test 2: the cellar stays closed without a pass.** Going straight to `/cellar` must land back at the entrance, with the "Verify my age" button.

@@ 41-44
**Test 3: a verify link without its secret explains what to do.** A link with a valid-looking session ID but no `#cs=` part must say "This link doesn't work" — politely, and without asking the API anything.

@@ 46-52
**Test 4: a return link only works in the browser that started the check.** Opening the shop's return address directly — as someone would with a link sent by a friend — must lead to the "Please finish the check where you started it" page, because this browser never started that check.
