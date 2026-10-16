---
fingerprint: fbf82de55d2fc65c
---
The **root `package.json`** — for the JavaScript side of the project, it plays the role the root `pyproject.toml` plays for Python. It is written in **JSON** (§0.11): curly braces hold labelled values, square brackets hold lists, and every key and text value is in double quotes. JSON has no comments, which is why the explanations live here.

@@ 1
`{` — the whole file is one JSON object.

@@ 2
`"name": "dwarpal"` — the workspace's name. Package names are lowercase by npm's rules.

@@ 3
`"private": true` — **never publish this to the public npm registry.** A safety catch: even a mistaken `pnpm publish` command will refuse to run.

@@ 4
`"description"` — one line saying what this is.

@@ 5
`"packageManager": "pnpm@12.11.2"` — the exact package manager and version this project uses. pnpm itself, Corepack and the CI setup action (§5.0.6) all read it, so every machine installs with the same tool and gets the same lockfile behaviour.

@@ 6-8
`"engines"` — which Node.js versions are supported: `>=24.11.0 <25`, the **Node 24 LTS** line (24.11.0 was its first Long-Term-Support release). Node 25 is a short-lived "current" release that the project doesn't test on.

@@ 9
`"scripts"` — short commands runnable as `pnpm <name>`. For example, `pnpm lint` runs the command stored under `"lint"`.

@@ 10
`"build": "turbo run build"` — build every app and package, in dependency order, through Turborepo (§4.4).

@@ 11
`"dev": "turbo run dev"` — start every development server at once (from Phase 1).

@@ 12
`"lint": "biome check ."` — Biome checks formatting, lint rules and import order for every supported file in the repository. It only reports, without changing anything; CI runs this.

@@ 13
`"format": "biome check --write ."` — the same check, but `--write` applies the fixes.

@@ 14
`"typecheck": "turbo run typecheck"` — run each package's TypeScript type check, through Turborepo.

@@ 15
`"test": "turbo run test"` — run each package's unit tests, through Turborepo.

@@ 16
`"e2e": "turbo run e2e"` — run the end-to-end test (added in Phase 1). It is a separate command because it needs much more than the unit tests: Docker, the Python services, and a real browser. Through Turborepo, the packages it depends on — the SDK and both web apps — are built first.

@@ 17
`}` — the end of the scripts.

@@ 18-21
`"devDependencies"` — tools needed to *work on* the project, not to run it. Each is pinned to an exact version (no `^` or `~`, which would allow automatic upgrades):

- `@biomejs/biome` 2.5.15 — the formatter and linter;
- `turbo` 2.11.7 — the task runner.

!!! real "Real world — why turbo went *down* a version"
    Phase 0 pinned turbo 2.11.8, which had been published only two days earlier. In Phase 1 the workspace gained a **release cooldown** (`pnpm-workspace.yaml`): no package version younger than seven days may be installed. The new rule immediately refused 2.11.8, so turbo stepped back to 2.11.7, released a week before that.

`@biomejs/` is a **scope**: a namespace on npm owned by one organisation, so nobody else can publish under that name.

@@ 22
`}` — the end of the file.
