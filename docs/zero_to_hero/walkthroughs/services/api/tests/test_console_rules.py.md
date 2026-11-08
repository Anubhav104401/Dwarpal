---
fingerprint: 5c591ea37bbe0d14
---
Tests of the console's rules that need no database (Phase 4): the role matrix, checked cell by cell; one-time codes, checked against the standard's own published examples; and password hashing.

@@ 1-2
The docstring.

@@ 4
The project-wide type-hint setting.

@@ 6
`base64`, to write the standard's test secret in Base32.

@@ 8
`pytest`.

@@ 10-12
The code under test.

@@ 14-25
**`MATRIX`** — the design's role matrix written out again, independently of `domain/roles.py`: one row per action, one column per role, `True` where allowed. If someone changes the code's matrix by mistake, the two disagree. Since 8 Nov it has a row for making and changing projects: owners and admins (decision D28).

@@ 26
The roles, in the columns' order.

@@ 29-32
**Every cell.** The table covers every action there is, and for each, the four roles' answers match its row exactly.

@@ 35-36
**An unknown role** may do nothing at all.

@@ 39-41
The test values from **RFC 6238, appendix B**: the secret is the ASCII text `12345678901234567890`, and the standard lists 8-digit codes at given times. Our codes have 6 digits, which are the last six of those.

@@ 44-46
**Matching the standard.** One test per published example: the code computed for that time's step must be the last six digits of the standard's.

@@ 49-57
**Accepted once, near its time.** A code for now is accepted, and returns its step; also from a phone 30 seconds behind; not 90 seconds later; not once its step has been used; and never if it is not six digits.

@@ 60-63
**The provisioning address** names Dwarpal and the account, carries the secret, and states six digits and 30 seconds.

@@ 66-72
**Passwords.** Hashing the same password twice gives two different Argon2id hashes (a fresh salt each time); the right password matches; one extra character does not; and with no account at all, the answer is no, after checking the decoy, so it takes as long as a real check.
