---
fingerprint: cfede83a9a538718
---
The shop's **age-check button** — exactly the code a website writes to use Dwarpal's React SDK. It replaced a form that sent the whole page to the verify page.

@@ 1
It runs in the browser (it opens the modal there).

@@ 3-4
The SDK's button, and React's type for anything drawable.

@@ 6
The shop's button style.

@@ 8
The **server action** that creates a session (`actions.ts`). Next.js lets a browser component call it: the call travels to the shop's server, which uses the secret key, and only the session's link comes back.

@@ 10-14
The comment says what matters: the session is created on the server; the check opens over the page; the result is fetched by the server, never trusted from the browser.

@@ 15-25
**`AgeCheckButton`** — the SDK's button, given the server action as `createSession`, the shop's style, and the words chosen by each page that uses it. If creating the session fails, the visitor is sent to the *refused* page, which explains. At the end of the check, the SDK's default moves the page to the shop's return address (`/age-check/complete`), whose route checks the result and opens the cellar.
