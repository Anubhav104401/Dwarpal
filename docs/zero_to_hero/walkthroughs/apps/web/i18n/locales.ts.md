---
fingerprint: 23de27492f22f484
---
The public pages' **languages** (decision D2, §5.5.11): English and Hindi, and how one is chosen for a request. Pure functions — no request, no cookies — so they are tested like any other.

@@ 1
The module's comment: the public pages' two languages, and that the console stays in English.

@@ 3-5
**`LOCALES`** — the languages, by their standard codes (`en`, `hi`); `as const` keeps them as exactly these two texts, so `Locale` — "one of them" — is a type TypeScript checks. English is the default.

@@ 6-7
**`LOCALE_COOKIE`** — the cookie that remembers a person's own choice, under next-intl's usual name.

@@ 9-11
**`isLocale`** — is this value one of the languages? Written as a *type guard* (`value is Locale`): after a `true`, TypeScript knows the value is a `Locale`.

@@ 13-17
**`pickLocale`** — the language to answer in. Its comment gives the order: the person's own choice; else their browser's languages, most wanted first; else English.

@@ 18-20
A choice that is one of the languages wins.

@@ 21-24
Otherwise read the browser's **`Accept-Language`** header, such as `hi-IN,hi;q=0.9,en;q=0.8`: a list, split at commas, of language tags each with optional parameters after `;`.

@@ 25-26
Each tag's **quality** — how much it is wanted — is its `q=` parameter, from 0 to 1, or 1 when it has none.

@@ 27-31
Keep the language without its region (`hi-IN` → `hi`), its quality (a broken number counts as 0), and its place in the list.

@@ 32-34
Drop the ones marked unwanted (`q=0`), and order the rest by quality, then by their place — the header's own order breaks ties.

@@ 35-36
The first that the pages are written in; if none, English.
