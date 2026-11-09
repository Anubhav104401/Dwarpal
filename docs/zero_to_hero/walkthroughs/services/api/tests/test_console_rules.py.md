---
fingerprint: 9f2595856e15fb18
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

@@ 10-13
The code under test. Since 9 Nov also `lock_s`, the lock-out back-off's rule.

@@ 15-26
**`MATRIX`** — the design's role matrix written out again, independently of `domain/roles.py`: one row per action, one column per role, `True` where allowed. If someone changes the code's matrix by mistake, the two disagree. Since 8 Nov it has a row for making and changing projects: owners and admins (decision D28).

@@ 27
The roles, in the columns' order.

@@ 30-33
**Every cell.** The table covers every action there is, and for each, the four roles' answers match its row exactly.

@@ 36-37
**An unknown role** may do nothing at all.

@@ 46-48
The test values from **RFC 6238, appendix B**: the secret is the ASCII text `12345678901234567890`, and the standard lists 8-digit codes at given times. Our codes have 6 digits, which are the last six of those.

@@ 51-53
**Matching the standard.** One test per published example: the code computed for that time's step must be the last six digits of the standard's.

@@ 56-64
**Accepted once, near its time.** A code for now is accepted, and returns its step; also from a phone 30 seconds behind; not 90 seconds later; not once its step has been used; and never if it is not six digits.

@@ 67-70
**The provisioning address** names Dwarpal and the account, carries the secret, and states six digits and 30 seconds.

@@ 73-79
**Passwords.** Hashing the same password twice gives two different Argon2id hashes (a fresh salt each time); the right password matches; one extra character does not; and with no account at all, the answer is no, after checking the decoy, so it takes as long as a real check.

@@ 40-43
**Test — locks start after the free tries, then double up to the longest** (9 Nov): with five free tries, a 60-second first lock and an hour at most, tries 1 to 14 give no lock five times, then 1, 2, 4, 8, 16 and 32 minutes, then an hour each time; and even a billion tries give an hour, at once.
