---
fingerprint: 882d109099238712
---
**The end-to-end tests**: short stories, acted out by **Playwright** in a real Chromium browser (§4.20). The first one is the whole slice working together — the shop, the SDKs, the verify page in its modal, the camera, the API, the inference service, the decision engine, the signed token and the shop's pass:

```
shop: "Verify my age"  →  modal over the shop: intro  →  camera (fake)  →  "You're all set"  →  shop: the cellar
```

Playwright finds things on the page the way a person would — by their **role** and **name**: "the button called *Start*", "the heading *You're all set*". Tests written that way keep working when the page's design changes, and they quietly check accessibility too: an element a screen reader couldn't name, the test couldn't find either.

@@ 1
From Playwright: `test` (one story) and `expect` (a check that *waits* for the page: `toBeVisible()` keeps looking for up to 5 seconds before failing).

@@ 3-4
The two websites' addresses.

@@ 6-8
**Test 1: an adult passes the check in a modal over the shop, and is let into the cellar** (since decision D16 the check opens in a frame on the shop's page). Playwright passes each test a fresh browser `page`, and `info` — information about the running test, used here to choose where screenshots go.

@@ 9-10
Open the shop, and press "Verify my age to enter".

@@ 12-14
As the comment says, the check opens over the shop. `modal` is the dialog the SDK adds; `check` is the page inside its frame — a **frame locator** lets the test look inside a frame as if it were a page of its own.

@@ 15-16
The verify page's intro appears inside the frame, naming the age — and the shop's own address hasn't changed.

@@ 17-20
The frame shows a verify page, `/v/` and a session's ID, opened with its secret (`#cs=`) — the link the shop's server got from Dwarpal.

@@ 21-23
**The secret is gone from the address.** Among the page's frames (`page.frames()`), the verify page's own address must be exactly `/v/` and the session's ID, nothing after it: the page wiped the secret as soon as it read it. The `$` at the end of the pattern means "and then the address ends", so a leftover `#cs=…` would fail the test.

@@ 24
A screenshot of the intro over the shop, for people to look at. `animations: "disabled"` finishes any animation first, so the picture is never caught halfway through a fade.

@@ 26-29
Start the camera, wait until the **Start** button is enabled, and take a screenshot of the camera screen — all inside the frame, which proves a page in a frame can use the camera when the website allows it (`allow="camera"`). `exact: true` matters: without it, "Start" would also match "Start the camera".

As the comment says, the button is enabled once the live guidance sees a well-placed face — or after a grace period, because the guidance only *advises*: it must never lock out someone whose face it can't read. 15 seconds allows for MediaPipe loading.

@@ 30-31
Press Start. The comment explains the long waits that follow: the fake camera plays a still portrait that never turns, so the page waits the full 5 seconds at each pose before moving on.

@@ 32-39
Follow the check as it happens, with a screenshot at each stage:

- the colour phase, recognised by its instruction "Keep looking at the screen." (`.first()`: the text may appear in more than one place);
- a pose prompt, up to 10 seconds later. `/^(Turn your head|Lift your chin)/` is a **regular expression**: text that *starts with* (`^`) either phrase (`|` means "or") — the poses are random, so the test can't know which comes first;
- the result, "You're all set", within 45 seconds. Meanwhile the photos travel to the API, then to the inference service: the real face detector finds the face, liveness (in the labels test mode) accepts the poses, the stand-in model reports 30, and the decision engine says pass.

@@ 41-43
Press "Continue to …" (the `/^Continue to /` pattern matches any website's name). As the comment says, the verify page tells the shop's page, which closes the modal and goes to the shop's return address.

@@ 44
The shop's return route has done all its checks — the browser binding, the API's result, the token's signature — and the browser is now in the cellar.

@@ 45
The cellar shows its "Age verified" badge.

@@ 46
A full-page screenshot of the cellar.

@@ 48
The comment says what the last part checks: leaving forgets the pass.

@@ 49-50
Press **Leave the cellar**, and the front page appears again, offering a new age check.

@@ 51-52
Try the cellar's address directly: the shop sends the browser back to the front page, because the pass is gone. The end of the story.

@@ 53
The end of test 1.

@@ 55-59
**Test 2: the cellar stays closed without a pass.** Going straight to `/cellar` must land back at the entrance, with the "Verify my age" button.

@@ 61-64
**Test 3: a verify link without its secret explains what to do.** A link with a valid-looking session ID but no `#cs=` part must say "This link doesn't work" — politely, and without asking the API anything.

@@ 66-72
**Test 4: a return link only works in the browser that started the check.** Opening the shop's return address directly — as someone would with a link sent by a friend — must lead to the "Please finish the check where you started it" page, because this browser never started that check.

@@ 74-78
**Test 5: the modal closes, and the shop is as it was.** Open the check, and wait for it inside the frame.

@@ 79-80
Press the modal's **Close**: the dialog is gone.

@@ 81
And the keyboard focus is back on the button that opened it, so someone using a keyboard carries on where they were. (This caught a real bug: the React button was *disabled* while busy, which threw the focus away.)

@@ 82
End of test 5.

@@ 84-87
**Test 6: no other website may frame a verify page.** Ask the verify page's web server directly for a page whose session doesn't exist: its policy must say `frame-ancestors 'none'` — no website at all may show it in a frame.
