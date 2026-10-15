---
fingerprint: b0f137da5bf86f92
---
The first workspace package, **`@dwarpal/config`**. It holds no code, only shared settings — today the TypeScript configuration — so that every app and package uses identical rules.

@@ 1
`{` — start of the JSON object.

@@ 2
`"name": "@dwarpal/config"` — a **scoped** name: `@dwarpal` is the project's namespace, `config` the package. Other workspace packages refer to it by this name.

@@ 3
`"version": "0.0.0"` — this package is internal and never published, so its version is a placeholder.

@@ 4
`"private": true` — never publish it to npm.

@@ 5
`"description"` — shared TypeScript settings for every app and package.

@@ 6-8
`"exports"` — the package's **public doors**: which files other packages are allowed to import. Only `./tsconfig.base.json` is exported, mapped to the file of the same name. Anything else inside the package stays private, so it can be reorganised without breaking anyone.

@@ 9
`}` — the end of the file.
