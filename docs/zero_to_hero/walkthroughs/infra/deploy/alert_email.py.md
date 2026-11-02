---
fingerprint: ecbf3fc8f5cd36bd
---
**Alerts by email** (decided 2 Nov 2026, §5.8.4): a script the owner runs once on the server. It writes Alertmanager's settings, keeps the mail password in a file only its owner can read, and switches the alert services on.

@@ 1-10
The module's docstring: what it does — writes Alertmanager's settings and the password's file, and switches the `alerts` services on — where it runs (on the server, after `gen_secrets.py`), and why it asks for the password instead of taking it as an option: a command line is saved in the shell's history, typed answers aren't.

@@ 12
The project-wide type-hint setting.

@@ 14-21
Command-line options, **`getpass`** (asks for text without showing it on screen), JSON (for quoting), file calls, patterns, the error stream, the type of a function, and paths.

@@ 23-26
What counts as a plain address (`name@domain.tld`) and a plain mail server (`host:port`). Each value is written into a YAML file; a value with a line break or a quote in it could add settings of its own — the YAML version of an injection — so anything else is refused.

@@ 28-29
Where the password's file appears inside the Alertmanager container (compose.yaml mounts it there). The `noqa` tells the linter, which suspects a hard-coded password in any name containing *password*, that this is only a path.

@@ 32-33
**`alertmanager_config`** — Alertmanager's settings for the three values given.

@@ 34-40
Each value is checked against its pattern; the first that fails stops everything with a message naming the option.

@@ 41-42
Each value written as a JSON string: double quotes, with any special character escaped. A JSON string is also a valid YAML string, so the value can't be misread.

@@ 43-49
The settings shared by every mail: the mail server, the sender (the account itself), its user name, the **file** holding its password — so the password never sits in this file — and TLS required, so the password is never sent in the clear.

@@ 50-55
The **route**: every alert goes to the receiver `owner`. Alerts of the same name are grouped into one mail; the first waits 30 seconds for company, later changes go out at most every 5 minutes, and an alert still firing is mailed again every 4 hours.

@@ 56-61
The one receiver: mail to the owner's address, and a second mail when the alert is over (`send_resolved`).

@@ 64-65
**`switched_on`** — the `.env` text with the three settings the alerts need.

@@ 66-70
**`COMPOSE_PROFILES=alerts`** makes Compose start the services marked `profiles: [alerts]` (Compose reads this from `.env` by itself); the API is pointed at the collector; and Alertmanager runs as the account that owns the password's file.

@@ 71-73
Every line that already sets one of the three is dropped and the three are added at the end, so running the script twice leaves one of each.

@@ 76-77
**`write_private`** — writes a file that only its owner can read or write.

@@ 78-79
The file is opened (made if missing, emptied if not) with mode 600 — but a file that already existed keeps its old mode, so the mode is set again before anything is written.

@@ 80-81
Then the text goes in.

@@ 84-88
**`current_user`** — this account's user and group numbers, `uid:gid`, as Compose's `user:` wants them. Windows has neither; there (only ever in tests) the usual *nobody* stands in.

@@ 91-97
**`main`**: the three options and the folder to write into. `ask` is the function that asks for the password — `getpass` normally; the tests pass their own, so they can answer without a keyboard.

@@ 98-101
Without `.env` there is no server set up yet: `gen_secrets.py` comes first.

@@ 102-106
The settings are made before the password is asked for, so a mistyped address is reported before anyone types a secret.

@@ 107-110
The password, asked twice; empty or different answers stop with nothing written.

@@ 111-112
The password into its private file, the settings beside it (they hold no secret).

@@ 113-114
The three settings into `.env`. Writing an existing file keeps its mode, so `.env` stays readable by its owner only.

@@ 115-116
What to do next: `docker compose up -d --wait` starts the three new services.

@@ 119-120
Run as a program, `main`'s answer becomes the exit code.
