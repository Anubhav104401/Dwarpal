---
fingerprint: 67718a7700fb14cc
---
The **camera screen**: the live preview with an oval to line the face up with, a line of guidance, and the **Start** button. Since Phase 3 it does three new things (§5.3):

- **live guidance** — MediaPipe's face landmarker watches the preview and says, in plain words, what to fix: "Move a little closer", "Look straight at the camera";
- **the challenge** — when the person presses Start, it fetches a fresh challenge and plays it: colours that light the whole screen, then prompts to turn or tilt the head;
- **signals** — it notes what the browser can tell about itself (is a program driving it? is the camera a virtual one? was the page hidden?) and sends that along.

When the challenge is done, it switches the camera off at once and hands the labelled photos to the verify flow.

It is a **client component** (§4.17): it runs in the browser, where the camera is, and uses React's **hooks** — `useState` for values that change the screen, `useRef` for values that don't, and `useEffect` for work that must happen after the screen is drawn (§4.16).

@@ 1
`"use client"` — the line that makes this file a client component. It must be the very first line.

@@ 3
The `FaceLandmarker` type, from MediaPipe — only the type, so this line loads nothing. The landmarker itself is loaded later, and only if needed (`landmarker.ts`).

@@ 4
Three React hooks.

@@ 5
`createPortal` — React's way of drawing part of a component somewhere else in the page. Used for the full-screen colours (line 208).

@@ 7-11
Our own pieces: the saffron button style; the camera helpers; from `challenge.ts`, the `Challenge` type, `FRONTAL_YAW` (how straight "looking straight" must be) and `isVirtualCamera`; the `CapturedAttempt` type; and from `landmarker.ts`, the loader, the `Reading` type and `read`.

@@ 13-14
`GUIDANCE_GRACE_MS = 8000` — after 8 seconds, Start can be pressed even if the guidance isn't satisfied. As the comment says: the guidance only *advises*; the server decides. Someone whose face the landmarker reads badly — unusual lighting, glasses, a face it was not trained on well — must never be locked out by the page itself.

@@ 16-21
**`CameraViewProps`** — what the parent gives this component:

- `tip` — guidance from a previous attempt ("It's too dark…"), or `null` for the first one;
- `getChallenge` — a function that fetches a fresh challenge;
- `onCaptured` — a function to call with the captured attempt;
- `onCameraError` — a function to call if the camera fails.

Passing functions down like this — **callbacks** — keeps the camera screen simple: it doesn't need to know how the API is called or what happens with the photos.

@@ 23-25
**`FaceGuide`** — the oval overlay. Its two inputs: whether the check is running (`active`), and whether the guidance is happy with the face (`good`). In either case the outline is saffron (`stroke-brand-400`); otherwise white at 80 %.

@@ 26-27
An SVG drawing (§0.10) laid over the video: `absolute inset-0 size-full` stretches it over the whole preview, and `pointer-events-none` lets clicks pass through it. Its 400 × 300 drawing space matches the preview's 4 : 3 shape.

@@ 28-33
A **mask** named `face-window` — a stencil. Where a mask is white, things show; where it's black, they're hidden. This one is white everywhere except a black oval in the middle.

@@ 34
A rectangle covering everything, in near-black at 50 % opacity, **cut out by the mask**: it darkens the whole preview *except* the oval, so the eye goes straight to where the face should be.

@@ 35-42
The oval's outline: the same position and size as the mask's hole, no fill, a 3-unit line with rounded ends.

@@ 43
While the check runs, the outline becomes **dashed**: 6 units of line, 10 of gap. Otherwise it's solid (`undefined` leaves the attribute out).

@@ 44
While the check runs, the dashes **march** around the oval (`globals.css`), a sign that something is happening — but only for people who haven't asked for less motion (`motion-safe:`). Then the colour, `tone`.

@@ 45-48
The closing tags.

@@ 50-51
**`guidance`** — turn what the landmarker sees into one plain instruction, and say whether the face is ready (`good`). The checks go from the most basic problem to the finest, and the first one that applies wins.

@@ 52-54
No reading, or no face: ask the person to look at the camera.

@@ 55-57
More than one face.

@@ 58-60
The face is too small in the picture: too far away.

@@ 61-63
The face is off to one side.

@@ 64-66
The head is turned: its sideways angle is more than `FRONTAL_YAW` either way (`Math.abs` ignores the direction). The challenge starts with frontal photos, so the person should begin looking straight ahead.

@@ 67-68
All good: say so, and invite them to press Start.

@@ 70
**`CameraView`** — the screen itself. Its props are taken out by destructuring.

@@ 71
`video` — a **ref** to the `<video>` element, so the code can reach the real element in the page. `useRef` keeps the same box across every redraw; it starts empty (`null`) until React fills it.

@@ 72
`stream` — a ref holding the camera's stream, so it can be stopped later. A ref (rather than state) because changing it shouldn't redraw anything.

@@ 73-74
`landmarker` — the loaded MediaPipe landmarker, once there is one. `reading` — what it saw most recently. Both refs: the reading changes up to 60 times a second, and redrawing the screen that often for it would be wasteful. The challenge reads it directly when it needs it.

@@ 75
`hidden` — how long the page has been hidden: `since` (when it was last hidden, or `null` while it's showing) and `total` (milliseconds so far). `null as number | null` tells TypeScript that `since` may later hold a number.

@@ 76-83
The **state** — each piece with the function that changes it. Each time one of them changes, React draws the screen again:

- `ready` — has the video started showing pictures?
- `guide` — the current guidance text, and whether the face is good;
- `graceOver` — has the 8-second grace period passed?
- `running` — is the challenge in progress?
- `colour` — the colour on screen now, or `null`;
- `cue` — the pose instruction now, or `null`;
- `progress` — photos taken, out of how many. `[number, number]` is a **tuple** type: a list of exactly two numbers.

Also `reach` (added after the owner's tests) — how much of the current pose is reached, from 0 to 1, for the meter; `null` hides it.

@@ 85
**Open the camera when the screen appears.** `useEffect` runs its function after React has drawn the screen.

@@ 86
`active` — a flag that tells whether this screen is still showing. The function returned at the end (the **cleanup**) sets it to false when the screen goes away.

@@ 87-93
Open the camera. When the stream arrives: if the screen has been removed in the meantime, switch the camera straight off again and stop. Otherwise, keep the stream.

@@ 94-97
Show the stream in the `<video>` element. `srcObject` is how a live stream (rather than a file) is given to a video.

@@ 98-102
If opening failed — permission refused, no camera — tell the parent, unless the screen is already gone.

@@ 103
The end of the `then`.

@@ 104-108
**The cleanup**: when this screen disappears for any reason — finished, or the person navigates away — mark it inactive and **switch the camera off**. The camera light never stays on after the camera screen is gone.

@@ 109
The **dependency list**: run this effect again only if `onCameraError` changes. The parent makes sure it never does (`useCallback` in `verify-flow.tsx`), so the camera opens exactly once per screen.

@@ 111-115
**Live guidance**, as the comment says. This effect depends on `ready`, so it runs again when the video starts; until then, it does nothing.

@@ 116-118
The `active` flag again, the number of the scheduled screen refresh (to cancel it later), and the **grace timer**: after 8 seconds, `graceOver` becomes true.

@@ 119-123
Load the landmarker. It takes a moment — a few megabytes of model and WebAssembly. If the screen has gone by the time it arrives, close it straight away (`loaded?.close()`: only if one loaded) and stop.

@@ 124
Keep it.

@@ 125-128
**`loop`** — runs once per screen refresh. It stops as soon as the screen is gone or something is missing.

@@ 129
Read the face in the video's current picture. `performance.now()` gives MediaPipe the time, which it needs for following a face from one picture to the next.

@@ 130-131
Work out the guidance, and store it — but only if the text changed. `setGuide` given a function receives the previous value; returning that same object tells React nothing changed, so the screen isn't redrawn 60 times a second for nothing.

@@ 132-133
Ask to run again at the next screen refresh, keeping its number for cancelling.

@@ 134-138
If the landmarker couldn't be loaded at all (`null`: an old browser, or a blocked download), give up on guidance and let the person start at once. Otherwise, start the loop.

@@ 139
The end of the `then`.

@@ 140-147
**The cleanup**: stop the grace timer and the loop, close the landmarker — freeing its memory and the graphics card — and forget it. `[ready]` is the dependency list.

@@ 149
The comment explains the next effect: if the page is hidden during the check — another tab or app in front — something else could be playing to the camera in its place. The time is reported, and the server weighs it.

@@ 150-152
`onChange` — runs whenever the page is hidden or shown again. First, the time now.

@@ 153-154
Just hidden: remember when.

@@ 155-158
Shown again after being hidden: add the hidden stretch to the total, and clear `since`.

@@ 159
The end of `onChange`.

@@ 160-162
Listen for the browser's `visibilitychange` event for as long as the screen exists, and stop listening when it goes. The empty dependency list `[]` means: set this up once.

@@ 164
**`start`** — what the Start button does.

@@ 165-167
If the video element somehow isn't there, do nothing.

@@ 168
Mark the check as running: the button disables itself and the outline starts marching.

@@ 169-170
Fetch a fresh challenge from the server.

@@ 171
**Calm mode?** `matchMedia("(prefers-reduced-motion: reduce)")` asks whether the person has told their device they want less motion. If so, no colours are flashed (`camera.ts`).

@@ 172
Start counting hidden time afresh, for this check only.

@@ 173-180
**Play the challenge**, wiring each hook to the screen: colours, cues and the pose reach go straight into state; progress goes into `progress`; `readAngles` reads the latest landmarker reading (`?.` and `?? null`: `null` if there is no reading or it has no angles).

@@ 181
The camera's name, as the browser reports it — used to recognise virtual cameras. `?.` at each step guards against there being no stream or no track; `?? ""` gives an empty name then.

@@ 182-183
Switch the camera off immediately — before the photos are even uploaded.

@@ 184-187
Hand over the attempt: the challenge's ID, the labelled frames, and when the colours began.

@@ 188-193
And the **signals**:

- `automation` — `navigator.webdriver` is `true` when a program such as a test tool is driving the browser;
- `virtualCamera` — whether the camera's name looks like virtual-camera software;
- `hiddenMs` — the total hidden time;
- `lightShown` — whether the colours were shown (not in calm mode).

A dishonest browser can fake every one of these, which is why they can only make the check *stricter*.

@@ 194
The end of the attempt.

@@ 195-198
If anything failed — fetching the challenge, the camera — take any colour off the screen and report it like a camera error.

@@ 199
The end of `start`.

@@ 201
The progress, unpacked into two names.

@@ 202-204
**What the guidance line says.** While running: the pose instruction if there is one; otherwise, during the colours, "Keep looking at the screen."; otherwise the progress ("Hold still… 3 of 7"). Before starting: the tip from the last attempt, or the live guidance, or — while nothing is known yet — "Starting the camera…". `??` picks the first value that isn't `null` or `undefined`.

@@ 206-207
The screen's layout begins.

@@ 208-210
**The colour.** When there is one, draw it with `createPortal` …

@@ 211-212
… straight into the page's `<body>`, as the comment explains. The card around the camera has a blurred background, and in CSS such an element becomes the frame of reference for `fixed` elements inside it. A colour drawn inside the card would cover the card only — not enough light on the face. Drawn in the body, it covers the whole screen.

@@ 213-217
A layer covering the whole screen (`fixed inset-0`), above everything else (`z-40`), in the current colour. `aria-hidden` hides it from screen readers, which announce the guidance line instead. `transition-colors duration-200` softens each change over 0.2 seconds.

@@ 218-220
In its middle, a dark rounded label: "Keep looking at the screen."

@@ 221-223
The end of the layer, and the destination: `document.body`.

@@ 224
The preview box: a 4 : 3 rectangle (`aspect-[4/3]`), hiding anything that spills out (`overflow-hidden`), with rounded corners, a dark background while the camera starts, and a hair-thin ring around it.

@@ 225-232
**The live preview.** `ref={video}` connects the element to the ref. Three attributes make live video work on every browser: `autoPlay` (start immediately), `playsInline` (on iPhones, play inside the page rather than full-screen) and `muted` (browsers only autoplay silent video; there's no sound anyway). `onLoadedData` fires when the first picture arrives, which starts the guidance.

Its classes: fill the box (`size-full`), crop rather than squash (`object-cover`), and **mirror it** (`-scale-x-100` flips it left to right). People expect a front camera to behave like a mirror, and lining up a face in a non-mirrored image feels backwards. Only the preview is mirrored; the photos sent are not (`camera.ts`).

@@ 233
The oval overlay on top: active while running, saffron once the face is good.

@@ 234-238
Until the first picture arrives, show "Starting the camera…" in the middle of the box. `grid place-items-center` centres it both ways.

@@ 239-240
While there is a pose instruction, show a dark band at the bottom of the preview, so it can be read while turning the head.

@@ 241
The instruction — or, once the meter is full, "That's it — hold still…" while the three photos are taken.

@@ 242-243
**The pose meter** (added after the owner's first tests, in which people couldn't tell how far to turn). As the comment says, it fills as the person turns, so they can see when it is enough.

@@ 244
The meter's track: a thin, rounded, faint white bar. `aria-hidden` — screen readers get the instruction instead.

@@ 245-248
The filled part: as wide as the share reached (`width: 40%` for 0.4), saffron while filling and green when full. The width glides over a tenth of a second — `motion-safe:`, so for people who asked their system for reduced motion it simply jumps.

@@ 249-252
The closing tags.

@@ 253
The end of the preview box.

@@ 254-257
The guidance line. `aria-live="polite"` makes screen readers *announce* the text whenever it changes, after they finish what they're saying — so a blind person hears each instruction. `min-h-12` keeps its height steady, so the button doesn't jump when the text changes length.

@@ 258
What it says: `message`, worked out above.

@@ 259
The end of the guidance line.

@@ 260-267
**The Start button.** `type="button"` makes clear it submits no form. It is disabled until the video shows pictures, while the check is running (so it can't be pressed twice), and until the guidance is satisfied *or* the grace period is over. Its label changes while the check runs.

@@ 268-270
The closing tags.
