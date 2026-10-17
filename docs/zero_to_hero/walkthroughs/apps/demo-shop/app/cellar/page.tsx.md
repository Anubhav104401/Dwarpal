---
fingerprint: c80958d8a50866f6
---
**The cellar**, at `/cellar` — the age-restricted part of the shop: four wines, and a badge saying the visitor's age check is valid. Its first job is to keep everyone else out: without a valid pass, the visitor is sent back to the entrance before anything is drawn.

The wines and their makers are invented for this demo.

@@ 1-2
Next.js's `cookies` and `redirect`.

@@ 4-6
The bottle drawing, the settings, and the pass functions.

@@ 8
`leaveCellar` — the server action behind the **Leave the cellar** button (`actions.ts`).

@@ 10
**`WINES`** — the shop's list, as data.

@@ 11-17
A Shiraz from "Kesari Ridge" (*kesari* is Hindi for saffron): its grape and year, tasting notes, price in rupees (`₹`), and its colour as a **hex code** — `#5b1424` is a deep red, written as three pairs of hexadecimal digits for red, green and blue.

@@ 18-24
A Chenin Blanc, golden.

@@ 25-31
A Cabernet Sauvignon, nearly black.

@@ 32-38
A skin-contact Viognier — an "orange wine", amber-coloured.

@@ 39
The end of the list.

@@ 41
**`Cellar`**, the page.

@@ 42-45
**The gate.** Read and check the pass; without a valid one, `redirect("/")` stops here and sends the visitor to the entrance. After this line, TypeScript knows `pass` can't be `null`.

@@ 46-50
The pass's expiry as a time such as "10:30", in UTC — the same for every visitor, so the server-drawn page can't show a different time from what the visitor's browser would.

@@ 51-53
The page: a header row, wrapping onto two lines on narrow screens.

@@ 54-57
The heading and a short subtitle.

@@ 58
A row holding the badge and the button, side by side, wrapping onto two lines on a narrow screen (`flex-wrap`).

@@ 59-61
**The badge**: "Age verified · valid until 10:30 UTC", in green. `role="status"` marks it as status information; the end-to-end test also finds it by this role.

@@ 62-69
**The Leave the cellar button** (added in Phase 3). A `<form>` whose `action` is a server action: pressing the button runs `leaveCellar` on the shop's server — it works even without JavaScript. The button has a quiet outline style, so it doesn't compete with the wines.

@@ 70
The end of the row.

@@ 71
The end of the header row.

@@ 72
The wine list: one column on phones, two from 640 pixels wide (`sm:grid-cols-2`).

@@ 73-77
One card per wine. React needs a `key` for each item of a list; the wine's name is unique. The card is a row: bottle beside text.

@@ 78
The bottle, in the wine's colour, labelled with the first word of its name. `split(" ")[0]` takes that word; `?? wine.name` satisfies TypeScript's strict check that a list position might be empty.

@@ 79-84
The name in serif, the grape in rosé, the notes, and the price in amber.

@@ 85-90
The closing tags.
