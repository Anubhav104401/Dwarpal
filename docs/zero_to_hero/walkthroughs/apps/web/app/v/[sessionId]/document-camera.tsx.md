---
fingerprint: dbd8b01f5b72f1da
---
**The document camera** (decision D43, 9 Nov 2026, §5.6.5): on a computer, the webcam's picture with a passport-shaped guide, a photo taken when asked, and a look at it before it is used.

@@ 1
A component that runs in the browser: it uses the camera and keeps state.

@@ 3-4
The page's words, and React's state, effects and references.

@@ 6-8
The shared button styles; switching a camera off (`closeCamera`, shared with the face check); and the helpers above.

@@ 10-12
What the component is given: **`onTaken`**, for the photo the person took and accepted…

@@ 13-14
…**`onChooseFile`**, for someone who would rather choose a file…

@@ 15-18
…and **`onUnavailable`**, for a camera that can't be opened. It must stay the same function from one render to the next: the effect that opens the camera depends on it, so a new function would open the camera again.

@@ 20-23
**`Size`** — a picture's width and height, in pixels.

@@ 25-27
**`DocumentGuide`** — the frame drawn over the picture: shaped like the passport's photo page, with a dashed box where the lines with `<<<` go.

@@ 28-29
A layer over the whole picture, centring what it holds; clicks pass through it (`pointer-events-none`), and screen readers skip it (`aria-hidden`): it is a drawing.

@@ 30-33
The frame: a white rounded border, sized by `guideShare`. Its **shadow** is the trick that dims everything around it: no blur, spread 100vmax (as wide as the screen's longer side) in every direction, half-transparent — and the picture's box cuts it off at its edges (`overflow-hidden`, below).

@@ 34
The dashed box for the machine-readable zone: the bottom 22 % of the page, 4 % in from its sides and bottom.

@@ 35-38
Ends of the frame, the layer and the component.

@@ 40-42
**`DocumentCamera`** (decision D43) — the webcam's picture with the guide; a photo taken when asked; and a look at the photo before it is used.

@@ 43-44
References to the `<video>` element and to the camera's stream, which isn't drawn, so it isn't state.

@@ 45-47
**`size`** — the camera picture's size once known; **`photo`** — the photo taken, with its size and an address the page can show it from; **`taking`** — whether a photo is being taken.

@@ 48
This component's words (`DocumentCamera` in `messages/`).

@@ 50-54
**The camera's effect.** The camera is on only while no photo waits to be looked at: with one taken, it stays off — its light goes out while the person decides.

@@ 55-56
`active` notes whether this effect is still current: the camera may answer after the person has moved on.

@@ 57-61
An answer that comes too late is switched off at once…

@@ 62-66
…otherwise it is kept, and shown in the `<video>`.

@@ 67-72
A refusal — no permission, no camera, a camera in use — is reported, unless this effect is already over.

@@ 73-79
Leaving, or taking a photo, ends the effect: the camera is switched off and its size forgotten. It runs again when the photo is dropped (*Take it again*), opening the camera anew.

@@ 81-88
A photo's **object URL** (`blob:…`, an address for data held in this page) is handed back when that photo is replaced or the component goes, so its memory is freed.

@@ 90-94
**`take`** — the video on screen; nothing to do without one.

@@ 95-98
Mark the photo as being taken, take it, and keep it with an address to show it and the camera picture's size.

@@ 99-100
A browser that can't draw or encode it is treated like a camera that can't be used.

@@ 101-104
Either way, no longer taking.

@@ 106
The size to give the picture's box: the photo's if there is one, else the camera's.

@@ 107-112
The picture's box: rounded and dark while the camera starts, cutting off whatever spills over (the guide's shadow), with the camera picture's own proportions — or 16:9 until they are known.

@@ 113-125
Without a photo, the video: playing at once, inline on phones (`playsInline`), silent, named for screen readers, its size noted as soon as the browser knows it (`onLoadedMetadata`), shown whole (`object-contain`).

@@ 126-127
Once the size is known, the guide over it.

@@ 128-132
With a photo, the photo. A plain `<img>`: Next.js's `<Image>` sends pictures through its image service, which can't fetch a `blob:` address that exists only in this page — so Biome's rule against plain images is set aside here, with the reason given.

@@ 133
End of the picture's box.

@@ 134-139
What to do, announced to screen readers as it changes (`aria-live`): starting; then where to hold the document; and with a photo, whether its lines can be read.

@@ 140-142
Without a photo: a note that the picture isn't mirrored — people expect a mirror from a webcam, and could otherwise turn the page the wrong way…

@@ 143-150
…the button to take the photo, until the camera shows a picture or while one is being taken…

@@ 151-154
…and the way back to the file chooser.

@@ 155-159
With a photo: use it — the photo goes to the verify flow, as a chosen file would…

@@ 160-164
…or take it again, which drops the photo and so turns the camera back on.

@@ 165-167
Ends of the view and of the component.
