---
fingerprint: 2473945c5f9baea3
---
The **shared TypeScript configuration**. Every app and package will start its own `tsconfig.json` with "extend `@dwarpal/config/tsconfig.base.json`", so all of them follow the same, strict rules.

TypeScript (§0.4) adds **types** to JavaScript, and its compiler checks them before the code runs. These options decide how strict that checking is and what kind of JavaScript comes out.

@@ 1
`{` — start of the JSON object.

@@ 2
`"$schema"` — the community-maintained schema for `tsconfig` files, for editor autocompletion.

@@ 3
`"compilerOptions"` — the settings for the TypeScript compiler.

@@ 4
`"target": "ES2024"` — which version of JavaScript to produce. ECMAScript (ES) is JavaScript's official name, and a new edition comes out every year. Every browser we support understands ES2024, so modern features are kept as they are instead of being rewritten into older, longer code.

@@ 5
`"lib": ["ES2024", "DOM", "DOM.Iterable"]` — which built-in features the compiler should know about:

- the ES2024 standard library;
- the **DOM** — the browser's page objects such as `document` and `window`;
- `DOM.Iterable` — lets you loop over lists of page elements with `for … of`.

@@ 6
`"module": "ESNext"` — write imports and exports in the modern standard form (`import x from "y"`), as today's tools expect.

@@ 7
`"moduleResolution": "Bundler"` — find imported files the way modern **bundlers** do. A bundler is a tool, such as Next.js's Turbopack, that combines many source files into a few optimised files for the browser.

@@ 8
`"strict": true` — switch on TypeScript's whole family of strict checks. The most important one: a value that might be `null` or `undefined` must be checked before it is used.

@@ 9
`"noUncheckedIndexedAccess": true` — reading `list[5]` or `settings[key]` might find nothing, so TypeScript treats the result as "maybe `undefined`" until you check. This catches a very common class of crash.

@@ 10
`"exactOptionalPropertyTypes": true` — an *optional* property (may be left out) is not the same as one explicitly set to `undefined`, and TypeScript keeps the two apart. This matters for API messages, where "missing" and "empty" can mean different things.

@@ 11
`"noImplicitOverride": true` — when a class replaces a method it inherited, it must say so with the `override` keyword. Renaming a method in the parent class can then never silently leave a child's "replacement" pointing at nothing.

@@ 12
`"noFallthroughCasesInSwitch": true` — in a `switch` statement, forgetting `break` makes one case "fall through" into the next, which is a classic bug. This makes it an error.

@@ 13
`"verbatimModuleSyntax": true` — imports that only bring in *types* must say so (`import type { User } from …`). Tools can then delete them safely and predictably when producing JavaScript, where types don't exist.

@@ 14
`"isolatedModules": true` — every file must be understandable on its own. Fast tools translate files one at a time without looking at the rest of the project, and this setting guarantees that is always possible.

@@ 15
`"resolveJsonModule": true` — allow importing `.json` files directly, with their contents typed automatically.

@@ 16
`"skipLibCheck": true` — don't re-check the type declarations shipped *inside* installed libraries. Their mistakes aren't ours to fix, and checking them makes every type check much slower.

@@ 17
`"forceConsistentCasingInFileNames": true` — `import "./Button"` and a file named `button.tsx` would work on Windows and macOS, whose file systems ignore letter case, but **fail on the Linux server**. This catches the mismatch on the developer's machine.

@@ 18-19
`}` `}` — the end of the compiler options, and the end of the file.
