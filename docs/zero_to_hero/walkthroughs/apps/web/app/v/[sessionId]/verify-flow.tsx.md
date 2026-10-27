---
fingerprint: 7be7be0ba77af190
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
From React: the `ReactNode` type and four hooks (§4.16).

@@ 5-10
The shared styles and page frame, the friendly messages, the `Challenge` type, the flow client and its types — including `CapturedAttempt`, what one attempt produced — and the camera screen.

@@ 12
`Ending` — the four ways a check can end.

@@ 14-20
**`Stage`** — every possible stage, as a **discriminated union** (§4.15): a list of object shapes that each carry a `kind`. Checking `stage.kind` tells TypeScript exactly which other fields exist. After `if (stage.kind === "camera")`, the code may use `stage.tip`; in any other stage, TypeScript refuses it. Impossible combinations — a "checking" screen without a session, say — can't even be written.

- `loading` — waiting for the API;
- `intro` — the explanation and the "Start the camera" button;
- `camera` — the camera screen, with a tip after a retry;
- `checking` — photos uploaded, waiting for the decision;
- `finished` — an ending;
- `problem` — something stopped the check, with the request ID if the API gave one.

@@ 22-23
**`takeSecretFromLink`** — read the one-time secret from the link, then wipe it from the address bar.

@@ 24
`window.location.hash` is the address's fragment, such as `#cs=vs_…_secret_…`. `.slice(1)` drops the `#`, and `URLSearchParams` reads it as `name=value` pairs; `.get("cs")` returns the secret, or `null`.

@@ 25-27
If there was a secret, rewrite the address **without its fragment**, using `history.replaceState`. It *replaces* the current entry in the browser's history rather than adding one, so the secret is gone from the address bar, from the back button's history, and from any screenshot the person might take.

@@ 28-29
Return the secret.

@@ 31
**`problemStage`** — turn any error into a `problem` stage.

@@ 32-34
An error from the API: the message for its code, and its request ID.

@@ 35-40
Errors from the camera are **`DOMException`s**, the browser's own error type, named by kind: `NotAllowedError` when permission was refused, `NotFoundError` when there's no camera. Each gets its own message.

@@ 41-42
Anything else: the general message (`unknown` isn't in the list of codes).

@@ 44-49
**`endingOf`** — the ending of a session that was already finished when the page opened (for example, after a reload): awaiting a stronger check means "step up"; a stored "pass" or "fail" is used as it is; anything else is treated as "reject" — the safe choice, which never lets anyone through.

@@ 51
**`Icon`** — the round-cornered square with a symbol at the top of each result screen. `tone` gives its colours; `children` is the symbol's drawing.

@@ 52-66
A 48-pixel tile, holding a 24 × 24 SVG drawn with lines (`stroke`) in the tile's text colour (`currentColor`), with no fill. It is decoration, so it is hidden from screen readers.

@@ 68-71
**`ENDINGS`** — the four result screens, as data: for each ending, a title, the body text (a function, because the text includes the website's name and age), the colours, and the icon's drawing. A `Record<Ending, …>` must have an entry for *every* ending — if a fifth were added to `Ending`, TypeScript would refuse to compile until its screen was written here.

@@ 72-78
**Pass** — "You're all set", in green, with a tick. The text tells the person exactly what the website learned: that they are old enough, *nothing else*.

@@ 79-84
**Fail** — in rose, with a cross; it states the result without judging the person.

@@ 85-91
**Step up** — in amber, with an exclamation mark: too close to call; the website will offer another way.

@@ 92-97
**Reject** — in rose. Deliberately vague, like the API (§5.1.3): it says only that the check couldn't be completed, never why.

@@ 98
The end of the endings.

@@ 100-104
**`PROMISES`** — the three numbered promises on the intro screen: what will happen, what the AI does and doesn't do, and what happens to the photos.

@@ 106
**`VerifyFlow`** — the component. It receives the session's ID and the API's address from the server page.

@@ 107
`stage` — the current stage, starting at `loading`. `useState<Stage>` names its type.

@@ 108
`leaving` — true while the "Continue" button is fetching the return address.

@@ 109-110
Two refs: the secret, and the flow client once `start` has succeeded.

@@ 112
**Start the flow, once, when the page appears.**

@@ 113
The `active` flag, as in `camera-view.tsx`.

@@ 114
`??=` assigns only if the current value is `null` or `undefined`: read the secret from the link *only the first time*.

!!! why "Why store the secret in a ref?"
    In development, React's **Strict Mode** deliberately runs every effect twice — set up, clean up, set up again — to expose code that breaks when that happens. The first run removes the secret from the address; a second run that read the address again would find nothing, and show "This link doesn't work". Keeping the secret in a ref, which survives between the two runs, makes the effect safe to repeat.

@@ 115-118
No secret in the link at all: show "This link doesn't work" and stop.

@@ 119-120
Make a flow client, and start the flow with the secret.

@@ 121-125
When the session arrives — and the page is still active — keep the client for the later steps.

@@ 126-131
Then choose the stage: a session in progress shows the intro; a finished one (after a reload) goes straight to its ending.

@@ 132-136
If starting failed, show the problem.

@@ 137-141
The cleanup, and the dependency list: the effect depends on the API's address and the session's ID, which never change while the page is open.

@@ 143
**`onCameraError`** — the camera screen's error callback. `useCallback(…, [])` makes React keep the *same* function across every redraw. That matters: the camera screen opens the camera in an effect that depends on this function, and a new function on each redraw would close and re-open the camera every time.

@@ 145-148
**`getChallenge`** (Phase 3) — fetch a fresh challenge for the camera screen. If the check hasn't started yet there is no client, and it returns a **rejected** promise (a promise that holds an error) rather than crashing. `useCallback` with an empty list keeps the same function between renders, because it reads the client through the `flow` ref.

@@ 150
**`onCaptured`** — called with the captured attempt. It receives the session too, so it can carry the session into the next stage.

@@ 151-154
Use the flow client; without one (which shouldn't happen) do nothing.

@@ 155
Show the "checking" screen.

@@ 156-157
Upload the attempt, and wait for the decision.

@@ 158
A copy of the session with the updated number of attempts left.

@@ 159-163
**A retry** goes back to the camera, now with a tip for the main problem. **Anything else** is an ending — and TypeScript knows that, apart from "retry", every outcome *is* an `Ending`.

@@ 164-167
If the upload failed, show the problem. The end of the callback.

@@ 169
**`leave`** — what the "Continue" button does.

@@ 170-174
Use the flow client, and show "Returning…" on the button.

@@ 175-180
Ask the API where to go, and go there. `window.location.assign` navigates the whole tab to the website's return address.

@@ 181-183
If finishing failed, show the problem.

@@ 184-185
If there was nowhere to go, or it failed, re-enable the button.

@@ 187-195
**Loading**: a card with a short message. `aria-busy="true"` tells screen readers that this part of the page is still loading.

@@ 197-212
**A problem**: a neutral grey warning icon (a triangle with an exclamation mark), the title, the explanation, and — if the API gave one — the request ID as a **reference** in small monospace letters (`font-mono`). If the person contacts the website for help, that reference leads straight to the right line in the logs (§4.13).

@@ 214-215
From here on, every stage has a session: take it out, and make the label for the top-right corner, such as "Amber Cellars · 18+".

@@ 217-224
**The intro**: the heading names the age; the paragraph names the website.

@@ 225-234
The three promises as a **numbered list** (`<ol>`). `PROMISES.map(…)` turns each text into a list item; React needs a stable **`key`** for every item of a list, to tell them apart between redraws — the text itself serves. Each number sits in a small saffron circle, in the darker `brand-700` so it is readable (§5.5.5).

@@ 235-241
"Start the camera" moves to the camera stage, with no tip yet. The camera is only switched on *after* the person has read what will happen, and clicked.

@@ 242-245
The closing tags.

@@ 247-256
**The camera stage**: the camera screen, given the tip, the way to fetch a challenge, a callback that adds the session to the captured attempt, and the error callback.

@@ 257-263
Below it, the attempts left — "Last try" when one remains.

@@ 265-279
**Checking**: a spinning ring (`animate-spin` on a circle whose top border alone is saffron; it holds still for reduced-motion visitors) and two lines of text. `role="status"` makes screen readers announce "Checking your photos…".

@@ 281
**An ending** — the only stage left. Look its screen up in `ENDINGS`.

@@ 282-287
The icon, in the ending's colours, drawing the ending's symbol with rounded line ends.

@@ 288-289
The title, and the body text built for this session.

@@ 290-292
"Continue to Amber Cellars", or "Returning…" while it works.

@@ 293-296
The closing tags.
