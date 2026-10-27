---
fingerprint: 926f2c3a09abb872
---
This file tells pnpm that this repository is a **workspace**: several JavaScript packages managed together, installed together and able to depend on each other (§4.4).

It is written in **YAML**:

- `key:` followed by indented lines groups things together;
- a line starting with `- ` is one item of a list;
- **indentation is part of the meaning**, just as in Python.

@@ 1
`packages:` — the list of places where workspace packages live.

@@ 2
`- "apps/*"` — every folder directly inside `apps/` is a package: the website and the demo shop (from Phase 1). `*` matches any folder name.

@@ 3
`- "packages/*"` — every folder directly inside `packages/` is a package: `config` and, since Phase 1, the Node SDK `sdk-node`. Later phases add more here.

@@ 4
`- "e2e"` — the end-to-end test is a package too (added in Phase 1). It is a single folder rather than a pattern, because there is only one.

@@ 6
`minimumReleaseAge: 10080` — a **release cooldown**: pnpm refuses to install any version of any package — including the packages our packages depend on — that was published less than 10,080 minutes (7 days) ago.

Why wait? When an attacker takes over a popular package and publishes a poisoned version, the community usually notices and removes it within hours or days. A project that installs only versions at least a week old simply never meets most of these attacks. The price is small: a bug fix reaches us a week later.

!!! key "A cooldown that checks itself"
    pnpm also checks the cooldown when it reads an *existing* lockfile. On its first run it caught `turbo` 2.11.8, pinned in Phase 0 only two days after its release, and refused to go on until it was replaced (see `package.json`).

@@ 8-9
**`overrides`** (Phase 5, decision D14) — versions pnpm must use for a package wherever it appears in the tree, whatever the package that asked for it wanted. Lighthouse CI (§5.5.5) brought older versions of these four with known flaws (`pnpm audit`); these are the fixed ones. They are development tools only — nothing here reaches the apps.

@@ 10-13
The four: `tmp` (temporary files), `uuid` (random IDs), `basic-ftp` (an FTP client deep in Lighthouse's proxy support) and `zod` (data validation in the browser driver). Three of them jump a major version, which can break a program; the Lighthouse test ran after the change and still passed.
