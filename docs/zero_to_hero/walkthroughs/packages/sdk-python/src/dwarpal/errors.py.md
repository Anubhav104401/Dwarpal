---
fingerprint: 07b33393e3378905
---
The SDK's **exceptions** (§5.9.1), one per kind of failure, so a website can catch exactly the one it handles.

@@ 1
The module's docstring.

@@ 3
The project-wide type-hint setting.

@@ 6-13
**`DwarpalApiError`** — the API refused: the HTTP status, a stable `code` for programs (such as `policy_not_supported`), a message for people, and the request's ID, to quote when asking for help.

@@ 16-17
**`AgeTokenError`** — an age token failed a check.

@@ 20-21
**`WebhookSignatureError`** — a webhook failed its signature check.
