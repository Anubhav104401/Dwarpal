---
fingerprint: e4f1ade7d2039c46
---
**Backups** (Phase 8, §5.8.2): the database and the secrets file, encrypted with **restic** before they leave the server, sent to off-site storage, and thinned out over time. A systemd timer runs it daily (`infra/deploy/README.md`).

@@ 1
Run with bash.

@@ 2-6
What it does — an encrypted backup to off-site storage, daily — and the settings it needs in `backup.env`: where the backups go (Oracle's Object Storage, through its S3-compatible interface), the password that encrypts them (kept offline too: without it no backup can be read), and the storage's access key.

@@ 7-10
What is backed up: the database, and the `.env` — its master key is needed to read the signing keys in the database. What isn't: Valkey's short-lived state, the images (rebuilt from Git), and never a photo — Dwarpal never stores one.

@@ 11-12
Stop at the first failure, and work in the script's folder.

@@ 14-18
**`restic`** — run restic from its official image, with its settings from `backup.env`, its cache in a named volume (so each backup only sends what changed), and the `.env` file mounted read-only for it to back up.

@@ 20-21
Create the encrypted repository the first time: if `cat config` fails, there is none yet.

@@ 23-25
Dump the database inside its container (`pg_dump`, PostgreSQL's own compact format) and pipe it straight into restic, which encrypts it as it reads: the dump is never written to the server's disk unencrypted.

@@ 26
Back up the `.env` too, tagged `secrets`.

@@ 28-31
Keep 7 daily, 4 weekly and 6 monthly backups and delete the rest (`forget --prune`); verify the repository's integrity (`check`); and say it is done.
