---
fingerprint: 1549cff88983f667
---
**The document camera's helpers** (decision D43, 9 Nov 2026, §5.6.5): whether to offer it, how big its guide is, opening the camera, and taking the photo.

@@ 1-2
The module's comment: the **document camera** (decision D43) — on a computer, the webcam photographs the ID document, held inside a guide shaped like a passport's photo page; the file chooser stays beside it.

@@ 4-6
**`GUIDE_ASPECT`** — the guide's shape, width over height: a passport's photo page is 125 × 88 mm (the size ICAO calls TD3). An ID card, smaller, fits inside the same guide.

@@ 7-8
**`GUIDE_FILL`** — the guide takes at most 90 % of the picture's width and of its height, leaving a margin.

@@ 9-10
**`PHOTO_QUALITY`** — the JPEG quality of the photo taken, 0.95 of the best: small print must survive. `prepareDocument` (§5.6.3) scales and re-encodes it to the API's limit afterwards anyway.

@@ 12-13
**`canFilmDocument`** — whether this is a computer that can film the document: a mouse or trackpad and a camera API. Phones are left as they were: their file chooser opens their own camera app, which takes sharper photos of small print than a video stream.

@@ 14-16
`(pointer: fine)` is a **media query** that is true when the main pointer is precise — a mouse or a trackpad, not a finger. `navigator.mediaDevices?.getUserMedia` is the camera API; the `?.` gives `undefined` instead of an error where even `mediaDevices` is missing (pages not served over HTTPS, for example).

@@ 18-19
**`guideShare`** — how big the guide is in a picture of `width` × `height`, as shares of each side: as large as fits within 90 % of both, in the passport page's shape.

@@ 20-21
The guide's width as a share: 90 %, unless the picture is so wide that a guide 90 % of its *height* tall is narrower — its width in pixels is then `0.9 × height × GUIDE_ASPECT`, divided by the picture's width for the share. A 1920 × 1080 webcam gets 72 %.

@@ 22-23
Its height follows from the shape: the width in pixels over `GUIDE_ASPECT`, as a share of the picture's height.

@@ 25-27
**`openDocumentCamera`** — ask the browser for the camera (it asks the person first).

@@ 28-31
No sound. The camera facing *away* from the person if there is one (`environment`, a phone's back camera), otherwise whichever there is — `ideal` asks without insisting — at up to 1920 × 1080: the lines at the bottom of the page are small.

@@ 32
End of the function.

@@ 34-36
**`takePhoto`** — the camera's picture at this moment, as a JPEG. Whole, not cut to the guide: the check finds the document wherever it is, so a page held a little outside the guide still counts. And unmirrored, as the camera sees it, so the writing reads the right way round.

@@ 37-39
A **canvas** — a drawing surface in memory, never shown — exactly the size of the camera's picture.

@@ 40-43
Its 2D drawing tools; a browser that can't provide them makes the promise fail with a reason.

@@ 44
Draw the video's current frame onto it, at its corner.

@@ 45-51
Encode the canvas as a JPEG (`toBlob`, which answers through a callback, wrapped here in a promise): the photo, or a failure if the browser couldn't encode it.

@@ 52
End of the function.
