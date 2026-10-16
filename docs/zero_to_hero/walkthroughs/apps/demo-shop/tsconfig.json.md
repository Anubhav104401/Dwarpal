---
fingerprint: 755737ac6cac2bd9
---
The demo shop's TypeScript settings. They are identical to the verify page's, line for line; see `apps/web/tsconfig.json` for the full explanation of each.

@@ 1
The opening brace.

@@ 2
Start from the project's shared strict settings.

@@ 3
The additions for a Next.js app:

@@ 4
`"jsx": "react-jsx"` — compile JSX with React's modern functions.

@@ 5
`"noEmit": true` — TypeScript only checks; Next.js compiles.

@@ 6
`"allowJs": false` — TypeScript files only.

@@ 7
`"incremental": true` — remember results between runs, for speed.

@@ 8
The Next.js plugin for code editors.

@@ 9
The `@/` import alias for the app's top folder.

@@ 10
The end of the options.

@@ 11
Which files to check, including the types Next.js generates.

@@ 12
Never look inside installed packages or the build folder.

@@ 13
The closing brace.
