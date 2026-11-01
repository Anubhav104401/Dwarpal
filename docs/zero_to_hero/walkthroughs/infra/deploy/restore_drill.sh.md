---
fingerprint: 5ee16a0240beff39
---
**The restore drill** (Phase 8, §5.8.2): restore the latest backup into a throwaway database and show what came back. Run monthly, and its report kept.

@@ 1
Run with bash.

@@ 2-5
Why it exists — Phase 8's exit asks for a restore *on record*: a backup nobody has restored is only a hope — what it does, without touching the live database, and how to run it.

@@ 6-7
Stop at the first failure; work in the script's folder.

@@ 9-12
Restic from its image, with the backup settings and cache, as in `backup.sh`.

@@ 14-17
A name for the throwaway database container, a random password for it, and a **trap**: whatever happens — success, failure, Ctrl-C — the container is removed when the script exits.

@@ 19-22
Start an empty PostgreSQL of the same version as the live one, with no ports open, and wait until it answers.

@@ 23-24
Create the two roles the dump's permissions mention, so restoring them doesn't fail.

@@ 26-28
Find the latest database backup (restic lists snapshots as JSON; Python picks the last one's ID) and pipe it from restic straight into `pg_restore`, stopping at the first error.

@@ 30-31
Have PostgreSQL count each table's rows afresh (`ANALYZE`).

@@ 32-36
Report the time, the snapshot, the database's migration version and every table's row count — the record for the Phase 8 report — and that the drill succeeded.
