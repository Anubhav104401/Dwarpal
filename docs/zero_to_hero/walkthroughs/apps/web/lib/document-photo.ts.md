---
fingerprint: abe4828fb61f35c1
---
Preparing the **document photo** in the browser (Phase 6, §5.6.3), before the verify page sends it to the API: scaled to at most 2000 pixels on its longer side, and re-encoded as a JPEG under the API's 1 MB limit. A phone's camera easily makes 4000-pixel photos of several megabytes; the MRZ needs far less.

Redrawing the picture also drops everything but its pixels — such as where and with which phone it was taken.

@@ 1-3
The module's comment: the document photo is scaled down and re-encoded in the browser before it is sent — to fit the API's limit, and so that whatever else the file carried is left behind. A phone's photo file can hold where it was taken and on which camera (its *EXIF* data); a picture redrawn on a canvas holds only pixels.

@@ 5-7
The limits: the API's 1 MB for a document photo, and 2000 pixels on the longer side (the inference service accepts up to 2400).

@@ 9-13
**`fitWithin`** — the size to draw a picture at so its longer side fits: a scale of at most 1 (never enlarged), applied to both sides so the shape stays, rounded, and never below one pixel.

@@ 15-16
**`QUALITIES`** — the JPEG qualities to try, from 90 % down to 60 %, until the photo fits under the limit. `as const` makes it a fixed list of exactly these numbers.

@@ 18-20
**`DocumentPhotoError`** — the file couldn't be prepared; the page turns it into a tip.

@@ 22-23
**`prepareDocument`** — prepare the chosen file.

@@ 24-29
Decode it with the browser's `createImageBitmap`, turned as the photo's own orientation tag says (phones often store photos sideways with a tag saying so). A file that isn't a readable picture is a `DocumentPhotoError`.

@@ 30-34
The size to draw it at, and a canvas — an off-screen drawing surface — of that size, with its 2D drawing context.

@@ 35-38
A browser that can't give one: release the decoded picture and report it.

@@ 39-40
Draw the picture onto the canvas at the new size, then release the decoded original: from here on only the canvas's pixels exist.

@@ 41-46
Encode the canvas as a JPEG at each quality in turn (`toBlob` calls back with the result, wrapped here in a `Promise` so it can be awaited), and return the first that fits. None does: a `DocumentPhotoError` suggesting a plainer background (busy patterns compress badly).

@@ 47-48
No quality fitted: a `DocumentPhotoError` suggesting a plainer background (busy patterns compress badly).
