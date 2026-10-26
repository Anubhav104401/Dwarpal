---
fingerprint: 8da7363c95208abf
---
The console, tested in a real browser (Phase 5): a new customer signs up, creates an API key, and sees it in an intact audit log; and a wrong password is refused without revealing whether the account exists.

@@ 1
Playwright's `expect` and `test`.

@@ 3
The console's address.

@@ 5-8
**Test — a new customer.** A fresh address each run, from the current time.

@@ 9-14
Open the console, switch to creating an account, fill in the form by its labels — as a person, or a screen reader, finds the fields — and create it.

@@ 16-20
The organisation list appears; open the organisation; its heading, the person's role, and their address among the members are shown.

@@ 22-23
Create a key with the default scopes: the new key is shown, starting `dk_test_`.

@@ 24-27
The audit log shows an intact chain, with the key's creation and the organisation's.

@@ 28
A screenshot, for the record.

@@ 30-32
**Shown once**: after a reload, the key is gone from the page; only the audit entry remains.

@@ 33
End of the test.

@@ 35-39
**Test — a wrong password**, for an address nobody has.

@@ 40-42
The refusal says only that the address or password is wrong. (Next.js keeps its own empty `role="alert"` region for announcing page changes; the test picks the alert that has words in it.)

@@ 43
End of the test.
