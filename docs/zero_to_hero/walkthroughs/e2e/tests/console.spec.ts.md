---
fingerprint: c3e50541ec65a48f
---
The console, tested in a real browser (Phase 5): a new customer signs up, creates an API key, sees it in an intact audit log, then follows a real session onto the project's page, adds a policy version and a webhook endpoint; a wrong password is refused without revealing whether the account exists; and a member turns on one-time codes, after which signing in needs one.

@@ 1-3
Node's `createHmac`, to compute one-time codes as an authenticator app would; and Playwright's `expect`, `Page` type and `test`.

@@ 7-8
The console's address, and the API's.

@@ 10-11
**`oneTimeCode`** — what an authenticator app does (RFC 6238, §5.4.5), so the test can play the person's phone.

@@ 12-16
Turn the Base32 secret into bytes: each letter is 5 bits; join them, and read them back 8 at a time.

@@ 17-18
The step: the number of whole 30-second periods since 1970, as 8 bytes.

@@ 19-21
An HMAC-SHA1 of the step; take 4 bytes from where its last 4 bits point; keep 31 bits; the last six digits.

@@ 22
End of `oneTimeCode`.

@@ 24-27
**Test — a new customer.** Besides the page, it uses `request`, Playwright's way to call an HTTP API directly, as a website's server would.

@@ 28
A fresh address each run, from the current time.

@@ 29-34
Open the console, switch to creating an account, fill in the form by its labels — as a person, or a screen reader, finds the fields — and create it.

@@ 36-40
The organisation list appears; open the organisation; its heading, the person's role, and their address among the members are shown.

@@ 42-43
Create a key with the default scopes: the new key is shown, starting `dk_test_`.

@@ 44-47
The audit log shows an intact chain, with the key's creation and the organisation's.

@@ 48
A screenshot, for the record.

@@ 50-53
**Shown once**: keep the key's text for the next step, reload, and the key is gone from the page.

@@ 55-60
**A website uses the key**: create a session through the website API, as the shop's server would. It is accepted (`201`).

@@ 61-62
Open the project's page from the organisation page.

@@ 63-64
The session is listed, still `created`.

@@ 65-68
**Searching**: for sessions that passed — none has yet, so nothing matches.

@@ 69-71
Back to any outcome, and the session is listed again.

@@ 72-73
Its decision trace opens: no attempts yet.

@@ 75-85
**A policy version** (§5.5.8): the editor offers the model's own lines, with the 18+ line chosen first (`18@0.02`: the stand-in model's line at a 2 % risk budget). The stand-in was never measured, so the projection says *Not measured*. An owner adds `shop_18` on that line, ticking **Accept Age Passes** (Phase 9), and `shop_18@1` is listed at once.

@@ 88-93
**A webhook endpoint**: add one on the demo shop's address; its secret (`whsec_…`) is shown; send a test event; it is listed as `pending` — no delivery worker runs during the test.

@@ 94-99
**Switching it off and on**: off, and the endpoint is marked *Off*; on again, and the mark is gone.

@@ 100
End of the test.

@@ 102-106
**Test — a wrong password**, for an address nobody has.

@@ 107-109
The refusal says only that the address or password is wrong. (Next.js keeps its own empty `role="alert"` region for announcing page changes; the test picks the alert that has words in it.)

@@ 110
End of the test.

@@ 112-114
**Test — one-time codes.** A fresh address, and a password to use twice.

@@ 115-120
Create an account.

@@ 122-125
Open *Security* and start setting up: a QR code appears. Read the secret the page shows in text, as a person would type it into their app.

@@ 126-128
Enter the current code and turn it on: the page says "On."

@@ 129-132
Keep the first recovery code the page showed, and check its shape.

@@ 134-139
Sign out, and sign in with the password alone: the console asks for a code. A code works only once, so the test uses the next 30 seconds' code, which the API accepts for clocks that run a little fast.

@@ 140-144
Enter it and sign in: the organisations appear.

@@ 146-155
**A lost phone**: sign out and in again with the recovery code instead of a code — it works, and the Security page now says nine are left.

@@ 157-159
**Switching codes off** needs a code nobody has used. The next one was just used to sign in, so wait for the clock's next 30-second step, as a person would wait for a new code…

@@ 160-163
…then give the password and the code after it, and turn codes off: the page offers to set them up again.

@@ 164
End of the test.

@@ 166-175
**`signUp`** — create an account in a given browser page, with its own organisation, and wait for the organisations page: the steps of the first test, made reusable.

@@ 177-179
**Test — the model page** (§5.5.2).

@@ 180
Ask the API itself which model it is deciding with: its public configuration names it.

@@ 181-182
Sign up, and follow the *Age model* link.

@@ 184-185
The page has its heading and shows exactly the version the API named — the page and the API can't disagree.

@@ 186-188
And in the table of lines, a row for each of the four ages.

@@ 189
End of the test.

@@ 191-192
**Test — the command palette** (§5.5.6): find a project by typing, and go there without the mouse.

@@ 193-198
Press ⌘K or Ctrl+K (`ControlOrMeta` picks the right one for the system) until the search box has the focus. "Until": the shortcut works only once the page's script has started, which in a busy test run can trail the page's first appearance by a moment — so press again, within a second each time, as a person would.

@@ 200-201
Type two words — the organisation's name and part of the project's — and only the project is left in the results.

@@ 202-203
The down arrow moves from the box into the list, onto the project's link.

@@ 204-206
Enter follows it: the project's page opens, and the palette has closed.

@@ 207
End of the test.

@@ 209-211
**Test — managing a member** (Phase 5). Two fresh addresses: the owner's and a colleague's.

@@ 212-214
The colleague signs up in a browser of their own — a second **context**, with its own cookies, so their session never mixes with the owner's — which is then closed.

@@ 215-217
The owner signs up and opens the organisation; the members' panel is where everything happens.

@@ 219-223
Add the colleague as an analyst: their row appears, with a role menu showing *analyst*.

@@ 225-228
Change it to developer; then reload the page, to prove the change was saved, not just shown.

@@ 230-231
Remove them: their address is gone from the members.

@@ 232
End of the test.

@@ 371-376
**Test — a fresh nonce each time** (Phase 7). Ask for the console's page twice, as the website API's client would, and keep each answer's content security policy.

@@ 377-378
Pick out each policy's script rule, and the nonce in it.

@@ 379-381
There is a nonce; the two differ; and inline scripts are not allowed.

@@ 382
End of the test.

@@ 384-386
**Test — a member adds a passkey, then signs in with it alone** (Phase 9, §5.9.2). It runs in Chromium only: Chromium's developer tools can attach a *virtual authenticator*, a software device that makes real key pairs; WebKit has nothing like it, so the test is skipped there.

@@ 387-398
Through the developer tools protocol (CDP), switch WebAuthn's test mode on and attach a device: CTAP2 (the modern protocol), built into the computer, able to keep passkeys, and able to verify the person — and to say yes at once, as if a finger touched the sensor.

@@ 399-406
Sign up; on the Security page, name the passkey, give the password, and add it: it appears in the list.

@@ 408-412
Sign out, then **Use a passkey instead**: no e-mail address, no password, and the organisations appear.

@@ 413-414
Back on the Security page, the passkey now shows when it was last used.

@@ 415
End of the test.

@@ 86-87
Its row says the version accepts Age Passes.

@@ 5
The accessibility checker's helper (`axe.ts`), for the project page.

@@ 234-237
**Test — a project for a website** (decisions D28–D30), in a real browser.

@@ 238-239
A new owner opens their organisation.

@@ 241-245
A new project, its two origins typed one per line — one in capitals with a trailing `/`.

@@ 246-247
The list shows them written the standard way.

@@ 249-252
A key for the new project, read from the page.

@@ 253-259
A website using the key may create a session returning to the shop's origin, and not one returning elsewhere.

@@ 261-264
On the project's page, the keys panel doesn't show the secret.

@@ 265-268
Stopping the key asks for confirmation (accepted here); the key is marked *Stopped*, and refused at once.

@@ 270-275
Renamed in its settings: *Saved.*, and the heading follows.

@@ 276-277
No accessibility problems on the page, and a screenshot for the record.

@@ 278
End of the test.

@@ 280-284
**Test — an invitation** (decision D44): an owner and their organisation's members.

@@ 286-291
Adding an address without an account invites it: the notice says so, and it is listed as waiting.

@@ 293-297
In another browser, that address signs up — and finds the inviting organisation in its list.

@@ 299-302
Back with the owner: the newcomer is a member, with the invited role, and nothing waits any more.

@@ 304-311
**Test — a new password, and deleting the account** (decisions D31, D32): the two passwords, and a sign-up.

@@ 312-318
The same account signs in from a second browser.

@@ 320-328
On the account page, the password is changed; the notice says every other browser was signed out.

@@ 329-331
The second browser, reloaded, is at the sign-in form again.

@@ 333-338
Deleting the account needs the password and the tick; afterwards the console is signed out.

@@ 339-341
Signing in with that address and the new password…

@@ 342-344
…fails like any wrong sign-in: the account is gone. (The message is found by its text: after a navigation, Next.js's own route announcer is an alert too.)

@@ 346-349
**Test — a live check while no age model is certified** (decision D24).

@@ 350-355
A new owner makes a live key on their organisation's page.

@@ 357-362
A website creates a live session with it — allowed now — and gets its ID and secret.

@@ 363-366
The verify page opens on the document check's words, and offers no camera estimate…

@@ 367-369
…and its button leads to the document check itself.
