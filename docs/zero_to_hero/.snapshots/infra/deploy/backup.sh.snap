#!/usr/bin/env bash
# Back up Dwarpal's database, encrypted, to off-site storage (Phase 8). Run daily by a systemd timer
# (infra/deploy/README.md). It needs restic's settings in /opt/dwarpal/backup.env (readable by its owner only):
#   RESTIC_REPOSITORY=s3:https://<namespace>.compat.objectstorage.ap-hyderabad-1.oraclecloud.com/dwarpal-backups
#   RESTIC_PASSWORD=<a long random password, also kept offline: without it no backup can be read>
#   AWS_ACCESS_KEY_ID=…  AWS_SECRET_ACCESS_KEY=…   (an Oracle "customer secret key", for the S3-compatible API)
#
# What is backed up: a full dump of the database, and the secrets file (.env) — the master key in it is needed to
# read the token-signing keys the database holds. restic encrypts both before they leave the server.
# What isn't: Valkey (short-lived state only), images (rebuilt from Git), and never any photo — none is ever stored.
set -euo pipefail
cd "$(dirname "$0")"

restic() {
  docker run --rm -i --env-file backup.env -e RESTIC_CACHE_DIR=/cache \
    -v dwarpal-restic-cache:/cache -v "$PWD/.env:/secrets/.env:ro" \
    restic/restic:0.19.1 "$@"
}

# Create the repository on first use (restic says so, harmlessly, if it already exists).
restic cat config >/dev/null 2>&1 || restic init

# The dump goes straight from PostgreSQL into restic: it is never written to the server's disk unencrypted.
docker compose exec -T postgres pg_dump -U dwarpal -d dwarpal --format=custom \
  | restic backup --stdin --stdin-filename dwarpal.dump --tag database
restic backup /secrets/.env --tag secrets

# Keep 7 daily, 4 weekly and 6 monthly backups; delete the rest, and check the repository's integrity.
restic forget --prune --keep-daily 7 --keep-weekly 4 --keep-monthly 6
restic check
echo "backup done"
