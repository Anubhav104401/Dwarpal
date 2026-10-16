---
fingerprint: 961fa2093791c3d1
---
The SDK's **TypeScript settings** for checking its code. It starts from the project's shared strict settings (`packages/config/tsconfig.base.json`, §5.0.4) and changes only what a library for Node.js needs differently from a web app.

@@ 1
The opening brace.

@@ 2
`"extends"` — start from the shared settings, by their package name. Everything there — strict mode, the extra safety checks — applies here unless changed below.

@@ 3
`"compilerOptions"` — the changes.

@@ 4
`"lib": ["ES2024"]` — which built-in JavaScript features exist. The shared settings also include `DOM`, the browser's features (windows, buttons, cameras). The SDK runs on servers, where there is no DOM, so it is left out: a mistaken use of `window` is then caught as an error.

@@ 5-6
`"module"` and `"moduleResolution": "NodeNext"` — follow **Node.js's own rules** for modules, exactly. The web apps use a bundler that is more forgiving; a library that Node.js loads directly must follow Node.js's rules, so every import of our own files is written with its `.js` ending (`./errors.js`), as Node.js requires.

@@ 7
`"types": ["node"]` — load the type descriptions of Node.js's built-ins: `fetch`, `Response`, `AbortSignal`, `Buffer`…

@@ 8
`"noEmit": true` — only check; never write JavaScript files. Writing is the job of `tsconfig.build.json`.

@@ 9
The closing brace of the options.

@@ 10
`"include"` — check both the source code (`src`) and the tests (`test`).

@@ 11
The closing brace.
