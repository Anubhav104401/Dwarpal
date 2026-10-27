---
fingerprint: c395b8c77fc5efad
---
A small script for the scanners (Phase 7): copy every file Git tracks — and nothing else — into a folder of its own, so Trivy sees the project's real files in seconds instead of crawling models and packages for a quarter of an hour.

@@ 1-8
What it does, how to run it, and why it exists.

@@ 10
Newer type-hint syntax on older Pythons.

@@ 12-15
Standard tools: copying files and folders, running Git, the command line's arguments, and file paths.

@@ 17
The project's root folder: two levels up from this file.

@@ 20-21
**`main`** — start by removing any earlier copy, so files deleted since don't linger.

@@ 22
Ask Git for every tracked file (`git ls-files`), separated by NUL characters (`-z`), which no file name can contain — so names with spaces or odd characters come through intact. (`S607` is the linter's warning about running a program found on the `PATH`; Git is meant to be found there.)

@@ 23
Split the list into names, dropping the empty one at the end.

@@ 24-31
Copy each file that still exists into the same place under the target folder, creating folders as needed, and count them.

@@ 32-33
Say how many were copied.

@@ 36-37
Run `main` with the target folder from the command line.
