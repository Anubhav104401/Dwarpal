---
fingerprint: 08d75840c97ab0e7
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
`- "packages/*"` — every folder directly inside `packages/` is a package: today `config`, later `ui`, `capture` and the SDKs.
