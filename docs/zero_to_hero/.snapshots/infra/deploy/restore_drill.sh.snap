#!/usr/bin/env bash
# The restore drill (Phase 8's exit asks for one on record): prove the latest backup can be read back into a working
# database — without touching the live one. It restores into a throwaway PostgreSQL container, reports the migration
# version and every table's rows, then removes the container.
#   ./restore_drill.sh           # prints a short report; append it to docs/reports/phase-8.md
set -euo pipefail
cd "$(dirname "$0")"

restic() {
  docker run --rm -i --env-file backup.env -e RESTIC_CACHE_DIR=/cache -v dwarpal-restic-cache:/cache \
    restic/restic:0.19.1 "$@"
}

drill=dwarpal-restore-drill
password="$(openssl rand -hex 16)"
cleanup() { docker rm -f "$drill" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# A fresh, empty PostgreSQL, of the same version as the live one, with no ports open.
docker run -d --name "$drill" -e POSTGRES_PASSWORD="$password" -e POSTGRES_DB=dwarpal -e POSTGRES_USER=dwarpal \
  postgres:18.6-alpine3.24 >/dev/null
# Ready over TCP, not just the socket: on first start the image runs a temporary server, on the socket only, to set the
# database up, then stops it — a command sent then fails with "the database system is shutting down".
until docker exec "$drill" pg_isready -h 127.0.0.1 -U dwarpal -d dwarpal >/dev/null 2>&1; do sleep 1; done
# The restricted role the dump's grants refer to.
docker exec "$drill" psql -q -U dwarpal -d dwarpal -c "CREATE ROLE dwarpal_app NOLOGIN; CREATE ROLE dwarpal_api LOGIN"

# The latest database backup, straight from restic into pg_restore.
snapshot="$(restic snapshots --tag database --latest 1 --json | python3 -c 'import json,sys; print(json.load(sys.stdin)[-1]["short_id"])')"
restic dump "$snapshot" dwarpal.dump | docker exec -i "$drill" pg_restore -U dwarpal -d dwarpal --exit-on-error

# What came back: the migrations' version, and each table's rows (counted fresh by ANALYZE).
docker exec "$drill" psql -U dwarpal -d dwarpal -c "ANALYZE" >/dev/null
echo "restore drill $(date -u +%Y-%m-%dT%H:%MZ): snapshot $snapshot restored"
docker exec "$drill" psql -U dwarpal -d dwarpal -At -c "
  SELECT 'migration ' || version_num FROM alembic_version;
  SELECT '  ' || relname || ': ' || n_live_tup || ' rows' FROM pg_stat_user_tables ORDER BY relname;"
echo "restore drill: OK"
