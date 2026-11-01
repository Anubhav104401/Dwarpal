---
fingerprint: bf705c8a11eef397
---
**The server's secrets** (Phase 8, §5.8.2): every password and key Dwarpal needs, made fresh and random, written into `/opt/dwarpal/.env`, readable by its owner only.

@@ 1-8
The module's docstring: what it writes, where it runs — **on the server**, so the secrets are made where they are used and never travel — how to run it, and why it refuses to overwrite: a new master key would make every stored signing key unreadable.

@@ 10
The project-wide type-hint setting.

@@ 12-17
Command-line options, base64, the operating system's file calls, Python's **`secrets`** module (randomness meant for passwords and keys, unlike `random`), error output, and paths.

@@ 20-22
**`token`** — a random secret of 32 bytes, written with letters, digits, `-` and `_` only, so it is safe inside a URL (the database address holds the password) and in `.env`.

@@ 25-26
**`secrets_file`** — the `.env` text.

@@ 27-31
The settings given on the command line — the domain, the e-mail for Let's Encrypt, the GitHub account (in lower case: GHCR's names are) — and the first image tag, `latest`.

@@ 32-33
The **master key**: 32 random bytes in base64, the form the API reads (`MasterKey`).

@@ 34-37
A fresh password for the database's owner, another for the services' login, one for Valkey, and the demo shop's cookie-signing secret.

@@ 38-39
The demo shop's project and key: empty for now — they exist only once the console has made them (README, step 7).

@@ 41-46
One `NAME=value` line each, under a comment saying never to copy, commit or share the file.

@@ 49-55
**`main`** — the command line: the three required settings, and where to write (`.env` by default).

@@ 56-58
A file there already? Refuse, and say why. Exit code 1 tells a calling script it failed.

@@ 59-62
Create the file **readable and writable by its owner only** (`0600`), and fail if it appeared meanwhile (`O_EXCL`) — permissions set *before* a single secret is written, so there is no moment when others could read it. Then write the text.

@@ 63-64
Say so, and succeed.

@@ 67-68
Run `main` when the file is run as a program, and exit with its code.

@@ 40
The end of the values.
