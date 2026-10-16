---
fingerprint: c615c796c216bcd2
---
The **camera screen**: the live preview with an oval to line the face up with, a line of guidance, and the "Take photos" button. When the burst is done, it switches the camera off at once and hands the photos to the verify flow.

It is a **client component** (§4.17): it runs in the browser, where the camera is, and uses React's **hooks** — `useState` for values that change the screen, `useRef` for values that don't, and `useEffect` for work that must happen after the screen is drawn (§4.16).

@@ 1
`"use client"` — the line that makes this file a client component. It must be the very first line.

@@ 3
Three React hooks.

@@ 5-7
The saffron button style, the camera helpers, and the frame type.

@@ 9-13
**`CameraViewProps`** — what the parent gives this component:

- `tip` — guidance from a previous attempt ("It's too dark…"), or `null` for the first one;
- `onCaptured` — a function to call with the photos;
- `onCameraError` — a function to call if the camera fails.

Passing functions down like this — **callbacks** — keeps the camera screen simple: it doesn't need to know what happens with the photos.

@@ 15-16
**`FaceGuide`** — the oval overlay. Its one input says whether photos are being taken.

@@ 17-18
An SVG drawing (§0.10) laid over the video: `absolute inset-0 size-full` stretches it over the whole preview, and `pointer-events-none` lets clicks pass through it. Its 400 × 300 drawing space matches the preview's 4 : 3 shape.

@@ 19-24
A **mask** named `face-window` — a stencil. Where a mask is white, things show; where it's black, they're hidden. This one is white everywhere except a black oval in the middle.

@@ 25
A rectangle covering everything, in near-black at 50 % opacity, **cut out by the mask**: it darkens the whole preview *except* the oval, so the eye goes straight to where the face should be.

@@ 26-33
The oval's outline: the same position and size as the mask's hole, no fill, a 3-unit line with rounded ends.

@@ 34
While capturing, the outline becomes **dashed**: 6 units of line, 10 of gap. Otherwise it's solid (`undefined` leaves the attribute out).

@@ 35
While capturing, the dashes **march** around the oval in saffron (`globals.css`), a sign that something is happening; otherwise the outline is white at 80 %.

@@ 36-39
The closing tags.

@@ 41
**`CameraView`** — the screen itself. Its props are taken out by destructuring.

@@ 42
`video` — a **ref** to the `<video>` element, so the code can reach the real element in the page. `useRef` keeps the same box across every redraw; it starts empty (`null`) until React fills it.

@@ 43
`stream` — a ref holding the camera's stream, so it can be stopped later. A ref (rather than state) because changing it shouldn't redraw anything.

@@ 44-46
Three pieces of **state**, each with the function that changes it:

- `ready` — has the video started showing pictures?
- `taken` — how many photos of the burst are done;
- `capturing` — is a burst in progress?

Each time one of them changes, React draws the screen again.

@@ 48
**Open the camera when the screen appears.** `useEffect` runs its function after React has drawn the screen.

@@ 49
`active` — a flag that tells whether this screen is still showing. The function returned at the end (the **cleanup**) sets it to false when the screen goes away.

@@ 50-56
Open the camera. When the stream arrives: if the screen has been removed in the meantime, switch the camera straight off again and stop. Otherwise, keep the stream.

@@ 57-60
Show the stream in the `<video>` element. `srcObject` is how a live stream (rather than a file) is given to a video.

@@ 61-65
If opening failed — permission refused, no camera — tell the parent, unless the screen is already gone.

@@ 66
The end of the `then`.

@@ 67-71
**The cleanup**: when this screen disappears for any reason — finished, or the person navigates away — mark it inactive and **switch the camera off**. The camera light never stays on after the camera screen is gone.

@@ 72
The **dependency list**: run this effect again only if `onCameraError` changes. The parent makes sure it never does (`useCallback` in `verify-flow.tsx`), so the camera opens exactly once per screen.

@@ 74
**`capture`** — what the button does.

@@ 75-77
If the video element somehow isn't there, do nothing.

@@ 78
Mark the burst as running: the button disables itself and the outline starts marching.

@@ 79-83
Take the burst, reporting progress through `setTaken` — which *is* a function taking a number, so it can be passed straight in as the progress callback. Then switch the camera off immediately — before the photos are even uploaded — and hand them over.

@@ 84-86
If anything failed while capturing, report it like a camera error.

@@ 87
The end of `capture`.

@@ 89-91
The screen's layout. First, the preview box: a 4 : 3 rectangle (`aspect-[4/3]`), hiding anything that spills out (`overflow-hidden`), with rounded corners, a dark background while the camera starts, and a hair-thin ring around it.

@@ 92-99
**The live preview.** `ref={video}` connects the element to the ref. Three attributes make live video work on every browser: `autoPlay` (start immediately), `playsInline` (on iPhones, play inside the page rather than full-screen) and `muted` (browsers only autoplay silent video; there's no sound anyway). `onLoadedData` fires when the first picture arrives, which enables the button.

Its classes: fill the box (`size-full`), crop rather than squash (`object-cover`), and **mirror it** (`-scale-x-100` flips it left to right). People expect a front camera to behave like a mirror, and lining up a face in a non-mirrored image feels backwards. Only the preview is mirrored; the photos sent are not (`camera.ts`).

@@ 100
The oval overlay on top.

@@ 101-105
Until the first picture arrives, show "Starting the camera…" in the middle of the box. `grid place-items-center` centres it both ways.

@@ 106
The end of the preview box.

@@ 107-110
The guidance line. `aria-live="polite"` makes screen readers *announce* the text whenever it changes, after they finish what they're saying — so a blind person hears the tip, and then the progress. `min-h-12` keeps its height steady, so the button doesn't jump when the text changes length.

@@ 111-113
What it says: while capturing, the progress ("Hold still… 3 of 5"); otherwise, the tip from the last attempt — or, the first time, the basic guidance.

@@ 114
The end of the guidance line.

@@ 115-122
**The button.** `type="button"` makes clear it submits no form. It is disabled until the video shows pictures, and while a burst is running, so it can't be pressed twice. Its label changes while photos are taken.

@@ 123-125
The closing tags.
