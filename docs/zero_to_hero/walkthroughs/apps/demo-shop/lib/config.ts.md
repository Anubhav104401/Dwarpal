---
fingerprint: 9ae96a7c9cbdcfe5
---
The demo shop's **settings**, read from environment variables, and a helper that makes an SDK client from them. It follows the same idea as the API's `settings.py` (§5.1.2): every value that may differ between machines lives in the environment, and a missing one stops the shop with a clear message instead of failing later in a confusing way.

@@ 1
The SDK's client class.

@@ 3-5
The shop's age rule, in one place: the UK 18+ preset policy, and the matching age, 18. The doc comment says why: the shop sells alcohol.

@@ 7-14
**`ShopConfig`** — the six settings, each as text: the API's address and issuer name, the API key, the project ID, the shop's own address, and the secret for its cookie.

@@ 16-17
**`shopConfig`** — read the settings. Its one parameter has a default: the real environment, `process.env`. A test could pass a made-up environment instead. `NodeJS.ProcessEnv` is Node.js's type for it: names mapped to text, or nothing.

@@ 18
The API's address, or the local default.

@@ 19-26
Build the settings: each from its variable, with a default where a safe one exists (the issuer defaults to the API's address). The key, project and secret have no safe default, so they fall back to empty text — caught just below. The shop's address loses any trailing slash.

@@ 27-31
List what's missing: each line gives a variable's name if its value is empty (or, for the secret, shorter than 32 characters), or `null` if it's fine. `.filter((name) => name !== null)` keeps only the names — and TypeScript understands that the result is a list of text, with the `null`s gone.

@@ 32-34
Anything missing? Stop, naming every missing setting at once — not one per restart.

@@ 35-36
All present: return the settings.

@@ 38-40
**`dwarpal`** — a new SDK client with the shop's key and the API's address. It is cheap to make, so the shop simply makes one where it needs one.
