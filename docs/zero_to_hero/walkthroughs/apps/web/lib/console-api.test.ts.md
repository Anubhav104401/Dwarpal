---
fingerprint: 82e44489e86c1374
---
Unit tests of the console's client (Phase 5), with the network replaced by a stand-in `fetch` that records each request and hands back prepared answers.

@@ 1
Vitest's tools; `vi` replaces things for a test (here, the global `fetch`).

@@ 3
The code under test.

@@ 5-10
**`answer`** — a prepared HTTP answer: a status and a JSON body (none for `204`).

@@ 12-18
**`ME`** — what the API says about a signed-in person, including the CSRF token.

@@ 20-22
After each test, put the real `fetch` back.

@@ 24
The client's tests.

@@ 25-31
**The CSRF rule.** A stand-in `fetch` records every request and answers in turn: signed in, a list of members, a member added.

@@ 32-35
Sign in, read the members, add a member.

@@ 37
The person's organisations were read from the sign-in answer.

@@ 38-42
The three requests went to the right addresses on this site, with the right methods.

@@ 43-44
The read carried no CSRF token; the change carried the one the sign-in answer gave.

@@ 45
End of the test.

@@ 47-52
**Refusals.** The stand-in answers `401`, then `403`.

@@ 53-54
Asking who is signed in gets `null`, not an error: nobody is.

@@ 55-57
Creating a key is refused with a `ConsoleError` carrying the status and code.

@@ 58
End of the test.

@@ 60-68
**The audit log.** One entry, and a broken chain.

@@ 69-71
The entry is read, and so is the verdict: not intact, broken at entry 2.

@@ 72-73
End of the test and the group.

@@ 75-76
**The page's role checks** match the API's matrix where the pages use them.

@@ 77-82
Every role but an analyst may manage keys. (`as never` lets a plain text stand in for the `Role` type in this table.)

@@ 83-84
A developer may not manage members; an admin may read the audit log.

@@ 85-86
End of the test and the group.
