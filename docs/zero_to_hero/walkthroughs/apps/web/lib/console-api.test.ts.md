---
fingerprint: f5dfd01f039021f2
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

@@ 77-95
Three prepared answers: a page of one session with a cursor; that session's trace with one attempt and two scores; and the counts — the first day, one daily row and the totals.

@@ 96-99
A stand-in `fetch` that records each address and hands back the next answer.

@@ 100-103
Ask for live sessions after a cursor, the trace, and the test counts.

@@ 104-107
The first request's address carried the mode, the page size and the cursor exactly.

@@ 108-111
The page, the trace's scores, the totals and the daily rows came back as they were sent — each row without its policy.

@@ 112-113
End of the test and the group.

@@ 115-116
**The webhook requests.** Every one carries the mode, and the new endpoint's secret comes back.

@@ 117
Each request seen: its method, address and body.

@@ 118-128
Four prepared answers: who is signed in (with a CSRF token), the new endpoint with its secret, one dead delivery, and an empty `204`.

@@ 129-132
A stand-in `fetch` that records each request and hands back the next answer.

@@ 133-139
Sign in (for the token), add a live endpoint, read its deliveries, and delete it.

@@ 141
The secret came back.

@@ 142-146
The creation's body carried the address, the events and the mode.

@@ 147-149
The deliveries' address carried the mode.

@@ 150-154
The delivery was read as sent: dead, last answered `500`, with no error text.

@@ 155-158
The deletion was a `DELETE`, with the mode in its address.

@@ 159-160
End of the test and the group.

@@ 162-163
**Searching sessions.** Only the filters that are set go into the address.

@@ 164-168
A stand-in `fetch` that records each address and answers with an empty page.

@@ 169-171
Search with an outcome and a reference (with a space in it), then with an empty outcome.

@@ 173-175
The first address carried both filters — the space written as `+`, as addresses require.

@@ 176
The second carried neither: an empty filter means any.

@@ 177-178
End of the test and the group.

@@ 180-181
**Switching a webhook.** The request's method, address and body, and the answer read back.

@@ 182-190
Two prepared answers: who is signed in, and the endpoint, now off; a stand-in `fetch` records each request.

@@ 191-193
Sign in (for the token), and switch the endpoint off.

@@ 195-199
It was a `PATCH` to the endpoint's address, with the mode, carrying `enabled: false`.

@@ 200-202
The endpoint came back off. End of the test and the group.

@@ 204-205
**Members and one-time codes.** The right methods and addresses, and the bodies.

@@ 206-213
Each request seen; and five prepared answers: who is signed in, a changed role, an empty `204`, a secret, and the recovery codes.

@@ 214-217
A stand-in `fetch` that records each request and hands back the next answer.

@@ 218-223
Sign in (for the token); change a role; remove the member; ask for a secret; confirm a code, keeping the recovery codes.

@@ 225-230
After `/me`, the four requests went out with these methods to these addresses.

@@ 231-233
The role change sent only the role; the secret came back; the confirmation sent the code.

@@ 234
And the recovery codes came back as sent.

@@ 235-236
End of the test and the group.

@@ 238-239
**The page's role checks** match the API's matrix where the pages use them.

@@ 240-245
Every role but an analyst may manage keys. (`as never` lets a plain text stand in for the `Role` type in this table.)

@@ 246-247
A developer may not manage members; an admin may read the audit log.

@@ 248-249
End of the test and the group.
