---
fingerprint: 7bc7c8ad30b08d0b
---
The page at **`/v/<session ID>`** — the address in every verify link. In Next.js's App Router, a folder name in square brackets is a **dynamic segment**: `app/v/[sessionId]/page.tsx` answers `/v/vs_01JA8XQ2…`, and Next.js hands the actual ID to the page as `sessionId`.

This page itself runs on the **server**. It only checks the ID's shape and hands over to `VerifyFlow`, the interactive part that runs in the browser (§4.17).

@@ 1
The `Metadata` type.

@@ 2
`notFound` — a Next.js function that stops the page and shows the standard "404 — not found" page instead.

@@ 4
The interactive verify flow, from the file next to this one.

@@ 6
The tab's title for this page: "Confirm your age · Dwarpal".

@@ 8
The shape of a session ID: `vs_` and 26 letters or digits.

@@ 10
`VerifyPage` — an **async** server component, because Next.js passes the address's parameters as a **promise** (`params`), which must be awaited.

@@ 11
Wait for the parameters, and take `sessionId` out by destructuring.

@@ 12-14
A malformed ID can't be a real session: show "not found" straight away, without asking the API anything.

@@ 15-20
Draw the verify flow, giving it the session's ID and the API's address. Text from the address bar is never trusted beyond its shape check: everything else about the session comes from the API, after the secret has been checked.

@@ 21
The closing brace.
