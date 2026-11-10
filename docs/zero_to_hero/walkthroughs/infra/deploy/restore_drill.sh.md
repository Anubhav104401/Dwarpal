---
fingerprint: c8adc2cd04dc606e
---
**The restore drill** (Phase 8, §5.8.2): restore the latest backup into a throwaway database and show what came back. Run monthly, and its report kept.

@@ 1
Run with bash.

@@ 2-5
Why it exists — Phase 8's exit asks for a restore *on record*: a backup nobody has restored is only a hope — what it does, without touching the live database, and how to run it.

@@ 6-7
Stop at the first failure; work in the script's folder.

@@ 13-16
Restic from its image, with the backup settings, the region option and the cache, as in `backup.sh`.

@@ 9-11
The storage's region, read out of its address, exactly as in `backup.sh` (lines 14–17 there explain why Oracle needs it).

@@ 18-21
A name for the throwaway database container, a random password for it, and a **trap**: whatever happens — success, failure, Ctrl-C — the container is removed when the script exits.

@@ 29-30
Create the two roles the dump's permissions mention, so restoring them doesn't fail.

@@ 32-34
Find the latest database backup (restic lists snapshots as JSON; Python picks the last one's ID) and pipe it from restic straight into `pg_restore`, stopping at the first error.

@@ 36-37
Have PostgreSQL count each table's rows afresh (`ANALYZE`).

@@ 38-42
Report the time, the snapshot, the database's migration version and every table's row count — the record for the Phase 8 report — and that the drill succeeded.

@@ 23-25
Start an empty PostgreSQL of the same version as the live one, with no ports open to the outside.

@@ 26-28
Wait until it answers **over TCP** (`-h 127.0.0.1`), not just on its socket. On first start, PostgreSQL's image runs a temporary server — on the socket only — to set the database up, then stops it and starts the real one. Asking only the socket can catch the temporary server, and the next command then fails with *the database system is shutting down*: exactly what CI's rehearsal of this drill found on its first run (9 Nov). Only the real server listens on TCP.
