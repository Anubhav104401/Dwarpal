---
fingerprint: fc9ed371d9a33e05
---
The **root layout**: the outer frame of every page of the verify app — the `<html>` and `<body>` elements, the font, the global styles, and the page's information for browsers and search engines. In Next.js's App Router (§4.17), a file named `layout.tsx` wraps every page in its folder and below.

@@ 1
The Geist typeface, from the `geist` package. `GeistSans` provides a class that makes the font available as a CSS variable.

@@ 2
Two Next.js types: `Metadata` (the page's title and description) and `Viewport` (how it should fit and colour the screen).

@@ 3
React's `ReactNode` type: "anything React can draw" — elements, text, lists of them, or nothing.

@@ 5
Load the global stylesheet. Importing a CSS file from a layout applies it to every page.

@@ 7-11
**`metadata`** — Next.js reads this exported object and writes the matching tags into the page's `<head>`:

- the title, shown in the browser tab;
- a description;
- `robots: { index: false, follow: false }` — ask search engines not to list these pages or follow their links. Verify pages are personal, one-time pages; they have no business in search results.

@@ 13-19
**`viewport`** — how the page meets the screen: it supports light and dark modes, and on phones the browser's own bar takes a matching colour — off-white in light mode, near-black in dark mode, chosen by a **media query** about the visitor's preference.

@@ 21
**`RootLayout`** — the layout component itself. Its one input, `children`, is the page being shown inside it. `export default` marks it as the file's main export, which is how Next.js finds it.

@@ 22-23
It returns **JSX** (§4.16). `<html lang="en">` declares the language — screen readers then pronounce the text correctly — and the class from Geist makes the font variable available.

@@ 24
`<body>` with Tailwind classes:

- `min-h-dvh` — at least the full height of the screen (`dvh`, the *dynamic* viewport height, stays correct on phones while their address bar slides in and out);
- `bg-stone-50`, `text-zinc-900` — a warm off-white background with near-black text;
- `font-sans` — the Geist font, through the `--font-sans` token;
- `antialiased` — smoother text edges on some screens;
- `dark:bg-zinc-950`, `dark:text-zinc-100` — the same in dark mode: near-black background, light text.

@@ 25
`{children}` — the page itself goes here. Curly braces put a JavaScript value into JSX.

@@ 26-29
The closing tags and braces.
