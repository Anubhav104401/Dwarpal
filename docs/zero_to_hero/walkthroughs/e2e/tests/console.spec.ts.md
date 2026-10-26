---
fingerprint: ab08335fb833c36f
---
The console, tested in a real browser (Phase 5): a new customer signs up, creates an API key, sees it in an intact audit log, then follows a real session onto the project's page and adds a policy version; and a wrong password is refused without revealing whether the account exists.

@@ 1
Playwright's `expect` and `test`.

@@ 3-4
The console's address, and the API's.

@@ 6-9
**Test — a new customer.** Besides the page, it uses `request`, Playwright's way to call an HTTP API directly, as a website's server would.

@@ 10
A fresh address each run, from the current time.

@@ 11-16
Open the console, switch to creating an account, fill in the form by its labels — as a person, or a screen reader, finds the fields — and create it.

@@ 18-22
The organisation list appears; open the organisation; its heading, the person's role, and their address among the members are shown.

@@ 24-25
Create a key with the default scopes: the new key is shown, starting `dk_test_`.

@@ 26-29
The audit log shows an intact chain, with the key's creation and the organisation's.

@@ 30
A screenshot, for the record.

@@ 32-35
**Shown once**: keep the key's text for the next step, reload, and the key is gone from the page.

@@ 37-42
**A website uses the key**: create a session through the website API, as the shop's server would. It is accepted (`201`).

@@ 43-44
Open the project's page from the organisation page.

@@ 45-46
The session is listed, still `created`.

@@ 47-48
Its decision trace opens: no attempts yet.

@@ 50-53
**A policy version**: an owner adds `shop_18`, and `shop_18@1` is listed at once.

@@ 54
End of the test.

@@ 56-60
**Test — a wrong password**, for an address nobody has.

@@ 61-63
The refusal says only that the address or password is wrong. (Next.js keeps its own empty `role="alert"` region for announcing page changes; the test picks the alert that has words in it.)

@@ 64
End of the test.
