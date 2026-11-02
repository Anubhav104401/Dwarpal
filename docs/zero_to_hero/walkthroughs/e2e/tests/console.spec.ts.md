---
fingerprint: 6f0291cf176c7a18
---
The console, tested in a real browser (Phase 5): a new customer signs up, creates an API key, sees it in an intact audit log, then follows a real session onto the project's page, adds a policy version and a webhook endpoint; a wrong password is refused without revealing whether the account exists; and a member turns on one-time codes, after which signing in needs one.

@@ 1-3
Node's `createHmac`, to compute one-time codes as an authenticator app would; and Playwright's `expect`, `Page` type and `test`.

@@ 5-6
The console's address, and the API's.

@@ 8-9
**`oneTimeCode`** — what an authenticator app does (RFC 6238, §5.4.5), so the test can play the person's phone.

@@ 10-14
Turn the Base32 secret into bytes: each letter is 5 bits; join them, and read them back 8 at a time.

@@ 15-16
The step: the number of whole 30-second periods since 1970, as 8 bytes.

@@ 17-19
An HMAC-SHA1 of the step; take 4 bytes from where its last 4 bits point; keep 31 bits; the last six digits.

@@ 20
End of `oneTimeCode`.

@@ 22-25
**Test — a new customer.** Besides the page, it uses `request`, Playwright's way to call an HTTP API directly, as a website's server would.

@@ 26
A fresh address each run, from the current time.

@@ 27-32
Open the console, switch to creating an account, fill in the form by its labels — as a person, or a screen reader, finds the fields — and create it.

@@ 34-38
The organisation list appears; open the organisation; its heading, the person's role, and their address among the members are shown.

@@ 40-41
Create a key with the default scopes: the new key is shown, starting `dk_test_`.

@@ 42-45
The audit log shows an intact chain, with the key's creation and the organisation's.

@@ 46
A screenshot, for the record.

@@ 48-51
**Shown once**: keep the key's text for the next step, reload, and the key is gone from the page.

@@ 53-58
**A website uses the key**: create a session through the website API, as the shop's server would. It is accepted (`201`).

@@ 59-60
Open the project's page from the organisation page.

@@ 61-62
The session is listed, still `created`.

@@ 63-66
**Searching**: for sessions that passed — none has yet, so nothing matches.

@@ 67-69
Back to any outcome, and the session is listed again.

@@ 70-71
Its decision trace opens: no attempts yet.

@@ 73-83
**A policy version** (§5.5.8): the editor offers the model's own lines, with the 18+ line chosen first (`18@0.02`: the stand-in model's line at a 2 % risk budget). The stand-in was never measured, so the projection says *Not measured*. An owner adds `shop_18` on that line, ticking **Accept Age Passes** (Phase 9), and `shop_18@1` is listed at once.

@@ 86-91
**A webhook endpoint**: add one on the demo shop's address; its secret (`whsec_…`) is shown; send a test event; it is listed as `pending` — no delivery worker runs during the test.

@@ 92-97
**Switching it off and on**: off, and the endpoint is marked *Off*; on again, and the mark is gone.

@@ 98
End of the test.

@@ 100-104
**Test — a wrong password**, for an address nobody has.

@@ 105-107
The refusal says only that the address or password is wrong. (Next.js keeps its own empty `role="alert"` region for announcing page changes; the test picks the alert that has words in it.)

@@ 108
End of the test.

@@ 110-112
**Test — one-time codes.** A fresh address, and a password to use twice.

@@ 113-118
Create an account.

@@ 120-123
Open *Security* and start setting up: a QR code appears. Read the secret the page shows in text, as a person would type it into their app.

@@ 124-126
Enter the current code and turn it on: the page says "On."

@@ 127-130
Keep the first recovery code the page showed, and check its shape.

@@ 132-137
Sign out, and sign in with the password alone: the console asks for a code. A code works only once, so the test uses the next 30 seconds' code, which the API accepts for clocks that run a little fast.

@@ 138-142
Enter it and sign in: the organisations appear.

@@ 144-153
**A lost phone**: sign out and in again with the recovery code instead of a code — it works, and the Security page now says nine are left.

@@ 155-157
**Switching codes off** needs a code nobody has used. The next one was just used to sign in, so wait for the clock's next 30-second step, as a person would wait for a new code…

@@ 158-161
…then give the password and the code after it, and turn codes off: the page offers to set them up again.

@@ 162
End of the test.

@@ 164-173
**`signUp`** — create an account in a given browser page, with its own organisation, and wait for the organisations page: the steps of the first test, made reusable.

@@ 175-177
**Test — the model page** (§5.5.2).

@@ 178
Ask the API itself which model it is deciding with: its public configuration names it.

@@ 179-180
Sign up, and follow the *Age model* link.

@@ 182-183
The page has its heading and shows exactly the version the API named — the page and the API can't disagree.

@@ 184-186
And in the table of lines, a row for each of the four ages.

@@ 187
End of the test.

@@ 189-190
**Test — the command palette** (§5.5.6): find a project by typing, and go there without the mouse.

@@ 191-196
Press ⌘K or Ctrl+K (`ControlOrMeta` picks the right one for the system) until the search box has the focus. "Until": the shortcut works only once the page's script has started, which in a busy test run can trail the page's first appearance by a moment — so press again, within a second each time, as a person would.

@@ 198-199
Type two words — the organisation's name and part of the project's — and only the project is left in the results.

@@ 200-201
The down arrow moves from the box into the list, onto the project's link.

@@ 202-204
Enter follows it: the project's page opens, and the palette has closed.

@@ 205
End of the test.

@@ 207-209
**Test — managing a member** (Phase 5). Two fresh addresses: the owner's and a colleague's.

@@ 210-212
The colleague signs up in a browser of their own — a second **context**, with its own cookies, so their session never mixes with the owner's — which is then closed.

@@ 213-215
The owner signs up and opens the organisation; the members' panel is where everything happens.

@@ 217-221
Add the colleague as an analyst: their row appears, with a role menu showing *analyst*.

@@ 223-226
Change it to developer; then reload the page, to prove the change was saved, not just shown.

@@ 228-229
Remove them: their address is gone from the members.

@@ 230
End of the test.

@@ 232-237
**Test — a fresh nonce each time** (Phase 7). Ask for the console's page twice, as the website API's client would, and keep each answer's content security policy.

@@ 238-239
Pick out each policy's script rule, and the nonce in it.

@@ 240-242
There is a nonce; the two differ; and inline scripts are not allowed.

@@ 243
End of the test.

@@ 245-247
**Test — a member adds a passkey, then signs in with it alone** (Phase 9, §5.9.2). It runs in Chromium only: Chromium's developer tools can attach a *virtual authenticator*, a software device that makes real key pairs; WebKit has nothing like it, so the test is skipped there.

@@ 248-259
Through the developer tools protocol (CDP), switch WebAuthn's test mode on and attach a device: CTAP2 (the modern protocol), built into the computer, able to keep passkeys, and able to verify the person — and to say yes at once, as if a finger touched the sensor.

@@ 260-267
Sign up; on the Security page, name the passkey, give the password, and add it: it appears in the list.

@@ 269-273
Sign out, then **Use a passkey instead**: no e-mail address, no password, and the organisations appear.

@@ 274-275
Back on the Security page, the passkey now shows when it was last used.

@@ 276
End of the test.

@@ 84-85
Its row says the version accepts Age Passes.
