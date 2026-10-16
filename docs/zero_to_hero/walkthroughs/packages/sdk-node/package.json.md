---
fingerprint: 2191b1a96983332f
---
The package description of **`@dwarpal/node`**, the **SDK** (Software Development Kit) for websites that use Dwarpal. An SDK is a small library a service gives its customers, so that each customer doesn't have to write — and get right — the same code: calling the API with the key, and above all **checking the signature** of every age token.

`package.json` is to a JavaScript package what `pyproject.toml` is to a Python one (§4.4): its name, its version, how to build and test it, and what it depends on.

@@ 1
The opening brace of the JSON object.

@@ 2
`"name": "@dwarpal/node"` — the package's name. `@dwarpal/` is a **scope**: a family name for all of this project's packages. Apps import the SDK by exactly this name.

@@ 3
`"version": "0.1.0"` — semantic versioning (§0.17); a major version of 0 means "early, may still change".

@@ 4
A one-line description.

@@ 5
`"private": true` — never publish this package to the public npm registry by accident. Publishing it, and under which licence, is the project owner's decision for later; until then this line makes `npm publish` refuse.

@@ 6
`"type": "module"` — the package's JavaScript files are **ES modules**, the modern standard way JavaScript files import each other (`import … from …`), rather than the older CommonJS style (`require(…)`).

@@ 7-12
`"exports"` — what other code may import, and from which files. `"."` means "the package itself", as in `import { verifyAgeToken } from "@dwarpal/node"`:

- `"types"` — the file that describes the package's types, for TypeScript;
- `"default"` — the JavaScript file that actually runs.

Both are in `dist/`, the folder the build writes. Anything not listed here can't be imported from outside, which keeps the package's insides private.

@@ 13-15
`"files"` — when the package is packed for publishing, include only `dist/`: the built code, not the sources or the tests.

@@ 16-18
`"engines"` — Node.js 24.11 or newer. The SDK uses modern built-ins such as `fetch` and `AbortSignal.timeout`.

@@ 19-23
The **scripts** (run with `pnpm build`, `pnpm typecheck`, `pnpm test`):

- `build` — compile `src/` into `dist/` with the TypeScript compiler, using `tsconfig.build.json`;
- `typecheck` — check every file, including the tests, without writing anything (`tsconfig.json`);
- `test` — run the tests once with **Vitest** (§4.20). `run` means "once, then stop", instead of watching for changes.

@@ 24-26
`"dependencies"` — what the SDK needs when it runs: only **jose** 6.2.12, a widely used library for JWTs and JWKs that runs in Node.js, browsers and other JavaScript runtimes, and has no dependencies of its own. Every dependency is code a website must trust, so the SDK keeps the list as short as possible.

@@ 27-32
`"devDependencies"` — what's needed only while developing:

- `@dwarpal/config` — the shared TypeScript settings. `workspace:*` means "the copy in this repository", never a published one;
- `@types/node` — type descriptions of Node.js's built-in modules, for the version we run (24);
- `typescript` 7.0.2 — the compiler (§4.15);
- `vitest` 5.0.3 — the test runner.

@@ 33
The closing brace.
