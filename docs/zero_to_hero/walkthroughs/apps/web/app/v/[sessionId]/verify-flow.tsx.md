---
fingerprint: 94183891a4adddd6
---
**The verify flow** — every screen a person sees during an age check, and the logic that moves between them. It is a **state machine** like the API's session (§5.1.2), but for the screen: at any moment the page is in exactly one **stage**, and each stage draws one screen.

```
loading ──► intro ──► camera ──► checking ──► finished (pass · fail · step up · reject)
   │                    ▲            │
   │                    └── retry ───┘
   └──────────► problem   (from anywhere: bad link, expired, camera refused, offline)
```

The whole page is one **client component**: it runs in the browser, because the camera, the secret in the link, and the flow token all live there (§4.17).

@@ 1
`"use client"` — this file runs in the browser.

@@ 3
From the browser SDK (decision D16): the name every message carries, and the messages' type — the very ones the SDK reads on the website's side, so the two can't drift apart.

@@ 5
From React: the `ReactNode` type and four hooks (§4.16).

@@ 7-24
The shared styles (since Phase 6 with the quiet button) and page frame, the choice of tip and problem (`advice.ts`), the Age Pass's functions and types (Phase 9), the `Challenge` type, the document photo's preparation (§5.6.3), the flow client and its types — including `CapturedAttempt`, what one attempt produced — and the camera screen — and since 9 Nov `canFilmDocument` (`document-camera.ts`): whether this computer can film the document.

@@ 27
`Ending` — the four ways a check can end.

@@ 29-43
**`Stage`** — every possible stage, as a **discriminated union** (§4.15): a list of object shapes that each carry a `kind`. Checking `stage.kind` tells TypeScript exactly which other fields exist. After `if (stage.kind === "camera")`, the code may use `stage.tip`; in any other stage, TypeScript refuses it. Impossible combinations — a "checking" screen without a session, say — can't even be written.

- `loading` — waiting for the API;
- `intro` — the explanation and the "Start the camera" button; since Phase 9, `passRefused` when an Age Pass was just refused;
- `camera` — the camera screen, with a tip after a retry;
- `checking` — photos uploaded, waiting for the decision;
- `document` (§5.6.3) — the document check's explanation and its photo button, with a tip after a retry;
- `documentCamera` (§5.6.5, since 9 Nov) — a computer's webcam photographing the document (D43);
- `selfie` — the document's photo chosen and prepared (`document`), and the camera for the selfie;
- `finished` — an ending; since Phase 9, `earned` when a face or document check passed just now, the only time passes may be saved;
- `problem` — something stopped the check, with the request ID if the API gave one.

As the comment says, a tip or a problem is kept as the **key** of its words (§5.5.11), and put into the page's language only when shown.

@@ 45-46
**`takeSecretFromLink`** — read the one-time secret from the link, then wipe it from the address bar.

@@ 47
`window.location.hash` is the address's fragment, such as `#cs=vs_…_secret_…`. `.slice(1)` drops the `#`, and `URLSearchParams` reads it as `name=value` pairs; `.get("cs")` returns the secret, or `null`.

@@ 48-50
If there was a secret, rewrite the address **without its fragment**, using `history.replaceState`. It *replaces* the current entry in the browser's history rather than adding one, so the secret is gone from the address bar, from the back button's history, and from any screenshot the person might take.

@@ 51-52
Return the secret.

@@ 54-58
**`framingWebsite`** (decision D16) — the website whose frame this page is in, if any. `window.parent` is the page around a frame; for a page on its own, it is the page itself. Inside a frame, the answer is the session's return origin — the one website this page will talk to. The browser has already made sure no other website could frame it (`proxy.ts`).

@@ 60
**`problemStage`** — turn any error into a `problem` stage.

@@ 61-63
An error from the API: the message for its code, and its request ID.

@@ 64-69
Errors from the camera are **`DOMException`s**, the browser's own error type, named by kind: `NotAllowedError` when permission was refused, `NotFoundError` when there's no camera. Each gets its own message.

@@ 70-71
Anything else: the general message (`unknown` isn't in the list of codes).

@@ 73-78
**`endingOf`** — the ending of a session that was already finished when the page opened (for example, after a reload): awaiting a stronger check means "step up"; a stored "pass" or "fail" is used as it is; anything else is treated as "reject" — the safe choice, which never lets anyone through.

@@ 80
**`Icon`** — the round-cornered square with a symbol at the top of each result screen. `tone` gives its colours; `children` is the symbol's drawing.

@@ 81-95
A 48-pixel tile, holding a 24 × 24 SVG drawn with lines (`stroke`) in the tile's text colour (`currentColor`), with no fill. It is decoration, so it is hidden from screen readers.

@@ 143
**Start the flow, once, when the page appears.**

@@ 144
The `active` flag, as in `camera-view.tsx`.

@@ 145
`??=` assigns only if the current value is `null` or `undefined`: read the secret from the link *only the first time*.

!!! why "Why store the secret in a ref?"
    In development, React's **Strict Mode** deliberately runs every effect twice — set up, clean up, set up again — to expose code that breaks when that happens. The first run removes the secret from the address; a second run that read the address again would find nothing, and show "This link doesn't work". Keeping the secret in a ref, which survives between the two runs, makes the effect safe to repeat.

@@ 146-149
No secret in the link at all: show "This link doesn't work" and stop.

@@ 150-151
Make a flow client, and start the flow with the secret.

@@ 152-156
When the session arrives — and the page is still active — keep the client for the later steps.

@@ 157
Note whether the page is in the session's website's frame.

@@ 168-173
Then choose the stage: a session in progress shows the intro; a finished one (after a reload) goes straight to its ending.

@@ 174-178
If starting failed, show the problem.

@@ 179-183
The cleanup, and the dependency list: the effect depends on the API's address and the session's ID, which never change while the page is open.

@@ 185
**`onCameraError`** — the camera screen's error callback. `useCallback(…, [])` makes React keep the *same* function across every redraw. That matters: the camera screen opens the camera in an effect that depends on this function, and a new function on each redraw would close and re-open the camera every time.

@@ 187-190
**`getChallenge`** (Phase 3) — fetch a fresh challenge for the camera screen. If the check hasn't started yet there is no client, and it returns a **rejected** promise (a promise that holds an error) rather than crashing. `useCallback` with an empty list keeps the same function between renders, because it reads the client through the `flow` ref.

@@ 192
**`onCaptured`** — called with the captured attempt. It receives the session too, so it can carry the session into the next stage.

@@ 193-196
Use the flow client; without one (which shouldn't happen) do nothing.

@@ 197
Show the "checking" screen.

@@ 198-199
Upload the attempt, and wait for the decision.

@@ 200
A copy of the session with the updated number of attempts left.

@@ 201-205
**A retry** goes back to the camera, now with a tip for the main problem. **Anything else** is an ending — and TypeScript knows that, apart from "retry", every outcome *is* an `Ending`. A pass is marked `earned`.

@@ 324-329
**`tellWebsite`** — send a message to the framing website with `postMessage`, naming its origin as the only one that may receive it. If the page around has moved to another website meanwhile, the browser drops the message. On its own, the page tells no one.

@@ 331
**`leave`** — what the "Continue" button does.

@@ 332-336
Use the flow client, and show "Returning…" on the button.

@@ 337-338
Ask the API where to go.

@@ 339-343
In a frame, the page can't (and mustn't) move the website's tab itself: it tells the website the check is *finished*, with the return address, and the website's page goes there (the SDK checks the address is the website's own). The button stays at "Returning…" meanwhile.

@@ 344-347
On its own, go there: `window.location.assign` navigates the whole tab to the website's return address.

@@ 348-350
If finishing failed, show the problem.

@@ 351-352
If there was nowhere to go, or it failed, re-enable the button.

@@ 354-362
**Loading**: a card with a short message. `aria-busy="true"` tells screen readers that this part of the page is still loading.

@@ 364-392
**A problem**: a neutral grey warning icon (a triangle with an exclamation mark), the title, the explanation; in a website's frame, a button that asks the website to **open the check in a full page** — for when a browser won't let a frame use the camera, say (the check then carries on there, with the same link); and — if the API gave one — the request ID as a **reference** in small monospace letters (`font-mono`). If the person contacts the website for help, that reference leads straight to the right line in the logs (§4.13).

@@ 394-396
From here on, every stage has a session: take it out, and make the label for the top-right corner, such as "Amber Cellars (demo) · 18+", from its words; and `tries`, the attempts left in words ("2 tries left", "Last try" — next-intl picks the plural form each language needs).

@@ 398-409
**The intro**: the heading names the age; the paragraph names the website. A document-only check (D24) has its own lead sentence, saying the website checks age with an ID document; `steps` is the list shown below it.

@@ 410-419
The three promises as a **numbered list** (`<ol>`). `PROMISES.map(…)` turns each text into a list item; React needs a stable **`key`** for every item of a list, to tell them apart between redraws — the text itself serves. Each number sits in a small saffron circle, in the darker `brand-700` so it is readable (§5.5.5). In a document-only check the list is the document check's three steps instead (`steps`).

@@ 443-455
"Start the camera" moves to the camera stage, with no tip yet. The camera is only switched on *after* the person has read what will happen, and clicked. When an Age Pass is offered, this button becomes the quiet one: one loud button per screen. In a document-only check (D24) the same button says "Use a passport or ID card" and opens the document check instead of the camera.

@@ 456-459
The closing tags.

@@ 461-470
**The camera stage**: the camera screen, given the tip, the way to fetch a challenge, a callback that adds the session to the captured attempt, and the error callback.

@@ 471-477
Below it, the attempts left — "Last try" when one remains.

@@ 567-581
**Checking**: a spinning ring (`animate-spin` on a circle whose top border alone is saffron; it holds still for reduced-motion visitors) and two lines of text. `role="status"` makes screen readers announce "Checking your photos…".

@@ 583
**An ending** — the only stage left. Look its screen up in `ENDINGS`.

@@ 584-589
The icon, in the ending's colours, drawing the ending's symbol with rounded line ends.

@@ 590-593
The title and body text in the page's language (§5.5.11), with the website's name and the age filled in.

@@ 646-649
The closing tags.

@@ 263-268
**`onSelfieCaptured`** — the selfie was taken. As for a face attempt, nothing happens without a client.

@@ 269-272
Show "checking", upload the document and the selfie together, and remember the tries left.

@@ 273-282
A retry goes back to the document stage, with the reason turned into a tip. Anything else is an ending; the API never answers a document check with another step-up, but if it did, it would count as a fail, never a pass. A pass is marked `earned`.

@@ 283-288
Any error — the network, the API — becomes a problem screen, as everywhere on this page.

@@ 479-491
**The document stage** (§5.6.3): the heading, and the tip after a retry — in amber, and marked `role="alert"` so screen readers announce it as soon as it appears.

@@ 492-501
The three steps, as numbered circles, styled like the intro's promises.

@@ 512-525
The photo button. On a phone, a file input with `capture="environment"` opens the **rear camera**; on a computer, it opens a file picker. The input itself is hidden visually (`sr-only`, still there for screen readers and the keyboard), and its `<label>` wears the button's look — clicking a label clicks its input. `has-focus-visible:` gives the label the focus ring whenever the hidden input has keyboard focus, as the comment says. Only JPEG, PNG and WebP pictures are offered. Since 9 Nov, on a computer it comes second, in the quiet style, as *Choose a photo file instead*.

@@ 550-565
**The selfie stage**: a line saying the document's photo is ready and why a selfie follows, then the very same camera screen as a face check — its challenge, poses and colours — whose capture goes to `onSelfieCaptured` with the document.

@@ 4
`useTranslations` — next-intl's way for a component to get its words, in the page's language (§5.5.11); and since Phase 9 `useFormatter`, for writing a date the way the page's language does.

@@ 97-103
**`ENDINGS`** — how each of the four result screens looks: its icon's colours and shape — green with a tick for a pass, rose with a cross for a fail or an incomplete check, amber with an exclamation mark for a step-up. Their words are in `Verify.ending` in the message files (§5.5.11).

@@ 105
**`PROMISES`** — the keys of the three numbered promises on the intro screen: what will happen, what the AI does and doesn't do, and what happens to the photos.

@@ 107-108
**`DOCUMENT_STEPS`** (§5.6.3) — the keys of the document check's three steps, said *before* anything is chosen, as the design asks of consent: the photo, the selfie and why, and exactly what is read, what is never kept, and that both photos are deleted straight after.

@@ 110-111
**`DOCUMENT_TRIES`** — how many tries the document check allows, the API's own number, shown before the first answer gives the real count.

@@ 127-130
**`VerifyFlow`** — the whole page. Its state: the stage, whether it is leaving, the website framing it (if any).

@@ 131
`documentTries` — the document check's tries left, updated from each answer.

@@ 136-139
The page's words, in three groups (`messages/`, §5.5.11): its own (`Verify`), the tips and the problems; and the formatter for dates.

@@ 140-141
Two **refs** (§4.17): the secret and the flow client, kept between draws without causing one.

@@ 113-114
How many Age Passes are saved at once (Phase 9): twenty, as the API gives.

@@ 116-121
**`Saving`** — the state of saving passes after a passed check: not started, under way, saved (how many, until when), or failed.

@@ 123-125
The refusals that say nothing against a pass itself — an expired nonce, a website that doesn't take passes. On any other `age_pass_` refusal, the pass is removed: it would never be accepted.

@@ 134-135
Since Phase 9: the kept pass that can answer this check, if any, and the state of saving passes.

@@ 158-167
**An Age Pass** (Phase 9): if the session is still open, its website takes passes, and this page isn't inside another website's frame, look for a kept pass. Inside a frame, browsers give each website a separate storage area for the framed page, so a pass saved there would be found only under that website again — and offering passes in one place but not another would only confuse. If the browser has no storage at all (a private window, say), the camera works as always.

@@ 206-209
If the upload failed, show the problem. The end of the callback.

@@ 211-217
**`answerWithPass`** (Phase 9) — answer the check with a kept pass. The checking screen shows while it works.

@@ 218-224
Ask for a nonce; make the presentation for the pass's line; send it. Passed: the pass is forgotten — each pass works once — and the check is finished, not `earned`: a pass doesn't give out new passes.

@@ 225-233
A refusal about the pass: no pass is offered any more, the pass is removed unless the refusal said nothing against it, and the introduction returns with a notice — the camera is the way on.

@@ 234-236
Anything else (the network, say) is a problem, as for the camera. The end of the callback.

@@ 290-297
**`savePasses`** (Phase 9) — save a batch of passes. The saving state shows while it works.

@@ 298-303
Make twenty key pairs; send their public halves; read back the passes and their expiry.

@@ 304-317
Pair each pass with its key's private half, the lines, the expiry and the mode, and keep them all in IndexedDB.

@@ 318-322
Saved: show how many, and until when. Anything that went wrong: say saving failed — the check itself has passed either way.

@@ 420-427
After a refused pass, a notice saying so, in a region screen readers announce.

@@ 428-442
**The Age Pass's offer**, when a kept pass can answer this check: a panel with a title, what the pass will show — this website, this line, only that, no camera — and the loud button, **Use my Age Pass**.

@@ 594-607
At the end: after a step-up, two choices — **"Use a passport or ID card"**, the loud one, which starts the document stage; and **"Not now — return to …"**, the quiet one, for someone who would rather not. "Returning…" while it works.

@@ 608-610
**Saving passes** (Phase 9) is offered only after a pass earned just now, where the website takes passes, and on this page's own tab: a panel.

@@ 611-617
Saved: how many uses, and until when, as a date written the page's way ("January 31, 2027"; in Hindi, the Hindi way), in a region screen readers announce.

@@ 618-637
Not yet saved: the title, what an Age Pass is and isn't — no photo, name or date of birth; twenty uses in ninety days; nothing websites can recognise someone by — a failure message if saving failed, and the quiet **Save an Age Pass** button, which says "Saving…" while it works.

@@ 638-645
Every ending but the step-up then has its one loud button, "Continue to …", and "Returning…" while it works.

@@ 25
The document camera (decision D43), in its own file.

@@ 132-133
**`computer`** — whether the document can be photographed with this computer's webcam (D43). It starts `false`, as the server renders the page, and is set once the page runs in the browser, the only place that can tell.

@@ 238
Once in the browser, find out (`canFilmDocument`: a mouse or trackpad, and a camera API).

@@ 240-252
**`onDocumentChosen`** — the person chose a photo, or (since 9 Nov) took one with the document camera: either way a `Blob`, which a chosen file is too. None at all means the picker was cancelled, and nothing happens. The photo is prepared for sending — scaled, re-encoded, under the size limit (`document-photo.ts`) — and the selfie stage begins with it. A file the browser can't read as a picture brings the document stage back with the `document_unusable` tip.

@@ 254-261
**`onDocumentCameraUnavailable`** (D43) — the webcam couldn't be opened: back to the document stage, with a tip to choose a file instead. It reads the current stage (`setStage` given a function) instead of being given the session, so it can stay the same function forever (`useCallback` with no dependencies): the camera component opens the camera again whenever it gets a new one.

@@ 502-511
On a computer (D43), a button for its webcam comes first, in the accent style; it opens the `documentCamera` stage.

@@ 526
The tries left, or "Last try".

@@ 527-530
The end of the document stage's card and page.

@@ 532-536
**The document camera's stage** (D43): the same title, in the same card…

@@ 537-543
…and the camera (`document-camera.tsx`). A photo taken and accepted goes the way a chosen file does (`onDocumentChosen`); *Choose a file instead* goes back to the document stage; a camera that can't be opened goes back too, with a tip.

@@ 544
The tries left.

@@ 545-548
The end of the document camera's card and page.
