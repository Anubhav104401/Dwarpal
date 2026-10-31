---
fingerprint: 15dc5586bb0d75ca
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

@@ 73-81
**A policy version** (§5.5.8): the editor offers the model's own lines, with the 18+ line chosen first (`18@0.02`: the stand-in model's line at a 2 % risk budget). The stand-in was never measured, so the projection says *Not measured*. An owner adds `shop_18` on that line, and `shop_18@1` is listed at once.

@@ 83-88
**A webhook endpoint**: add one on the demo shop's address; its secret (`whsec_…`) is shown; send a test event; it is listed as `pending` — no delivery worker runs during the test.

@@ 89-94
**Switching it off and on**: off, and the endpoint is marked *Off*; on again, and the mark is gone.

@@ 95
End of the test.

@@ 97-101
**Test — a wrong password**, for an address nobody has.

@@ 102-104
The refusal says only that the address or password is wrong. (Next.js keeps its own empty `role="alert"` region for announcing page changes; the test picks the alert that has words in it.)

@@ 105
End of the test.

@@ 107-109
**Test — one-time codes.** A fresh address, and a password to use twice.

@@ 110-115
Create an account.

@@ 117-120
Open *Security* and start setting up: a QR code appears. Read the secret the page shows in text, as a person would type it into their app.

@@ 121-123
Enter the current code and turn it on: the page says "On."

@@ 124-127
Keep the first recovery code the page showed, and check its shape.

@@ 129-134
Sign out, and sign in with the password alone: the console asks for a code. A code works only once, so the test uses the next 30 seconds' code, which the API accepts for clocks that run a little fast.

@@ 135-139
Enter it and sign in: the organisations appear.

@@ 141-150
**A lost phone**: sign out and in again with the recovery code instead of a code — it works, and the Security page now says nine are left.

@@ 152-154
**Switching codes off** needs a code nobody has used. The next one was just used to sign in, so wait for the clock's next 30-second step, as a person would wait for a new code…

@@ 155-158
…then give the password and the code after it, and turn codes off: the page offers to set them up again.

@@ 159
End of the test.

@@ 161-170
**`signUp`** — create an account in a given browser page, with its own organisation, and wait for the organisations page: the steps of the first test, made reusable.

@@ 172-174
**Test — the model page** (§5.5.2).

@@ 175
Ask the API itself which model it is deciding with: its public configuration names it.

@@ 176-177
Sign up, and follow the *Age model* link.

@@ 179-180
The page has its heading and shows exactly the version the API named — the page and the API can't disagree.

@@ 181-183
And in the table of lines, a row for each of the four ages.

@@ 184
End of the test.

@@ 186-187
**Test — the command palette** (§5.5.6): find a project by typing, and go there without the mouse.

@@ 188-193
Press ⌘K or Ctrl+K (`ControlOrMeta` picks the right one for the system) until the search box has the focus. "Until": the shortcut works only once the page's script has started, which in a busy test run can trail the page's first appearance by a moment — so press again, within a second each time, as a person would.

@@ 195-196
Type two words — the organisation's name and part of the project's — and only the project is left in the results.

@@ 197-198
The down arrow moves from the box into the list, onto the project's link.

@@ 199-201
Enter follows it: the project's page opens, and the palette has closed.

@@ 202
End of the test.

@@ 204-206
**Test — managing a member** (Phase 5). Two fresh addresses: the owner's and a colleague's.

@@ 207-209
The colleague signs up in a browser of their own — a second **context**, with its own cookies, so their session never mixes with the owner's — which is then closed.

@@ 210-212
The owner signs up and opens the organisation; the members' panel is where everything happens.

@@ 214-218
Add the colleague as an analyst: their row appears, with a role menu showing *analyst*.

@@ 220-223
Change it to developer; then reload the page, to prove the change was saved, not just shown.

@@ 225-226
Remove them: their address is gone from the members.

@@ 227
End of the test.

@@ 229-234
**Test — a fresh nonce each time** (Phase 7). Ask for the console's page twice, as the website API's client would, and keep each answer's content security policy.

@@ 235-236
Pick out each policy's script rule, and the nonce in it.

@@ 237-239
There is a nonce; the two differ; and inline scripts are not allowed.

@@ 240
End of the test.
