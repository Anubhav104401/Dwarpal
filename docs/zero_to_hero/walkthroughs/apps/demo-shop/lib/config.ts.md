---
fingerprint: ee63651dfaf7b942
---
The demo shop's **settings**, read from environment variables, and a helper that makes an SDK client from them. It follows the same idea as the API's `settings.py` (§5.1.2): every value that may differ between machines lives in the environment, and a missing one stops the shop with a clear message instead of failing later in a confusing way.

@@ 1
The SDK's client class.

@@ 3-7
The shop's age rule, in one place: the UK 18+ preset policy, and the matching age, 18. The doc comment says why: the shop sells alcohol. Since 13 Nov the preset is only the **default**: the setting `DWARPAL_POLICY` can name another policy of the shop's project. The comment says when that is needed — an age model with no pass marks for the presets' 2 % risk budget, which makes the API refuse every preset (§6.19).

@@ 9
**`PROJECT_ID`** — the shape of a project ID as the console shows it: `prj_` and then letters and digits. A **regular expression**: `^` and `$` pin it to the whole text, `[0-9A-Za-z]+` means one or more letters or digits. Added on 11 Nov 2026 (§6.14).

@@ 10
`POLICY_NAME` — the shape of a policy's name, the same rule the API applies: 3 to 40 lower-case letters, digits or underscores.

@@ 12-20
**`ShopConfig`** — the six settings, each as text: the API's address and issuer name, the API key, the project ID, the shop's own address, and the secret for its cookie. Since 13 Nov a seventh: the name of the policy its checks follow.

@@ 22-23
**`shopConfig`** — read the settings. Its one parameter has a default: the real environment, `process.env`. A test could pass a made-up environment instead. `NodeJS.ProcessEnv` is Node.js's type for it: names mapped to text, or nothing.

@@ 24
The API's address, or the local default.

@@ 25-34
Build the settings: each from its variable, with a default where a safe one exists (the issuer defaults to the API's address). The key, project and secret have no safe default, so they fall back to empty text — caught just below. The shop's address loses any trailing slash. Since 13 Nov also the policy: `DWARPAL_POLICY`, or the preset. Here `||` is used and not `??`, and the comment says why: `??` falls back only when a setting is *absent*, but Docker Compose passes an unset setting on as an **empty** one, and `||` falls back for empty text too.

@@ 35-44
List what's missing: each line gives a variable's name if its value is empty (or, for the secret, shorter than 32 characters), or `null` if it's fine. `.filter((name) => name !== null)` keeps only the names — and TypeScript understands that the result is a list of text, with the `null`s gone.

The project ID must also have the right **form**. The database keeps the same ID as a UUID (`01a1c66b-…`), but pass tokens name their audience in the console's `prj_…` form, and the shop refuses a token whose audience isn't its own. On launch night the UUID went into the server's settings: every check passed, and every visitor was then turned away at the door (§6.14). Now the shop refuses to start with it — the home page reads these settings, so its health check fails and a deploy stops — instead of failing for each customer. Since 13 Nov a policy name of the wrong shape is listed too, so a typing mistake stops the shop at start-up, not at the first visitor.

@@ 45-47
Anything missing? Stop, naming every missing setting at once — not one per restart.

@@ 48-49
All present: return the settings.

@@ 51-53
**`dwarpal`** — a new SDK client with the shop's key and the API's address. It is cheap to make, so the shop simply makes one where it needs one.
