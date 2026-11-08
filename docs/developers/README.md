# Integrating Dwarpal

Dwarpal answers one question for your website: **is this live person over N?** The answer comes back as a **signed age token** that your server checks with Dwarpal's public keys. You never see a face, an estimated age or an identity — only "old enough" or not.

This guide gets an age check working on your website. The [demo shop](../../apps/demo-shop) is a complete, tested example of everything below.

| Guide | What it covers |
| :-- | :-- |
| This page | how an age check works, and a quick start |
| [Browser SDKs](browser-sdk.md) | `@dwarpal/js` and `@dwarpal/react`: opening the check on your page |
| [Node.js SDK](node-sdk.md) | `@dwarpal/node`: sessions, token verification, webhooks |
| [Integration checklist](integration-checklist.md) | what to check before you go live |
| [API reference](../api/openapi.json) | every endpoint, as an OpenAPI 3.1 document |

> **Status.** Dwarpal is in development and not yet hosted anywhere. The SDKs are not published to a package registry: inside this repository they are used as workspace packages (`workspace:*`); outside it, install them from the repository, as below. They will be published at launch (decided 2 Nov 2026).

## Installing the SDKs before they are published

Pin a commit, so what you install can't change under you.

**Python** — pip builds the package straight from its folder in the repository:

```
pip install "dwarpal @ git+https://github.com/Anubhav104401/Dwarpal@<commit>#subdirectory=packages/sdk-python"
```

**JavaScript** (`@dwarpal/node`, `@dwarpal/js`, `@dwarpal/react`) — build a package file from a checkout, and install
that file:

```
git clone https://github.com/Anubhav104401/Dwarpal && cd Dwarpal && git checkout <commit>
pnpm install && pnpm --filter @dwarpal/node build && pnpm --filter @dwarpal/node pack
npm install /path/to/Dwarpal/packages/sdk-node/dwarpal-node-0.1.0.tgz   # in your own project
```

`@dwarpal/react` needs `@dwarpal/js`: pack and install both.

## How an age check works

```
 your server                 your page                    Dwarpal
 ───────────                 ─────────                    ───────
 1. create a session ───────────────────────────────────► API  (secret key)
    ◄──────────────── session id + verify link ─────────
 2. hand the link ─────────► 3. open the check ─────────► verify page, in a modal
    to your page                                          (camera, liveness, age)
                             4. "finished" ◄──────────── verify page
                                go to your return address
 5. your return route ──────────────────────────────────► API: the session's result
    ◄──────────────── status, outcome, age token ───────
 6. verify the token (Dwarpal's public keys) → let the person in, or not
```

1. **Your server creates a session** with your secret API key, naming a **policy** (which age, which rules) and a **return address** on your website.
2. It hands the session's **verify link** to your page. The link carries a one-time secret in its `#fragment`; never log it or store it.
3. **Your page opens the check** with the browser SDK: by default in a modal over your page, or by sending the whole page to it.
4. When the person finishes, the verify page tells your page, which goes to your return address with `?session_id=vs_…`.
5. **Your return route asks Dwarpal for the result**, again with your secret key.
6. **It verifies the age token** — its signature, issuer, audience, expiry and age claim — and only then lets the person in.

Never trust anything the browser tells you about the result: the return address, a callback, a query string. Only a token your server has verified proves an age check passed.

## Quick start

You need a Dwarpal project, its **project ID** (`prj_…`) and a **test key** (`dk_test_…`), created in the console. Test keys only ever see test sessions, and no real person's check counts in test mode.

### 1. Create a session on your server

```ts
import { DwarpalClient } from "@dwarpal/node";

const dwarpal = new DwarpalClient({
  apiKey: process.env.DWARPAL_API_KEY!, // dk_test_… — on your server only, never in a browser
  baseUrl: "https://api.dwarpal.example",
});

export async function createAgeCheck(): Promise<string> {
  const session = await dwarpal.createSession({
    policy: "uk_osa_18",
    returnUrl: "https://shop.example/age-check/complete",
  });
  // Remember which session this browser started (an HttpOnly cookie), so a return link
  // can't be finished in another browser — see the integration checklist.
  return session.url;
}
```

The return address must be on one of your project's **allowed origins**, set in the console.

### 2. Open the check on your page

With React:

```tsx
import { VerifyAgeButton } from "@dwarpal/react";

<VerifyAgeButton createSession={createAgeCheck}>Verify my age</VerifyAgeButton>;
```

Without React:

```ts
import { openAgeCheck } from "@dwarpal/js";

button.addEventListener("click", async () => {
  const url = await fetch("/api/age-check", { method: "POST" }).then((answer) => answer.text());
  openAgeCheck(url);
});
```

### 3. Check the result on your return route

```ts
import { verifyAgeToken } from "@dwarpal/node";

const sessionId = new URL(request.url).searchParams.get("session_id") ?? "";
// …check sessionId is the one this browser started…
const session = await dwarpal.retrieveSession(sessionId);
if (session.status !== "completed" || session.ageToken === null) {
  // not finished, or sent to a stronger check: don't let them in
}
const verdict = await verifyAgeToken(session.ageToken!, {
  issuer: "https://api.dwarpal.example",
  audience: process.env.DWARPAL_PROJECT_ID!, // prj_…
  minAge: 18,
  sessionId,
});
if (verdict.allowed) {
  // let the person in — and remember it in your own session, briefly
}
```

## Policies

A policy names the age to check and the rules to follow. The presets:

| Policy | Age | For |
| :-- | :-: | :-- |
| `uk_osa_18` | 18 | UK Online Safety Act (the default) |
| `eu_dsa_18` | 18 | EU Digital Services Act |
| `in_dpdp_18` | 18 | India's DPDP Rules |
| `au_smma_16` | 16 | Australia's social-media minimum age |
| `us_21` | 21 | US alcohol and similar |
| `teen_13` | 13 | services for teenagers |

Each preset has a **risk budget** of 2 %: the share of minors just under the age line that the age model may let through. A model is allowed to decide live checks for a policy only once it is shown to meet that budget. Your project can add its own versions in the console's policy editor; a session keeps the version it started with.

## Live checks today: an ID document

No age model is yet certified for live checks, so **a live check is decided by an ID document** (decision D24): the person photographs their passport's photo page (or an ID card with a machine-readable zone) and takes a short selfie, turning their head as asked. Dwarpal reads the date of birth from the document, checks the selfie is a live person, and matches it to the document's photo. Nothing changes for your integration — you create sessions and verify tokens exactly as below — but:

- the verify page opens on the document check instead of the camera's age estimate;
- the token's `methods` claim is `["document_mrz", "face_match"]`, and its `model` claim is `null` (no age model decided);
- an Age Pass, where your policy accepts them, still answers the check in place of the document;
- `GET /.well-known/dwarpal-configuration` says `"live_checks": "document"` now, and `"face_estimation"` once a model is certified.

Test sessions are unchanged: the face check's age estimate decides them, so you can try every outcome with a test key.

## Outcomes

| Session status | Outcome | What it means | What to do |
| :-- | :-- | :-- | :-- |
| `completed` | `pass` | old enough | verify the token, then let them in |
| `completed` | `fail` | not shown to be old enough | refuse, kindly |
| `completed` | `reject` | the check couldn't be trusted (a likely spoof) | refuse; don't say why |
| `awaiting_step_up` | `step_up` | photos were too close to call | nothing: the verify page offers the document check, and the session completes when it is done |
| `expired` | — | not finished within 30 minutes | start a new check |

`fail` and `reject` tokens are signed too, with `age_over_18: false` (or your policy's age): they prove a check happened without letting anyone in.
