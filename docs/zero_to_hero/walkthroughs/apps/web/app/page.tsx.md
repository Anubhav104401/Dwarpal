---
fingerprint: 82a2abfda11274d8
---
The **home page**, at `/`. Nobody is meant to start here — people arrive through a link from a website — so it simply explains what the site is, for anyone who types the address by hand. In Next.js's App Router, a file named `page.tsx` is the page for its folder's address: `app/page.tsx` is `/`.

@@ 1
The shared page frame (`Shell`) and the card style, from `components/shell.tsx`. `@/` is the app's import alias for its top folder (see `tsconfig.json`).

@@ 3
`Home` — the page component, the file's default export.

@@ 4-6
Inside the shell, one card: a `<section>`, styled with the shared `card` classes.

@@ 7
The heading, in a large size (`text-2xl`), semibold, with letters set slightly closer (`tracking-tight`), as headings usually are.

@@ 8-11
A paragraph explaining the service in plain words. `leading-relaxed` adds space between lines for easier reading; the grey text colours differ for light and dark mode.

@@ 12-14
What to do: use the link the website gave you.

@@ 15-18
The closing tags.
