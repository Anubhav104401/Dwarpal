---
fingerprint: dcacc902c3dd1ea3
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

@@ 77-100
Three prepared answers: a page of one session with a cursor; that session's trace with one attempt and two scores; and the counts — the first day, one daily row, the totals, and the face checks' figures, whose median is in the open-ended last band.

@@ 101-104
A stand-in `fetch` that records each address and hands back the next answer.

@@ 105-108
Ask for live sessions after a cursor, the trace, and the test counts.

@@ 109-112
The first request's address carried the mode, the page size and the cursor exactly.

@@ 113-116
The page, the trace's scores, the totals and the daily rows came back as they were sent — each row without its policy.

@@ 122-123
End of the test and the group.

@@ 125-126
**The webhook requests.** Every one carries the mode, and the new endpoint's secret comes back.

@@ 127
Each request seen: its method, address and body.

@@ 128-138
Four prepared answers: who is signed in (with a CSRF token), the new endpoint with its secret, one dead delivery, and an empty `204`.

@@ 139-142
A stand-in `fetch` that records each request and hands back the next answer.

@@ 143-149
Sign in (for the token), add a live endpoint, read its deliveries, and delete it.

@@ 151
The secret came back.

@@ 152-156
The creation's body carried the address, the events and the mode.

@@ 157-159
The deliveries' address carried the mode.

@@ 160-164
The delivery was read as sent: dead, last answered `500`, with no error text.

@@ 165-168
The deletion was a `DELETE`, with the mode in its address.

@@ 169-170
End of the test and the group.

@@ 172-173
**Searching sessions.** Only the filters that are set go into the address.

@@ 174-178
A stand-in `fetch` that records each address and answers with an empty page.

@@ 179-181
Search with an outcome and a reference (with a space in it), then with an empty outcome.

@@ 183-185
The first address carried both filters — the space written as `+`, as addresses require.

@@ 186
The second carried neither: an empty filter means any.

@@ 187-188
End of the test and the group.

@@ 190-191
**Switching a webhook.** The request's method, address and body, and the answer read back.

@@ 192-200
Two prepared answers: who is signed in, and the endpoint, now off; a stand-in `fetch` records each request.

@@ 201-203
Sign in (for the token), and switch the endpoint off.

@@ 205-209
It was a `PATCH` to the endpoint's address, with the mode, carrying `enabled: false`.

@@ 210-212
The endpoint came back off. End of the test and the group.

@@ 214-215
**Members and one-time codes.** The right methods and addresses, and the bodies.

@@ 216-223
Each request seen; and five prepared answers: who is signed in, a changed role, an empty `204`, a secret, and the recovery codes.

@@ 224-227
A stand-in `fetch` that records each request and hands back the next answer.

@@ 228-233
Sign in (for the token); change a role; remove the member; ask for a secret; confirm a code, keeping the recovery codes.

@@ 235-240
After `/me`, the four requests went out with these methods to these addresses.

@@ 241-243
The role change sent only the role; the secret came back; the confirmation sent the code.

@@ 244
And the recovery codes came back as sent.

@@ 245-246
End of the test and the group.

@@ 248-249
**The page's role checks** match the API's matrix where the pages use them.

@@ 250-255
Every role but an analyst may manage keys. (`as never` lets a plain text stand in for the `Role` type in this table.)

@@ 256-257
A developer may not manage members; an admin may read the audit log.

@@ 258-259
End of the test and the group.

@@ 261-262
**The model page's client.**

@@ 263-286
Two prepared answers: a model's details, with a training dataset that records no number of faces and one line whose adult bound is missing; then a 401.

@@ 287-288
Every request gets the next answer; a fresh client.

@@ 290
Ask for the model.

@@ 292-306
The training faces are read with their number of faces unknown (`null`), the calibration's number is kept, and the line arrives with every field renamed and the missing bound as `null`.

@@ 307
Signed out, the client answers `null` rather than failing.

@@ 308-309
End of the test and the group.

@@ 117-121
And the face checks' figures, read whole: five decided, four passes and a step-up, and a median band with no end.
