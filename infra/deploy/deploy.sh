#!/usr/bin/env bash
# Deploy one version of Dwarpal on the server (Phase 8, ADR-0015), and roll back if it doesn't come up healthy.
#   ./deploy.sh <tag>          # a commit's short hash, as the images on GHCR are tagged
# Run in /opt/dwarpal, next to compose.yaml, Caddyfile and .env. GitHub Actions runs it over SSH after building the
# images (infra/deploy/README.md); a person can run it by hand the same way.
set -euo pipefail

tag="${1:?usage: deploy.sh <tag>}"
cd "$(dirname "$0")"

# The secrets file decides the passwords; read the two this script itself needs.
env_value() { grep -E "^$1=" .env | head -n1 | cut -d= -f2-; }
owner_password="$(env_value DWARPAL_DB_OWNER_PASSWORD)"
api_password="$(env_value DWARPAL_DB_API_PASSWORD)"
previous="$(env_value DWARPAL_TAG)"

set_tag() { sed -i "s/^DWARPAL_TAG=.*/DWARPAL_TAG=$1/" .env; }

echo "deploying $tag (was $previous)"
set_tag "$tag"
docker compose pull --quiet

# The databases first; then the migrations, as the database's owner (the services never log in as it).
docker compose up -d --wait postgres valkey
docker compose run --rm --no-deps \
  -e DWARPAL_DATABASE_URL="postgresql+asyncpg://dwarpal:${owner_password}@postgres:5432/dwarpal" \
  api python -m dwarpal_api.cli migrate

# The services' own login, `dwarpal_api`: a member of the restricted `dwarpal_app` role (made by the migrations) and
# nothing else, so row-level security binds everything it does. Made once; its password follows .env every time.
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U dwarpal -d dwarpal -v pw="$api_password" <<'SQL'
SELECT 'CREATE ROLE dwarpal_api LOGIN IN ROLE dwarpal_app'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'dwarpal_api')
\gexec
ALTER ROLE dwarpal_api WITH LOGIN PASSWORD :'pw';
SQL

# The demo shop runs only once its project and key are in .env (README, step 7). Until then it can't serve a page,
# so waiting for it would fail every deploy: it is left out, scaled to no containers at all.
shop=()
[ -n "$(env_value DWARPAL_SHOP_API_KEY)" ] || shop=(--scale shop=0)

# Everything else, waiting until each service's health check passes (or 5 minutes go by).
if docker compose up -d --wait --wait-timeout 300 --remove-orphans "${shop[@]}"; then
  echo "deployed $tag"
  docker image prune --force --filter "until=168h" >/dev/null
  exit 0
fi

# Not healthy: go back to the version that was running. (Migrations are not undone: each one must work with the
# previous version of the code too — see the deploy runbook.)
echo "$tag did not come up healthy; rolling back to $previous" >&2
docker compose ps >&2
set_tag "$previous"
docker compose up -d --wait --wait-timeout 300 --remove-orphans "${shop[@]}"
exit 1
