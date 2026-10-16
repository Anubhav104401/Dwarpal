---
fingerprint: 5a9a2d463507b47b
---
**PostCSS** is a tool that transforms stylesheets with plugins, and Next.js runs it on every CSS file. This configuration adds one plugin: **Tailwind CSS** (§4.18), which reads the classes used in the code and writes exactly the CSS they need.

The file ends in `.mjs` — a JavaScript **module** file — because it is plain JavaScript that Next.js loads directly, not TypeScript.

@@ 1
`export default { … }` — the file's one **default export**: the configuration object that PostCSS reads.

@@ 2
`plugins` — one plugin, `@tailwindcss/postcss`, with no options of its own (`{}`). Tailwind 4 finds the files to scan by itself.

@@ 3
The closing brace.
