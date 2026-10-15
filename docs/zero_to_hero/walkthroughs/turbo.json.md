---
fingerprint: b7d3b437a76a9414
---
`turbo.json` configures **Turborepo**: which tasks exist, the order they must run in, and what can be cached (§4.4).

@@ 1
`{` — start of the JSON object.

@@ 2
`"$schema"` — the web address of a **JSON Schema**: a machine-readable description of every setting this file may contain. Code editors use it to offer autocompletion and to flag mistakes as you type. Turborepo itself ignores it.

@@ 3
`"ui": "stream"` — print every task's output as one continuous stream of lines. The alternative is a full-screen terminal interface; plain lines are better in CI logs and easier to copy.

@@ 4
`"tasks"` — one entry per task name. A package takes part in a task if its own `package.json` has a script with the same name.

@@ 5-8
**`build`:**

- `"dependsOn": ["^build"]` — before building a package, build every workspace package it **depends on**. The `^` means "my dependencies", not "myself". The design-system package must be built before the website that uses it.
- `"outputs"` — which files the build produces, so Turborepo can **cache** them:
    - `.next/**` — everything under `.next` (the Next.js output, `**` meaning any depth);
    - `!.next/cache/**` — except Next's own internal cache, which would bloat Turborepo's;
    - `dist/**` — everything under `dist`.

If nothing in a package changed, the next build restores these files from the cache in milliseconds instead of rebuilding.

@@ 9-11
**`typecheck`** also depends on `^build`. Checking a package's TypeScript needs the *type declarations* that its dependencies produce when they are built.

@@ 12-14
**`test`** depends on `^build` for the same reason: tests import the built versions of dependency packages.

@@ 15-18
**`dev`** — development servers:

- `"cache": false` — a running server's output is never cached; there is nothing to reuse;
- `"persistent": true` — this task runs forever, until stopped. Turborepo then knows never to wait for it to finish, and never to let another task depend on it.

@@ 19-20
`}` `}` — the end of the tasks object, and the end of the file.
