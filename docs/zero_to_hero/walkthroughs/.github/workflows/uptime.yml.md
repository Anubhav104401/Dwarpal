---
fingerprint: 9e1d7999ac31c2c1
---
**Watching from outside** (decision D33, Phase 8, §5.8.5): a scheduled GitHub workflow that checks the live server every 15 minutes, so a whole server going down still reaches the owner's inbox.

@@ 1
The workflow's name, as GitHub's *Actions* tab shows it.

@@ 3-6
What it does (decision D33): every 15 minutes, ask the live API whether it is ready, load the home page, and check both certificates. A failed check fails the run, and GitHub emails the owner about failed runs — the one alert that still comes when the whole server is down. Before the server exists, runs are skipped.

@@ 7-8
**When** it runs: on a **schedule**…

@@ 9-10
…written in *cron*'s notation — minute, hour, day of the month, month, day of the week, with `*` meaning every: minutes 7, 22, 37 and 52 of every hour. Not 0, 15, 30, 45: GitHub's schedules are busiest, and most often late, at the start of an hour.

@@ 11
…and by hand (`workflow_dispatch`, the *Run workflow* button), to try it at once.

@@ 13-14
**`permissions: {}`** — the run's GitHub token may do nothing at all: it reads no code and writes nothing, so there is nothing for it to misuse.

@@ 16-19
One run at a time: if a check is still running when the next starts, the old one is cancelled — only the newest answer matters.

@@ 21-23
Every step's commands run in **bash**, which GitHub then starts with `-e` and `-o pipefail`: any failed command, even inside a pipe, fails the step.

@@ 25-27
**The `check` job**, with a name that says what it checks.

@@ 28
Run only when the repository's variable `DWARPAL_PUBLIC_API_URL` is set (README, step 5): until the server exists, the job is *skipped* — which isn't a failure, so no email.

@@ 32-35
**Step 1 — the addresses**, with an `id` (`where`) so later steps can ask whether it worked. The variable is handed to it as `API_URL`.

@@ 36-37
The API's address without a trailing `/` (`%/` removes one from the end, if there is one).

@@ 38-42
The home page is the same address without `api.`: `${api#https://api.}` removes that from the front. An address that doesn't start with `https://api.` is a mistake in the setting: say so (`::error::` makes GitHub show it as an error on the run's page) and stop.

@@ 43
Write `API=…` and `WEB=…` into the file named by **`$GITHUB_ENV`**: every later step gets them as variables.

@@ 44-48
**Step 2 — the API is ready.** `curl` asks for `/readyz`; `--fail` turns an error answer (such as 503 when the database is down) into a failure; `--silent --show-error` prints only errors; each try waits 20 seconds at most; and `--retry 2 --retry-delay 15 --retry-all-errors` tries twice more, 15 seconds apart, so one lost answer doesn't wake anyone.

@@ 49-54
**Step 3 — the home page loads**, asked the same way, its page thrown away (`--output /dev/null`). It runs even if step 2 failed (`!cancelled()`), so a failed run shows which checks failed — but only if step 1 worked, since without it there are no addresses.

@@ 55-57
**Step 4 — the certificates last another week**, under the same condition.

@@ 58
For each of the two names (the address without `https://`)…

@@ 59-60
…connect as a browser would (`openssl s_client`, naming the site with `-servername` so the server picks the right certificate) and keep just the certificate (`openssl x509`). If that fails, say so and stop.

@@ 61
Print when it ends, for the run's log.

@@ 62-66
`-checkend 604800` (7 days, in seconds) fails if the certificate ends within a week. Caddy renews at a third of a certificate's life — a month before, for Let's Encrypt's 90-day ones — so this means renewal has been failing for weeks: say so, and fail the run.

@@ 67
End of the loop.

@@ 29-31
On one of GitHub's Ubuntu machines, for 5 minutes at most; then its steps, in order.
