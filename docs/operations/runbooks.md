# Runbooks

What to do, step by step, for the five things that happen to a running Dwarpal (Phase 8). All commands run on the
server in `/opt/dwarpal` (`ssh ubuntu@<server>`, then `cd /opt/dwarpal`), unless they say otherwise. First-time setup
is in [infra/deploy/README.md](../../infra/deploy/README.md).

## 1. Deploy a new version

1. Make sure the commit's **CI passed** on GitHub.
2. GitHub → Actions → **deploy** → *Run workflow* on `main`. It builds the images (tagged with the commit's first 12
   characters), copies the deploy files, and runs `deploy.sh <tag>` on the server.
3. `deploy.sh` waits until every service's health check passes. If one doesn't within 5 minutes, it **rolls back by
   itself** to the version that was running, and the workflow fails — read its log, then section 5. (The demo shop is
   left out until its project and key are in `.env`: without them it can't serve a page.)
4. Read the end of the deploy's log: `inference: {…}` should say `"antispoof":"loaded"`. A **warning** that the
   anti-spoofing networks are missing means every live check will be refused until the two `minifasnet_*.onnx` files
   are in `models/third_party` (README, step 4); copy them, then `docker compose restart inference`.
5. Check by hand: `https://<domain>` loads, `https://api.<domain>/readyz` answers `ready`, and the demo shop's age check
   works.

**Rule for migrations:** the database is never migrated backwards. Every migration must work with the code before it
too (add columns and tables; remove them only in a later release). That is what makes rolling back safe.

## 2. Roll back

Automatic when a deploy is unhealthy. To go back by hand to a known-good version:

```
grep DWARPAL_TAG .env            # the version running now
./deploy.sh <earlier tag>        # any tag GHCR still has: GitHub → Packages lists them
```

## 3. Rotate keys

| What | How | Effect |
| :-- | :-- | :-- |
| **A website's API key** | `docker compose run --rm operator rotate-key --lookup <12 characters after dk_test_ or dk_live_>` | Prints the new key **once**; the old one keeps working for 24 h (`--grace-hours`). Give the new one to the website. |
| **A leaked API key** | `docker compose run --rm operator revoke-key --lookup <id>` | Stops it at once. |
| **Token-signing key** | Rotates itself (§5.4): the new key signs, the old one stays in `/.well-known/jwks.json` until its tokens expire. | Nothing to do. |
| **Database or Valkey password** | Change the value in `.env`, then `./deploy.sh $(grep -oP '(?<=DWARPAL_TAG=).*' .env)` (the deploy resets `dwarpal_api`'s password from `.env`). For the owner or Valkey password, also change it inside the database / restart Valkey. | Seconds of reconnecting. |
| **Master key** | **Never replaced in place**: it seals every signing key. If it may have leaked, treat it as an incident (section 5): new master key, new signing keys, websites told. | — |
| **Deploy SSH key** | Make a new pair; put the public half in `~/.ssh/authorized_keys`, the private half in GitHub's `DEPLOY_SSH_KEY`; remove the old public half. | — |

## 4. Restore from a backup

Only when the live database is lost or damaged. (To *check* backups without touching anything, run
`./restore_drill.sh` instead — monthly.)

**If the server itself was lost**, make a new one first: README steps 1, 2 and 4 (not step 3 — the secrets come
back from the backup), then write `backup.env` again (README step 8, with the restic password from your offline
copy). Bring back `.env` — it holds the master key, without which the signing keys can't be read — start the
databases, and make the two roles the backup's permissions name:

```
docker run --rm --env-file backup.env -v "$PWD/restored:/restored" restic/restic:0.19.1 \
  restore latest --tag secrets --target /restored
sudo install -m 600 -o ubuntu -g ubuntu restored/secrets/.env .env && sudo rm -rf restored
docker compose up -d --wait postgres valkey
docker compose exec -T postgres psql -q -U dwarpal -d dwarpal \
  -c "CREATE ROLE dwarpal_app NOLOGIN; CREATE ROLE dwarpal_api LOGIN"
```

Then, on the old server or the new one:

1. Stop everything that writes: `docker compose stop api webhooks maintenance web shop`.
2. Find the snapshot: `docker run --rm --env-file backup.env restic/restic:0.19.1 snapshots --tag database`.
3. Empty the database and restore into it:

   ```
   docker compose exec -T postgres dropdb -U dwarpal dwarpal
   docker compose exec -T postgres createdb -U dwarpal dwarpal
   docker run --rm -i --env-file backup.env restic/restic:0.19.1 dump <snapshot> dwarpal.dump \
     | docker compose exec -T postgres pg_restore -U dwarpal -d dwarpal --exit-on-error
   ```

4. `./deploy.sh <the tag that was running>` (it also gives `dwarpal_api` its password from `.env`) and check as in
   section 1.
5. Sessions started after the snapshot are gone; websites get their state from their webhooks' outbox only from the
   snapshot onward. Write down the time lost.

## 5. Incident

1. **See:** the alert's mail, if one came (README step 10: its subject names the rule in `alerts.yaml`);
   `docker compose ps` (what's unhealthy), `docker compose logs --since 30m <service>`; the alerts firing now,
   as Prometheus sees them (`docker compose exec prometheus wget -qO- localhost:9090/api/v1/alerts`), or
   Grafana's *Dwarpal API* dashboard on a laptop running the observability profile.
2. **Stop the harm first.** Dwarpal fails closed (§5.7.1): with the inference service or a database down, nobody
   passes — people are told to retry. If a release is at fault, roll back (section 2). If the server is overloaded,
   `docker compose restart inference`.
3. **Suspected compromise** (a leaked key or secret, an unknown process, odd logins in `journalctl -u ssh`):
   - revoke affected API keys (section 3) and tell their websites;
   - replace the secrets in `.env` and redeploy;
   - if the master key may be out, make a new `.env` and new signing keys, and tell websites to refetch the JWKS;
   - keep the logs (`docker compose logs > incident-<date>.log`) before anything is rebuilt.
4. **Personal data:** Dwarpal stores no photos, names or document numbers, only outcomes and scores. If those may have
   leaked, the DPIA's breach process applies (`docs/privacy/dpia.md`): note what, when, whose, and tell the
   operator's data-protection contact (O6) at once — some laws allow only 72 hours.
5. **Afterwards:** a short write-up in `docs/reports/`: what happened, why, what changes so it can't again.
