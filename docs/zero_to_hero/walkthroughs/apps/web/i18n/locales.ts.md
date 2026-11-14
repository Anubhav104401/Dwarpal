---
fingerprint: a1d2cbfd00f04e39
---
The public pages' **languages** (decision D2, §5.5.11): English and Hindi, and how one is chosen for a request. Pure functions — no request, no cookies — so they are tested like any other.

@@ 1-5
The module's comment: the public pages' languages — English and Hindi since Phase 5 (decision D2), and since 14 Nov eight more of India's major languages (§7.15) — that each is written as its ISO 639-1 code, the same two letters browsers send, and that the console stays in English.

@@ 6-8
**`LOCALES`** — the ten languages by their standard codes: `en` English, `hi` Hindi, `bn` Bengali, `mr` Marathi, `te` Telugu, `ta` Tamil, `gu` Gujarati, `kn` Kannada, `ml` Malayalam, `pa` Punjabi. `as const` keeps them as exactly these texts, so `Locale` — "one of them" — is a type TypeScript checks. The order is the menu's order. English is the default.

@@ 9-10
**`LOCALE_COOKIE`** — the cookie that remembers a person's own choice, under next-intl's usual name.

@@ 12-14
**`isLocale`** — is this value one of the languages? Written as a *type guard* (`value is Locale`): after a `true`, TypeScript knows the value is a `Locale`.

@@ 16-20
**`pickLocale`** — the language to answer in. Its comment gives the order: the person's own choice; else their browser's languages, most wanted first; else English.

@@ 21-23
A choice that is one of the languages wins.

@@ 24-27
Otherwise read the browser's **`Accept-Language`** header, such as `hi-IN,hi;q=0.9,en;q=0.8`: a list, split at commas, of language tags each with optional parameters after `;`.

@@ 28-29
Each tag's **quality** — how much it is wanted — is its `q=` parameter, from 0 to 1, or 1 when it has none.

@@ 30-34
Keep the language without its region (`hi-IN` → `hi`), its quality (a broken number counts as 0), and its place in the list.

@@ 35-37
Drop the ones marked unwanted (`q=0`), and order the rest by quality, then by their place — the header's own order breaks ties.

@@ 38-39
The first that the pages are written in; if none, English.
