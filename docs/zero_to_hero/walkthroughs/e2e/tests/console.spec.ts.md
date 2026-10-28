---
fingerprint: 3bcb12307fbd56bb
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

@@ 73-76
**A policy version**: an owner adds `shop_18`, and `shop_18@1` is listed at once.

@@ 78-83
**A webhook endpoint**: add one on the demo shop's address; its secret (`whsec_…`) is shown; send a test event; it is listed as `pending` — no delivery worker runs during the test.

@@ 84-89
**Switching it off and on**: off, and the endpoint is marked *Off*; on again, and the mark is gone.

@@ 90
End of the test.

@@ 92-96
**Test — a wrong password**, for an address nobody has.

@@ 97-99
The refusal says only that the address or password is wrong. (Next.js keeps its own empty `role="alert"` region for announcing page changes; the test picks the alert that has words in it.)

@@ 100
End of the test.

@@ 102-104
**Test — one-time codes.** A fresh address, and a password to use twice.

@@ 105-110
Create an account.

@@ 112-115
Open *Security* and start setting up: a QR code appears. Read the secret the page shows in text, as a person would type it into their app.

@@ 116-118
Enter the current code and turn it on: the page says "On."

@@ 120-125
Sign out, and sign in with the password alone: the console asks for a code. A code works only once, so the test uses the next 30 seconds' code, which the API accepts for clocks that run a little fast.

@@ 126-130
Enter it and sign in: the organisations appear.

@@ 131
End of the test.

@@ 133-142
**`signUp`** — create an account in a given browser page, with its own organisation, and wait for the organisations page: the steps of the first test, made reusable.

@@ 144-146
**Test — managing a member** (Phase 5). Two fresh addresses: the owner's and a colleague's.

@@ 147-149
The colleague signs up in a browser of their own — a second **context**, with its own cookies, so their session never mixes with the owner's — which is then closed.

@@ 150-152
The owner signs up and opens the organisation; the members' panel is where everything happens.

@@ 154-158
Add the colleague as an analyst: their row appears, with a role menu showing *analyst*.

@@ 160-163
Change it to developer; then reload the page, to prove the change was saved, not just shown.

@@ 165-166
Remove them: their address is gone from the members.

@@ 167
End of the test.
