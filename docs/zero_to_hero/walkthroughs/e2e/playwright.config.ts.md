---
fingerprint: a9753c8124636377
---
The **Playwright configuration** — everything the end-to-end test needs before its first click: the databases, the tables, a demo project with a fresh key, a fake camera, a browser that uses that camera, and all four services running. With it, one command — `pnpm e2e` — tests the entire system from scratch, the same way on a laptop and in CI.

```
pnpm e2e
  └─ Turborepo builds the SDK, the verify page and the shop
      └─ Playwright loads this file
          ├─ prepare(): databases up · migrate · seed a project and key · make the fake camera video
          ├─ start: inference (8001) · API (8000) · verify page (3000) · shop (3100)
          └─ run the tests in Chromium, with the fake camera
```

@@ 1-4
From Node.js:

- `execFileSync` — run another program and wait for it to finish;
- `randomBytes` — secure random bytes;
- `existsSync` — does a file exist?
- `fileURLToPath` — turn a `file://` address into an ordinary path.

@@ 6
From Playwright: `defineConfig` (which type-checks the configuration) and `devices` (ready-made browser settings).

@@ 8
`ROOT` — the repository's top folder. `import.meta.url` is this file's own address; `new URL("..", …)` goes one folder up.

@@ 9
`FAKE_CAMERA` — where the fake camera's video lives: `e2e/.cache/fake-camera.y4m`.

@@ 11
`UV` — how to run uv: the `UV` environment variable if it is set (on machines where uv isn't on the `PATH`), otherwise simply `uv`.

@@ 12
`CI` — true when running on GitHub Actions, which sets that variable.

@@ 14-16
**`run`** — run a program in the repository's folder and return what it printed. The output is captured (`"pipe"`) rather than shown; errors still go to the screen (`"inherit"`). Capturing matters below: the seed prints a secret key, which must not end up in a log.

@@ 18-19
**`prepare`** — everything that must exist before any service starts. It returns the shop's settings.

@@ 20
Start PostgreSQL and Valkey with Docker Compose, and wait until they are healthy (§4.5).

@@ 21
Bring the tables up to date (§5.1.3, `cli.py`).

@@ 22
Seed a fresh demo project with a test key, and capture what was printed.

@@ 23-24
Find the project ID and the key in that output with two **regular expressions**: `\s+` means "one or more spaces", and the brackets **capture** the part that matters. `?.[1]` takes the captured text if there was a match.

@@ 25-27
If either is missing, stop with a clear message.

@@ 28-30
Make the fake camera's video, unless it already exists (`infra/scripts/make_fake_camera.py`).

@@ 48-52
The shop's settings: the new project, the new key, and a fresh random secret for its cookies — new every run, so nothing secret is ever stored.

@@ 53
The closing brace.

@@ 55
**Prepare exactly once.** Playwright loads this file in its main process *and* again in every worker process that runs tests. Workers have `TEST_WORKER_INDEX` set; only the main process (where it isn't) prepares — otherwise every worker would seed its own project.

@@ 57-60
**`ENGINES`** (Phase 5) — which browser engines to test: all three by default, as CI does; `E2E_ENGINES=chromium,webkit` names fewer, for a machine where one can't start — as on the owner's Windows computer, where Playwright's Firefox fails with a "side-by-side configuration" error (the Phase 5 report). And the two test files only Chromium runs.

@@ 62-71
**`server`** — the settings for one service to start: its command, the address to poll until it answers, extra environment variables, the folder to start in, and:

- `reuseExistingServer: !CI` — on a laptop, reuse a service that is already running (handy while developing); in CI, always start fresh;
- `timeout` — wait up to 3 minutes for it to start;
- `stdout: "ignore"`, `stderr: "pipe"` — hide normal output, but show errors.

`as const` keeps the exact texts `"ignore"` and `"pipe"` as their types, which Playwright's configuration type requires.

@@ 73
The configuration itself.

@@ 74
The tests are in `tests/`.

@@ 75
Each test may take up to 90 seconds. The main story needs about a minute: its still portrait can't turn, so the page waits out 6 seconds at each of up to four poses.

@@ 76
In CI, retry a failed test once: a run that fails only *sometimes* — an overloaded CI machine, say — is then visible as "flaky" instead of failing the whole build. Locally, never retry: a failure should be seen at once.

@@ 77
One test at a time. The tests share one set of services and one database; running them side by side would make their results depend on each other.

@@ 78
How to report: GitHub-style annotations in CI, a simple list locally.

@@ 79-82
Settings for every test: addresses without a host mean the shop (`baseURL`), and a **trace** — a step-by-step recording with screenshots and network requests — is kept for every failing test.

@@ 83-85
One browser project, named `chromium`.

@@ 86
Chromium runs everything except Lighthouse, which starts its own browser.

@@ 87-88
It starts from Playwright's ready-made "Desktop Chrome" settings (`...` copies them in).

@@ 89
Grant camera permission up front, so no permission prompt can block the test.

@@ 90-98
Four Chromium switches:

- `--use-fake-ui-for-media-stream` — accept camera requests without showing a prompt;
- `--disable-blink-features=AutomationControlled` — don't announce that a program is driving the browser (added in Phase 3). Normally Playwright's browser sets `navigator.webdriver`, which the verify page reports as an injection sign — and the session would be stepped up. An attacker's tool can hide it the same way, which is the point of the comment: the server treats the page's signals as hints, never as proof;
- `--use-fake-device-for-media-stream` — use a pretend camera instead of real hardware;
- `--use-file-for-fake-video-capture=…` — and play *this video file* as its picture.

So the "person" in front of the camera is the test portrait, every time.

@@ 99-107
The closing brackets of Chromium's project; then **Firefox** and **WebKit** (Safari's engine), which run everything that needs no camera — only Chromium can play a video file as one, so the age-check story stays there; and **Lighthouse**, which goes with Chromium. Finally the list keeps only the engines asked for.

@@ 108
**The services**, started in this order:

@@ 109-126
The inference service on port 8001, ready when `/readyz` answers. `DWARPAL_INFERENCE_STUB_AGE=30` makes the stand-in age model see a 30-year-old: an adult.

`DWARPAL_INFERENCE_LIVENESS=labels` (Phase 3): the fake camera plays a still portrait that can't turn its head, so liveness believes the frames' labels here. This test mode is only allowed with the stand-in age model, so it can never weaken a real check.

And since Phase 6, Tesseract for the document check: run inside the OCR container, which the compose file starts with the databases (§5.6.2), given as a JSON list.

@@ 127-141
The API on port 8000, with its JSON logs, and four settings for testing:

- private webhook addresses are allowed, because the console test registers the demo shop's — on this computer. Production refuses them (the SSRF guard, §5.4.3);
- the session cookie is plain, not `__Host-` and `Secure`: these servers speak plain HTTP, and WebKit drops a `Secure` cookie there (Chromium and Firefox treat `localhost` as secure). The API's own test checks the production cookie, and production refuses to start without it;
- the sign-in limit is generous and refills fast: every engine signs in from this one computer, and the limiter remembers earlier runs in Valkey.

@@ 142-145
The web app on port 3000 (its production build): the home page, the console and the verify page. The home page is told where the demo shop is, so it can link to it (§5.5.9).

@@ 146
The shop on port 3100, with the settings `prepare` returned.

@@ 147-148
The closing brackets.

@@ 10
Where the specimen passport for the document check is kept (§5.6.3), in the same untracked `.cache` folder.

@@ 31-44
Draw a **specimen passport** (§5.6.2) for the document test — ICAO's fictional Utopia, born 1990 — with the same public-domain portrait the fake camera plays, so the selfie matches it. Made once, like the camera's video.

@@ 45-47
Hand the demo project's test key to the tests: the document test creates its own session through the API. The tests run in worker processes started from this one, so they inherit its environment; the key is never written anywhere.
