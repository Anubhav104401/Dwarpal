---
fingerprint: 3a0414d493aa3fcb
---
Everything the verify page does with the **camera**, in three functions: open it, take a quick burst of still photos, and switch it off (§4.19). The photos never touch the device's storage: they exist as bytes in the page's memory, travel once to the API, and are forgotten.

@@ 1
The doc comment: open, take one burst, switch off.

@@ 3
The `CapturedFrame` type, from `flow-api.ts`.

@@ 5
`BURST_SIZE = 5` — five photos per attempt. The decision engine needs at least three usable ones (`MIN_USABLE_FRAMES`); five leave room for a blink or a blurred frame.

@@ 6
`BURST_GAP_MS = 150` — 150 milliseconds between photos: a whole burst takes about 0.6 seconds. Short enough to hold still for; long enough that the frames aren't identical copies, which lets the engine notice frames that disagree (`inconsistent_frames`).

@@ 7
`MAX_WIDTH = 960` — photos are at most 960 pixels wide. More pixels wouldn't help the AI, which works on small, aligned face crops (§5.1.1); they would only make the upload bigger and slower.

@@ 8
`JPEG_QUALITY = 0.85` — 85 % JPEG quality: visually almost perfect, and a fraction of the size of an uncompressed picture. A 960 × 540 photo then comes to well under the 512 KiB limit per frame.

@@ 10
**`openCamera`** — ask the browser for the camera. It returns a **`MediaStream`**: a live flow of video frames.

@@ 11
`navigator.mediaDevices.getUserMedia(…)` — the browser's standard camera-and-microphone function. The first time, the browser asks the person for permission; if they refuse, the promise fails with a `NotAllowedError`, which the screens turn into "We need your camera".

@@ 12
`audio: false` — never the microphone.

@@ 13
The video wishes: `facingMode: "user"` — the camera facing the person (a phone's front camera), not the one on the back; and an **ideal** size of 1280 × 720. "Ideal" is a wish, not a demand: a camera that can't do it gives its nearest size instead of failing.

@@ 14-15
The closing brackets.

@@ 17
**`closeCamera`** — switch the camera off. It accepts `null`, so callers can pass a stream that may not exist yet.

@@ 18-21
A stream is made of **tracks** (here, one video track). Stopping every track switches the camera off — and with it the camera's indicator light — immediately. `stream?.getTracks() ?? []` means: the tracks if there is a stream, otherwise an empty list.

@@ 23
**`wait`** — a promise that comes true after the given number of milliseconds, built on the browser's timer `setTimeout`. `await wait(150)` pauses the burst without freezing the page.

@@ 25
**`toJpeg`** — turn the picture currently on a **canvas** (an in-memory drawing surface) into JPEG bytes.

@@ 26-33
`canvas.toBlob` is an older-style function that reports its result by calling a function back, instead of returning a promise. Wrapping it in `new Promise((resolve, reject) => …)` turns it into one, so it can be `await`ed. It asks for a JPEG at the chosen quality; if the browser gives `null` instead of a blob, the promise fails with a clear error.

@@ 35-39
**`captureBurst`** — take the burst from a video element that is showing the camera. `onFrame?` is an optional progress report, called after each photo with the number taken so far; the screen uses it to show "Hold still… 3 of 5".

@@ 40
The scale: shrink frames wider than 960 pixels, but never enlarge smaller ones (`Math.min(1, …)`).

@@ 41-43
Make a canvas of the scaled size. `Math.round` because pixel sizes must be whole numbers.

@@ 44-47
Get the canvas's **2D drawing context** — the object that does the drawing. In the rare browser that can't provide one, stop with a clear error.

@@ 48
Start the stopwatch. `performance.now()` is a precise, steadily increasing clock in milliseconds, for measuring time spans.

@@ 49
An empty list for the frames.

@@ 50
Repeat `BURST_SIZE` times, counting from 0. (`index += 1` adds one; the project avoids the shorter `++`.)

@@ 51-53
Before every photo but the first, wait 150 ms.

@@ 54
Copy the video's *current* picture onto the canvas, scaled to fit. The picture is drawn as the camera sees it — *not* mirrored like the preview the person sees, so the AI gets the real view.

@@ 55
Encode it as JPEG, and add it to the list with its time since the start.

@@ 56
Report progress, if anyone asked: `onFrame?.(…)` calls the function only if it was given.

@@ 57-59
After five photos, return them all.
