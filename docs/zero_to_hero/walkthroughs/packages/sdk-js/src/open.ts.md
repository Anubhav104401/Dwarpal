---
fingerprint: 4f098f49076b2a36
---
**Opening the age check** on a website's page — the part of the SDK a website calls. By default it opens a **modal**: a layer over the page, holding the verify page in an **iframe** (a frame: one page shown inside another). Or, if the website asks, it sends the whole page there (**redirect**).

The verify page agrees to be framed only by the website the session returns to (decision D16, `proxy.ts`), and the browser enforces it.

@@ 1-2
The link checks and the message reader.

@@ 4-5
**`Mode`** — the two ways to open.

@@ 7-10
**`Finished`** — what a website's code is told at the end: the session and the address to go to.

@@ 12-13
**`OpenOptions`** — the choices a website can make, all optional (`?`): the mode…

@@ 14-16
…what to do at the end, `onFinished`. By default the page goes to the return address, where the website's server asks Dwarpal for the result. The comment warns what matters most: the callback proves nothing. Anyone can call a function in their own browser, so a website must never let someone in because the callback ran — only because its server got the result with its key.

@@ 17-19
…and `onClose`, when the person closes the modal before the end. The session isn't cancelled; it simply expires if nobody comes back.

@@ 21-24
**`AgeCheck`** — what opening returns: a way to close it.

@@ 26-28
**`openAgeCheck`** — the SDK's main function. Check the link first; a bad link throws, and nothing opens.

@@ 29-32
Redirect mode: send the whole page to the verify page, and return a `close` that does nothing (the page is leaving anyway).

@@ 33-34
Otherwise, the modal.

@@ 36-37
**`openModal`**. First note which element has the keyboard focus (the button that was pressed, usually), to give it back when the modal closes — so a keyboard user carries on from where they were.

@@ 38-41
The layer: a `div` that assistive technology announces as a **dialog** (`role`), **modal** (the page behind can't be used meanwhile) and named "Age check".

@@ 42-50
Its look, set straight on the element's `style` — the SDK brings no stylesheet that a website would have to load. Fixed over the whole window (`inset: 0`), above everything else (`zIndex` — the highest value browsers allow), centring its content, with a margin and a dark see-through background. A website's content policy may forbid `style="…"` *attributes*, but setting styles from a script like this is always allowed.

@@ 52-55
The frame: showing the verify link; with a `title`, which screen readers announce for a frame; and **`allow`**: the camera — a page in a frame may use it only if the page around it allows that — and full screen.

@@ 56-63
The frame's look: at most 480 by 760 pixels, never larger than the window (`min(…, 100%)` — a phone gets the whole screen less the margin); no border; rounded corners; white behind it while it loads; a shadow.

@@ 65-68
A **Close** button. Its label for screen readers says what it closes.

@@ 69-81
Its look: in the corner; 44 pixels high at least, the smallest target WCAG recommends for a finger; a white pill with dark text, in the system's own font.

@@ 83-85
Put the frame and the button in the layer, the layer on the page, and the focus on the button.

@@ 87
Whether the modal is still open.

@@ 88-98
**`remove`** — take the modal away, once: stop listening, remove the layer, give the focus back. It answers whether it did anything, so a second call is harmless.

@@ 99-103
**`close`** — the person closed it: remove it and, if it was open, tell the website (`onClose`).

@@ 105-109
**`onMessage`** — every message the page receives comes here. Accept it only from **this frame** (`event.source`) **and** from the verify page's origin (`event.origin`). Both are set by the browser, so another frame or another website can't pretend.

@@ 110-113
Read it with the protocol's reader; ignore anything that isn't one of our messages about *this* session.

@@ 114-116
*Full page*: remove the modal and send the whole page to the verify link — the same link, with its secret, so the check carries on there.

@@ 117-122
*Finished*, with an address on this website's own origin: remove the modal, then call the website's `onFinished` — or, by default, go to that address. `??` picks the default when no callback was given. A *finished* message pointing anywhere else is ignored.

@@ 124-128
**`onKey`** — Escape closes the modal, as people expect of dialogs.

@@ 130-134
Wire it all up: the button, the messages, the keys. Return the way to close it.
