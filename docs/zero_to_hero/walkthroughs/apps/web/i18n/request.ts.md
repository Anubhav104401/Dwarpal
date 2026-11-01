---
fingerprint: 3964be0d19a5d88a
---
**Each request's language and words** (decision D2, §5.5.11), for next-intl.

@@ 1-4
Next.js's readers for the request's cookies and headers; next-intl's way to configure each request; and the language chooser.

@@ 6-7
**The request configuration** — next-intl calls this once per request, and every page and component that asks for words gets them from here (`next.config.ts` points the plugin at this file).

@@ 8-9
The language: the person's own choice from the cookie, else their browser's `Accept-Language`, through `pickLocale`.

@@ 10-11
Answer with the language and its words, loaded from its file in `messages/` — only the chosen language's file is read.
