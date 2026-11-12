---
fingerprint: 2c339d57b4f5c4ed
---
Tests for the shop's settings (added on 11 Nov 2026, §6.14): they are read from the environment, a project ID in the database's UUID form is refused, and every missing setting is named at once.

@@ 1
Vitest's building blocks.

@@ 3
The code under test. Since 13 Nov also the default policy's name.

@@ 5-10
**`SETTINGS`** — a made-up but valid environment: a test key's shape, the demo shop's real project ID in its `prj_…` form, and a 32-character secret. `NODE_ENV` is there because Node.js's type for an environment requires it. Nothing here is a real secret.

@@ 12
`describe` groups the tests under one name in the report.

@@ 13-15
A valid environment gives back its project ID unchanged.

@@ 17-20
The launch-night mistake, replayed: the same project's ID as a UUID. `{ ...SETTINGS, … }` copies the settings and replaces one. `toThrow(…)` passes only if `shopConfig` stops with a message containing that text.

@@ 22-27
**The policy** (13 Nov, §6.19): with no setting, or an empty one — which is what Docker Compose passes for an unset variable — the shop uses the preset; with a name, that policy; and a name of the wrong shape is refused at start-up.

@@ 29-31
An empty environment: the message names the key and the project ID together, so one restart is enough to see everything that's missing.

@@ 32
The end of the group.
