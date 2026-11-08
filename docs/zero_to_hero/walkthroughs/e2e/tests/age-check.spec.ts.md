---
fingerprint: a7ec7339fdbc6d93
---
**The end-to-end tests**: short stories, acted out by **Playwright** in a real Chromium browser (§4.20). The first one is the whole slice working together — the shop, the SDKs, the verify page in its modal, the camera, the API, the inference service, the decision engine, the signed token and the shop's pass:

```
shop: "Verify my age"  →  modal over the shop: intro  →  camera (fake)  →  "You're all set"  →  shop: the cellar
```

Playwright finds things on the page the way a person would — by their **role** and **name**: "the button called *Start*", "the heading *You're all set*". Tests written that way keep working when the page's design changes, and they quietly check accessibility too: an element a screen reader couldn't name, the test couldn't find either.

@@ 2-6
Node's `fileURLToPath` (to find the specimen passport's file); from Playwright, `test` (one story), `expect` (a check that *waits* for the page: `toBeVisible()` keeps looking for up to 5 seconds before failing) and the type of its HTTP client; and the axe check (`axe.ts`).

@@ 8-9
The two websites' addresses.

@@ 42-44
**Test 1: an adult passes the check in a modal over the shop, and is let into the cellar** (since decision D16 the check opens in a frame on the shop's page). Playwright passes each test a fresh browser `page`, and `info` — information about the running test, used here to choose where screenshots go.

@@ 45-46
Open the shop, and press "Verify my age to enter".

@@ 48-50
As the comment says, the check opens over the shop. `modal` is the dialog the SDK adds; `check` is the page inside its frame — a **frame locator** lets the test look inside a frame as if it were a page of its own.

@@ 51-52
The verify page's intro appears inside the frame, naming the age — and the shop's own address hasn't changed.

@@ 53-56
The frame shows a verify page, `/v/` and a session's ID, opened with its secret (`#cs=`) — the link the shop's server got from Dwarpal.

@@ 57-59
**The secret is gone from the address.** Among the page's frames (`page.frames()`), the verify page's own address must be exactly `/v/` and the session's ID, nothing after it: the page wiped the secret as soon as it read it. The `$` at the end of the pattern means "and then the address ends", so a leftover `#cs=…` would fail the test.

@@ 60
A screenshot of the intro over the shop, for people to look at. `animations: "disabled"` finishes any animation first, so the picture is never caught halfway through a fade.

@@ 62-65
Start the camera, wait until the **Start** button is enabled, and take a screenshot of the camera screen — all inside the frame, which proves a page in a frame can use the camera when the website allows it (`allow="camera"`). `exact: true` matters: without it, "Start" would also match "Start the camera".

As the comment says, the button is enabled once the live guidance sees a well-placed face — or after a grace period, because the guidance only *advises*: it must never lock out someone whose face it can't read. 15 seconds allows for MediaPipe loading.

@@ 66-67
Press Start. The comment explains the long waits that follow: the fake camera plays a still portrait that never turns, so the page waits the full 5 seconds at each pose before moving on.

@@ 68-75
Follow the check as it happens, with a screenshot at each stage:

- the colour phase, recognised by its instruction "Keep looking at the screen." (`.first()`: the text may appear in more than one place);
- a pose prompt, up to 10 seconds later. `/^(Turn your head|Lift your chin)/` is a **regular expression**: text that *starts with* (`^`) either phrase (`|` means "or") — the poses are random, so the test can't know which comes first;
- the result, "You're all set", within 45 seconds. Meanwhile the photos travel to the API, then to the inference service: the real face detector finds the face, liveness (in the labels test mode) accepts the poses, the stand-in model reports 30, and the decision engine says pass.

@@ 77-79
Press "Continue to …" (the `/^Continue to /` pattern matches any website's name). As the comment says, the verify page tells the shop's page, which closes the modal and goes to the shop's return address.

@@ 80
The shop's return route has done all its checks — the browser binding, the API's result, the token's signature — and the browser is now in the cellar.

@@ 81
The cellar shows its "Age verified" badge.

@@ 82
A full-page screenshot of the cellar.

@@ 84
The comment says what the last part checks: leaving forgets the pass.

@@ 85-86
Press **Leave the cellar**, and the front page appears again, offering a new age check.

@@ 87-88
Try the cellar's address directly: the shop sends the browser back to the front page, because the pass is gone. The end of the story.

@@ 89
The end of test 1.

@@ 91-95
**Test 2: the cellar stays closed without a pass.** Going straight to `/cellar` must land back at the entrance, with the "Verify my age" button.

@@ 97-108
**Test 3: a verify link without its secret explains what to do, in the person's language.** A link with a valid-looking session ID but no `#cs=` part must say "This link doesn't work" — and, in a browser set to Hindi, "यह लिंक काम नहीं करता" (§5.5.11).

@@ 110-116
**Test 4: a return link only works in the browser that started the check.** Opening the shop's return address directly — as someone would with a link sent by a friend — must lead to the "Please finish the check where you started it" page, because this browser never started that check.

@@ 118-122
**Test 5: the modal closes, and the shop is as it was.** Open the check, and wait for it inside the frame.

@@ 123-124
Press the modal's **Close**: the dialog is gone.

@@ 125
And the keyboard focus is back on the button that opened it, so someone using a keyboard carries on where they were. (This caught a real bug: the React button was *disabled* while busy, which threw the focus away.)

@@ 126
End of test 5.

@@ 128-131
**Test 6: no other website may frame a verify page.** Ask the verify page's web server directly for a page whose session doesn't exist: its policy must say `frame-ancestors 'none'` — no website at all may show it in a frame.

@@ 10-12
The API's address, for the document test, which creates its own session; the inference service's, for the probe; and the specimen passport the configuration drew.

@@ 133-134
**`steppedUp`** (§5.6.3) — a session the face check couldn't decide. The fake camera's portrait passes every face check, so this one is made through the API instead.

@@ 135-139
Create a session with the demo project's test key (handed over by the configuration), and keep its ID and client secret.

@@ 140-143
Start its flow with the secret, as the verify page would, and keep the flow token.

@@ 144-148
Three face attempts, each with a fresh challenge…

@@ 149-160
…whose three frames, labelled as frontal, are not pictures at all (the bytes `not a picture`): the inference service can't decode them, so each attempt is retried — and the third steps up.

@@ 161-169
Post each attempt; after the third, the outcome must be `step_up`. Return the session's ID and secret.

@@ 171-178
**Test — a person the face check can't decide confirms their age with a passport and a selfie.** It gets three minutes rather than the usual ninety seconds: on CI's machines, with no graphics card, reading the document and matching two faces is slow, and it once ran out of time there. Then open the verify page with the stepped-up session's link: the secret travels in the `#` fragment, as a real link carries it.

@@ 179-180
The step-up ending, and its new button.

@@ 182-189
The document stage says what will happen — including that the name and document number are never kept — before anything is chosen, and breaks no accessibility rule. On a computer its webcam is offered first (D43); the specimen passport is chosen through the file chooser beside it, as a person would choose a photo (`setInputFiles` fills the hidden file input).

@@ 220-224
The website's view, with the same test key: the session…

@@ 191-196
The selfie stage: the same camera screen as a face check, playing the fake camera's portrait — the same face as on the specimen. Its result, within two minutes: "You're all set".

@@ 218
A screenshot of the result.

@@ 269-273
**Test — an Age Pass saved after one check answers the next, with no camera** (Phase 9, §5.9.3). Three minutes: it runs two checks.

@@ 274-280
A policy of the website's own that accepts passes — no preset does.

@@ 281-288
**`session`** — a new session under that policy, and its verify link.

@@ 290-294
The first check: no pass is offered yet.

@@ 295-298
The camera, as in the first test.

@@ 299-301
After the pass, **Save an Age Pass**: twenty uses, until a date.

@@ 303-308
The next check, in the same browser: the pass is offered, and the page is still accessible (axe).

@@ 309-312
**Use my Age Pass**: passed, with no camera — and no offer to save passes, since a pass can't renew itself.

@@ 314-321
The website's view: completed, passed, and the token's `methods` say `age_pass`.

@@ 1
Reading a file whole, for the probe below (the specimen passport's bytes).

@@ 14-16
**`probeDocumentCheck`**: when the document test fails with *the checker is busy*, ask the inference service directly what it makes of the specimen passport — with the passport's own face as the selfie. That message can mean the service is busy, slow, or that the OCR couldn't run; the probe's answer says which, in the failure's message, which CI shows to anyone (its log needs a sign-in). Added 3 Nov, after the test failed so twice.

@@ 17-18
The passport's bytes, and a stopwatch.

@@ 19-27
The same request the API sends: the description of one frame, the frame, and the document, as a multipart form, allowed a minute.

@@ 28-31
How long it took; an answer other than 200 is reported with its first 200 characters.

@@ 32-36
Otherwise, what it found: the time it took (and its own measure of it), how many zone lines the OCR read, any problem (`ocr_unavailable` means Tesseract couldn't run or took too long), and the faces on the document.

@@ 37-40
No answer at all — refused, or over a minute — is reported too, with how long it waited.

@@ 210-217
And what the inference service says about the passport right now (the probe above), all in the one message; the original error stays attached as its cause.

@@ 197-209
If that heading never comes, the test fails with a message saying **what the page showed instead** and **what the API recorded** for the session (its status and outcome). The test once failed on GitHub, where only signed-in people can read the full log; a failing test's message, though, anyone can read.

@@ 225-228
…is completed with a pass, and its token's claims (the middle part of the JWT, decoded) say how: a face estimate, the document's MRZ and a face match.

@@ 230-237
**Test — the document camera** (decision D43): a session sent to the stronger check, opened, and the computer's camera chosen.

@@ 239-244
The *Take the photo* button works once the fake camera's picture shows (`take` names it once, for reuse), what to do is said, no accessibility rule is broken, and a screenshot is kept.

@@ 246-249
Taking the photo shows it, with the question to ask of it…

@@ 250-253
…taking it again turns the camera back on; then a photo is taken and used.

@@ 255-257
The verify flow goes on to the selfie, as it does with a chosen file. (The fake camera shows a portrait, not a passport, so the check itself isn't tried: the passport test above does that with a file.)

@@ 259-263
**Test — leaving the document camera** (D43): from the camera…

@@ 264-267
…*Choose a file instead* goes back to the document stage, with its file chooser and the camera's button.
