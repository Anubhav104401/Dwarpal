---
fingerprint: 9f15794a24a06cb8
---
The shop's **entrance**, at `/`: who the shop is, why it checks ages, and the button that starts the check. A visitor who already holds a valid pass sees "Enter the cellar" instead.

It is an async **server component**: it reads the visitor's cookies on the server, and the page arrives already showing the right button.

@@ 1-2
Next.js's `cookies` and `Link`.

@@ 4-6
The button style, the age and settings, and the pass functions.

@@ 8
The shop's age-check button (`age-check-button.tsx`), which opens Dwarpal's check in a modal.

@@ 10
**`Entrance`**, the page.

@@ 11
Read the pass cookie, if any, and check it with the shop's secret. `pass` is a valid pass, or `null`.

@@ 12-13
A centred section, with more space above it on larger screens.

@@ 14
A small line above the heading in spaced-out capitals (`uppercase tracking-[0.3em]`), in rosé.

@@ 15
The big serif headline, larger still on screens from 640 pixels wide.

@@ 16-19
Why the shop checks: it sells alcohol, so everyone confirms they are 18 or over. `{" "}` keeps a space at the line break in the code: JSX would otherwise drop it.

@@ 20-21
The action area. No valid pass?

@@ 22
Then show the age-check button. Pressing it asks the shop's server for a session, and opens the check over this page. (Until decision D16 this was a form that sent the whole page to the verify page; a modal keeps the visitor on the shop, but needs the page's JavaScript.)

@@ 23-27
With a valid pass, simply link to the cellar.

@@ 28
The end of the action area.

@@ 29-32
Small print in plain words: who checks ages, that photos are never stored, and what the shop learns — "only whether you are old enough".

@@ 33-35
The closing tags.
