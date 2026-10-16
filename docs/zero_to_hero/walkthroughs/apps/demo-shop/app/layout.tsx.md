---
fingerprint: 3df4bab726e9bc54
---
The shop's **root layout**: the frame around every page — the dark background with its wine-red glow, the shop's name, and a clear label that this is a demo.

@@ 1-4
The Geist typeface, the metadata type, Next.js's `Link` component, and `ReactNode`.

@@ 6
The shop's stylesheet.

@@ 8-11
The tab title and description.

@@ 13
**`RootLayout`**, wrapping each page (`children`).

@@ 14-15
`<html>` in English, with the Geist font variable.

@@ 16
`<body>`: at least a full screen tall, a near-black warm background (`stone-950`), light text, the Geist font.

@@ 17
**The glow**: an empty layer fixed over the whole window (`fixed inset-0`), painted with a wide radial gradient of deep wine red fading out from the top centre. `pointer-events-none` lets clicks pass through.

@@ 18
The header row: centred, at most 64 rem wide (`max-w-5xl`), the name on the left and the label on the right (`justify-between`). `relative` lifts it above the glow layer.

@@ 19-21
The shop's name as a link to the entrance. **`Link`** is Next.js's version of the `<a>` tag: it moves between the shop's own pages without reloading the whole page.

@@ 22-24
A small, honest label: "Demo shop · not a real store".

@@ 25
The end of the header.

@@ 26
`<main>` — the page's content, in the same centred column.

@@ 27-30
The closing tags.
