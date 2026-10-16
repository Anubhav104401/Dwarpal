---
fingerprint: b6ad2ca3cf43cdd7
---
The shop's **error page**. In Next.js, a file named `error.tsx` catches errors thrown while drawing the pages in its folder, and shows itself instead of a broken page. The likeliest error here is a server action that couldn't reach Dwarpal's API — for example, when "Verify my age to enter" is pressed while the API is down.

@@ 1
An error page must be a client component, because it offers a "try again" button that runs in the browser.

@@ 3
The quiet button style.

@@ 5
**`ErrorPage`** — Next.js gives it the `error` and a `reset` function, which tries to draw the page again. Only `reset` is used: the error's details are for the shop's developers (they appear in the server's log), never for visitors.

@@ 6-11
A calm explanation: the age-check service didn't answer; try again in a moment.

@@ 12-14
"Try again" calls `reset`.

@@ 15-17
The closing tags.
