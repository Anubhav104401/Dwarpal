---
fingerprint: 8ce9a6263f46b306
---
Everything the verify page does with the **camera**: open it, play a liveness challenge on it, and switch it off (§4.19). Since Phase 3 the photos are no longer a quick burst of identical shots. The page plays the server's **challenge** (§5.3): first a few screen colours, one photo per colour, then a head pose per prompt, one photo per pose. Each photo is **labelled** with the part of the challenge it belongs to.

The photos never touch the device's storage: they exist as bytes in the page's memory, travel once to the API, and are forgotten.

@@ 1
The doc comment: open the camera, play a challenge on it — screen colours, then head poses — and switch it off.

@@ 3
From `challenge.ts`: the `Challenge` type, `CUES` (the instruction for each pose), the types `HeadAngles`, `Phase` and `Pose`, and `reached`, which says whether the head shows a pose.

@@ 5
`MAX_WIDTH = 960` — photos are at most 960 pixels wide. More pixels wouldn't help the AI, which works on small, aligned face crops (§5.1.1); they would only make the upload bigger and slower.

@@ 6
`JPEG_QUALITY = 0.85` — 85 % JPEG quality: visually almost perfect, and a fraction of the size of an uncompressed picture. A 960 × 540 photo then comes to well under the 512 KiB limit per frame.

@@ 7-9
**Calm mode.** Some people set their device to **reduce motion** — flashing colours can be uncomfortable, and for a few people with photosensitive conditions, harmful. For them the page shows no colours and instead takes `CALM_BASELINE = 4` ordinary frames, `CALM_GAP_MS = 300` milliseconds apart. The light check then simply has nothing to measure, which never counts against anyone (it is recorded, not decided on).

@@ 10-11
`POSE_TIMEOUT_MS = 5000` — wait at most 5 seconds for each pose. Then the photo is taken anyway. As the comment says, the server judges every photo itself; the page's own view of the head only decides *when* to take it. A page that refused to go on would lock out anyone whose face the guidance can't read. `export` lets the camera screen use the same number.

@@ 12-13
`STEADY_READINGS = 3` — a pose counts as reached only after 3 readings in a row show it (about a twentieth of a second). A head passing through the pose on its way somewhere else doesn't trigger the photo.

@@ 15-19
**`LabelledFrame`** — one photo: the JPEG as a `Blob` (a chunk of raw bytes held by the browser), when it was taken (`tMs`, milliseconds since the challenge began), and its `phase` — `"baseline"` for the colour photos, or the pose it was taken for.

@@ 21-31
**`ChallengeHooks`** — how the camera code talks to the screen, without knowing anything about how the screen looks:

- `onColour` — show this colour around the screen, or none (`null`);
- `onCue` — show this instruction, such as "Slowly turn your head to the left", or none;
- `onProgress` — how many photos are taken, out of how many;
- `readAngles` — a function the camera code can call at any moment to get the head's current angles from the landmarker, or `null`;
- `calm` — whether to use calm mode.

Passing functions in like this keeps `camera.ts` free of React, so it is easy to test and to reason about.

@@ 33-37
**`ChallengeRun`** — what a challenge produces: the frames, and when the colours began (`null` if none were shown). The server needs that start time to work out which colour was on screen when each photo was taken.

@@ 39
**`openCamera`** — ask the browser for the camera. It returns a **`MediaStream`**: a live flow of video frames.

@@ 40
`navigator.mediaDevices.getUserMedia(…)` — the browser's standard camera-and-microphone function. The first time, the browser asks the person for permission; if they refuse, the promise fails with a `NotAllowedError`, which the screens turn into "We need your camera".

@@ 41
`audio: false` — never the microphone.

@@ 42
The video wishes: `facingMode: "user"` — the camera facing the person (a phone's front camera), not the one on the back; and an **ideal** size of 1280 × 720. "Ideal" is a wish, not a demand: a camera that can't do it gives its nearest size instead of failing.

@@ 43-44
The closing brackets.

@@ 46
**`closeCamera`** — switch the camera off. It accepts `null`, so callers can pass a stream that may not exist yet.

@@ 47-50
A stream is made of **tracks** (here, one video track). Stopping every track switches the camera off — and with it the camera's indicator light — immediately. `stream?.getTracks() ?? []` means: the tracks if there is a stream, otherwise an empty list.

@@ 52
**`wait`** — a promise that comes true after the given number of milliseconds, built on the browser's timer `setTimeout`. `await wait(300)` pauses the challenge without freezing the page.

@@ 53
**`nextPaint`** — a promise that comes true just before the browser next draws the screen, usually 60 times a second. `requestAnimationFrame` is the browser's way of saying "call me at the next frame". Waiting for it is the natural pace for checking the head: no faster than the screen changes.

@@ 55
**`toJpeg`** — turn the picture currently on a **canvas** (an in-memory drawing surface) into JPEG bytes.

@@ 56-63
`canvas.toBlob` is an older-style function that reports its result by calling a function back, instead of returning a promise. Wrapping it in `new Promise((resolve, reject) => …)` turns it into one, so it can be `await`ed. It asks for a JPEG at the chosen quality; if the browser gives `null` instead of a blob, the promise fails with a clear error.

@@ 65-66
**`holdPose`** — wait until the head shows the pose steadily, or until the timeout, whichever comes first. It is given the pose and the function that reads the head's angles.

@@ 67-68
The deadline — 5 seconds from now — and a counter of steady readings, starting at 0.

@@ 69
Keep going while there is time left *and* the pose hasn't yet been held for 3 readings.

@@ 70-71
Wait for the next screen frame, then read the head's angles.

@@ 72
If there is a reading and it shows the pose, add one to the counter; otherwise start again from 0. That is what makes the 3 readings **in a row**.

@@ 73-74
The closing brackets. The function simply returns: either the pose was held or time ran out, and the caller takes the photo in both cases.

@@ 76-81
**`runChallenge`** — play the challenge on a video element that is showing the camera, and return the labelled frames. It receives the video, the challenge from the server, and the hooks.

@@ 82
The scale: shrink frames wider than 960 pixels, but never enlarge smaller ones (`Math.min(1, …)`).

@@ 83-85
Make a canvas of the scaled size. `Math.round` because pixel sizes must be whole numbers.

@@ 86-89
Get the canvas's **2D drawing context** — the object that does the drawing. In the rare browser that can't provide one, stop with a clear error.

@@ 90-91
How many photos there will be: the baseline ones — one per colour, or the 4 calm ones — plus one per pose. The progress display needs the total in advance.

@@ 92
Start the stopwatch. `performance.now()` is a precise, steadily increasing clock in milliseconds, for measuring time spans.

@@ 93
An empty list for the frames.

@@ 94
**`snap`** — take one photo with the given label. It is defined inside `runChallenge` so it can use the canvas, the stopwatch and the list directly.

@@ 95
Copy the video's *current* picture onto the canvas, scaled to fit. The picture is drawn as the camera sees it — *not* mirrored like the preview the person sees — so a head turned to the person's left appears turned to the left in the photo too, as the server expects.

@@ 96
Encode it as JPEG, and add it to the list with its time since the start and its label.

@@ 97-98
Report progress, and close `snap`.

@@ 100
When the colours began — `null` until they do. `let`, not `const`, because it is set later.

@@ 101-105
**Calm mode**: 4 baseline photos, each after a 300 ms pause. No colours.

@@ 106-108
**Otherwise, the colours.** The comment explains the care taken with timing. Encoding a photo takes a few milliseconds, and those would add up: if each colour simply waited 600 ms *after* the previous photo, the colours would drift later and later. The server matches photos to colours by their times alone, so the page keeps to a fixed timetable instead.

@@ 109
The timetable's starting point, measured on the stopwatch.

@@ 110-111
**`until`** — wait until a given moment on the timetable: `ms` milliseconds after the colours began. It works out how long that is from *now*; if the moment has already passed, it waits 0 (`Math.max(0, …)`) rather than a negative time.

@@ 112
Remember the start, to send to the server.

@@ 113
For each colour, with its position: `entries()` gives pairs of `[position, colour]`, which `const [step, colour]` unpacks.

@@ 114-115
At the colour's moment on the timetable, show it.

@@ 116-117
Halfway through its time on screen, take the photo — by then the screen has certainly changed, and the camera has caught up with the new light.

@@ 118
The end of the loop.

@@ 119-121
When the last colour's time is up, take the colour away.

@@ 123
**Then the poses**, one at a time, in the server's order.

@@ 124
Show the pose's instruction, from `CUES`.

@@ 125
Wait until the head shows the pose — or 5 seconds.

@@ 126-127
Take the photo, labelled with the pose.

@@ 128
Remove the last instruction.

@@ 129-130
Return the frames and the colours' start time.
