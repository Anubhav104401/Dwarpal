# Decisions waiting for the owner

Work that needs your answer — a download, a design choice, an account, or something only you can do — is collected here instead of stopping the work. Everything else carries on. Each item says what it unblocks.

**Started:** 26 Oct 2026, overnight run. **Phase 4 is complete** (commits `450bfba`, `7d730ee`, `95f3e91`).

## Decisions for the night of 8→9 Nov (recorded at its start, for your review at 10 am)

The owner asked (8 Nov, evening) for every decision of the night to be recorded at once, at its start, and not to be
disturbed until 10 am on 9 Nov — except when the deployment on Oracle needs them. These are the defaults taken; each can
be reversed in the morning.

| # | Decision | Default taken |
| :-: | :-- | :-- |
| **D24** | How a live check works while no age model is certified (asked and answered, 8 Nov) | **ID document only**: a live session skips the age estimate and is decided by the passport/ID check, whose own selfie and challenge still prove a live person. The age estimate comes back for live checks once a model is certified |
| **D25** | Email from the app (password reset, invitations) (asked and answered, 8 Nov) | **Not now**: recovery stays with passkeys, one-time codes and recovery codes |
| D26 | Age Passes in document-only sessions | Given out after a passed check and accepted as before: a pass is as strong as the check that issued it, and its token says `age_pass` |
| D27 | Custom policies in document-only mode | Allowed whatever their risk budget: the age model's thresholds don't apply when it doesn't decide |
| D28 | Creating projects in the console | Owners and admins; at most 20 projects per organisation; a name of 1–80 characters |
| D29 | Allowed origins | Exact origins only (scheme, host and port; no paths, no wildcards); `https://` in production, `http://` also for `localhost` in development; at most 10 per project; changes are audited |
| D30 | API keys in the console | Listed with their prefix, scopes, mode, creation and expiry — never the secret; revoking is immediate and audited; the same roles that create keys may revoke them |
| D31 | Changing a password | Needs the current password (and a one-time code if switched on); ends every other console session of that person |
| D32 | Deleting one's own account | Needs the password (and a one-time code if switched on). Refused while the person is the only owner of an organisation that has other members (hand ownership over first). An organisation where they are the only member is closed with them: its keys are revoked, and its records are purged by the usual retention. The person's email, password, one-time-code secret, passkeys and console sessions are erased; their ID stays in the audit chain, so the chain still verifies |
| D33 | Watching the server from outside | A scheduled GitHub workflow every 15 minutes checks the API's `/readyz` and the web home page once `DWARPAL_PUBLIC_API_URL` is set; GitHub emails the owner when a run fails. No new account |
| D34 | Fixable vulnerabilities found by tonight's scans | Package upgrades are downloads, so they are **not** applied: each is listed here, with file, source and size, for approval |
| D35 | More made-up people | Render 40 more (render-041…080) with the tools already approved (D23), so the split by person is less lumpy; no download |
| D36 | Hindi for new screens | Machine-drafted, as all the Hindi (D2), and flagged for the native review |
| D37 | The public pages | The model page, the discovery document and the developers' guide say that live checks use an ID document until a model is certified; the practice statement's draft (still waiting for O5) says the same |
| D38 | Commits | Pushed to `main` in checked batches (as authorised); CI watched through the public API |
| D39 | When to disturb the owner | Only when the deployment on Oracle needs them (O2c, O10, O8, O9), once all else is done |

**Asked and answered on 8 Nov, before the night** (the owner asked to be asked everything at once):

| # | Decision | Answer |
| :-: | :-- | :-- |
| D40 | The domain for the deployment (O10) | **A free DuckDNS name** (stays Always Free), such as `dwarpal.duckdns.org` with `api.` and `shop.` under it; the owner creates the DuckDNS account at deploy time. The deploy files and README are adapted tonight |
| D41 | How the age estimate becomes usable for live checks | **Keep document-only (D24) for now**; revisit after launch. No new data work |
| D42 | `joserfc` 1.7.6 (`joserfc-1.7.6-py3-none-any.whl`, 71,588 bytes, pypi.org, BSD-3-Clause, released 18 Oct) for CVE-2026-119284 / GHSA-9pg5-8c7x-5hfx (memory exhaustion while parsing a compact JWS) | **Approved**: installed tonight |
| D43 | A live document camera on computers | **Build it**: a framing guide over the webcam; the file chooser stays as a fallback |
| D44 | Inviting people who haven't signed up | **Pending invitations**: no email is sent (D25); the person joins when they sign up with that address |
| D32 | Deleting an account that is an organisation's only member | **Confirmed**: the organisation is closed with it (keys revoked at once, records purged by retention) |
| D45 | The Kubernetes chart | **Keep it checked in CI, no cluster**; optional in the roadmap |

## Morning summary — 9 Nov (overnight work, 8→9 Nov)

**Only the deployment is left for you.** Everything that doesn't need the server is built, tested and pushed. The steps,
in order (details in [`infra/deploy/README.md`](../../infra/deploy/README.md)):

| # | What | Unblocks |
| :-: | :-- | :-- |
| O2c | Create the Oracle instance with `infra/vm/cloud-init.yaml`, and open ports 80 and 443 in its security list; then the README's steps 2–4 (files, secrets, and the models — **step 4's list includes the two `minifasnet_*.onnx` files**) | everything below |
| O10 | **The DuckDNS name** (D40): sign in at duckdns.org, add a name and set it to the instance's public IP (README step 1). `dwarpal` itself is taken; `dwarpal-age` and `getdwarpal` were free at 2 am | HTTPS certificates |
| O9 | GitHub settings (README step 5): the variables `DWARPAL_PUBLIC_API_URL`, `DEPLOY_HOST`, `DEPLOY_KNOWN_HOSTS`, the secret `DEPLOY_SSH_KEY`, and a `production` environment | the first deploy, and the outside uptime check (D33) |
| O8 | An Object Storage bucket and a customer secret key for backups (README step 8) | backups and the restore drill — Phase 8's exit |

Still open from before, not blocking the deploy: O11 (the two dataset requests), O12 (the consent form's review, then
filming yourself), O5 (the legal review of the compliance map and practice statement).

**Done overnight** (no decision needed; all pushed, CI green on `5ea6b69`):

- **Live checks by ID document** (D24, `3ac4b3a`): while no age model is certified, a live session opens on the passport
  check; the token's methods say `document_mrz` and `face_match`. Test sessions are unchanged. **`joserfc` 1.7.6**
  installed (D42).
- **The console, ready for a launch** (`ff53957`): projects and their allowed origins (D28, D29) — which deploy step 7
  needs — keys listed and stopped (D30), a password change (D31), account deletion (D32), and invitations for people
  without an account (D44). Migration 0012.
- **40 more made-up people** (D35): 80 in all, filed as 240 injected clips (59 people for training, 11 for validation,
  10 for testing); 98.5 % of sampled frames give exactly one face. Training still waits for real people (O12).
- **The deployment takes a DuckDNS name** (D40, `4ed0d89`): checked first that DuckDNS answers every name under one (`api.`,
  `shop.`) and that duckdns.org is on the Public Suffix List, so the console's sign-in and Let's Encrypt work as with a
  bought domain. `gen_secrets.py` refuses anything but a bare name.
- **Watching from outside** (D33, `4ed0d89`): the `uptime` workflow checks the API, the home page and both certificates every 15
  minutes once `DWARPAL_PUBLIC_API_URL` is set; a failure makes GitHub email you.
- **Safe retries** (`4ed0d89`): the developers guide tells websites to use a fresh random idempotency key per session (Phase 4 open
  item 6), and both SDKs take one.
- **A document camera for computers** (D43, `4ed0d89`): the webcam with a passport-shaped guide, the photo looked at before it is
  used, the file chooser beside it; phones unchanged. Two new browser tests.
- **The verify page's calls limited per address** (Phase 4, open item 5, `9b339be`): 10 a second, bursts of 300 — far above what people sharing a network need — so a flood from one address stops before the database; the page says to wait and reload.
- **The production images are built in CI** on every push (`9b339be`, `5ea6b69`), on GitHub's Arm machines and never published (D17 allows exactly that), then started as far as each can be alone. **Its first run found two problems that would have stopped your first deploy**: the Python images didn't copy the Python SDK's `pyproject.toml`, and the deploy workflow ran the model fetcher without httpx. Both are fixed and guarded by tests; all four images now build and start. A third trap, found by reading `deploy.sh`: the first deploy would have waited for the demo shop, which can't start before step 7 gives it a key, and rolled back. The shop is now left out until its key is in `.env`. **And one that needs you to copy two more files**: the anti-spoofing networks are served as ONNX files that `dwarpal_ml.antispoof` made on your computer on 20 Oct, and the README's model step named only what the fetcher fetches — a server set up by it would have refused every live check. Step 4 now lists exactly which files to copy (the two `minifasnet_*.onnx` included), and every deploy says whether they are loaded.
- **The first deploy, a backup and the restore drill are rehearsed in CI** on every push, with the API's image and the real scripts: migrations, the restricted database login, the API in production mode, `backup.sh` and `restore_drill.sh`. The first rehearsal found the drill broken (it could start restoring before PostgreSQL was really up — your step 9 would have failed); fixed, and the drill now restores a backup on every push. The rehearsal also switches **alerts by email** on as README step 10 does: the API's counts reach Prometheus, the availability rule computes and Alertmanager is connected — only the mail itself waits for your mail account on the server.
- **A sixth trap, found by reading**: the webhook worker and the hourly maintenance would have logged in as the API's restricted database user, which row-level security binds — so on the server they would have quietly done nothing: no webhooks, no expired sessions, and no deletion after the retention period. They now log in as the database's owner, like the migrations; the runbooks' key commands use a new `operator` service. Rehearsed in CI.
- **Browser tests**: the full suite passes in Chromium and WebKit (50 tests; the WebKit passkey test is skipped by design).
- **Scans** (D34): `pip-audit` finds nothing; `pnpm audit` finds nothing in what ships — only the two old `extract-zip`
  advisories inside Lighthouse CI, a test tool, with no fixed version. Nothing to approve.
- **Hindi** (D36): the new screens' words are machine-drafted, like all the Hindi, for the native review.
- **The book**: every new and changed file explained (348 files, 31,305 lines at 100 %), with §5.6.5, §5.8.5 and eleven new glossary terms.

## Morning summary — 4 Nov (overnight work, 3→4 Nov)

**Your answers still open**, in the order they unblock things:

| # | What | Unblocks |
| :-: | :-- | :-- |
| D23 | Approve the three downloads for making renders (Blender 5.2.3, MPFB 2.0.18, MakeHuman's CC0 assets — sizes and sources under *Waiting for you (3 Nov)*) | the made-up people; then training |
| O11 | Send the two dataset requests (`docs/data/dataset-requests.md`) | other people's renders, if allowed |
| O12 | Have the consent form reviewed (English, and the new Hindi draft), then film yourself first | the real side of the data |
| O2c, O10, O8, O9 | The server, the domain, backup storage, GitHub deploy settings (unchanged since 2 Nov) | the first deploy |

**Done overnight** (no decision needed):

- **The render detector's code, ready for the data** (§5.9.4): MiniFASNet V2 with a two-answer head; crops prepared only from clips with a standing consent; training; a threshold that refuses at most 5 % of real people on validation; APCER and BPCER on the test people against release gates (`ml/render_gates.toml`, provisional — yours to confirm); an ONNX export; and the inference service records its chance (never decides) once `DWARPAL_INFERENCE_RENDER_MODEL` names a trained file. Tested on fake pictures only.
- **CI flakes**: Lighthouse's home-page performance (87, under 90) is fixed — English pages no longer fetch the Devanagari font for the one Hindi word in the language switch. The passport test's "checker is busy" is **not** fixed: the document check now waits up to 20 s, which wasn't enough (it failed again on `d49c416`); the test now reports what the inference service says when it fails, so the next failure names the cause.
- **A Hindi draft of the consent form** (`docs/data/consent-form.hi.md`), marked for native and legal review.
- **`renders film`**: plays a rendered sequence full-screen and films it in step with the webcam (protocol step 5).
- **CI**: `c3c4bb7` green; `d49c416` red on the passport test only (above); `8cfd9e3` green (the flake didn't recur, so the probe has nothing to report yet).

## Morning summary — 2 Nov, 10 am (overnight work on Phases 8 and 9)

**Still waiting for you** — steps only you can take (each says what it unblocks):

| # | Step | Unblocks |
| :-: | :-- | :-- |
| O2c | **Create the server** from `infra/vm/cloud-init.yaml` (Always Free Ampere, 2 cores / 12 GB, Ubuntu 24.04), open ports 80 and 443 in its security list, and send me its public IP address | the first deploy |
| O10 | **Choose and point a domain** at that address (an `A` record for the domain, `www.`, `api.` and `shop.`) | HTTPS, and the first deploy |
| O8 | **Create the backup storage**: in Oracle, an Object Storage bucket `dwarpal-backups` (Always Free: 20 GB) and a *customer secret key*; choose a restic password and keep it offline too (`infra/deploy/README.md`, step 8) | backups, and Phase 8's restore drill |
| O9 | **GitHub settings for deploys**: a separate deploy SSH key, the `production` environment (ideally with your approval required), and the variables listed in `infra/deploy/README.md`, step 5 | automatic deploys; after the first image build, set each `dwarpal-*` package on GitHub to **Public** (D18) |

**Done overnight** (no decision needed; all checks green):

- **Phase 8** — Dockerfiles, Compose with Caddy, deploy/backup/restore scripts, the manual GHCR deploy workflow, runbooks, and the Helm chart (`6b6a1da`). Waiting only on the server, the domain, O8 and O9 (D17–D19 approved 2 Nov).
- **Phase 9** — the Python SDK (`9ca1bfd`); **passkeys** for console sign-in (§5.9.2), with a software test device and a Chromium end-to-end test; and on 2 Nov, after the owner's answers, the **Age Pass** itself (D21, §5.9.3) and Helm's check of the chart in CI (D19).
- **CI is fully green on GitHub** (`03f3f5b`) for the first time since Phase 6: Lighthouse now starts its browser on GitHub's Linux machines, and the Python job's 30-minute timeouts were one ML test hanging (forked worker processes); it now takes 2 minutes.

**Blocked, and why** (nothing for you to do yet):

- **CGI-render detector** (liveness level 6) — needs examples of computer-rendered faces to train and measure against, and none are licensed for this project. It waits for a dataset decision, which I will bring with options when the rest is done.
- **Kubernetes deployment** — the Helm chart exists; trying it needs a local cluster tool (kind, a further download; Helm itself was approved 2 Nov, D19), and the Always Free server (O2b) is a single machine, where Compose is the better fit. Left optional, as the roadmap says.

## Waiting for you (3 Nov)

| # | Question | Unblocks |
| :-: | :-- | :-- |
| ~~D23~~ | **(approved 4 Nov)** **Downloads for making renders** (D22): Blender 5.2.3 LTS (`blender-5.2.3-windows-x64.zip`, 406 MB, download.blender.org, GPL — its output is ours), the MPFB extension 2.0.18 (43.8 MB, extensions.blender.org, GPL-3.0; assets CC0) and MakeHuman's system assets (`makehuman_system_assets_cc0.zip`, 267 MB, makehumancommunity.org, CC0). Desktop tools on your machine only, never in an image | the made-up people (protocol step 1) |
| O11 | **Send the two requests** in [docs/data/dataset-requests.md](../data/dataset-requests.md) from your own address, after checking each contact on the dataset's page; record the answers there | other people's renders, if allowed |
| O12 | **Have the [consent form](../data/consent-form.md) reviewed** (with O5), fill in your name, contact and the deletion date, then film yourself first | the real side of the render detector's data |
| D1b | `@types/three` 0.186.0 (1.9 MB, npm, MIT) — **not approved** on 2 Nov; the hand-written types stay | — |

## Decided on 4 Nov 2026

| # | Decision |
| :-: | :-- |
| D23 | **Approved and done**: Blender 5.2.3 (`blender-5.2.3-windows-x64.zip`, 405,839,452 bytes, SHA-256 `723f08a4…5dc2fb` — matches download.blender.org's), MPFB 2.0.18 (45,956,992 bytes, SHA-256 `c075b3e9…2a2dad` — matches extensions.blender.org's), MakeHuman system assets (`makehuman_system_assets_cc0.zip`, 280,737,770 bytes, SHA-256 `b542127a…a0107`; no published fingerprint, every file passes the zip's own CRC check). Kept in `.tools/` (ignored by git), a portable Blender with MPFB's online access off. The first 40 made-up people are rendered (`ml/blender/render_people.py`, 34 min) and filed as 120 injected clips. **Next is yours**: film yourself under consent `c-001` (O12) and film the renders on a screen (`renders film`) — then training can start |

## Decided on 3 Nov 2026

| # | Decision |
| :-: | :-- |
| D22 | **Make our own, and ask** ([ADR-0021](../adr/0021-render-detector-data.md)). **Done:** the [protocol](../data/render-detector-protocol.md), the [consent form](../data/consent-form.md) (draft), the [requests to two dataset authors](../data/dataset-requests.md) (drafts), and `ml/src/dwarpal_ml/renders.py`, which files clips and refuses a real person's clip without a standing consent (§5.9.4). Next: D23, O11, O12 |

## Decided on 2 Nov 2026 (afternoon)

| # | Decision |
| :-: | :-- |
| Alerts | **By email**: Alertmanager v0.34.1 (`prom/alertmanager`, Docker Hub, 38 MB arm64, Apache-2.0), with the collector and Prometheus already approved (D11), pulled only on the server and by CI's settings check. **Done**: `infra/deploy/alert_email.py`, the `alerts` profile, README step 10; the owner runs the script once the server exists |
| D2b | **Approved**: `@fontsource-variable/noto-sans-devanagari` 5.3.0 (0.73 MB, npm, OFL-1.1). **Done**: the Hindi pages use it, served by the site |
| SDKs | **Stay unpublished until launch**; installing from the repository is documented in `docs/developers/README.md` |
| Render detector | **Look for a dataset**: done — [render-detector-datasets.md](render-detector-datasets.md); the choice of route is D22 |

## Decided on 2 Nov 2026

The owner answered the overnight decisions in the morning, each with the recommended option.

| # | Decision |
| :-: | :-- |
| D17 | **Approved**: the five base images — `python:3.13.17-slim-bookworm` (44 MB), `node:24.22.1-bookworm-slim` (81 MB), `caddy:2.11.6-alpine` (24 MB), `restic/restic:0.19.1` (17 MB) from Docker Hub, and `ghcr.io/astral-sh/uv:0.13.1` (18 MB) from GitHub (sizes for arm64) — pulled only on GitHub's build machines and the server |
| D18 | **Approved, public**: Dwarpal's images go to GitHub's container registry under the owner's account and are made public, so the server pulls them without a token |
| D19 | **Approved**: Helm **4.3.1** (`helm-v4.3.1-linux-amd64.tar.gz`, 20.4 MB, get.helm.sh, Apache-2.0) on CI's machines only, checked against its SHA-256, to lint and render the chart. Helm 3, first proposed, stops getting security fixes on 11 Nov 2026 |
| D20 | **Kept**: signing in with a passkey needs no one-time code; the device's own check of the person is the second factor |
| D21 | **Build the Age Pass now**, with the suggested defaults: passes last 90 days, are issued 20 at a time, each is used once, and websites opt in through their policy (off by default) |

## Decided on 1 Nov 2026

The owner answered every waiting decision at once, and asked for the decided work to be done before the project moves on.

| # | Decision |
| :-: | :-- |
| D15 | **Approved**: `pillow` 13.0.0, `certifi` 2026.10.19, `filelock` 4.2.1, `setuptools` 84.1.0 (pypi.org, through uv's `override-dependencies`); re-run the ML tests after |
| D14b | **Approved**: `tmp` 0.2.7 (40 KB, registry.npmjs.org) in place of 0.2.6 |
| D1 | **Approved**: `three` **0.186.1** (20.4 MB, npm, MIT); 0.187.0 is still inside the cooldown. The home page's 3D hero, with the still artwork as its fallback |
| D2 | **Approved**: `next-intl` 4.14.9 (0.4 MB, npm, MIT; brings `@swc/core`). English and Hindi; the Hindi is machine-drafted and marked for review by a native speaker |
| D6b | **Docker**: Tesseract from Debian's `tesseract-ocr` in a `debian:bookworm-slim` image (~75 MB), plus `pytesseract` 0.3.13; `eng` model limited to MRZ characters first (D6c) |
| D7b | **Accept SFace, int8** (`face_recognition_sface_2021dec_int8.onnx`, 9.9 MB, OpenCV Zoo, Apache-2.0). Its training data (web-scraped, without consent) is stated in the model card; faces are compared in memory only |
| D8, O7 | **Aadhaar deferred**: finish the MRZ route first; Aadhaar waits for UIDAI's material or OVSE registration |
| O1 | **Repository**: https://github.com/Anubhav104401/Dwarpal — **public**; push now (history checked for secrets first) |
| Licence | **Apache-2.0** for the repository |
| O6 | Placeholder stays; publishing the practice statement stays blocked |
| O5 | The DPIA, practice statement and compliance map are labelled **draft, not legally reviewed** |
| O2 | **Oracle free tier** for Phase 8 when it starts (the owner creates the account and domain) |
| O2b | **Decided 1 Nov: stay on Always Free.** Oracle tenancy in India South (Hyderabad); the server is sized to the Always Free allowance, **2 Ampere cores / 12 GB** (1,500 OCPU-h, 9,000 GB-h a month), from the start, so nothing is disabled when the 30-day trial (16 cores / 96 GB) ends. Consequences: NFR-05 (50 people in a check) was met on 4 cores, so the capacity on 2 must be measured again in Phase 8; Always Free servers idle for 7 days (A1: memory under 20 %) can be reclaimed, which the running stack's memory use keeps clear of |
| D2b | *Optional, not blocking*: a Devanagari typeface for the Hindi pages (e.g. Noto Sans Devanagari, SIL OFL), which Geist lacks; today the visitor's system font is used. Not downloaded; ask when convenient |
| D2c | *Not a download*: a native Hindi speaker to review `apps/web/messages/hi.json`, machine-drafted on 1 Nov |
| D1b | *Optional, not blocking*: `@types/three` (TypeScript types for three.js, npm, 0.186.x) would replace the hand-written `apps/web/types/three.d.ts`. Not downloaded; ask when convenient |

## Decided on 27 Oct 2026

| # | Decision |
| :-: | :-- |
| D12 | **Approved**: Next.js 16.4.0 → 16.4.2 (`next`, `@next/swc-win32-x64-msvc`, `@next/env`) in both apps; done first |
| C1 | **Keep Geist**; the design system builds on it |
| D13 | **Done** (QR code on the Security page). **Approved**: `qrcode` 1.5.4 (+ `pngjs`, `yargs`, `dijkstrajs`) and `@types/qrcode` 1.5.6 |
| D4 | **Done** (axe tests, clean). **Approved**: `@axe-core/playwright` 4.14.0 (+ `axe-core` 4.14.0) |
| D3 | **Done**: WebKit passes; Firefox installed but **can't start on this Windows build** (side-by-side error; runs on CI). **Approved**: Playwright 1.64.0's Firefox and WebKit browsers (~200 MB, Playwright's CDN) |
| D5 | **Done** (Lighthouse ≥ 90; uses Playwright's headless shell). **Approved**: `@lhci/cli` 0.15.1 (+ `lighthouse` 13.5.0 and its dependencies) |
| D1, D2 | Not approved yet (`three` 0.186.1, 20.4 MB; `next-intl` 4.14.9 with `@swc/core`) — marketing hero and Hindi wait |
| D6–D11 | **Approved 27 Oct** ("approved", after the details below were listed), with the recommendations as written: Tesseract's own `eng` model limited to MRZ characters before any OCR-B model (D6c); SFace's training data checked before it is used (D7); UIDAI material from uidai.gov.in only (D8) |
| D7 | **Condition not met — not downloaded.** The SFace paper trains on CASIA-WebFace, VGGFace2 and MS-Celeb-1M ([arXiv 2205.12010](https://arxiv.org/pdf/2205.12010)); OpenCV Zoo's file doesn't say which ([model folder](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md)). All three are web-scraped celebrity photos without consent; MS-Celeb-1M was withdrawn for that. **Needs a decision (D7b)**: accept SFace anyway, look for a face-match model trained on consented data, or drop selfie ↔ document matching from Phase 6 |
| D6 | **Install route needed (D6b)**: Tesseract on this Windows computer means running the UB Mannheim *installer* (an `.exe`, system-wide install), or I can run Tesseract inside a Docker container instead (Debian's `tesseract-ocr` 5.x package in a `debian:bookworm-slim` image, ~75 MB pulled), which is also how the API's production image would get it. I recommend Docker |
| D8 | **Blocked on material**: UIDAI's technical Secure QR specification and current certificate weren't found on uidai.gov.in; the 2021 regulations require OVSE registration (O7). Nothing downloaded |
| D9 | **Done 27–28 Oct**: pip-audit, Trivy, ZAP and Semgrep run and triaged (`docs/reports/phase-7.md`); Semgrep now reports 0 |
| D10, D11 | **Done 27 Oct**: Locust load test (result → **P1**); OpenTelemetry traces with collector, Tempo, Grafana (Prometheus approved, not pulled: no metrics yet) |
| D14 | **Done 27 Oct** for `tmp` 0.2.6, `uuid` 11.1.1, `basic-ftp` 6.2.1, `zod` 4.6.6 (`pnpm-workspace.yaml` overrides; Lighthouse test still passes): `pnpm audit` 8 → 4 findings. `body-parser` 1.20.9 **done 30 Oct** (after its cooldown; Lighthouse test passes; `pnpm audit` → 3). Left: `extract-zip` has no fix; and a **new** advisory (GHSA-7c78-jf6q-g5cm) says `tmp` 0.2.6 is affected too — fixed in **0.2.7** (40 KB, registry.npmjs.org, 27 May 2026): **needs approval** (D14b) |
| O1 | The owner creates an empty private GitHub repository and gives its URL; push only after the owner confirms |
| O6 | Placeholder stays in the practice statement; publishing it stays blocked |

## Downloads (each needs your explicit approval: file, source, size)

| # | What | Unblocks | Notes |
| :-: | :-- | :-- | :-- |
| D1 | `three` (npm) | Phase 5 marketing hero (3D face mesh) | exact version and size to be confirmed when asked |
| D2 | `next-intl` (npm) | Phase 5 English/Hindi | |
| D3 | Playwright Firefox and WebKit browsers (~200 MB) | Phase 5 exit: e2e on three engines | |
| D4 | `@axe-core/playwright` (npm) | Phase 5 exit: "axe clean" | |
| D5 | Lighthouse CI (npm) | Phase 5 exit: Lighthouse ≥ 90 | |
| D6 | **Reading the MRZ from a photo.** (a) Tesseract OCR **5.5.3** (Apache-2.0, released 24 Jul 2026): on Linux from Debian's `tesseract-ocr` package inside the API's Docker image; on Windows the UB Mannheim installer is only at 5.4.0 (`tesseract-ocr-w64-setup-5.4.0.20240606.exe`, 50.2 MB, github.com/UB-Mannheim/tesseract). (b) `pytesseract` 0.3.13 (Apache-2.0, 0.01 MB, PyPI; needs Pillow). (c) An **OCR-B model**: the usual one, `ocrb.traineddata` (11.4 MB, github.com/Shreeshrii/tessdata_ocrb), has **no licence**, so it can't be used. The alternatives are Tesseract's own `eng` model limited to MRZ characters (no extra download), or training our own OCR-B model | Phase 6 MRZ reading from photos (the MRZ *parser* is already built) | **choose (c)**: I recommend trying `eng` first and measuring it on the ICAO specimens |
| D7 | **Face match** (selfie ↔ document photo): OpenCV Zoo's **SFace** (Apache-2.0), `face_recognition_sface_2021dec.onnx` **38.7 MB** (or the int8 version, 9.9 MB), from github.com/opencv/opencv_zoo (`models/face_recognition_sface`, Git LFS); run by OpenCV, already installed | Phase 6 selfie ↔ document match | the files are Apache-2.0, but the **training data** behind them (face datasets like MS-Celeb-1M were withdrawn over consent) must be checked before use; the model never stores faces, only compares two in memory |
| D8 | **Aadhaar Secure QR**: UIDAI's signing certificate for Secure QR and its QR format, **from uidai.gov.in only**. My search didn't find the technical specification on the site, only the [Secure QR reader FAQ](https://uidai.gov.in/en/306-faqs/aadhaar-online-services/secure-qr-code-reader-beta.html), the [data and downloads page](https://uidai.gov.in/en/data-and-download) and the [Authentication and Offline Verification Regulations, 2021](https://old.uidai.gov.in/images/The_Aadhaar_Authentication_and_Offline_Verifications_Regulations_2021-_Clean_copy-30122025.pdf). The certificate listed there expired in 2021: the current one must be found | Phase 6 Aadhaar | the regulations require an **Offline Verification Seeking Entity** to verify UIDAI's digital signature before accepting an Aadhaar QR, so registration may be needed first (O7) |
| D9 | **Security scanners**, development only: `pip-audit` **2.10.1** (Apache-2.0, 0.06 MB + ~20 small deps, PyPI); **Semgrep** 1.182.0 (LGPL-2.1, **59–72 MB** wheel + 27 deps, PyPI; its rule registry is fetched at run time); **Trivy** 0.76.0 (Apache-2.0, Docker image `aquasec/trivy`, **63 MB** compressed; downloads its vulnerability database, ~0.5 GB, on first run); **OWASP ZAP** (Apache-2.0, Docker image `zaproxy/zap-stable:20261016`, **1.2 GB** compressed) | Phase 7 scans | could approve pip-audit alone first: smallest, and it covers the Python dependencies |
| D10 | **Load testing**: **Locust** 2.46.7 (MIT, 1.5 MB, PyPI, released 4 Oct) + 15 deps (Flask, gevent, pyzmq, psutil and others, roughly 30 MB together) | Phase 7 load tests (p95 latency targets) | development only |
| D11 | **Observability**: in the API, `opentelemetry-sdk` **1.45.1**, `opentelemetry-exporter-otlp-proto-http` 1.45.1, `opentelemetry-instrumentation-fastapi` **0.66b1** (a *beta*, as all its versions are) — Apache-2.0, all under 1 MB, PyPI; for local viewing, Docker images `otel/opentelemetry-collector-contrib:0.163.1` (116 MB), `grafana/grafana:13.0.11` (358 MB, AGPL-3.0), `grafana/tempo:2.10.9` (38 MB, AGPL-3.0), `prom/prometheus:v3.13.4` (107 MB, Apache-2.0); sizes compressed, linux/amd64 | Phase 7 observability | the libraries go into the API itself; the images only run locally. Grafana and Tempo are AGPL, which is fine to *run* but matters if modified and offered as a service |
| ~~D12~~ | ~~Upgrade Next.js 16.4.0 → 16.4.2~~ | **done 27 Oct** — both apps on 16.4.2; `pnpm audit`: no known vulnerabilities; all checks and the 7 browser tests pass | |
| D13 | A QR-code library for the web app (e.g. `qrcode`, npm; version and size to be confirmed when asked) | Phase 5: a QR code on the console's *Security* page, so phones can scan the one-time-code secret (today: text and an `otpauth://` link) | |
| **D15** | **Python security fixes** (from pip-audit and Trivy, 27 Oct), forced with uv's `override-dependencies`, from pypi.org: `pillow` **13.0.0** (7.3 MB wheel, 16 Oct; a *major* version, comes in through torchvision — training only), `certifi` 2026.10.19 (0.14 MB), `filelock` 4.2.1 (0.16 MB), `setuptools` 84.1.0 (0.8 MB) — all past the cooldown | clears 47 known flaws (6 critical) | I'd re-run the ML tests after: Pillow 13 may change image decoding |
| D14b | `tmp` **0.2.7** (40 KB, registry.npmjs.org, 27 May 2026) replacing the approved 0.2.6, which a new advisory (GHSA-7c78-jf6q-g5cm) also covers | the last fixable `tmp` finding | development only |
| D14 | Patched versions of Lighthouse CI's dependencies, forced with `pnpm.overrides`, from registry.npmjs.org: `tmp` 0.2.6 (40 KB), `uuid` 11.1.1 (134 KB), `basic-ftp` 6.2.1 (155 KB), `zod` 4.6.6 (6.1 MB); and `body-parser` 1.20.9 (62 KB), released 22 Oct, so only after 29 Oct (cooldown). `extract-zip` has **no** fixed version | clears 7 of `pnpm audit`'s 8 findings (1 low, 1 moderate, 6 high), all in development-only tools run against local servers; nothing ships in the apps | overriding may break Lighthouse CI: re-run its test after |

## Design choices

| # | Question | Unblocks |
| :-: | :-- | :-- |
| ~~P1~~ | **Decided 28 Oct: (a), then (b) if needed.** Done: the age model sees the 3 sharpest frames (safety lines re-checked, unchanged within chance); dynamic INT8 tried — slower, not adopted; a 1 s queue for workers. Result: server processing p95 1.21 s for 50 people at a realistic pace | |
| ~~P2~~ | **Decided 29 Oct: 50 people in a check** — each sending an attempt every ~20 s; 4 cores kept. Met on the laptop (analysis p95 1.21 s, throttled); to be measured again on the Phase 8 server. Design documents reworded (NFR-05, §10/§13 of the implementation design, architecture quality table) | |
| C1 | The console/marketing **typeface** (the design says: chosen from a type specimen). The web app already uses **Geist** (installed in Phase 1): keep it, or choose another? | Phase 5 design system |
| ~~D16~~ | **Decided 30 Oct: (a)**, framing per session by the return address's origin, COOP kept — **done** (§5.5.7 of the book; `@dwarpal/js`, `@dwarpal/react`, the shop uses the modal). Was: **How the browser SDK opens the check** (`@dwarpal/js`, `@dwarpal/react`, roadmap Phase 5). The design's first choice is a **modal with an iframe**, then a **popup**, then a full **redirect** (§4.1 of the implementation design). Our own security headers forbid the first two today: `frame-ancestors 'none'` stops any site framing the verify page, and `Cross-Origin-Opener-Policy: same-origin` cuts a popup off from the page that opened it. Options: (a) allow framing *per session*, only by the origin of the session's `return_url` (which the website registered with its secret key), and keep COOP for everything else — I recommend this; (b) also relax COOP on `/v/*` to allow the popup fallback; (c) redirect only for now — the SDK still saves websites the plumbing, and the shop already works this way | the JS and React SDKs; their tests |

## Things only you can do

| # | What | Unblocks |
| :-: | :-- | :-- |
| O1 | Push to GitHub and let remote CI run (nothing has been pushed since Phase 3) | CI evidence for every phase report |
| O2 | Choose a VM provider and create the account; choose a domain and add DNS records | Phase 8 deployment |
| O3 | Your own Aadhaar QR for testing (never anyone else's) | Phase 6 Aadhaar end-to-end |
| O4 | More people for genuine liveness and age attempts (ages, skin tones, glasses) | Phase 3 exit criterion; fairness of the anti-spoofing model |
| O5 | Legal review of the DPIA and practice statement (drafts in `docs/privacy/`) for your launch markets | production launch |
| O6 | The operator's name and contact details for data-protection requests (practice statement §8) | publishing the practice statement |
| O7 | Register Dwarpal with UIDAI as an **Offline Verification Seeking Entity** ([OVSE registration](https://uidai.gov.in/en/ovse)), if the Aadhaar route goes ahead; check what the 2021 regulations require of it | Phase 6 Aadhaar in production (testing with your own QR is unaffected) |

## Morning summary — night of 28–29 Oct

**Waiting for you** (each row above has the details):
- **D15** — Python security fixes (`pillow` 13.0.0 and three small ones): approve the downloads?
- **D14b** — `tmp` 0.2.7 (40 KB) in place of the approved 0.2.6, which a newer advisory also covers. `body-parser` 1.20.9 (already approved) can go in from 11:38 UTC today.
- **D7b** — SFace's training data failed your condition; not downloaded. Accept anyway, look for a consented model, or drop selfie ↔ document matching?
- **D6b** — Tesseract via Docker (recommended) or the Windows installer?
- **D8 / O7** — Aadhaar is blocked on UIDAI material, and probably on OVSE registration.
- **O1** — the GitHub repository's URL, so CI (and Firefox) can run.

**Done tonight** (all committed; every check, the browser tests and the book at 100 %):
- `22d2b2f` P2 recorded: NFR-05 means 50 people in a check, on 4 cores; the design documents now say so.
- `dd14d78` Webhook endpoints can be switched off and on (API, console, tests).
- `e081571` Sessions can be searched by outcome and by the website's reference.
- `8587058` A browser test of the member controls.
- `7a61996` Recovery codes (10, single-use, stored as HMACs) and switching one-time codes off (password + code).
- `c25ac7f` The web app's script policy uses a per-page nonce — ZAP's remaining warning fixed.
- `8cad67a` Valkey, PostgreSQL and inference stopped during a load test: nothing passed, all recovered; one 500 found and fixed.
- `ce9a191` Metrics, a Grafana dashboard and burn-rate alerts (Prometheus, approved under D11): request totals labelled by route pattern only; alerts on the 99.9 % promise and on NFR-05. Checked end to end on this laptop. Alerts aren't delivered anywhere yet — that needs Alertmanager and a destination, in Phase 8.
- `c64dbe0` The console's 30-day counts as a daily stacked chart (colours checked for colour-blind readers, numbers on hover or keyboard focus, and as a table).
- `d0bb90d` The age model's page in the console: which model decides, whether it may decide live checks, what it learnt from, and its lines with their measured worst cases — and nothing of its build.
- `946565f` The console's sidebar and ⌘K/Ctrl+K command palette, as the design asks. Lighthouse and axe still pass.
- Added later (29 Oct, after you said to leave deployment for now): the dashboard's face-check figures — median time to a decision, share rejected as a likely attack, share sent to a stronger check — from new daily counts by band of time (migration 0009; no exact times kept).
- Not done, because each needs something from you or doesn't exist yet: step-up conversion (needs the Phase 6 verifiers), the policy editor's projected step-up rate, and fairness charts on the model page (no fairness results are published yet).

## Done overnight (no decision needed)

Kept up to date as work lands; see the commit log for details.

- `95f3e91` — **Phase 4 complete**: console accounts, Argon2id, TOTP, CSRF, roles; published OpenAPI document; Schemathesis contract tests (which found and fixed a missing `Allow` header).
- **Phase 6 begun**: the MRZ (passport/ID) parser and age rule, proved against ICAO's specimens and generated documents (`docs/reports/phase-6.md`).
- **Phase 7 begun**: `503` with `Retry-After` when the database or Valkey is down; inference failures never pass; security headers on every API answer (`docs/reports/phase-7.md`).
- **Phase 5 begun**: the console's first pages — sign-in/sign-up, organisations, members, keys (shown once), audit log with chain badge — tested in Chromium (`docs/reports/phase-5.md`).
- `478bddb`, `653d67f` and the next commit — **console pages**: a project's sessions with decision traces, counts and policies; webhooks (secret once, test, deliveries, replay); one-time-code set-up; members' roles and removal, with an owner always kept.
- **Phase 7 documents**: threat model (`docs/security/threat-model.md`), DPIA and practice statement drafts (`docs/privacy/`).
