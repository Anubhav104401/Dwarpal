---
fingerprint: 406630cc09e258bd
---
Two public addresses under `/.well-known/` — a path prefix reserved by an Internet standard (RFC 8615) for information about a site, at places everyone can predict:

| Address | What it holds |
| :-- | :-- |
| `/.well-known/jwks.json` | the **public keys** that check age-token signatures (§4.12) |
| `/.well-known/dwarpal-configuration` | a description of this issuer: its name, where its keys are, which algorithm and token type it uses, which policies exist, and which age model is active |

Neither needs a key: public keys are *meant* to be public. A website's SDK fetches the key set, keeps a copy for a few minutes, and from then on checks every token offline, without calling the API at all.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated` and `Any`.

@@ 7
The router, `Depends`, and `Response` (used to set a header).

@@ 9-12
The algorithm name and token type (`signing.py`), the toolbox, the list of preset policies, and the toolbox dependency.

@@ 14
The router: every path here starts with `/.well-known`.

@@ 17
`GET /.well-known/jwks.json`.

@@ 18
The `response` parameter lets the endpoint add headers to the response FastAPI will send.

@@ 19
`Cache-Control: public, max-age=300` — anyone (`public`), including shared caches, may keep a copy of this answer for 300 seconds (5 minutes). Websites then fetch the keys at most every few minutes, not once per token. And when a token names a key (`kid`) that a website's copy doesn't contain yet — right after a new key was created — a good verifier simply fetches the set again. Our SDK does exactly that, so a new key never causes failed checks.

@@ 20
Answer with the key set.

@@ 23-24
`GET /.well-known/dwarpal-configuration` — the **discovery document**. A program can learn everything it needs to verify our tokens from this one address. The idea is borrowed from OpenID Connect, which publishes the same kind of document for logins.

@@ 25
The issuer's own address, from the settings.

@@ 26-34
The document:

- `issuer` — exactly what tokens carry in their `iss` claim;
- `jwks_uri` — where the public keys are;
- `token_type` — the `typ` every age token has in its header;
- `token_signing_algorithms` — `["Ed25519"]`, the only algorithm a verifier should accept;
- `policies` — the names of the preset policies, sorted;
- `age_model` and `age_model_calibrated` — which age model decides, and whether it is calibrated. Anyone integrating can see at a glance that, today, only test sessions are possible.
