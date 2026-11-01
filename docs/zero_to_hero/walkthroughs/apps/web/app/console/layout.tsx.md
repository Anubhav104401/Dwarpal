---
fingerprint: c5c382af0775d3f9
---
The **console's layout** (§5.5.11): it marks the console's content as English.

@@ 1
React's type for anything that can be drawn.

@@ 3-5
**The console's layout** — Next.js wraps every console page in it. Its comment: the console is in English only, so its content says so (`lang="en"`), whatever language the page as a whole is in — a person who chose Hindi on the home page still gets the console's English read as English by a screen reader.

@@ 6-11
A `div` with `lang="en"` around the page; `contents` makes the `div` itself take no room, so the console's layout is exactly as before.
