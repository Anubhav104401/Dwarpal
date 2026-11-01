# Age Pass — design (Phase 9, FR-17)

**Status:** design for review; nothing built yet. Decision D21 in `docs/reports/pending-decisions.md` asks the owner to approve it before it is built.

## 1. The problem it solves

Today a person proves their age **once per website**: every shop that uses Dwarpal sends them through a face check. That is tiring, and each check is another moment a camera is on. An **Age Pass** lets a person who has passed once carry the result with them, so the next website can accept it in a second — without the camera, and **without Dwarpal or the websites being able to follow the person from site to site**.

## 2. What it is

A small signed credential, kept **in the person's own browser**, that says only "over 18" (or another age line), signed by Dwarpal. It follows two open standards:

| Standard | What it gives |
| :-- | :-- |
| **SD-JWT VC** (IETF, *SD-JWT-based Verifiable Credentials*) | The credential's format: a signed token whose claims are hidden until the holder chooses to show them (*selective disclosure*) |
| **Key binding** (part of SD-JWT) | The pass is tied to a key made by the person's browser; showing it needs a fresh signature from that key, so a copied pass is useless |

Nothing in it names the person: no face, no birth date, no estimated age — only the age lines passed (`age_over_18: true`, `age_over_16: true`), when it was issued (rounded to the day), and when it expires.

## 3. How it works

```text
 First check (website A)                         Later visits (websites B, C, …)
 ───────────────────────                         ───────────────────────────────
 face check passes                               website asks for proof of 18+
   │                                               │
   ▼                                               ▼
 browser makes a key pair  ──►  Dwarpal issues   browser picks one unused pass,
 (private key stays in the      a BATCH of N     discloses only age_over_18,
 browser, never sent)           passes, each     signs the website's fresh
                                bound to its     challenge with the bound key
                                own key          │
                                                 ▼
                                               Dwarpal checks it (or the website
                                               does, with Dwarpal's public keys)
                                               and the pass is used up
```

### Unlinkability: why a batch

If the same pass were shown everywhere, its signature would be the same everywhere, and two websites comparing notes could tell it was the same person. So Dwarpal issues a **batch** (say 20) of passes at once, each with its own random salts, its own key binding and its own signature, and the browser uses **each pass once**. Two websites see two passes that share nothing. When the batch runs low, the browser asks for a fresh batch — which needs a fresh face check only after the pass's lifetime ends.

Dwarpal must also not be able to link them: it keeps **no record of which passes it issued to whom** — only a count, for abuse limits. When a website asks Dwarpal to check a pass, Dwarpal sees a pass it can't connect to the first check.

### Lifetime

A pass lasts **90 days** (to be decided: D21). Age only ever goes up, so "over 18" stays true; the limit bounds the damage of a stolen browser profile and makes the model's improvements reach everyone in time.

## 4. Threats and answers

| Threat | Answer |
| :-- | :-- |
| A pass copied out of the browser and used elsewhere | Key binding: showing a pass needs a signature from the browser's private key, made non-extractable with WebCrypto |
| A child using a parent's browser that holds a pass | The same as a parent's logged-in shopping account today. Websites that need more set a policy that refuses passes (`accept_age_pass: false`), forcing a fresh face check |
| Websites linking visits | One pass per showing; salts and keys differ; issue time rounded to the day |
| Dwarpal linking visits | No issue log tied to people; the batch's passes share nothing Dwarpal keeps |
| A replayed showing | The website's challenge (`nonce`) and audience are inside the key-binding signature, and each pass is accepted once |
| A forged pass | Ed25519 signature with Dwarpal's published keys, as age tokens today |

## 5. What gets built

1. **Issuing** — after a passing face check, an endpoint `POST /v1/flow/sessions/{id}/age-pass` takes N public keys from the browser and returns N SD-JWT VCs. Only when the website's policy allows passes, and only for live, completed, passing sessions.
2. **Keeping** — the verify page stores the batch in the browser's IndexedDB, with private keys made non-extractable.
3. **Showing** — on a later check, before the camera starts, the verify page offers "Use your Age Pass"; with the person's consent it presents one pass to `POST /v1/flow/sessions/{id}/age-pass/present`. Dwarpal checks the pass and the key binding and completes the session with the usual signed age token — so **websites need no changes at all**.
4. **Policy** — a new policy field, `accept_age_pass` (default **off** until D21 is decided).
5. **Tests** — the format against the SD-JWT specification's own examples; unlinkability (two showings share no bytes but the issuer's key ID); replay; tampering.

Nothing new needs downloading: SD-JWT is plain JSON, base64url and SHA-256 with the libraries already used (`joserfc`, `cryptography`, and the browser's WebCrypto).

## 6. Open questions for the owner (D21)

1. Build it now, or after launch?
2. Pass lifetime: 90 days (suggested), 30, or 365?
3. Batch size: 20 (suggested)?
4. Default for new policies: passes **off** (suggested — websites opt in) or on?
