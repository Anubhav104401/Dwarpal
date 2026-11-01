---
fingerprint: 52b4623fd8aca5ec
---
The Lighthouse check (Phase 5's exit criterion "Lighthouse ≥ 90"), as one Playwright test, so it reuses the test servers Playwright already starts: run Lighthouse CI on three key pages, then confirm the private ones still ask search engines to stay away.

@@ 1-4
Node's tools: run a program and wait (`execFileSync`), check for, list and read files, find a package's files (`createRequire`), and work with paths.

@@ 6
Playwright's Chromium (to find where it is installed), `expect` and `test`.

@@ 8-10
Where Lighthouse CI's command-line program is. `require.resolve` finds a package's file the way Node would load it; this file is an ES module, so it makes a `require` of its own first.

@@ 11-13
**`headlessShell`** — the path of Playwright's **headless shell**: a build of Chromium that only runs without a window, installed beside the full browser. On the owner's Windows computer the full browser won't start (the same "side-by-side" error as Firefox; the Phase 5 report), while the shell does — and Playwright's own tests use it too.

@@ 14-16
From the full browser's path (…`/chromium-1248/chrome-win64/chrome.exe`), work out the build number and the shell's folder, `chromium_headless_shell-1248`.

@@ 17-19
Inside it, the one folder whose name starts `chrome-headless-shell`, and in that the program (`.exe` on Windows, no extension on Linux).

@@ 20
End of `headlessShell`.

@@ 22-30
The pages: the shop's front page, the home page (§5.5.9, named `HOME` for later), the console's sign-in, and the verify page's error state — all reachable without signing in.

@@ 32-33
**The test.** Lighthouse takes about 20 seconds a page, so the test may take five minutes.

@@ 34-40
Lighthouse CI's arguments: run everything (`autorun`: collect, assert, save) with `lighthouserc.json`, in the headless shell, on each page.

@@ 41-63
Run it with this same Node and wait. If any page misses a rule, it exits with an error, `execFileSync` throws, and the test fails.

Since the first runs on GitHub (§5.6.2) the failure explains itself: GitHub shows anyone a failing test's message, but its full log only to people signed in. So the output is collected quietly (`stdio: "pipe"`), and on failure:
- if there are **no reports at all**, Lighthouse failed before scoring a page — starting Chrome, say — and the error carries the last 30 lines of Lighthouse's own output;
- otherwise the error lists every page's four scores, as percentages, from the saved list of reports (`manifest.json`).

@@ 65-70
Then read the list of saved reports (`manifest.json`): each page's address and its report file. The home page is the exception among port 3000's pages: it asks to be found, and `lighthouserc.json` holds its search score to 90.

@@ 71-76
For each private page (port 3000, except the home page), its `is-crawlable` audit must score 0 — "blocked from indexing" — so a change that let search engines list the console would fail here.

@@ 77
End of the test.
