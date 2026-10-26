---
fingerprint: 669d950e46de1aed
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
**The project pages' requests.** Sessions by mode and cursor, a trace, and the counts.

@@ 77-91
Three prepared answers: a page of one session with a cursor; that session's trace with one attempt and two scores; and the counts.

@@ 92-95
A stand-in `fetch` that records each address and hands back the next answer.

@@ 96-99
Ask for live sessions after a cursor, the trace, and the test counts.

@@ 100-103
The first request's address carried the mode, the page size and the cursor exactly.

@@ 104-106
The page, the trace's scores and the totals came back as they were sent.

@@ 107-108
End of the test and the group.

@@ 110-111
**The webhook requests.** Every one carries the mode, and the new endpoint's secret comes back.

@@ 112
Each request seen: its method, address and body.

@@ 113-123
Four prepared answers: who is signed in (with a CSRF token), the new endpoint with its secret, one dead delivery, and an empty `204`.

@@ 124-127
A stand-in `fetch` that records each request and hands back the next answer.

@@ 128-134
Sign in (for the token), add a live endpoint, read its deliveries, and delete it.

@@ 136
The secret came back.

@@ 137-141
The creation's body carried the address, the events and the mode.

@@ 142-144
The deliveries' address carried the mode.

@@ 145-149
The delivery was read as sent: dead, last answered `500`, with no error text.

@@ 150-153
The deletion was a `DELETE`, with the mode in its address.

@@ 154-155
End of the test and the group.

@@ 157-158
**The page's role checks** match the API's matrix where the pages use them.

@@ 159-164
Every role but an analyst may manage keys. (`as never` lets a plain text stand in for the `Role` type in this table.)

@@ 165-166
A developer may not manage members; an admin may read the audit log.

@@ 167-168
End of the test and the group.
