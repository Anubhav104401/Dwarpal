---
fingerprint: c5e2766c55c6804b
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

@@ 22-23
Once a pose is held, take `FRAMES_PER_POSE = 2` photos of it. As the comment says, the server counts the best of them, so a blink or a small movement at the wrong moment doesn't spoil the pose.

@@ 24-26
`HALFWAY = 0.4` — and one more photo **on the way**, once the meter is 40 % full. The comment gives the reason, found in the owner's red-team tests: a real head passes through the angles between, while swiping between photos of a turned head jumps straight from one pose to the next. The server records whether each pose was caught partway.

@@ 27
`POSE_GAP_MS = 150` — the pause between the held photos.

@@ 29-33
**`LabelledFrame`** — one photo: the JPEG as a `Blob` (a chunk of raw bytes held by the browser), when it was taken (`tMs`, milliseconds since the challenge began), and its `phase` — `"baseline"` for the colour photos, or the pose it was taken for.

@@ 35-47
**`ChallengeHooks`** — how the camera code talks to the screen, without knowing anything about how the screen looks:

- `onColour` — show this colour around the screen, or none (`null`);
- `onCue` — show this instruction, such as "Turn your head to your left, eyes on the screen", or none;
- `onProgress` — how many photos are taken, out of how many;
- `onReach` — how much of the current pose is reached, from 0 to 1, for the on-screen meter (`null` hides it);
- `readAngles` — a function the camera code can call at any moment to get the head's current angles from the landmarker, or `null`;
- `calm` — whether to use calm mode.

Passing functions in like this keeps `camera.ts` free of React, so it is easy to test and to reason about.

@@ 49-53
**`ChallengeRun`** — what a challenge produces: the frames, and when the colours began (`null` if none were shown). The server needs that start time to work out which colour was on screen when each photo was taken.

@@ 55
**`openCamera`** — ask the browser for the camera. It returns a **`MediaStream`**: a live flow of video frames.

@@ 56
`navigator.mediaDevices.getUserMedia(…)` — the browser's standard camera-and-microphone function. The first time, the browser asks the person for permission; if they refuse, the promise fails with a `NotAllowedError`, which the screens turn into "We need your camera".

@@ 57
`audio: false` — never the microphone.

@@ 58
The video wishes: `facingMode: "user"` — the camera facing the person (a phone's front camera), not the one on the back; and an **ideal** size of 1280 × 720. "Ideal" is a wish, not a demand: a camera that can't do it gives its nearest size instead of failing.

@@ 59-60
The closing brackets.

@@ 62
**`closeCamera`** — switch the camera off. It accepts `null`, so callers can pass a stream that may not exist yet.

@@ 63-66
A stream is made of **tracks** (here, one video track). Stopping every track switches the camera off — and with it the camera's indicator light — immediately. `stream?.getTracks() ?? []` means: the tracks if there is a stream, otherwise an empty list.

@@ 68
**`wait`** — a promise that comes true after the given number of milliseconds, built on the browser's timer `setTimeout`. `await wait(300)` pauses the challenge without freezing the page.

@@ 69
**`nextPaint`** — a promise that comes true just before the browser next draws the screen, usually 60 times a second. `requestAnimationFrame` is the browser's way of saying "call me at the next frame". Waiting for it is the natural pace for checking the head: no faster than the screen changes.

@@ 71
**`toJpeg`** — turn the picture currently on a **canvas** (an in-memory drawing surface) into JPEG bytes.

@@ 72-79
`canvas.toBlob` is an older-style function that reports its result by calling a function back, instead of returning a promise. Wrapping it in `new Promise((resolve, reject) => …)` turns it into one, so it can be `await`ed. It asks for a JPEG at the chosen quality; if the browser gives `null` instead of a blob, the promise fails with a clear error.

@@ 81-88
**`holdPose`** — wait until the head shows the pose steadily, measured from its frontal angles (`baseline`), or until the timeout, whichever comes first — reporting how far it has got on the way. It is given the pose, the frontal angles (or `null`), two of the hooks, and `onHalfway`, a function to call once when the head is partway. `Pick<ChallengeHooks, "readAngles" | "onReach">` is a type with just those two hooks taken from `ChallengeHooks`.

@@ 89-91
The deadline — 6 seconds from now — a counter of steady readings, starting at 0, and whether the halfway photo has been taken yet.

@@ 92
Keep going while there is time left *and* the pose hasn't yet been held for 3 readings.

@@ 93-94
Wait for the next screen frame, then read the head's angles.

@@ 95
How much of the pose is reached: a number from 0 to 1, or `null` if there is no reading or no frontal angles to measure from.

@@ 96
Report it for the meter, rounded to steps of 0.05 (`Math.round(share * 20) / 20`). The screen only redraws when the value changes, so rounding spares it 60 redraws a second for invisible differences.

@@ 97-100
The first time the head is at least 40 % of the way there (but not yet all the way), call `onHalfway` — the caller takes a photo — and remember that it has been taken.

@@ 101
A full meter (exactly 1) adds one to the counter; anything less starts again from 0. That is what makes the 3 readings **in a row**.

@@ 102-103
The closing brackets. The function simply returns: either the pose was held or time ran out, and the caller takes the photos in both cases.

@@ 105-110
**`runChallenge`** — play the challenge on a video element that is showing the camera, and return the labelled frames. It receives the video, the challenge from the server, and the hooks.

@@ 111
The scale: shrink frames wider than 960 pixels, but never enlarge smaller ones (`Math.min(1, …)`).

@@ 112-113
The photos' size, scaled. `Math.round` because pixel sizes must be whole numbers.

@@ 114-115
How many photos there will be, for the progress display: the baseline ones — one per colour, or the 4 calm ones — plus 3 per pose (2 held, 1 on the way). If the head jumps straight to a pose, its halfway photo isn't taken, so the count is a little generous.

@@ 116
Start the stopwatch. `performance.now()` is a precise, steadily increasing clock in milliseconds, for measuring time spans.

@@ 117
`shots` — the pictures taken, each kept as its own canvas with its time and label, still unencoded.

@@ 118
`frontal` — the landmarker's readings taken with the baseline photos, from which the person's frontal angles are worked out.

@@ 119-121
The comment explains the most important timing rule, learned in the owner's tests. Copying a picture onto a canvas is instant; encoding it to JPEG took about a second on a busy laptop. Encoding during the challenge pushed later photos out of their colours — and the server matches photos to colours by their times alone — so every photo is stamped the moment it is copied, and encoded only when the challenge is over.

@@ 122
**`snap`** — take one photo with the given label. It is defined inside `runChallenge` so it can use the size, the stopwatch and the lists directly. It does no waiting: it returns at once.

@@ 123-126
For a baseline photo, also note the landmarker's reading of the head at that moment, if there is one.

@@ 127-133
A fresh canvas for this photo, at the photos' size, and its 2D drawing context. In the rare browser that can't provide one, stop with a clear error.

@@ 134
Copy the video's *current* picture onto it, scaled to fit. The picture is drawn as the camera sees it — *not* mirrored like the preview the person sees — so a head turned to the person's left appears turned to the left in the photo too, as the server expects.

@@ 135
Keep it, stamped with this moment and its label.

@@ 136-137
Report progress, and close `snap`.

@@ 139
When the colours began — `null` until they do. `let`, not `const`, because it is set later.

@@ 140-144
**Calm mode**: 4 baseline photos, each after a 300 ms pause. No colours.

@@ 145-146
**Otherwise, the colours**, on a fixed timetable. As the comment says, each colour starts exactly one step after the last, by the clock, so nothing slow can shift it.

@@ 147
The timetable's starting point, measured on the stopwatch.

@@ 148-149
**`until`** — wait until a given moment on the timetable: `ms` milliseconds after the colours began. It works out how long that is from *now*; if the moment has already passed, it waits 0 (`Math.max(0, …)`) rather than a negative time.

@@ 150
Remember the start, to send to the server.

@@ 151
For each colour, with its position: `entries()` gives pairs of `[position, colour]`, which `const [step, colour]` unpacks.

@@ 152-153
At the colour's moment on the timetable, show it.

@@ 154-155
Halfway through its time on screen, take the photo — by then the screen has certainly changed, and the camera has caught up with the new light.

@@ 156
The end of the loop.

@@ 157-159
When the last colour's time is up, take the colour away.

@@ 161
The person's frontal angles: the median of the baseline readings, or `null` if there were none.

@@ 162
**Then the poses**, one at a time, in the server's order.

@@ 163
Show the pose's instruction, from `CUES`.

@@ 164
Wait until the head shows the pose — measured from the frontal angles — or 6 seconds, taking a photo on the way when the head is partway (`() => snap(pose)` is the function `holdPose` calls).

@@ 165-168
Take the 2 held photos, labelled with the pose, 150 ms apart (no wait after the last one).

@@ 169-170
Hide the meter until the next pose.

@@ 171
Remove the last instruction.

@@ 172-180
**Now encode every photo to JPEG**, all at once: `shots.map(async …)` starts an encoding per photo, and `Promise.all` waits until every one has finished, keeping their order. Each becomes a `LabelledFrame` with its original time and label.

@@ 181-182
Return the frames and the colours' start time.
