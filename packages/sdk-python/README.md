# Dwarpal for Python

For a website's server: create an age check, send the person to it, and check the signed answer that comes back.
The same steps as the Node.js SDK (`@dwarpal/node`), in Python 3.11 and later.

```python
from dwarpal import Client, verify_age_token

dwarpal = Client("dk_test_…", base_url="https://api.dwarpal.example")  # your secret key: server only

# 1. Create a session, and send the person to its link.
session = dwarpal.create_session(policy="uk_osa_18", return_url="https://shop.example/age-check/complete")
redirect_to(session.url)  # the link carries a one-time secret: never log it

# 2. When they come back (?session_id=vs_…), read the result…
result = dwarpal.retrieve_session(session_id)

# 3. …and check its signed token yourself, before letting them in.
verdict = verify_age_token(
    result.age_token,
    issuer="https://api.dwarpal.example",  # as in /.well-known/openid-configuration
    audience="prj_…",                       # your project's ID
    min_age=18,
    session_id=session_id,
)
if verdict.allowed:
    ...
```

For `async` code, `AsyncClient` has the same methods (`await dwarpal.create_session(…)`).

To retry a `create_session` whose answer was lost — a timeout, a dropped connection — pass the same
`idempotency_key` both times: Dwarpal answers the repeat with the first session instead of making a second one.
Make the key random and new for each session (`secrets.token_urlsafe(16)`), never an order number or anything
another request could share — see *Retrying safely* in the [developers guide](../../docs/developers/README.md).

**Webhooks** — check each one before acting on it, with the body exactly as it arrived:

```python
from dwarpal import verify_webhook

event = verify_webhook(request.body, request.headers.get("Dwarpal-Signature"), webhook_secret)
```

Errors are exceptions to catch: `DwarpalApiError` (the API refused; `.code` is stable), `AgeTokenError` and
`WebhookSignatureError`. The developer guides in `docs/developers/` explain the whole flow.
