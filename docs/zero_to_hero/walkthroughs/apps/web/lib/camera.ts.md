---
fingerprint: e97fb213a8e99cb5
---
Everything the verify page does with the **camera**: open it, play a liveness challenge on it, and switch it off (§4.19). Since Phase 3 the photos are no longer a quick burst of identical shots. The page plays the server's **challenge** (§5.3): first a few screen colours, one photo per colour, then a head pose per prompt, three photos per pose once it is held. Each photo is **labelled** with the part of the challenge it belongs to.

The photos never touch the device's storage: they exist as bytes in the page's memory, travel once to the API, and are forgotten.

@@ 1
The doc comment: open the camera, play a challenge on it — screen colours, then head poses — and switch it off.

@@ 3-11
From `challenge.ts`: the `Challenge` type, `CUES` (the instruction for each pose), `frontalAngles` (the person's own angles when facing the camera), the types `HeadAngles`, `Phase` and `Pose`, and `poseProgress`, which says how much of a pose the head has reached. The list is written one name per line because it is too long for one.

@@ 13
`MAX_WIDTH = 960` — photos are at most 960 pixels wide. More pixels wouldn't help the AI, which works on small, aligned face crops (§5.1.1); they would only make the upload bigger and slower.

@@ 14
`JPEG_QUALITY = 0.85` — 85 % JPEG quality: visually almost perfect, and a fraction of the size of an uncompressed picture. A 960 × 540 photo then comes to well under the 512 KiB limit per frame.

@@ 15-17
**Calm mode.** Some people set their device to **reduce motion** — flashing colours can be uncomfortable, and for a few people with photosensitive conditions, harmful. For them the page shows no colours and instead takes `CALM_BASELINE = 4` ordinary frames, `CALM_GAP_MS = 300` milliseconds apart. The light check then simply has nothing to measure, which never counts against anyone (it is recorded, not decided on).

@@ 18-19
`POSE_TIMEOUT_MS = 6000` — wait at most 6 seconds for each pose. Then the photos are taken anyway. As the comment says, the server judges every photo itself; the page's own view of the head only decides *when* to take them. A page that refused to go on would lock out anyone whose face the guidance can't read. `export` lets the camera screen use the same number.

@@ 20-21
`STEADY_READINGS = 3` — a pose counts as reached only after 3 readings in a row show it (about a twentieth of a second). A head passing through the pose on its way somewhere else doesn't trigger the photos.

@@ 22-24
Once a pose is held, take `FRAMES_PER_POSE = 3` photos of it, `POSE_GAP_MS = 150` milliseconds apart. The comment gives the reason, learned in the owner's tests: with a single photo, a blink or a small movement at the wrong moment could spoil the pose. The server counts the best of the three.

@@ 26-30
**`LabelledFrame`** — one photo: the JPEG as a `Blob` (a chunk of raw bytes held by the browser), when it was taken (`tMs`, milliseconds since the challenge began), and its `phase` — `"baseline"` for the colour photos, or the pose it was taken for.

@@ 32-44
**`ChallengeHooks`** — how the camera code talks to the screen, without knowing anything about how the screen looks:

- `onColour` — show this colour around the screen, or none (`null`);
- `onCue` — show this instruction, such as "Turn your head to your left, eyes on the screen", or none;
- `onProgress` — how many photos are taken, out of how many;
- `onReach` — how much of the current pose is reached, from 0 to 1, for the on-screen meter (`null` hides it);
- `readAngles` — a function the camera code can call at any moment to get the head's current angles from the landmarker, or `null`;
- `calm` — whether to use calm mode.

Passing functions in like this keeps `camera.ts` free of React, so it is easy to test and to reason about.

@@ 46-50
**`ChallengeRun`** — what a challenge produces: the frames, and when the colours began (`null` if none were shown). The server needs that start time to work out which colour was on screen when each photo was taken.

@@ 52
**`openCamera`** — ask the browser for the camera. It returns a **`MediaStream`**: a live flow of video frames.

@@ 53
`navigator.mediaDevices.getUserMedia(…)` — the browser's standard camera-and-microphone function. The first time, the browser asks the person for permission; if they refuse, the promise fails with a `NotAllowedError`, which the screens turn into "We need your camera".

@@ 54
`audio: false` — never the microphone.

@@ 55
The video wishes: `facingMode: "user"` — the camera facing the person (a phone's front camera), not the one on the back; and an **ideal** size of 1280 × 720. "Ideal" is a wish, not a demand: a camera that can't do it gives its nearest size instead of failing.

@@ 56-57
The closing brackets.

@@ 59
**`closeCamera`** — switch the camera off. It accepts `null`, so callers can pass a stream that may not exist yet.

@@ 60-63
A stream is made of **tracks** (here, one video track). Stopping every track switches the camera off — and with it the camera's indicator light — immediately. `stream?.getTracks() ?? []` means: the tracks if there is a stream, otherwise an empty list.

@@ 65
**`wait`** — a promise that comes true after the given number of milliseconds, built on the browser's timer `setTimeout`. `await wait(300)` pauses the challenge without freezing the page.

@@ 66
**`nextPaint`** — a promise that comes true just before the browser next draws the screen, usually 60 times a second. `requestAnimationFrame` is the browser's way of saying "call me at the next frame". Waiting for it is the natural pace for checking the head: no faster than the screen changes.

@@ 68
**`toJpeg`** — turn the picture currently on a **canvas** (an in-memory drawing surface) into JPEG bytes.

@@ 69-76
`canvas.toBlob` is an older-style function that reports its result by calling a function back, instead of returning a promise. Wrapping it in `new Promise((resolve, reject) => …)` turns it into one, so it can be `await`ed. It asks for a JPEG at the chosen quality; if the browser gives `null` instead of a blob, the promise fails with a clear error.

@@ 78-84
**`holdPose`** — wait until the head shows the pose steadily, measured from its frontal angles (`baseline`), or until the timeout, whichever comes first — reporting how far it has got on the way. It is given the pose, the frontal angles (or `null` if they couldn't be measured), and two of the hooks. `Pick<ChallengeHooks, "readAngles" | "onReach">` is a type with just those two hooks taken from `ChallengeHooks`: the function needs no others.

@@ 85-86
The deadline — 6 seconds from now — and a counter of steady readings, starting at 0.

@@ 87
Keep going while there is time left *and* the pose hasn't yet been held for 3 readings.

@@ 88-89
Wait for the next screen frame, then read the head's angles.

@@ 90
How much of the pose is reached: a number from 0 to 1, or `null` if there is no reading or no frontal angles to measure from.

@@ 91
Report it for the meter, rounded to steps of 0.05 (`Math.round(share * 20) / 20`). The screen only redraws when the value changes, so rounding spares it 60 redraws a second for invisible differences.

@@ 92
A full meter (exactly 1) adds one to the counter; anything less starts again from 0. That is what makes the 3 readings **in a row**.

@@ 93-94
The closing brackets. The function simply returns: either the pose was held or time ran out, and the caller takes the photos in both cases.

@@ 96-101
**`runChallenge`** — play the challenge on a video element that is showing the camera, and return the labelled frames. It receives the video, the challenge from the server, and the hooks.

@@ 102
The scale: shrink frames wider than 960 pixels, but never enlarge smaller ones (`Math.min(1, …)`).

@@ 103-105
Make a canvas of the scaled size. `Math.round` because pixel sizes must be whole numbers.

@@ 106-109
Get the canvas's **2D drawing context** — the object that does the drawing. In the rare browser that can't provide one, stop with a clear error.

@@ 110-111
How many photos there will be: the baseline ones — one per colour, or the 4 calm ones — plus 3 per pose. The progress display needs the total in advance.

@@ 112
Start the stopwatch. `performance.now()` is a precise, steadily increasing clock in milliseconds, for measuring time spans.

@@ 113
An empty list for the frames.

@@ 114
`frontal` — the landmarker's readings taken with the baseline photos, from which the person's frontal angles are worked out.

@@ 115
**`snap`** — take one photo with the given label. It is defined inside `runChallenge` so it can use the canvas, the stopwatch and the lists directly.

@@ 116-119
For a baseline photo, also note the landmarker's reading of the head at that moment, if there is one.

@@ 120
Copy the video's *current* picture onto the canvas, scaled to fit. The picture is drawn as the camera sees it — *not* mirrored like the preview the person sees — so a head turned to the person's left appears turned to the left in the photo too, as the server expects.

@@ 121
Encode it as JPEG, and add it to the list with its time since the start and its label.

@@ 122-123
Report progress, and close `snap`.

@@ 125
When the colours began — `null` until they do. `let`, not `const`, because it is set later.

@@ 126-130
**Calm mode**: 4 baseline photos, each after a 300 ms pause. No colours.

@@ 131-133
**Otherwise, the colours.** The comment explains the care taken with timing. Encoding a photo takes a few milliseconds, and those would add up: if each colour simply waited 600 ms *after* the previous photo, the colours would drift later and later. The server matches photos to colours by their times alone, so the page keeps to a fixed timetable instead.

@@ 134
The timetable's starting point, measured on the stopwatch.

@@ 135-136
**`until`** — wait until a given moment on the timetable: `ms` milliseconds after the colours began. It works out how long that is from *now*; if the moment has already passed, it waits 0 (`Math.max(0, …)`) rather than a negative time.

@@ 137
Remember the start, to send to the server.

@@ 138
For each colour, with its position: `entries()` gives pairs of `[position, colour]`, which `const [step, colour]` unpacks.

@@ 139-140
At the colour's moment on the timetable, show it.

@@ 141-142
Halfway through its time on screen, take the photo — by then the screen has certainly changed, and the camera has caught up with the new light.

@@ 143
The end of the loop.

@@ 144-146
When the last colour's time is up, take the colour away.

@@ 148
The person's frontal angles: the median of the baseline readings, or `null` if there were none.

@@ 149
**Then the poses**, one at a time, in the server's order.

@@ 150
Show the pose's instruction, from `CUES`.

@@ 151
Wait until the head shows the pose — measured from the frontal angles — or 6 seconds.

@@ 152-155
Take 3 photos labelled with the pose, 150 ms apart (no wait after the last one).

@@ 156-157
Hide the meter until the next pose.

@@ 158
Remove the last instruction.

@@ 159-160
Return the frames and the colours' start time.
