---
fingerprint: f55b633d920a8dd6
---
Unit tests of the console's client (Phase 5), with the network replaced by a stand-in `fetch` that records each request and hands back prepared answers.

@@ 1
Vitest's tools; `vi` replaces things for a test (here, the global `fetch`).

@@ 3
The code under test. Since 9 Nov also `waitInWords`.

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

@@ 88-96
**The audit log.** One entry, and a broken chain.

@@ 97-99
The entry is read, and so is the verdict: not intact, broken at entry 2.

@@ 100-101
End of the test and the group.

@@ 103-104
**The project pages' requests.** Sessions by mode and cursor, a trace, and the counts.

@@ 105-129
Three prepared answers: a page of one session with a cursor; that session's trace with one attempt and two scores; and the counts — the first day, one daily row, the totals, and the face checks' figures, whose median is in the open-ended last band. Since 9 Nov the counts also carry `document_stage`: four reached, two passed and one failed.

@@ 130-133
A stand-in `fetch` that records each address and hands back the next answer.

@@ 134-137
Ask for live sessions after a cursor, the trace, and the test counts.

@@ 138-141
The first request's address carried the mode, the page size and the cursor exactly.

@@ 142-145
The page, the trace's scores, the totals and the daily rows came back as they were sent — each row without its policy.

@@ 152-153
End of the test and the group.

@@ 155-156
**The webhook requests.** Every one carries the mode, and the new endpoint's secret comes back.

@@ 157
Each request seen: its method, address and body.

@@ 158-168
Four prepared answers: who is signed in (with a CSRF token), the new endpoint with its secret, one dead delivery, and an empty `204`.

@@ 169-172
A stand-in `fetch` that records each request and hands back the next answer.

@@ 173-179
Sign in (for the token), add a live endpoint, read its deliveries, and delete it.

@@ 181
The secret came back.

@@ 182-186
The creation's body carried the address, the events and the mode.

@@ 187-189
The deliveries' address carried the mode.

@@ 190-194
The delivery was read as sent: dead, last answered `500`, with no error text.

@@ 195-198
The deletion was a `DELETE`, with the mode in its address.

@@ 199-200
End of the test and the group.

@@ 202-203
**Searching sessions.** Only the filters that are set go into the address.

@@ 204-208
A stand-in `fetch` that records each address and answers with an empty page.

@@ 209-211
Search with an outcome and a reference (with a space in it), then with an empty outcome.

@@ 213-215
The first address carried both filters — the space written as `+`, as addresses require.

@@ 216
The second carried neither: an empty filter means any.

@@ 217-218
End of the test and the group.

@@ 220-221
**Switching a webhook.** The request's method, address and body, and the answer read back.

@@ 222-230
Two prepared answers: who is signed in, and the endpoint, now off; a stand-in `fetch` records each request.

@@ 231-233
Sign in (for the token), and switch the endpoint off.

@@ 235-239
It was a `PATCH` to the endpoint's address, with the mode, carrying `enabled: false`.

@@ 240-242
The endpoint came back off. End of the test and the group.

@@ 244-245
**Members and one-time codes.** The right methods and addresses, and the bodies.

@@ 246-253
Each request seen; and five prepared answers: who is signed in, a changed role, an empty `204`, a secret, and the recovery codes.

@@ 254-257
A stand-in `fetch` that records each request and hands back the next answer.

@@ 258-263
Sign in (for the token); change a role; remove the member; ask for a secret; confirm a code, keeping the recovery codes.

@@ 265-270
After `/me`, the four requests went out with these methods to these addresses.

@@ 271-273
The role change sent only the role; the secret came back; the confirmation sent the code.

@@ 274
And the recovery codes came back as sent.

@@ 275-276
End of the test and the group.

@@ 427-432
Every role but an analyst may manage keys. (`as never` lets a plain text stand in for the `Role` type in this table.)

@@ 433-434
A developer may not manage members; an admin may read the audit log.

@@ 441-442
End of the test and the group.

@@ 444-445
**The model page's client.**

@@ 446-470
Two prepared answers: a model's details, with a training dataset that records no number of faces and one line whose adult bound is missing but whose adults were measured (one band); then a 401.

@@ 471-472
Every request gets the next answer; a fresh client.

@@ 474
Ask for the model.

@@ 476-491
The training faces are read with their number of faces unknown (`null`), the calibration's number is kept, and the line arrives with every field renamed, the missing bound as `null`, and its adult band read whole (`step_up` as `stepUp`).

@@ 492
Signed out, the client answers `null` rather than failing.

@@ 493-494
End of the test and the group.

@@ 146-150
And the face checks' figures, read whole: five decided, four passes and a step-up, and a median band with no end.

@@ 278-313
**Policies** (Phase 9): the list says which version accepts Age Passes (a version without the field doesn't), and adding a version sends the switch with the other rules.

@@ 425-426
**The page's role checks** match the API's matrix where the pages use them.

@@ 315-317
**Test — projects and keys** (decisions D28–D30): the client's four new calls, and what it reads back.

@@ 318-323
A project as the API would answer it.

@@ 324-342
The answers, in order: who is signed in; the new project; the renamed one; two keys — one without a state, one stopped; and the stop itself.

@@ 343-346
A stand-in `fetch` notes each request's method, address and body.

@@ 347-352
Make a project, rename it, list the keys, stop one.

@@ 354-359
Each request went where it should, and the rename sent only the name.

@@ 360-366
The project and the renamed one were read back in the page's own terms.

@@ 367-371
The keys too: a key without a state reads as active; the stopped one keeps its time.

@@ 372
End of the test.

@@ 374-375
**Test — invitations and the account** (decisions D31, D32, D44).

@@ 376-388
The answers, in order: who is signed in; an invitation (pending); the list; the cancellation; the password change with a new CSRF token; the deletion.

@@ 389-397
A stand-in `fetch` notes each request, its body and the CSRF token it carried.

@@ 398-404
Invite, list, cancel, change the password (with a code), delete the account.

@@ 406-409
The invitation was pending, and the list read back.

@@ 410-416
Each request went where it should.

@@ 417-419
The password change sent both passwords and the code.

@@ 420-421
The deletion carried the **new** session's CSRF token — the client kept it from the password change — and no code, since none was given.

@@ 422-423
End of the test.

@@ 435-440
And who may make projects: owners and admins only.

@@ 60-86
**Test — a locked sign-in keeps its wait, and says it in words** (9 Nov): an answer `429` with `Retry-After: 240` becomes an error whose `retryAfter` is 240; one with a date instead gives `null`. Then the words for a range of waits — nothing, a second, under a minute, exactly one, just over (rounded up to two), an hour and more.

@@ 151
And the ID-document checks' counts, read as they came (9 Nov).
