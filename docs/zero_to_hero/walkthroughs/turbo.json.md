---
fingerprint: 5226bc6fa664c942
---
`turbo.json` configures **Turborepo**: which tasks exist, the order they must run in, and what can be cached (§4.4).

@@ 1
`{` — start of the JSON object.

@@ 2
`"$schema"` — the web address of a **JSON Schema**: a machine-readable description of every setting this file may contain. Code editors use it to offer autocompletion and to flag mistakes as you type. Turborepo itself ignores it.

@@ 3
`"ui": "stream"` — print every task's output as one continuous stream of lines. The alternative is a full-screen terminal interface; plain lines are better in CI logs and easier to copy.

@@ 4
`"agentGuidance": false` (added in Phase 1) — when Turborepo detects that an AI coding assistant is running it, it writes a file of advice for that assistant, `AGENTS.md`, into the repository. That is the tool's business, not the project's: this line switches it off, so no machine-written file appears among the project's own.

@@ 5
`"tasks"` — one entry per task name. A package takes part in a task if its own `package.json` has a script with the same name.

@@ 6-9
**`build`:**

- `"dependsOn": ["^build"]` — before building a package, build every workspace package it **depends on**. The `^` means "my dependencies", not "myself". The design-system package must be built before the website that uses it.
- `"outputs"` — which files the build produces, so Turborepo can **cache** them:
    - `.next/**` — everything under `.next` (the Next.js output, `**` meaning any depth);
    - `!.next/cache/**` — except Next's own internal cache, which would bloat Turborepo's;
    - `dist/**` — everything under `dist`.

If nothing in a package changed, the next build restores these files from the cache in milliseconds instead of rebuilding.

@@ 10-12
**`typecheck`** also depends on `^build`. Checking a package's TypeScript needs the *type declarations* that its dependencies produce when they are built.

@@ 13-15
**`test`** depends on `^build` for the same reason: tests import the built versions of dependency packages.

@@ 16-20
**`e2e`** — the end-to-end test (added in Phase 1):

- `"dependsOn": ["^build"]` — build the packages it depends on first: the SDK and both web apps;
- `"passThroughEnv": ["UV", "CI"]` — Turborepo runs tasks in a **strict environment**: a task sees only the environment variables it was told about, so that no stray setting can change a result without anyone knowing. This line lets two through: `UV` (where the uv program is, on machines where it isn't on the `PATH`) and `CI` (set by GitHub Actions, which makes the test stricter there);
- `"cache": false` — never reuse an old result: the test checks the live system, which a cached "passed" would hide.

!!! real "Real world — the variable that vanished"
    The first run of the end-to-end test failed straight away: Playwright couldn't find `uv`, although `UV` had been set in the terminal. Turborepo's strict environment had quietly removed it. Declaring it here fixed it.

@@ 21-24
**`dev`** — development servers:

- `"cache": false` — a running server's output is never cached; there is nothing to reuse;
- `"persistent": true` — this task runs forever, until stopped. Turborepo then knows never to wait for it to finish, and never to let another task depend on it.

@@ 25-26
`}` `}` — the end of the tasks object, and the end of the file.
