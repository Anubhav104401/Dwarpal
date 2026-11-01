## 5.9 Phase 9 — beyond the plan

Phases 0–8 are the plan. Phase 9 is what comes after, chosen from the roadmap's list (§3.9) once the rest stands:

| Item | What | Status |
| :-- | :-- | :-- |
| Python SDK | The Node SDK's calls, for Python websites | 🟢 §5.9.1 |
| Passkeys | Console sign-in without passwords | 🗓 |
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
