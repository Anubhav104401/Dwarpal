---
fingerprint: 755737ac6cac2bd9
---
The verify page's **TypeScript settings**: the project's shared strict settings (§5.0.4), plus what a Next.js app needs.

@@ 1
The opening brace.

@@ 2
Start from the shared settings — including the browser's `DOM` types, which this app does need.

@@ 3
The additions:

@@ 4
`"jsx": "react-jsx"` — how to handle **JSX**, the HTML-like syntax inside `.tsx` files (§4.16). `react-jsx` turns each tag into a call to React's modern JSX functions, without needing `import React` in every file.

@@ 5
`"noEmit": true` — TypeScript only *checks*. Next.js does the compiling, with its own very fast compiler.

@@ 6
`"allowJs": false` — every file must be TypeScript; plain, unchecked JavaScript isn't allowed in.

@@ 7
`"incremental": true` — remember results between runs (in a `.tsbuildinfo` file, which Git ignores), so the next check only re-reads what changed.

@@ 8
`"plugins": [{ "name": "next" }]` — Next.js's helper for code editors: it warns, for example, when a setting is exported from a page that doesn't support it.

@@ 9
`"paths": { "@/*": ["./*"] }` — an **import alias**: `@/lib/advice` means `lib/advice` from the app's top folder, wherever the importing file is. Without it, a deeply nested file would need `../../../lib/advice`.

@@ 10
The end of the options.

@@ 11
`"include"` — which files to check:

- `next-env.d.ts` — type declarations Next.js writes itself;
- every `.ts` and `.tsx` file;
- `.next/types/**/*.ts` — types Next.js generates during a build, for example about the app's routes.

@@ 12
`"exclude"` — never look inside installed packages or the build folder.

@@ 13
The closing brace.
