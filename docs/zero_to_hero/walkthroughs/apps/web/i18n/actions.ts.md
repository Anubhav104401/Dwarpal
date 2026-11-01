---
fingerprint: 7864c2eb5abf722b
---
**Remembering a person's language** (§5.5.11): the language switch's form posts here.

@@ 1
`"use server"` — every function in this file is a **server action**: code that runs on the server, which a form in the browser can call by posting to it. Next.js makes the connection.

@@ 3-5
The response's cookies, and the language helpers.

@@ 7-9
**`chooseLocale`** — remember the language a person chose. A plain form posts here, so it works even without JavaScript; Next.js then draws the page again, now in that language.

@@ 10-14
Take the chosen language from the form and, only if it is one of the pages' languages, store it in the cookie for a year, for the whole site (`path: "/"`), sent along with ordinary links from other sites too (`sameSite: "lax"`). Anything else is ignored. The cookie holds only `en` or `hi`: it identifies no one.
