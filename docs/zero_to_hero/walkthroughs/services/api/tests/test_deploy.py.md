---
fingerprint: 2530a2f4762fd6b3
---
Tests for the **deployment's files** (§5.8.2). Most of Phase 8 runs on a real server, where tests can't reach; these check what can be checked here: the secrets are random, private and never replaced, and the Compose file and the generator agree.

@@ 1-2
The module's docstring: what is tested.

@@ 4
The project-wide type-hint setting.

@@ 6-18
base64; `importlib.util` (to load a file that isn't part of any package); the environment's variables (`os`); regular expressions; copying files and finding programs (`shutil`); file permissions; running a program (`subprocess`); the platform's name; reading TOML (`tomllib`, for the workspace's members); paths; the type of a loaded module; and pytest.

@@ 20-21
The repository's root, and the deploy folder in it.

@@ 24-30
**`generator`** — load `infra/deploy/gen_secrets.py` as a module, from its file: it is a standalone script, not part of an installed package, so it can't simply be imported.

@@ 33-34
**`parse`** — read `.env` text back into a dictionary, skipping comments.

@@ 37-40
**Test — every secret is fresh, and the master key is 32 random bytes.** Make two files; the master key decodes to exactly 32 bytes.

@@ 41-48
Every password and key differs between the two files — made fresh each time — and is at least 32 characters long.

@@ 49-51
The demo shop's secret meets the shop's own minimum, and the GitHub account is written in lower case, as GHCR requires.

@@ 54-58
**Test — the secrets file is private and never replaced.** Run the generator into a temporary folder: it succeeds…

@@ 59-60
…the file is readable by its owner only — checked where the operating system has owner-only permissions (Windows doesn't, the same way)…

@@ 61-63
…and a second run refuses, leaving the file exactly as it was: a new master key would orphan every signing key.

@@ 94-96
**Test — Compose asks only for settings the generator writes.** Every `${NAME}` without a default in the production Compose file…

@@ 97-100
…must be among the names the generator writes; otherwise the test names the missing ones. A server set up by the README then never starts with a setting missing.

@@ 103-107
**Test — each deploy script stops at the first error** (`set -euo pipefail`): a backup or a deploy must never carry on half-done as if it had worked.

@@ 110-116
**`alert_email`** — the alerts' script (§5.8.4), loaded from its file the same way as the secrets generator.

@@ 119-124
**Test — Alertmanager's settings name the addresses given**, each quoted, and point at the password's *file*: the password itself is never in them.

@@ 125-130
…and refuse anything else: an address with a line break (which would add a setting of its own), one with a quote, and a bare word; a mail server without its port. Each refusal names the option that was wrong.

@@ 133-142
**Test — switching alerts on twice leaves one of each setting**: the second run changes nothing; the old `COMPOSE_PROFILES` is replaced, not doubled; the three settings have their values; and the rest of `.env` is untouched.

@@ 145-148
**Test — the script itself**, run in a temporary folder with made-up addresses. The tests answer the password question themselves (`ask=`).

@@ 149
Before `.env` exists, it refuses: `gen_secrets.py` comes first.

@@ 150-153
With `.env`, but two different answers to the password question: it refuses, and no password's file is made.

@@ 154-157
With matching answers: the password is in its own file, nowhere in the settings, and `.env` now switches the alerts on.

@@ 158-159
On systems with owner-only permissions (not Windows), the password's file is readable by its owner only.

@@ 162-164
**Test — the deploy copies every file Compose mounts**: each `./file` in the production Compose file must reach the server through the deploy workflow, or be one of those made on the server (the models, and the mail settings). A new settings file that the deploy forgot would otherwise show only as a failed start on the server.

@@ 165-169
The mounted names, from lines like `- ./collector.yaml:`; the files the workflow copies, from the names ending `.yaml`, `.sh` or `.py` (and the Caddyfile), without their folders.

@@ 170
Every mounted file not made on the server must be copied; if not, the test names those missing.

@@ 66-68
**Test — the domain is a bare name** (decision D40): a DuckDNS name or one's own, in lower case; anything that would break `api.<domain>` is refused before a single secret is written.

@@ 69-71
A DuckDNS name in mixed case with spaces around comes back clean; an ordinary domain is kept as it is.

@@ 72-86
Eleven refusals, each naming `--domain`: a scheme, a path, a port, a wildcard, a single part, a hyphen at the start of a part, an empty part, a dot at the end, an IP address, 251 characters (fine alone, but too long once `shop.` is added), and nothing at all.

@@ 87-91
The command run with `https://` in front: it fails, says the domain must be a bare name, and writes no file.

@@ 282-284
**Test — the outside check** (decision D33): every 15 minutes, never on the hour, with a token that may do nothing, only once the API's address is set, and asking `/readyz` — what the README promises.

@@ 285-287
The workflow's text, and its schedule's minutes (the line `cron: "… * * * *"`); without one, the message says so.

@@ 288-290
The minutes in order, and the gap after each — the last one's to the first of the next hour: four gaps of 15 minutes.

@@ 291
None on the hour.

@@ 292-294
A token that may do nothing, the condition on the address, and the readiness check.

@@ 257-260
**Test — both Python images copy every workspace member's description** (9 Nov): uv reads the whole workspace to use the lockfile, so one missing `pyproject.toml` fails the build — as the Python SDK's did, found by CI's first image builds.

@@ 261-264
The workspace's member patterns (`services/*`, `libs/*`, …), each expanded to the folders that have a `pyproject.toml`, written as paths from the repository's root.

@@ 265
The SDK is among them — so the test can't pass by finding nothing.

@@ 266-268
In each Python Dockerfile, the folders whose `pyproject.toml` it copies (each `COPY` line, read with a pattern) must be exactly the members; the message names both lists.

@@ 271-273
**Test — the model fetcher gets its one dependency** (9 Nov): run without the project, `fetch_models.py` must be given httpx, at the lockfile's version.

@@ 274-275
httpx's version in `uv.lock`: its `[[package]]` entry, a `name` line followed by a `version` line.

@@ 276-279
Every workflow line that runs the fetcher without the project must give httpx at exactly that version.

@@ 173-183
**`FAKE_DOCKER`** — a stand-in for the `docker` command, as a small bash script: it writes each command it is given into the file named by `DOCKER_CALLS`, reads and drops any input (the SQL `deploy.sh` pipes in), answers the inference service's readiness question with `READYZ`, and — when `FAIL_FIRST_START` is set — fails the first full start (a command with `--wait-timeout`), leaving a marker file so the next one succeeds: a deploy that doesn't come up healthy, then a rollback that does.

@@ 184-186
**`NEEDS_BASH`** — these tests run `deploy.sh` in bash, so not on Windows (where `bash` may be another program) or without bash.

@@ 189-193
**`deploy`** — run the real `deploy.sh` in a folder: what it needs, and what it gives back — the run's result, and every full start it asked for.

@@ 194-197
The script, beside a `.env` from the real generator, with the shop's key as given.

@@ 198-204
The stand-in `docker`, made runnable, in a folder put first on `PATH`, so the script finds it instead of the real one; where it notes the commands; whether the first start fails, and the readiness answer to give.

@@ 205-214
Run `deploy.sh` with a version tag, with no input, keeping what it prints; bash's full path is looked up first.

@@ 215-216
The full starts it asked for, and the run.

@@ 219-224
**Test — deploys leave out the shop until it has its key** (9 Nov), four times over: without a key and with one, each healthy and unhealthy.

@@ 225-228
Why: the first deploy always comes before the shop has its key; waiting for it would fail every deploy.

@@ 229-232
The run succeeded or failed as the case should; an unhealthy start was followed by the rollback's; and each start left the shop out exactly when there was no key.

@@ 233-235
And Caddy doesn't wait for the shop: its `depends_on` doesn't name it.

@@ 238-246
**Test — a deploy says when the anti-spoofing networks are missing** (9 Nov), three times: loaded, missing, and no answer at all.

@@ 247-250
Why: the server starts without them but refuses every live check, as CI found when it first started the inference image as the server does.

@@ 251-254
Each deploy succeeds; it warns exactly when the networks aren't loaded; and it prints what the service answered.
