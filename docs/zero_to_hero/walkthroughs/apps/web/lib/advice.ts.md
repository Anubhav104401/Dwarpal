---
fingerprint: 67833c04bafe5681
---
**Friendly words for the API's short codes** (§5.1.2, rewritten in §5.5.11). The API answers with codes such as `too_dark` or `session_not_open`; a person should read "It's too dark. Face a window or a lamp."

Since the pages speak two languages (decision D2), the words themselves live in `messages/en.json` and `messages/hi.json`. This module only decides **which** words: the code's own, if it has some, or the general ones — so a raw code never reaches the person.

@@ 1-3
The module's comment: which codes have their own words, and where the words now are.

@@ 5-28
**`TIPS`** — the codes that have a tip of their own (a `Set`, which answers "is this in it?" quickly): the photo problems the decision engine names (§5.1.2), the two from the decision rules, the liveness ones — deliberately the same words whichever check it was, so nobody can learn which one to fool — and the document check's (§5.6.3).

@@ 41-42
**`DEFAULT`** — the key of the general tip and the general problem.

@@ 44-47
**`tipFor`** — the first reason that has a tip of its own, as its key in `Tips`; otherwise the general tip. `find` returns the first matching item, or `undefined`, which `??` replaces.

@@ 49-52
**`problemFor`** — the problem's own key in `Problems`, or the general one: never a raw code shown to the person.

@@ 29-40
**`PROBLEMS`** — the codes that have their own message when something stops the check: a link that doesn't work, an age check that has ended, too many tries, too many requests from one network (since 9 Nov), no camera, no network.
