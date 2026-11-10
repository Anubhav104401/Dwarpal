---
fingerprint: 6522d736180db732
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

@@ 14-17
**The storage's region**, found on the first real backup (10 Nov 2026). Oracle's S3-compatible storage checks that every request is *signed for its own region*, and answers anything else with a bare "Access Denied". Restic didn't work out the region by itself, so every request failed, even though the key was right. The fix reads the region out of the storage's address in `backup.env`: `sed -n 's/…/\1/p'` prints only the piece matched between `objectstorage.` and `.oraclecloud.com`, such as `ap-hyderabad-1`. `region_option` is then a bash *array*, either `-o s3.region=ap-hyderabad-1` or, for any other storage (like the folder CI's rehearsal uses), nothing at all: `${region:+…}` means "this, but only if `region` isn't empty".

@@ 19-23
**`restic`**: run restic from its official image, with its settings from `backup.env`, the region option from above (`"${region_option[@]}"` puts in the array's words, or none), its cache in a named volume (so each backup only sends what changed), and the `.env` file mounted read-only for it to back up.

@@ 25-26
Create the encrypted repository the first time: if `cat config` fails, there is none yet.

@@ 28-30
Dump the database inside its container (`pg_dump`, PostgreSQL's own compact format) and pipe it straight into restic, which encrypts it as it reads: the dump is never written to the server's disk unencrypted.

@@ 31
Back up the `.env` too, tagged `secrets`.

@@ 33-36
Keep 7 daily, 4 weekly and 6 monthly backups and delete the rest (`forget --prune`); verify the repository's integrity (`check`); and say it is done.
