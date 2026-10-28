---
fingerprint: 7432b0d63d44f667
---
**The load test** (Phase 7, decision D10): simulated people taking the age check at the same time, written for **Locust**. Each "user" is a Python object that runs the same steps over and over; Locust times every request and adds them up. The result is in §5.7.2 — and it fell far short of the target.

@@ 1-8
What it tests, the target it tests against (NFR-05: 50 people at once, each attempt answered within 1.5 s at the 95th percentile, on 4 cores), what each simulated person does, and how to run it.

@@ 10
Newer type-hint syntax on older Pythons.

@@ 12-15
Standard tools: JSON, environment variables, random IDs, file paths.

@@ 17-19
`requests`, a simple HTTP client (Locust's own dependency); and from Locust, the base class for a simulated person, the pause between their steps, test events, a task marker, and the type of a test run.

@@ 21
The website's test API key, from the environment — never written in the file.

@@ 22-24
The picture every frame carries: the astronaut portrait the API's own tests use, read once at start-up. With the same picture 8 times, the decision will likely say "try again" — but every step of the work is done, which is what is timed.

@@ 25
Frames per attempt, as the verify page sends.

@@ 26-28
**`POLICY`** — 18+ at a risk budget of 0.075. The ready-made policies ask for 0.02, which the current age model can't yet promise (Phase 2), so the API refuses to run them with it.

@@ 29-31
**`PAUSE`** — how long each person waits between checks, from `DWARPAL_LOAD_PAUSE_S` as "low-high". The default, 1 to 3 seconds, is a stress test: a real person spends 20 seconds or more on the verify page before sending an attempt, so `15-25` is closer to life (§5.7.4).

@@ 34-40
**`add_the_policy`** — once, before any simulated person starts (`events.test_start`), add the test's policy through the API, as a website would. Each run adds a new version; sessions name the policy without its version, so they get the newest.

@@ 43-46
**`Person`** — one simulated person, who takes the check again and again, pausing a random time within `PAUSE` between checks.

@@ 48-53
**The check** (`@task`). First, as the shop's server: create a session for the policy. `name=` is how Locust groups the timings in its report.

@@ 54-56
The session's ID, and a fresh random device ID for this visit: the per-device budget isn't what's being tested.

@@ 57-63
As the verify page: start the flow with the session's client secret, and keep the flow token it returns, together with the device ID, for the next requests.

@@ 64
Ask for a liveness challenge.

@@ 65-66
Label the frames as the page would: baseline frames first, then one for each pose the challenge asked for.

@@ 67-68
The 8 frames as file uploads, and the form fields: the labels and the challenge's ID.

@@ 69-78
**The face attempt.** `catch_response=True` lets the test decide whether this counts as a success, rather than Locust judging by the status code alone…

@@ 79-80
…because when the inference service is full, the API still answers at once — safely, with `analysis_unavailable`, which can never pass — and a fast refusal must not look like a fast analysis. That is exactly what the first run got wrong (§5.7.2).
