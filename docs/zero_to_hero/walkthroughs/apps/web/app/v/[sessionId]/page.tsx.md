---
fingerprint: 2b14b23fe4c42b6b
---
The page at **`/v/<session ID>`** — the address in every verify link. In Next.js's App Router, a folder name in square brackets is a **dynamic segment**: `app/v/[sessionId]/page.tsx` answers `/v/vs_01JA8XQ2…`, and Next.js hands the actual ID to the page as `sessionId`.

This page itself runs on the **server**. It only checks the ID's shape and hands over to `VerifyFlow`, the interactive part that runs in the browser (§4.17).

@@ 1
The `Metadata` type.

@@ 2
`notFound` — a Next.js function that stops the page and shows the standard "404 — not found" page instead.

@@ 6
The interactive verify flow, from the file next to this one.

@@ 15
The shape of a session ID: `vs_` and 26 letters or digits.

@@ 17
`VerifyPage` — an **async** server component, because Next.js passes the address's parameters as a **promise** (`params`), which must be awaited.

@@ 18
Wait for the parameters, and take `sessionId` out by destructuring.

@@ 19-21
A malformed ID can't be a real session: show "not found" straight away, without asking the API anything.

@@ 24-31
Draw the verify flow inside the provider, which hands it those words, giving it the session's ID and the API's address. Text from the address bar is never trusted beyond its shape check: everything else about the session comes from the API.

@@ 32
The closing brace.

@@ 3-4
From next-intl: the **provider** that hands words to components running in the browser, and the server's ways to get the request's words (`getMessages`) and a translator (`getTranslations`).

@@ 8-10
The tab's title for this page, in the person's language: "Confirm your age · Dwarpal", or its Hindi.

@@ 12-13
**`IN_BROWSER`** — the groups of words (`messages/`) the verify page uses in the browser: its own, the camera's, the tips and problems, the page frame's and the language switch's. Only these travel with the page.

@@ 22-23
All of the request's words, kept to those groups. `Object.fromEntries(Object.entries(…).filter(…))` takes an object apart into name–value pairs, keeps some, and puts it back together.
