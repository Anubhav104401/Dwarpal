---
fingerprint: 844e7838546d6460
---
The **continuous-integration workflow** (§4.6). GitHub reads every file in `.github/workflows/`. Whenever this repository receives new code, GitHub starts fresh Linux machines and runs these three jobs on them. If any step fails, the change is marked with a red ✗.

@@ 1
`name: ci` — the workflow's name, shown on GitHub's *Actions* page and next to each commit.

@@ 3
`on:` — **when** the workflow runs.

@@ 4-5
`push:` to the `main` branch — every time new commits land on the main line of history.

@@ 6
`pull_request:` — every time someone proposes a change through a pull request. Problems are therefore found **before** the change is merged, not after.

@@ 8-9
`permissions: contents: read` — the workflow may only **read** the repository. By default GitHub gives workflows more powers, such as writing to the repository. Following the principle of **least privilege**, nothing gets a power it doesn't need. Then even a compromised tool inside the workflow couldn't modify the code.

@@ 11-13
`concurrency:` — if a new commit arrives while an earlier run for the **same branch** is still going (`group: ci-${{ github.ref }}`, where `github.ref` is the branch name), cancel the old run (`cancel-in-progress: true`). Only the newest code matters, so this saves time.

@@ 15
`jobs:` — the work, divided into **jobs** that run at the same time on separate machines.

@@ 16
`python:` — the first job's internal name.

@@ 17
`name:` — the human-readable title shown on GitHub.

@@ 18
`runs-on: ubuntu-24.04` — a fresh virtual machine running Ubuntu Linux 24.04 LTS. It is pinned, rather than "latest", so an Ubuntu upgrade can't suddenly change our results.

@@ 19
`timeout-minutes: 45` — if something hangs, stop after 45 minutes instead of GitHub's default of six hours. (It was 15 until the first run on GitHub, then 30; GitHub's machines have no graphics card, and the whole suite outgrew 30 minutes there — see below.)

@@ 20
`steps:` — the job's steps, run in order.

@@ 21
`uses: actions/checkout@3d3c…90b1 # v7.0.1` — a published **action** that downloads this repository's code onto the machine. Every job starts from an empty machine, so this always comes first.

The action is pinned to an exact **commit** (the long hexadecimal ID), with its version in a comment. A version *tag* such as `v7.0.1` is a label its owner can move to other code — and a stolen account could move it to malicious code. A commit ID names one exact piece of code forever. Semgrep flagged the tags in Phase 7; every action here is now pinned this way.

@@ 22-25
`astral-sh/setup-uv@1c37…5884 # v10.3.0` — installs **uv** (pinned by commit, as above):

- `version: "0.13.1"` — the same uv version as on the developer's machine;
- `enable-cache: true` — keep downloaded packages between runs, which makes later runs much faster.

@@ 26
`run: uv sync --locked` — install Python 3.13 and every locked package. `--locked` means: **fail** if `uv.lock` doesn't exactly match the `pyproject.toml` files. Someone who changed a dependency but forgot to update the lockfile is told immediately.

@@ 27
`run: uv run infra/scripts/fetch_models.py` — download the third-party model files the tests need (the YuNet face detector, §5.1) and **verify each one's SHA-256 fingerprint** before using it. Model files are never stored in Git (`.gitignore`), so every fresh machine — including CI's — fetches them this way. Added in Phase 1.

@@ 64
`javascript:` — the second job, running at the same time on its own machine.

@@ 65-67
Its title, the same pinned Ubuntu machine, and the same 15-minute limit. Since Phase 1 the job also *builds* everything, hence "builds" in its name.

@@ 68
`steps:` — this job's steps.

@@ 69
Download the code, as in the first job.

@@ 70
`pnpm/action-setup` (pinned by commit) — installs **pnpm**. No version is given here, because the action reads the `packageManager` field of `package.json` (pnpm 12.11.2), so the version lives in one place only.

@@ 71-74
`actions/setup-node` (pinned by commit) — installs **Node.js 24** (the LTS line in `package.json`). `cache: pnpm` keeps pnpm's package store between runs.

@@ 75
`run: pnpm install --frozen-lockfile` — install exactly what `pnpm-lock.yaml` says, and **fail** if the lockfile is out of date. This is the JavaScript twin of `uv sync --locked`.

@@ 76
`run: pnpm lint` — Biome's formatting and lint checks.

@@ 77
`run: pnpm typecheck` — TypeScript checks for every package: the SDK, both web apps and the end-to-end tests (added in Phase 1).

@@ 78
`run: pnpm test` — JavaScript unit tests for every package (Vitest, §4.20).

@@ 79
`run: pnpm build` — build every package with Turborepo: the SDK compiles to plain JavaScript, and both Next.js apps make their production builds. A build that only fails on a clean machine is caught here, not on deployment day.

@@ 81-84
**The end-to-end job** (added in Phase 1): the whole system, in a real browser, exactly as a person would use it — the demo shop, the verify page, the API and the inference service, with a fake camera. It gets 20 minutes, because it installs a browser and builds everything first.

@@ 85-86
Its steps start, like every job, by checking out the code.

@@ 87-90
Install uv, as in the Python job: the API and the inference service are Python programs.

@@ 91-95
Install pnpm and Node.js 24, as in the JavaScript job: the web apps and the test runner are JavaScript programs.

@@ 96
`uv sync --locked` — install the Python side exactly as the lockfile says.

@@ 97
Download the face-detection model, which the inference service needs (§5.1.1).

@@ 98
Install the JavaScript side exactly as its lockfile says.

@@ 99
Download the three browsers Playwright drives — Chromium, Firefox and WebKit (§4.20, §5.5.5). The first run on GitHub (1 Nov) downloaded only Chromium, and every Firefox and WebKit test failed for want of a browser. `--with-deps` also installs the system libraries a browser needs on a bare Linux machine, such as fonts.

@@ 100
`pnpm e2e` — run the end-to-end test. Its configuration starts the databases with Docker Compose, prepares a demo project, and launches all four services itself (`e2e/playwright.config.ts`).

@@ 101-106
Only **if a step failed** (`if: failure()`), upload the test's results — screenshots and Playwright's step-by-step **trace** — as an **artifact**: a file bundle attached to the CI run, kept for 7 days. A failure on a machine nobody can log into is then still easy to investigate.

@@ 108
`infrastructure:` — the third job: proving the development databases start correctly on a completely clean machine.

@@ 109-111
Its title, machine and a 10-minute limit.

@@ 112
`steps:` — this job's steps.

@@ 113
Download the code.

@@ 114
Start PostgreSQL and Valkey and **wait until both report healthy**. If either image can't be downloaded, or either health check never passes, this step fails. GitHub's Ubuntu machines come with Docker already installed.

@@ 115
Stop the containers and delete their data volumes, leaving the machine clean. GitHub discards the machine anyway, but cleaning up after yourself is a good habit.

@@ 28
Install Tesseract (§5.6.2) from Ubuntu's packages: the document tests read specimen passports with it. (On this project's Windows computers it runs in a container instead.)

@@ 29-30
Lint and types: the first two parts of `uv run tasks.py check`, the command developers run locally (§5.0.3), as separate steps.

@@ 31-39
The tests, one step per test run, each with its own time limit, so GitHub records how long each took. They are the same two runs as `tasks.py test`, with two additions: `-v` prints each test's name as it starts, and `--durations=15` lists the fifteen slowest at the end. `tee` shows the output and also saves it to a file; `shell: bash` makes the step fail if pytest fails, even though its output goes through `tee`.

@@ 40-50
The book in strict mode — the last part of `tasks.py check`. Since 12 Nov the step has a name and keeps what it prints in `book.log` (`tee` copies it to the file and the screen; `shell: bash` makes the step fail if the book does, although `tee` itself succeeds). If it fails, the next step posts the book's `problem:` and `incomplete:` lines as an **error annotation**, readable without a sign-in — the same trick as for the test timings below.

@@ 51-56
**Test timings, as annotations.** GitHub shows a run's full log only to people signed in; *annotations* — short messages attached to a run — anyone can read, including through GitHub's public API. `if: always()` runs this step even after a failure or a step that ran out of time.

@@ 57-62
For each saved log: the slowest-tests section (from the line naming it to the next line of `=`), and the last three test names reached — if a step ran out of time, the last one is the test that was running. Each becomes one `::notice` line, which GitHub turns into an annotation (`|` stands in for line breaks, which an annotation's one line can't hold).

@@ 140-143
**`helm`** — a fifth job (decision D19): check the Kubernetes chart (§5.8.3). Ten minutes is far more than it needs.

@@ 144-146
Which Helm to use, and its **SHA-256 fingerprint**, written here rather than fetched: if anything — the download site, the network — handed over a different file, its fingerprint wouldn't match and the job would stop before running it.

@@ 147-148
Its steps, starting, as every job does, with this repository's code.

@@ 149-153
Download Helm 4.3.1 from Helm's own site (`--fail` makes an HTTP error stop the step), check its fingerprint (`sha256sum --check --strict` fails on any mismatch), and unpack only the `helm` program. Helm 4 rather than 3: Helm 3 stops getting security fixes on 11 November 2026.

@@ 154-159
**`helm lint --strict`** checks the chart for mistakes, failing on warnings too; **`helm template`** renders every template with the default settings, which fails if any template can't be filled in. The count of rendered objects goes into the log as a sign that everything rendered. As in the test steps, `shell: bash` makes a failure inside a `tee` pipeline count.

@@ 160-163
Whatever happened, the end of Helm's output becomes an annotation — readable by anyone, unlike the job's log. `|| true` keeps this step from failing when there is no log (if the download itself failed).

@@ 116-117
The server's alert settings (§5.8.4), checked by each program's own checker — none of them runs on a laptop's Compose start-up, so a mistake would otherwise show only on the server.

@@ 118-128
First, Alertmanager's settings exactly as `alert_email.py` writes them, for made-up addresses, and a made-up password's file — the script's function is loaded from its file and called.

@@ 129-132
**`promtool check config`**: Prometheus's settings and the shared rules, read by Prometheus's own checker.

@@ 133-134
**`validate`**: the collector's own check of its settings, including that every exporter named exists.

@@ 135-138
**`amtool check-config`**: Alertmanager's own check, with the password's file where the settings say it is.

@@ 165-168
**The `images` job** (9 Nov): the four production images, built exactly as the deploy workflow builds them — on GitHub's own **Arm** machines, from the base images approved for them (D17) — but never published. A broken Dockerfile then shows up on any push, not on the day of a deploy.

@@ 169-170
On an Arm machine (`ubuntu-24.04-arm`), for 45 minutes at most.

@@ 171-178
A **matrix**, as in the deploy workflow: the job runs four times side by side, one per image, each with its Dockerfile and build argument. `fail-fast: false` lets the other three finish when one fails, so one push shows every broken image at once.

@@ 179-183
Its steps: fetch the code, and set up uv at the project's version.

@@ 184-187
For the web app and the inference service, fetch the third-party models, exactly as the deploy workflow does — with httpx given at the lockfile's version (`--with`), which this job's first run showed was missing. The web app's build copies the face landmarker for browsers; the inference service is started below with all the serving models mounted, as on the server.

@@ 188
A failed build or start leaves its last lines as an annotation, as the comment says: anyone can read annotations, while a job's log needs a GitHub sign-in.

@@ 189-193
**Build** the image: the API's public address the web app's code is built with (a made-up one, since the image is never used), and the image's own build argument if it has one…

@@ 194-195
…named locally — `dwarpal-api:ci`, say — with everything Docker prints kept in `build.log`. If the build fails, its last 40 lines are printed and its last 3,000 characters become an error annotation (line ends turned into `|`, as an annotation is one line).

@@ 196-199
Then **start** each one, as far as it can be started without the others, as the comment says. The anti-spoofing networks are made from PyTorch weights on the owner's computer (`dwarpal_ml.antispoof`), so here they are missing — which is what the inference check reports, not what it requires.

@@ 200-203
The step runs in bash, with the image's local name.

@@ 204-205
Everything inside the braces writes to `start.log`; first, the choice of what to do for each image.

@@ 206
The API's command line loads all of the API's code (`--help` prints the commands and stops): the image's Python and its packages fit together.

@@ 207-214
The inference service runs as on the server: read-only (`--read-only`), with an in-memory `/tmp` (`--tmpfs`) and the fetched models mounted read-only. Its readiness answer (`/readyz`), asked until it comes, is shown as a notice — anyone can read it — and must say the service and Tesseract are **ready** (`[[ … == *text* ]]` asks whether the answer contains each); otherwise its last log lines are shown and the branch fails. Its first run here found the server would start without anti-spoofing: README step 4 now names the files.

@@ 215-219
The web app really runs: started in the background (`--detach`), then asked for a verify page until it answers (`--retry-connrefused`: also while it is still starting). If it never does, its last log lines are shown and the branch fails (`false`). Its proxy can't reach an API here, so the page simply allows no frame — the same safe answer as on a server whose API is down.

@@ 220
The demo shop's image holds Next.js and a finished build (`BUILD_ID`, which `next build` writes last).

@@ 221
End of the choice.

@@ 222-223
If anything in the braces failed, `start.log` is printed and its end becomes an annotation. Each branch joins its commands with `&&` on purpose: before `||`, bash doesn't stop at a failed command inside braces, so a later success would otherwise hide an earlier failure.

@@ 224-225
On success the log isn't printed, so a notice written inside the braces — the inference service's readiness answer — would never reach GitHub, which reads workflow commands only from the step's own output: pass those lines on (`|| true`: having none is fine).

@@ 226-228
**The rehearsal** (9 Nov): the API's image rehearses the server's first deploy, as far as one image can — with the real secrets generator, Compose file, migrations, backup script and restore drill. No test had ever run the API as the server does: in production mode, logged in as the restricted `dwarpal_api`.

@@ 229-232
Only in the API's run of the matrix, in bash, in `infra/deploy` — where the server's files sit side by side, as in `/opt/dwarpal`.

@@ 233-234
Everything the step prints also goes into `rehearsal.log` (`exec > >(tee …)` sends the script's own output through `tee` from here on), so a failure can be shown as an annotation by the next step.

@@ 235-237
Secrets made by the real generator, for a made-up domain; the image tag `ci`; and the image just built, given the name the Compose file asks for (`ghcr.io/<owner>/dwarpal-api:<tag>`), so nothing is pulled.

@@ 238-239
The one model file the API reads at start-up: the age model's manifest, copied where the server keeps it.

@@ 240
The services' password, which the next commands need, read from `.env` as `deploy.sh` reads it.

@@ 241-243
As `deploy.sh` does: the databases from the production Compose file, then the real migrations through the `operator` service, as the tables' owner.

@@ 244-249
The services' own login, `dwarpal_api` — a member of the restricted role and nothing else — made exactly as `deploy.sh` makes it.

@@ 250-251
The API alone (`--no-deps`: its inference service isn't needed to be ready), in production mode, logged in as `dwarpal_api`: it must load its signing keys and pass its health check within 3 minutes.

@@ 252-254
Its readiness answer, kept in a variable first (so a failure stops the script), then shown as a notice.

@@ 263-266
restic's settings for the rehearsal: a repository inside its cache volume (`/cache`, which `backup.sh` mounts), instead of Object Storage, and a random password; then the real `backup.sh` — the database dump and the secrets file, encrypted.

@@ 267-268
The real restore drill: the latest backup restored into a throwaway database, its report shown as a notice — the record Phase 8's exit asks for, rehearsed on every push.

@@ 300-304
If the rehearsal failed, its last 3,000 characters become an error annotation, readable without a sign-in.

@@ 275-279
**Alerts by email, rehearsed** (9 Nov): switched on as README step 10 does — the alert rules copied beside the Compose file, as the deploy workflow copies them, and `alert_email.py` run with a made-up mail password typed twice (it reads it from the input, as there is no terminal here). It writes Alertmanager's settings and the password's file, and turns the `alerts` services on in `.env`.

@@ 280-281
The collector, Prometheus and Alertmanager started with those files; then the API again, which now sends its counts to the collector (`.env` gained its address, so Compose recreates it).

@@ 282-284
**`ask`** — a question to Prometheus's API, from inside its own container (its image has `wget`).

@@ 285-287
Up to 24 times: one request the API counts (health checks aren't counted) — the discovery document — then…

@@ 288-292
…ask Prometheus for the sum of the API's request counts — `http_server_duration_milliseconds_count`, the metric every availability rule reads — and for the availability rule's share. Both answered with a result: stop; otherwise wait 10 seconds (the API sends every 15, Prometheus collects every 15).

@@ 293-294
No counts, or no share: say which, show the answer, and fail — the rules would never fire on the server.

@@ 295-298
The rule group is loaded, and Prometheus knows the Alertmanager to hand firing alerts to.

@@ 299
All of it as a notice. Only the mail itself is left untested: there is no mail server here.

@@ 255-257
**The jobs that work across every organisation** (9 Nov): demo data made through `operator` (its output, which holds a test key, thrown away)…

@@ 258-259
…then the maintenance service's own settings check every organisation's audit chain: the report must not start *0 organisations* — what the services' restricted login would see.

@@ 260-262
The maintenance job and the webhook worker each run once with their own settings, and the audit report is shown as a notice.

@@ 269-272
**The secrets file, restored** (9 Nov), with the runbook's own command for a lost server (section 4): the latest snapshot tagged `secrets`, restored into a folder mounted from outside the container — restored inside it alone, it would vanish with the container. Here restic's cache volume is mounted too, as this rehearsal keeps its repository there.

@@ 273-274
The restored `.env` must be byte for byte the one backed up (`cmp`, as root: restic restores the file's owner); then a notice says so.
