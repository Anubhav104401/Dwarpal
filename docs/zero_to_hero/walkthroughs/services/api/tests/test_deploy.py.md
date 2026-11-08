---
fingerprint: 30e0f5983a28e9b9
---
Tests for the **deployment's files** (§5.8.2). Most of Phase 8 runs on a real server, where tests can't reach; these check what can be checked here: the secrets are random, private and never replaced, and the Compose file and the generator agree.

@@ 1-2
The module's docstring: what is tested.

@@ 4
The project-wide type-hint setting.

@@ 6-15
base64; `importlib.util` (to load a file that isn't part of any package); regular expressions; file permissions; the platform's name; paths; the type of a loaded module; and pytest; and `tomllib`, to read the workspace's members from `pyproject.toml`.

@@ 17-18
The repository's root, and the deploy folder in it.

@@ 21-27
**`generator`** — load `infra/deploy/gen_secrets.py` as a module, from its file: it is a standalone script, not part of an installed package, so it can't simply be imported.

@@ 30-31
**`parse`** — read `.env` text back into a dictionary, skipping comments.

@@ 34-37
**Test — every secret is fresh, and the master key is 32 random bytes.** Make two files; the master key decodes to exactly 32 bytes.

@@ 38-45
Every password and key differs between the two files — made fresh each time — and is at least 32 characters long.

@@ 46-48
The demo shop's secret meets the shop's own minimum, and the GitHub account is written in lower case, as GHCR requires.

@@ 51-55
**Test — the secrets file is private and never replaced.** Run the generator into a temporary folder: it succeeds…

@@ 56-57
…the file is readable by its owner only — checked where the operating system has owner-only permissions (Windows doesn't, the same way)…

@@ 58-60
…and a second run refuses, leaving the file exactly as it was: a new master key would orphan every signing key.

@@ 91-93
**Test — Compose asks only for settings the generator writes.** Every `${NAME}` without a default in the production Compose file…

@@ 94-97
…must be among the names the generator writes; otherwise the test names the missing ones. A server set up by the README then never starts with a setting missing.

@@ 100-104
**Test — each deploy script stops at the first error** (`set -euo pipefail`): a backup or a deploy must never carry on half-done as if it had worked.

@@ 107-113
**`alert_email`** — the alerts' script (§5.8.4), loaded from its file the same way as the secrets generator.

@@ 116-121
**Test — Alertmanager's settings name the addresses given**, each quoted, and point at the password's *file*: the password itself is never in them.

@@ 122-127
…and refuse anything else: an address with a line break (which would add a setting of its own), one with a quote, and a bare word; a mail server without its port. Each refusal names the option that was wrong.

@@ 130-139
**Test — switching alerts on twice leaves one of each setting**: the second run changes nothing; the old `COMPOSE_PROFILES` is replaced, not doubled; the three settings have their values; and the rest of `.env` is untouched.

@@ 142-145
**Test — the script itself**, run in a temporary folder with made-up addresses. The tests answer the password question themselves (`ask=`).

@@ 146
Before `.env` exists, it refuses: `gen_secrets.py` comes first.

@@ 147-150
With `.env`, but two different answers to the password question: it refuses, and no password's file is made.

@@ 151-154
With matching answers: the password is in its own file, nowhere in the settings, and `.env` now switches the alerts on.

@@ 155-156
On systems with owner-only permissions (not Windows), the password's file is readable by its owner only.

@@ 159-161
**Test — the deploy copies every file Compose mounts**: each `./file` in the production Compose file must reach the server through the deploy workflow, or be one of those made on the server (the models, and the mail settings). A new settings file that the deploy forgot would otherwise show only as a failed start on the server.

@@ 162-166
The mounted names, from lines like `- ./collector.yaml:`; the files the workflow copies, from the names ending `.yaml`, `.sh` or `.py` (and the Caddyfile), without their folders.

@@ 167
Every mounted file not made on the server must be copied; if not, the test names those missing.

@@ 63-65
**Test — the domain is a bare name** (decision D40): a DuckDNS name or one's own, in lower case; anything that would break `api.<domain>` is refused before a single secret is written.

@@ 66-68
A DuckDNS name in mixed case with spaces around comes back clean; an ordinary domain is kept as it is.

@@ 69-83
Eleven refusals, each naming `--domain`: a scheme, a path, a port, a wildcard, a single part, a hyphen at the start of a part, an empty part, a dot at the end, an IP address, 251 characters (fine alone, but too long once `shop.` is added), and nothing at all.

@@ 84-88
The command run with `https://` in front: it fails, says the domain must be a bare name, and writes no file.

@@ 195-197
**Test — the outside check** (decision D33): every 15 minutes, never on the hour, with a token that may do nothing, only once the API's address is set, and asking `/readyz` — what the README promises.

@@ 198-200
The workflow's text, and its schedule's minutes (the line `cron: "… * * * *"`); without one, the message says so.

@@ 201-203
The minutes in order, and the gap after each — the last one's to the first of the next hour: four gaps of 15 minutes.

@@ 204
None on the hour.

@@ 205-207
A token that may do nothing, the condition on the address, and the readiness check.

@@ 170-173
**Test — both Python images copy every workspace member's description** (9 Nov): uv reads the whole workspace to use the lockfile, so one missing `pyproject.toml` fails the build — as the Python SDK's did, found by CI's first image builds.

@@ 174-177
The workspace's member patterns (`services/*`, `libs/*`, …), each expanded to the folders that have a `pyproject.toml`, written as paths from the repository's root.

@@ 178
The SDK is among them — so the test can't pass by finding nothing.

@@ 179-181
In each Python Dockerfile, the folders whose `pyproject.toml` it copies (each `COPY` line, read with a pattern) must be exactly the members; the message names both lists.

@@ 184-186
**Test — the model fetcher gets its one dependency** (9 Nov): run without the project, `fetch_models.py` must be given httpx, at the lockfile's version.

@@ 187-188
httpx's version in `uv.lock`: its `[[package]]` entry, a `name` line followed by a `version` line.

@@ 189-192
Every workflow line that runs the fetcher without the project must give httpx at exactly that version.
