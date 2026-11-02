## 5.9 Phase 9 — beyond the plan

Phases 0–8 are the plan. Phase 9 is what comes after, chosen from the roadmap's list (§3.9) once the rest stands:

| Item | What | Status |
| :-- | :-- | :-- |
| Python SDK | The Node SDK's calls, for Python websites | 🟢 §5.9.1 |
| Passkeys | Console sign-in without passwords | 🟢 §5.9.2 |
| Age Pass | A reusable "over 18" credential, kept by the person, unlinkable between websites | 🟢 §5.9.3 |
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
    Signing in with a passkey skips the one-time code, because the device has already verified the person. That is the usual rule, and the owner confirmed it (decision D20, 2 Nov). A passkey that syncs between devices (most phone passkeys do) is only as safe as the account it syncs through.

### 5.9.3 The Age Pass: proving your age once, for many websites

Every website that uses Dwarpal sends its visitors through a face check. Someone who visits five such websites does five checks: five times the camera, five times the wait. The **Age Pass** (decision D21) lets a person who has passed once keep the result **in their own browser**, and answer the next website's check with it — in a second, with no camera.

The obvious way to build that would be a cookie that says "this browser passed": any website could then ask Dwarpal "have you seen this browser before?", and Dwarpal would become exactly the tracker it promises not to be. The Age Pass is built so that **nobody — not the websites, not Dwarpal — can tell that two visits came from the same person**:

| Property | How |
| :-- | :-- |
| It says only an age line | A pass from an 18+ check states "over 13", "over 16" and "over 18" — no photo, name, birth date or estimate — and each claim stays **hidden** until the holder chooses to show it (*selective disclosure*). An 18+ website sees "over 18", and nothing else |
| A copy is useless | Each pass is **bound to a key** made by the browser, whose private half can't be exported even by the page. Showing a pass means signing the website's fresh challenge with that key |
| Visits can't be linked | Passes come **twenty at a time**, each with its own salts, key and signature, and each is **used once**. Two websites see two passes that share nothing but Dwarpal's name, the day they were issued and their type |
| Dwarpal can't link them either | It records **when** a check gave out passes — never the passes, their keys or their salts. A used pass is remembered only as a hash, until it would expire anyway, so it can't be used twice |
| Websites choose | A website's own policy must say `accept_age_pass`; no preset does. The website needs no other change: it gets the usual signed age token, whose `methods` say `age_pass` |

!!! key "Key idea — selective disclosure with salted hashes"
    The signed pass doesn't contain "age_over_18: true". It contains a **hash** of `[salt, "age_over_18", true]`, where the salt is 16 random bytes. The browser keeps the unhashed version — the *disclosure* — beside the pass. To prove it is over 18, it shows that one disclosure: the website hashes it and finds the hash in the signed pass. The other lines stay hashes, and without their salts nobody can guess them. Decoy hashes make every pass the same size, so even the number of lines is hidden.

The format is the IETF's **SD-JWT VC**: the signed pass, then the disclosures shown, then the holder's **key-binding JWT**, separated by `~`. The key-binding JWT is signed with the pass's key and names the website's nonce, the session, the time, and a hash of everything before it — so a disclosure can't be added, swapped or replayed. Dwarpal publishes where its keys are at `/.well-known/jwt-vc-issuer`, as the standard asks.

!walk services/api/src/dwarpal_api/domain/agepass.py

!walk services/api/src/dwarpal_api/migrations/versions/v0011_age_pass.py

!walk services/api/src/dwarpal_api/app/agepass.py

!walk services/api/tests/age_pass_holder.py

!walk services/api/tests/test_agepass.py

!walk apps/web/lib/age-pass.ts

!walk apps/web/lib/age-pass.test.ts

The tables, the policies (their switch, in the API, the console's editor and its list), the key ring (which now signs two types of token), the session's view and its token's methods, the flow API's three routes and the issuer metadata, the verify page and its words in English and Hindi, the flow and console clients, and the tests changed too; each was re-explained.

!!! honest "Honest limitations"
    - **A shared browser shares its passes.** A child using a parent's browser that holds passes could answer a check with one — as they could use a parent's signed-in shopping account today. A website that needs more simply leaves its policy's switch off.
    - **Passes live where they were saved.** Inside another website's frame, browsers keep a separate storage area for each website, so the verify page offers and saves passes only on its own tab. And a pass saved on one device or browser isn't on another.
    - **"Used once" relies on Valkey** remembering used passes until they expire. If that memory were lost, a holder could show one of their own passes twice — still only their own, and still only for its age line.
    - **The Hindi words are machine-drafted**, like the rest of the Hindi (D2): a native speaker's review is still needed.

### 5.9.4 The render detector's data: made by us, with consent

The fourth stretch item, a detector for **computer-rendered faces** (liveness level 6), needs examples, and none could be found that both shows rendered faces filmed by a camera and may be used in a service. On 2 November the owner chose to **make our own, and ask** (decision D22, [ADR-0021](../../adr/0021-render-detector-data.md)): made-up people rendered in Blender with MakeHuman's CC0 parts, and, for the real side, people who have signed a consent form. Meanwhile, two dataset authors are asked for terms (`docs/data/dataset-requests.md`).

A training set is the one place in Dwarpal where faces are kept, so it has rules the service doesn't need: it lives only on the owner's machine (`.datasets/`, which git ignores), a real person is filed only as `person-NNN` and only under a consent that stands, and withdrawing a consent deletes their clips. The protocol (`docs/data/render-detector-protocol.md`) says what to film; this tool enforces the rules, and films a render on a screen in step with the camera, one camera frame per rendered frame:

!walk ml/src/dwarpal_ml/renders.py

!walk ml/tests/test_renders.py

The detector itself starts from a network the service already trusts: **MiniFASNet V2**, the anti-spoofing network of §5.3, which has learnt what a camera sees of a screen or a print. Its last layer is swapped for one with two answers — *real*, *rendered* — and the whole network is trained further on the clips' face crops. The threshold is chosen on the validation people so that at most 5 % of real faces are called rendered, and the test people then measure the two standard error rates: **APCER** (renders taken for real) and **BPCER** (real people taken for renders). Only a network that passes its release gates can be exported.

!walk ml/src/dwarpal_ml/render_detector.py

!walk ml/src/dwarpal_ml/minifasnet_v2_shapes.json

!walk ml/render_gates.toml

!walk ml/tests/test_render_detector.py

In the service it is **recorded only**, like the screen light (§5.3): the inference service measures it on every face once `DWARPAL_INFERENCE_RENDER_MODEL` names a trained file, the attempt's median is stored with the other liveness evidence, and `liveness-report` summarises it — but no rule reads it until it has been measured on real attempts.

!walk libs/vision/src/dwarpal_vision/render.py

The contracts (`rendered_score` per frame, `rendered` per attempt), the vision package's list, the pipeline, the inference settings and start-up, the liveness report and their tests changed too; each was re-explained. The consent form has a Hindi draft (`docs/data/consent-form.hi.md`), machine-drafted like the rest of the Hindi.

!!! honest "Honest limitation"
    Nothing is filmed or trained yet: the renders need Blender, the MPFB extension and MakeHuman's assets, which wait for the owner's approval to download (D23); the consent form waits for a lawyer's review. The tests prove the machinery on fake pictures (speckle against smooth ramps), not that it can tell a real face from a good render: that needs the real clips. A first set will be small — 40 made-up people, a few cameras and rooms — and a real-time swap of a real person's face isn't covered at all.

