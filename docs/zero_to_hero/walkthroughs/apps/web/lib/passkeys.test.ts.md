---
fingerprint: 0ef5052399c4f48b
---
Tests for **`lib/passkeys.ts`** (§5.9.2). The whole ceremony, with a real (virtual) device, is in the end-to-end tests.

@@ 1-11
Vitest's functions, and the functions under test.

@@ 13-24
**base64url** — every byte value from 0 to 255 survives the round trip, the text has no `+`, `/` or `=`, and short lengths (0 to 4 bytes, which need different padding) do too.

@@ 26-44
**Registration options** — the challenge, the person's handle and the passkeys to leave out become bytes; the algorithms, the verification and "no attestation" come through.

@@ 46-51
**Sign-in options** — the site's name, the person verified, and no passkeys named.

@@ 54-55
**Answers** — a helper that makes an `ArrayBuffer` from some byte values.

@@ 57-62
A new passkey's two answers become base64url (`[1]` is `AQ`, `[2]` is `Ag`).

@@ 64-76
A sign-in's answers, with the account's handle when there is one and without it when there isn't.

@@ 78-83
A closed or timed-out prompt counts as cancelled; any other failure doesn't.

@@ 52
End of the options tests.

@@ 84
End of the answers tests.
