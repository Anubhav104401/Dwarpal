---
fingerprint: d04e4811e5550164
---
**The console's places** (§5.5.6): the fixed pages every signed-in person can open, which the sidebar lists, and the search the command palette runs over them together with the person's organisations and projects. Keeping the search a plain function means it can be tested without a browser.

@@ 1-2
What this module is for.

@@ 4-8
**`Place`** — somewhere to go: the name shown, its address, and a short hint that says what it is (and that the search also looks at).

@@ 10-14
**`PLACES`** — the three fixed places: all organisations, the age model's page and the person's security settings.

@@ 16-18
**`matching`** — the places that fit what was typed, best first.

@@ 19
Split what was typed into lower-case words at any run of spaces (`\s+`); `filter(Boolean)` drops the empty pieces that leading or trailing spaces leave.

@@ 20
Nothing typed: every place, in its usual order.

@@ 21-24
Keep a place only if *every* word appears somewhere in its name or hint, ignoring case — so "amber default" finds the *Default project* of *Amber Cellars*, whichever order the words come in.

@@ 25-27
Then put first the places whose name starts with the first word, since that is usually what someone means. `sort` keeps the original order within each group (JavaScript's sort is *stable*), so nothing else moves. `?? ""` is only for TypeScript: there is always a first word here.

@@ 28
End of the function.
