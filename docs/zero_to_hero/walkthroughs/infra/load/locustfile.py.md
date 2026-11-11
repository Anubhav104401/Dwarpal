---
fingerprint: aa04d1c58a0d58f3
---
**The load test** (Phase 7, decision D10): simulated people taking the age check at the same time, written for **Locust**. Each "user" is a Python object that runs the same steps over and over; Locust times every request and adds them up. The result is in §5.7.2 — and it fell far short of the target.

@@ 1-10
What it tests; the target it tests against — NFR-05 as the owner settled it in decision P2: 50 people in a check at once, each sending an attempt every 20 seconds or so, answered within 1.5 s at the 95th percentile on 4 cores; what each simulated person does; and how to run it, at the target's pace.

@@ 12
Newer type-hint syntax on older Pythons.

@@ 14-17
Standard tools: JSON, environment variables, random IDs, file paths.

@@ 19-21
`requests`, a simple HTTP client (Locust's own dependency); and from Locust, the base class for a simulated person, the pause between their steps, test events, a task marker, and the type of a test run.

@@ 23
The website's test API key, from the environment — never written in the file.

@@ 24-26
The picture every frame carries: the astronaut portrait the API's own tests use, read once at start-up. With the same picture 8 times, the decision will likely say "try again" — but every step of the work is done, which is what is timed.

@@ 27
Frames per attempt, as the verify page sends.

@@ 28-30
**`POLICY`** — 18+ at a risk budget of 0.075. The ready-made policies ask for 0.02, which the current age model can't yet promise (Phase 2), so the API refuses to run them with it.

@@ 31-33
**`EXISTING_POLICY`** — or, when `DWARPAL_LOAD_POLICY` names one, a policy that already exists, such as the preset `eu_dsa_18`. Added on 11 Nov 2026 for the first run against the live server: it has only the stand-in age model (§6.13; live checks are decided by an ID document, D24), whose thresholds exist for the presets' budget of 0.02 alone, so it refused `loadtest_18` — every one of the first run's 758 sessions came back `422 unknown_policy`.

@@ 34-36
**`PAUSE`** — how long each person waits between checks, from `DWARPAL_LOAD_PAUSE_S` as "low-high". The default, 1 to 3 seconds, is a stress test: a real person spends 20 seconds or more on the verify page before sending an attempt, so `15-25` is closer to life (§5.7.4).

@@ 39-47
**`add_the_policy`** — once, before any simulated person starts (`events.test_start`), add the test's policy through the API, as a website would. Each run adds a new version; sessions name the policy without its version, so they get the newest. With an existing policy chosen there is nothing to add, so it returns at once.

@@ 50-53
**`Person`** — one simulated person, who takes the check again and again, pausing a random time within `PAUSE` between checks.

@@ 55-63
**The check** (`@task`). First, as the shop's server: create a session for the policy — the existing one if chosen, otherwise the test's own. `name=` is how Locust groups the timings in its report.

@@ 64-66
The session's ID, and a fresh random device ID for this visit: the per-device budget isn't what's being tested.

@@ 67-73
As the verify page: start the flow with the session's client secret, and keep the flow token it returns, together with the device ID, for the next requests.

@@ 74
Ask for a liveness challenge.

@@ 75-76
Label the frames as the page would: baseline frames first, then one for each pose the challenge asked for.

@@ 77-78
The 8 frames as file uploads, and the form fields: the labels and the challenge's ID.

@@ 79-88
**The face attempt.** `catch_response=True` lets the test decide whether this counts as a success, rather than Locust judging by the status code alone…

@@ 89-90
…because when the inference service is full, the API still answers at once — safely, with `analysis_unavailable`, which can never pass — and a fast refusal must not look like a fast analysis. That is exactly what the first run got wrong (§5.7.2).
