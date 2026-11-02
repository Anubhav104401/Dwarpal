---
fingerprint: 5221886148d855ed
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

@@ 78-84
**`alert_email`** — the alerts' script (§5.8.4), loaded from its file the same way as the secrets generator.

@@ 87-92
**Test — Alertmanager's settings name the addresses given**, each quoted, and point at the password's *file*: the password itself is never in them.

@@ 93-98
…and refuse anything else: an address with a line break (which would add a setting of its own), one with a quote, and a bare word; a mail server without its port. Each refusal names the option that was wrong.

@@ 101-110
**Test — switching alerts on twice leaves one of each setting**: the second run changes nothing; the old `COMPOSE_PROFILES` is replaced, not doubled; the three settings have their values; and the rest of `.env` is untouched.

@@ 113-116
**Test — the script itself**, run in a temporary folder with made-up addresses. The tests answer the password question themselves (`ask=`).

@@ 117
Before `.env` exists, it refuses: `gen_secrets.py` comes first.

@@ 118-121
With `.env`, but two different answers to the password question: it refuses, and no password's file is made.

@@ 122-125
With matching answers: the password is in its own file, nowhere in the settings, and `.env` now switches the alerts on.

@@ 126-127
On systems with owner-only permissions (not Windows), the password's file is readable by its owner only.

@@ 130-132
**Test — the deploy copies every file Compose mounts**: each `./file` in the production Compose file must reach the server through the deploy workflow, or be one of those made on the server (the models, and the mail settings). A new settings file that the deploy forgot would otherwise show only as a failed start on the server.

@@ 133-137
The mounted names, from lines like `- ./collector.yaml:`; the files the workflow copies, from the names ending `.yaml`, `.sh` or `.py` (and the Caddyfile), without their folders.

@@ 138
Every mounted file not made on the server must be copied; if not, the test names those missing.
