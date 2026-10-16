---
fingerprint: 79633c3816d41dfd
---
The page a visitor sees when the age check didn't let them in, at `/refused?reason=…`. It explains what happened, kindly and without blame, and offers a way forward: try again, or go back. Whatever the reason, it never reveals anything about the person — only what the shop itself knows.

@@ 1
Next.js's `Link`.

@@ 3
The two button styles.

@@ 5
The server action that starts a new check.

@@ 7-10
**`FALLBACK`** — the message for errors, and for any reason the page doesn't know.

@@ 12
**`MESSAGES`** — a message for each reason the return route gives:

@@ 13-16
`not_confirmed` — the check didn't confirm 18 or over.

@@ 17-20
`step_up` — too close to call from photos; a stronger check (by ID document) arrives in Phase 6.

@@ 21-24
`other_browser` — the return link was opened in a different browser from the one that started the check, or so late that the reminder cookie had expired.

@@ 25-28
`unfinished` — the check never finished, probably because it expired.

@@ 29-30
`error` — the fallback. The end of the list.

@@ 32
**`Refused`**, the page. Next.js passes the address's query as a promise, `searchParams`; `reason?` is optional, because the address may have none.

@@ 33-34
Read the reason, and pick its message, or the fallback.

@@ 35-38
The title and explanation, centred.

@@ 39-44
"Try the age check again" — the same server-action form as on the entrance.

@@ 45-47
Or go back to the entrance.

@@ 48-51
The closing tags.
