---
fingerprint: 10cd0d0b49701485
---
Tests for the **deployment's files** (§5.8.2). Most of Phase 8 runs on a real server, where tests can't reach; these check what can be checked here: the secrets are random, private and never replaced, and the Compose file and the generator agree.

@@ 1-2
The module's docstring: what is tested.

@@ 4
The project-wide type-hint setting.

@@ 6-14
base64; `importlib.util` (to load a file that isn't part of any package); regular expressions; file permissions; the platform's name; paths; the type of a loaded module; and pytest.

@@ 16-17
The repository's root, and the deploy folder in it.

@@ 20-26
**`generator`** — load `infra/deploy/gen_secrets.py` as a module, from its file: it is a standalone script, not part of an installed package, so it can't simply be imported.

@@ 29-30
**`parse`** — read `.env` text back into a dictionary, skipping comments.

@@ 33-36
**Test — every secret is fresh, and the master key is 32 random bytes.** Make two files; the master key decodes to exactly 32 bytes.

@@ 37-44
Every password and key differs between the two files — made fresh each time — and is at least 32 characters long.

@@ 45-47
The demo shop's secret meets the shop's own minimum, and the GitHub account is written in lower case, as GHCR requires.

@@ 50-54
**Test — the secrets file is private and never replaced.** Run the generator into a temporary folder: it succeeds…

@@ 55-56
…the file is readable by its owner only — checked where the operating system has owner-only permissions (Windows doesn't, the same way)…

@@ 57-59
…and a second run refuses, leaving the file exactly as it was: a new master key would orphan every signing key.

@@ 62-64
**Test — Compose asks only for settings the generator writes.** Every `${NAME}` without a default in the production Compose file…

@@ 65-68
…must be among the names the generator writes; otherwise the test names the missing ones. A server set up by the README then never starts with a setting missing.

@@ 71-75
**Test — each deploy script stops at the first error** (`set -euo pipefail`): a backup or a deploy must never carry on half-done as if it had worked.
