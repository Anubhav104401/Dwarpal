---
fingerprint: 817a8dd419c445e6
---
The demo shop's **settings**, read from environment variables, and a helper that makes an SDK client from them. It follows the same idea as the API's `settings.py` (§5.1.2): every value that may differ between machines lives in the environment, and a missing one stops the shop with a clear message instead of failing later in a confusing way.

@@ 1
The SDK's client class.

@@ 3-5
The shop's age rule, in one place: the UK 18+ preset policy, and the matching age, 18. The doc comment says why: the shop sells alcohol.

@@ 7
**`PROJECT_ID`** — the shape of a project ID as the console shows it: `prj_` and then letters and digits. A **regular expression**: `^` and `$` pin it to the whole text, `[0-9A-Za-z]+` means one or more letters or digits. Added on 11 Nov 2026 (§6.14).

@@ 9-16
**`ShopConfig`** — the six settings, each as text: the API's address and issuer name, the API key, the project ID, the shop's own address, and the secret for its cookie.

@@ 18-19
**`shopConfig`** — read the settings. Its one parameter has a default: the real environment, `process.env`. A test could pass a made-up environment instead. `NodeJS.ProcessEnv` is Node.js's type for it: names mapped to text, or nothing.

@@ 20
The API's address, or the local default.

@@ 21-28
Build the settings: each from its variable, with a default where a safe one exists (the issuer defaults to the API's address). The key, project and secret have no safe default, so they fall back to empty text — caught just below. The shop's address loses any trailing slash.

@@ 29-35
List what's missing: each line gives a variable's name if its value is empty (or, for the secret, shorter than 32 characters), or `null` if it's fine. `.filter((name) => name !== null)` keeps only the names — and TypeScript understands that the result is a list of text, with the `null`s gone.

The project ID must also have the right **form**. The database keeps the same ID as a UUID (`01a1c66b-…`), but pass tokens name their audience in the console's `prj_…` form, and the shop refuses a token whose audience isn't its own. On launch night the UUID went into the server's settings: every check passed, and every visitor was then turned away at the door (§6.14). Now the shop refuses to start with it — the home page reads these settings, so its health check fails and a deploy stops — instead of failing for each customer.

@@ 36-38
Anything missing? Stop, naming every missing setting at once — not one per restart.

@@ 39-40
All present: return the settings.

@@ 42-44
**`dwarpal`** — a new SDK client with the shop's key and the API's address. It is cheap to make, so the shop simply makes one where it needs one.
