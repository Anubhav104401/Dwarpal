---
fingerprint: fc27763b24d94da7
---
**The server's secrets** (Phase 8, §5.8.2): every password and key Dwarpal needs, made fresh and random, written into `/opt/dwarpal/.env`, readable by its owner only.

@@ 1-9
The module's docstring: what it writes, where it runs — **on the server**, so the secrets are made where they are used and never travel — and how to run it, with a DuckDNS name as the example (decision D40). The domain is a bare name; the script refuses to overwrite, because a new master key would make every stored signing key unreadable; and the demo shop's project ID and key are filled in later, by hand (README, step 7).

@@ 11
The project-wide type-hint setting.

@@ 13-19
Command-line options, base64, the operating system's file calls, **patterns** (`re`, for checking the domain), Python's **`secrets`** module (randomness meant for passwords and keys, unlike `random`), error output, and paths.

@@ 38-40
**`token`** — a random secret of 32 bytes, written with letters, digits, `-` and `_` only, so it is safe inside a URL (the database address holds the password) and in `.env`.

@@ 43-44
**`secrets_file`** — the `.env` text.

@@ 45-49
The settings given on the command line — the domain, the e-mail for Let's Encrypt, the GitHub account (in lower case: GHCR's names are) — and the first image tag, `latest`.

@@ 50-51
The **master key**: 32 random bytes in base64, the form the API reads (`MasterKey`).

@@ 52-55
A fresh password for the database's owner, another for the services' login, one for Valkey, and the demo shop's cookie-signing secret.

@@ 56-57
The demo shop's project and key: empty for now — they exist only once the console has made them (README, step 7).

@@ 59-64
One `NAME=value` line each, under a comment saying never to copy, commit or share the file.

@@ 67-73
**`main`** — the command line: the three required settings (the domain's help shows a DuckDNS name), and where to write (`.env` by default).

@@ 79-81
A file there already? Refuse, and say why. Exit code 1 tells a calling script it failed.

@@ 82-85
Create the file **readable and writable by its owner only** (`0600`), and fail if it appeared meanwhile (`O_EXCL`) — permissions set *before* a single secret is written, so there is no moment when others could read it. Then write the text, with the checked domain.

@@ 86-87
Say so, and succeed.

@@ 90-91
Run `main` when the file is run as a program, and exit with its code.

@@ 58
The end of the values.

@@ 21-22
**`LABEL`** — one part of a name between dots (a DNS *label*): letters and digits, with hyphens only inside, 1 to 63 characters. The pattern is written in lower case: names are checked after being lowered.

@@ 25-27
**`domain_of`** (decision D40) — the domain as Caddy and Compose use it, or a `ValueError`. A slip such as `https://` in front would otherwise end up in every name made from it — `api.https://…` — and nothing would work.

@@ 28-29
The text without spaces around it and in lower case (names don't care about case, and one spelling is wanted), cut at its dots.

@@ 30-32
Refused unless it has two parts at least and each is a proper label — so `https://`, a `/`, a port, `*`, an empty part (`..`, or a dot at the end) all fail — and unless the last part has a letter, so an IP address fails too: the sites live at names *under* the domain, and an address has none. The message shows what was typed.

@@ 33-34
The longest name made from it, `shop.<domain>`, must fit within DNS's limit of 253 characters.

@@ 35
The checked domain.

@@ 74-78
The domain is checked first: if it isn't a bare name, say why and stop with exit code 1 — before anything is written.
