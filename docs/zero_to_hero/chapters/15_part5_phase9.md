## 5.9 Phase 9 — beyond the plan

Phases 0–8 are the plan. Phase 9 is what comes after, chosen from the roadmap's list (§3.9) once the rest stands:

| Item | What | Status |
| :-- | :-- | :-- |
| Python SDK | The Node SDK's calls, for Python websites | 🟢 §5.9.1 |
| Passkeys | Console sign-in without passwords | 🟢 §5.9.2 |
| Age Pass | A reusable "over 18" credential, kept by the person, unlinkable between websites | 🗓 |
| CGI-render detector | Spotting computer-rendered faces (liveness level 6) | 🗓 needs attack data |
| Kubernetes | A deployment from the Helm chart | 🟡 the chart exists (§5.8.3) |

### 5.9.1 A Python SDK

Many websites run Python — Django, Flask, FastAPI. The Node SDK (§5.5.7) gave JavaScript sites three things: create an age check, read its result, and verify the signed answer and the webhooks. The Python SDK gives the same three, in two forms — `Client`, which waits for each answer, and `AsyncClient`, for `async` frameworks — using the same two libraries the API itself uses, so nothing new was downloaded.

!!! key "Key idea — the website checks the answer itself"
    An SDK could simply ask Dwarpal "did this session pass?". This one checks the **signed token** on the website's own server: the signature with Dwarpal's published keys, who issued it, for whom, until when, and for which session. A website that verifies for itself can't be fooled by someone who sits between it and Dwarpal.

!walk packages/sdk-python/pyproject.toml

!walk packages/sdk-python/src/dwarpal/__init__.py

!walk packages/sdk-python/src/dwarpal/errors.py

!walk packages/sdk-python/src/dwarpal/client.py

!walk packages/sdk-python/src/dwarpal/tokens.py

!walk packages/sdk-python/src/dwarpal/webhooks.py

!walk packages/sdk-python/tests/test_sdk.py

The workspace's settings (a new member), the task runner (its tests), and the API's tests (a test that runs the SDK against the real API) changed too; each was re-explained.

!!! honest "Honest limitation"
    The SDK isn't published to PyPI: publishing, and choosing whether to, is the owner's (as for the JavaScript SDKs). It is installed from the repository for now.

### 5.9.2 Passkeys: signing in without a password

A password can be guessed, reused from a leak, or typed into a fake site. A **passkey** can't. When a person adds one, their device — a phone, a laptop, a security key — makes a pair of keys. The **private key never leaves the device**; the console keeps only the **public key**. To sign in, the console sends a fresh random **challenge**, the device asks the person for their fingerprint, face or PIN, and signs the challenge. The console checks the signature with the public key it kept.

!!! key "Key idea — a passkey can't be phished"
    The browser itself writes down which site asked for the signature (the *origin*), and the device signs that record. A passkey made for the console signs only for the console: a look-alike site gets a signature the console refuses, or nothing at all.

The standard for this is **WebAuthn** (W3C). The console supports the part it needs:

| Choice | Why |
| :-- | :-- |
| The device must verify the person | A passkey then counts as two factors — something you have (the device) and something you are or know — so it needs no one-time code as well |
| No *attestation* (proof of the device's make) | The console doesn't need to know who made the device; asking would only add a privacy cost |
| Ed25519 or P-256 keys only | The two that passkeys use in practice; anything else is refused rather than half-checked |
| Adding a passkey needs the password (and a code, if those are on) | A signed-in browser left open shouldn't be enough to add a lasting way in |
| Each challenge works once, for five minutes | A recorded answer can't be played back |

The checks are pure functions, tested against a **software device** that makes real signatures; a few hundred random inputs from Hypothesis found two ways that malformed data escaped as the wrong error, both fixed before anything else was written. The end-to-end test uses Chromium's *virtual authenticator*, a device built into its developer tools.

!walk services/api/src/dwarpal_api/domain/webauthn.py

!walk services/api/src/dwarpal_api/migrations/versions/v0010_passkeys.py

!walk services/api/src/dwarpal_api/app/passkeys.py

!walk services/api/tests/passkey_device.py

!walk services/api/tests/test_webauthn.py

!walk apps/web/lib/passkeys.ts

!walk apps/web/lib/passkeys.test.ts

The store (a take-once read), the tables, the passkey lookup, the settings, the console's routes and pages, its API client, the API's and the browser's tests, and the test settings changed too; each was re-explained.

!!! honest "Honest limitation"
    Signing in with a passkey skips the one-time code, because the device has already verified the person. That is the usual rule (decision D20 in the decision log), and the owner may choose otherwise. A passkey that syncs between devices (most phone passkeys do) is only as safe as the account it syncs through.
