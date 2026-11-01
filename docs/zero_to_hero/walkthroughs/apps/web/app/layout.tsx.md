---
fingerprint: 0f1f369d32343018
---
The **root layout**: the outer frame of every page of the verify app — the `<html>` and `<body>` elements, the font, the global styles, and the page's information for browsers and search engines. In Next.js's App Router (§4.17), a file named `layout.tsx` wraps every page in its folder and below.

@@ 1-2
The Geist typefaces, from the `geist` package: **Geist Mono** (Phase 5, for code and IDs) and **Geist Sans**. Each provides a class that makes its font available as a CSS variable (`--font-geist-mono`, `--font-geist-sans`), served from this site.

@@ 3
Two Next.js types: `Metadata` (the page's title and description) and `Viewport` (how it should fit and colour the screen).

@@ 4
`headers`, to read the request (Phase 7).

@@ 6
React's `ReactNode` type: "anything React can draw" — elements, text, lists of them, or nothing.

@@ 8
Load the global stylesheet. Importing a CSS file from a layout applies it to every page.

@@ 10-14
**`metadata`** — Next.js reads this exported object and writes the matching tags into the page's `<head>`:

- the title, shown in the browser tab;
- a description;
- `robots: { index: false, follow: false }` — ask search engines not to list these pages or follow their links. Verify pages are personal, one-time pages; they have no business in search results.

@@ 16-22
**`viewport`** — how the page meets the screen: it supports light and dark modes, and on phones the browser's own bar takes a matching colour — the design system's `ink-50` in light mode, `ink-950` in dark, chosen by a **media query** about the visitor's preference. (The hex codes are those two OKLCH tokens converted, because this setting doesn't read CSS variables.)

@@ 24-26
**`RootLayout`** — the layout component itself. Its one input, `children`, is the page being shown inside it. `export default` marks it as the file's main export, which is how Next.js finds it.

Since Phase 7 it is `async` and reads the request's headers. It doesn't need them; reading them tells Next.js that every page depends on its request, so pages are rendered when asked for, not once at build time — and only then can each carry the nonce of its own content security policy (`proxy.ts`).

@@ 29-30
It returns **JSX** (§4.16). `<html lang={locale}>` declares the page's language — `en` or `hi` — so screen readers pronounce the text correctly and browsers choose fonts with the right letters (Hindi is written in Devanagari). The classes from Geist make both typefaces available to the CSS.

@@ 31
`<body>` with Tailwind classes:

- `min-h-dvh` — at least the full height of the screen (`dvh`: the height that is actually visible on phones, whose toolbars come and go);
- `bg-ink-50`, `text-ink-900` — the design system's lightest ink as background, its near-darkest as text;
- `font-sans` — Geist;
- `antialiased` — smoother text edges on some screens;
- `dark:bg-ink-950`, `dark:text-ink-100` — the same in dark mode: a midnight background, light text.

@@ 32
`{children}` — the page itself goes here. Curly braces put a JavaScript value into JSX.

@@ 33-36
The closing tags and braces.

@@ 5
`getLocale` — the language next-intl chose for this request (`i18n/request.ts`).

@@ 27-28
The page's language (§5.5.11): English or Hindi.
