---
fingerprint: d97c6e5ad32ed579
---
The API's **settings**: every value that may differ between a laptop, the test suite and production — addresses, secrets, time limits — in one checked place. It follows the same pattern as the inference service's `settings.py` (§5.1.1), with two additions: a **secret** that must never leak into logs, and a **guard** that refuses unsafe values in production.

!!! kid "Explain like I'm six — the settings card"
    Imagine a robot that works in many different houses. Instead of rebuilding the robot for each house, you hand it a small card: "the kitchen is through the blue door, the spare key is under the mat". The robot stays the same; only the card changes. Environment variables are that card, and this file reads it.

@@ 1
The docstring names the prefix: every setting is read from an environment variable whose name starts with `DWARPAL_`.

@@ 3
The project-wide type-hint setting (§5.0.2).

@@ 5
`base64` — Python's built-in module for **Base64**, a way to write any bytes using only 64 safe, printable characters (`A`–`Z`, `a`–`z`, `0`–`9`, `+` and `/`). Every 3 bytes become 4 characters. It is needed because an environment variable holds *text*, while the master key is 32 *raw bytes*, some of which aren't printable characters at all.

@@ 6
`Path` — file-system paths (§4.2).

@@ 7
`Literal` — a type that allows only certain exact values.

@@ 9
From Pydantic (§4.8):

- `SecretStr` — a text value that **hides itself**. Printed or logged, it shows `**********`. The real value comes out only through `.get_secret_value()`, so it can't leak by accident;
- `model_validator` — marks a function that checks the *whole* settings object, after every field has been filled in.

@@ 10
From **pydantic-settings**: `BaseSettings` is a Pydantic model whose fields are filled from environment variables, and `SettingsConfigDict` configures how.

@@ 12
`REPO_ROOT` — the repository's top folder, found from this file's own location. `parents[4]` climbs five levels: `settings.py` → `dwarpal_api` → `src` → `api` → `services` → the root. It gives a sensible default for where model files live during development.

@@ 13
`DEV_MASTER_KEY` — the **development master key**: the 32 bytes of the text `dev-only-master-key-for-dwarpal!`, Base64-encoded. `.decode()` turns the encoder's bytes into ordinary text.

It is readable on purpose. Anyone who meets it — in a log, in a bug report — can see at once that it is the development key, published in this repository, and therefore protects nothing.

@@ 16
**`Settings`** — the class itself. Each field below becomes one environment variable.

@@ 17
`env_prefix="DWARPAL_"` means the field `database_url` is read from `DWARPAL_DATABASE_URL`. `extra="ignore"` lets other `DWARPAL_…` variables (for example, the inference service's) exist without causing an error here.

@@ 19
`environment` — which kind of place the API is running in: `"development"`, `"test"` or `"production"`. Any other value is refused at start-up. The default is the safe, local one.

@@ 20
`database_url` — the address of PostgreSQL, written as a URL:

```
postgresql+asyncpg://dwarpal:dwarpal-local-only@127.0.0.1:5432/dwarpal
└──── kind ──────┘   └user┘ └──── password ───┘ └─ host ┘ └port┘ └ db ┘
```

- `postgresql+asyncpg` — the kind of database, plus the driver to use (`asyncpg`, §4.10);
- `dwarpal` / `dwarpal-local-only` — the user name and password. They match the defaults in `infra/compose/compose.yaml`, so a fresh checkout works with no setup;
- `127.0.0.1` — the special address that always means "this same computer", also called **localhost**;
- `5432` — PostgreSQL's standard port;
- the final `dwarpal` — the name of the database inside the server.

@@ 21-22
`database_role` — the database role the API works as: `dwarpal_app`, which the migration `v0002_tenancy.py` creates. It owns no tables, so PostgreSQL's row-level security confines it to one tenant at a time (`db.py`). `None` means "stay the login you connected as"; that is for a deployment whose login is *already* a restricted role, as production's should be (§5.4.1).

@@ 23
`valkey_url` — where Valkey listens (§4.11). The scheme `redis://` means "speak the Redis language", which Valkey understands. Port `6379` is the standard one, and the `/0` picks database number 0 — Valkey keeps 16 numbered databases, and 0 is the default.

@@ 24
`inference_url` — where the inference service listens: port 8001 on this computer.

@@ 25
`inference_timeout_s` — give up on the inference service after 5 seconds. Phase 1 measured a whole burst at about 0.1 seconds (§5.1.1), so 5 seconds only ever runs out when something is wrong. The person then gets a "try again" instead of a page that hangs for ever.

@@ 29
`master_key` — the 32-byte key that **seals** the private signing keys before they are stored in the database (§4.12, `signing.py`). It is a `SecretStr`, so it never appears in logs. The default is the development key; production must provide a real one (see the guard below).

@@ 30
`issuer` — the API's own public address. It is written into every age token as the `iss` ("issuer") claim, and the address of the public keys is built from it.

@@ 31
`verify_url` — the address of the hosted **verify page** (`apps/web`, port 3000 in development). The link a website sends its user to is built from it.

@@ 32
`cors_origins` — the web pages that are allowed to call this API *from inside a browser* (CORS, §4.13). Only the verify page needs to. A list in an environment variable is written as JSON, for example `["https://verify.example.com"]`.

@@ 33
`models_dir` — the folder holding model files. In containers it is set to a mounted, read-only folder.

@@ 34
`age_manifest` — where, inside `models_dir`, the **manifest** of the active age model lives: the file that says which model versions are allowed and which thresholds they were calibrated for (`domain/policy.py`).

@@ 35
`session_ttl_s` — a verification session must be finished within **1,800 seconds (30 minutes)** of being created. "TTL" means **time to live**.

@@ 36
`flow_ttl_s` — a flow token (the browser's permission to work on one session) lasts **15 minutes**.

@@ 37
`challenge_ttl_s` — a challenge must be used within **2 minutes**. Frames must be captured *fresh*, not prepared in advance (Stage 3 §5).

@@ 38-39
The comment explains the two **per-device budgets** below: how many liveness challenges one device, and one network address, may take per project in an hour. A device is the random ID the verify page keeps (`apps/web/lib/device.ts`); many people can share one network, so its budget is larger.

@@ 40-41
`device_challenges_per_hour = 30` and `address_challenges_per_hour = 120`.

@@ 42-44
The rate limit for each API key (`http/deps.py`): 100 requests a second on average, with bursts of up to 200 at once — the figures of the implementation design (§3.7).

@@ 49-52
Webhooks (Phase 4): `webhook_allow_private` lets webhooks go to private or local addresses — needed on a developer's laptop and in tests, and refused in production (below). How long to wait for a receiver's answer (10 s), and how often the idle worker looks for due deliveries (every 2 s).

@@ 53-57
The console (Phase 4, step 2): `console_origins` — the addresses its pages are served from, checked against each change's `Origin` header (§5.4.5); how long a signed-in session lasts without use (12 hours); and whether its cookie may only travel over HTTPS. Only the tests, which talk plain HTTP inside one program, switch that off; production refuses to (below).

@@ 61-63
Sign-in attempts, counted per account and per network address: up to 5 at once, then one more a minute — slow enough that guessing a password is hopeless, generous enough for someone who mistypes.

@@ 70-71
**`otel_endpoint`** (Phase 7) — the address of an OpenTelemetry collector to send traces to (`DWARPAL_OTEL_ENDPOINT`). `None` by default: no traces are made at all unless someone asks for them.

@@ 73-74
The **production guard**. `@model_validator(mode="after")` makes Pydantic call this method after all the fields are filled in. It receives the finished settings object as `self`, and must either return it or raise an error. If it raises, the API refuses to start.

@@ 75-76
Outside production there is nothing more to check, so the settings are returned unchanged.

@@ 77-78
**Refuse the development key in production.** It is published in this repository, so with it anyone could unseal the signing keys and forge age tokens. The error names the exact variable to set.

@@ 79-80
Production must never send webhooks into private networks.

@@ 81-82
And production's cookie must always demand HTTPS.

@@ 83-85
**Refuse plain `http://` addresses in production.** Over `http://`, tokens and links travel unencrypted, and anyone on the network path could read or change them (§0.9).

`getattr(self, name)` reads a field whose name is held in the variable `name`, so one loop checks both fields. `name.upper()` turns `issuer` into `ISSUER`, so the message names the exact variable: `DWARPAL_ISSUER`.

@@ 86
All checks passed: return the settings.

!!! try "Try it yourself"
    The tests in `services/api/tests/test_domain.py` create production settings with and without a real key. Read `test_production_refuses_development_values`, then run `uv run pytest services/api/tests/test_domain.py -k production` and watch it pass.

@@ 58-60
`passkey_rp_id` (Phase 9) — the site name passkeys are bound to, WebAuthn's *relying party ID*: the console's host name in production. Empty means the host of the first console origin, `localhost` in development.

@@ 26-28
**How long the document check may take** before the API gives up on it: 20 seconds. It does more than the face check — the same face checks on the selfie, then reading the document's letters and comparing two faces — and 5 seconds wasn't always enough on a busy machine (CI's end-to-end test had twice seen "the checker is busy" by 2 Nov; it wasn't the only cause, as a third failure on 3 Nov showed). Giving up still means "try again", never a pass.

@@ 45-48
**`flow_requests_per_second`**, **`flow_burst`** (9 Nov) — the verify page's calls from one network address: 10 a second, in bursts of up to 300. Plenty for many people sharing one address — a school, an office, a mobile network's shared address — while a flood from one address is refused before it reaches the database.

@@ 64-69
**`login_free_failures`**, **`login_first_lock_s`**, **`login_longest_lock_s`** (9 Nov) — the design's lock-out back-off: after five wrong passwords or codes in a row for one account from one network address, that address waits before trying the account again — a minute, then twice as long after each further wrong one, at most an hour (`lock_s` in `app/console.py`). Only that address: a stranger's guessing can't lock the owner out.
