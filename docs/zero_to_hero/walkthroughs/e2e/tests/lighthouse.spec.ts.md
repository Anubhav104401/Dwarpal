---
fingerprint: 87c89bf0c6477956
---
The Lighthouse check (Phase 5's exit criterion "Lighthouse ≥ 90"), as one Playwright test, so it reuses the test servers Playwright already starts: run Lighthouse CI on three key pages, then confirm the private ones still ask search engines to stay away.

@@ 1-4
Node's tools: run a program and wait (`execFileSync`), read folders and files, find a package's files (`createRequire`), and work with paths.

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

@@ 22-27
The pages: the shop's front page, the console's sign-in, and the verify page's error state — all reachable without signing in.

@@ 29-30
**The test.** Lighthouse takes about 20 seconds a page, so the test may take five minutes.

@@ 31-37
Lighthouse CI's arguments: run everything (`autorun`: collect, assert, save) with `lighthouserc.json`, in the headless shell, on each page.

@@ 38-39
Run it with this same Node and wait, showing its output. If any page misses a rule, it exits with an error, `execFileSync` throws, and the test fails.

@@ 41-45
Then read the list of saved reports (`manifest.json`): each page's address and its report file.

@@ 46-49
For each private page (port 3000), its `is-crawlable` audit must score 0 — "blocked from indexing" — so a change that let search engines list the console would fail here.

@@ 50
End of the test.
