---
fingerprint: 88ea9278d35ea1c1
---
The **protocol** between the verify page and the website that framed it: the messages, and the one function that reads them. Both sides import this file — the SDK on the website's page, and the verify page itself (`verify-flow.tsx`) — so they can never disagree about a message's shape.

A page in a frame can't touch its parent page, and the parent can't touch it, when they come from different websites. The one way through is **`postMessage`**: one side sends a value; the other gets a `message` event saying who sent it (`event.origin`, set by the browser, impossible to fake). Two rules make it safe, and each side keeps one: the sender names the only origin allowed to receive the message, and the receiver checks the origin of everything it receives.

@@ 1-5
The comment says so, in short.

@@ 7
**`MESSAGE_SOURCE`** — every message says it comes from `"dwarpal"`, so the website can tell ours apart from any other messages its page receives (from its own widgets, say).

@@ 9-15
**`FinishedMessage`** — the check is over; the website should send the person to `redirectUrl`, its own return address with the session's ID added. It carries no result: the result is fetched by the website's *server*, with its key. `typeof MESSAGE_SOURCE` is the exact text `"dwarpal"`, not any text.

@@ 17-22
**`FullPageMessage`** — the check can't carry on inside the frame (a browser that won't let a frame use the camera, say); the website should open it as a whole page instead.

@@ 24
**`VerifyMessage`** — either of the two. `|` makes a **union** type: a value of one kind or the other, told apart by its `type`.

@@ 26
**`SESSION_ID`** — a session's public ID: `vs_` and 26 letters and digits.

@@ 28
`Fields` — an object whose fields are not yet known: what a message is until it has been checked.

@@ 30-40
**`isWebAddress`** — whether a value is text that reads as an `https:` or `http:` address. Nothing else — no `javascript:` address, which would run code if a page were sent to it. `text is string` tells TypeScript that after a `true`, the value is text. `new URL` throws on anything that isn't an address at all, and `catch` turns that into `false`.

@@ 42-43
**`readMessage`** — anything received (`event.data`, which could be anything at all) turned into one of our messages, or `null`.

@@ 44-46
Not an object (text, a number, nothing)? Not ours.

@@ 47-53
From now on, look at it as an object with unknown fields. Not from `"dwarpal"`, or without a session ID in the right shape? Not ours.

@@ 54-61
A *finished* message with a real web address: build a **new** object from the fields checked — so any other fields a sender added never travel further.

@@ 62-64
A *full page* message: likewise, a fresh object.

@@ 65-66
Anything else — an unknown type, a finished message without a proper address — is ignored.
