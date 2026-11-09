---
fingerprint: 62fb7330c9c6382c
---
The most important file of the SDK: **`verifyAgeToken`**, the function a website calls before letting anyone in. It answers one question — *does this token prove that this visitor passed my age check?* — and it answers "yes" only when every one of these is true:

| Check | Why |
| :-- | :-- |
| the signature is valid, made by one of the API's published keys | nobody else can make a token |
| the algorithm is exactly Ed25519 | no algorithm tricks (§4.12) |
| the token's type is `dwarpal-age+jwt` | no other kind of token can be passed off as an age token |
| it was issued by the expected API (`iss`) | tokens from another issuer are refused |
| it is addressed to *this* website (`aud`) | a token stolen from another website is useless here |
| it hasn't expired (`exp`), and is already valid (`nbf`) | old tokens can't be replayed for ever |
| it describes the session this visitor just finished (`sid`) | a token from someone else's session can't be swapped in |
| the outcome is `pass` **and** `age_over_<the site's age>` is literally `true` | the answer is unmistakable, and only for the age the site asked about (ADR-0020) |

Any failed check throws an `AgeTokenError`. A website's code should treat *any* error from this function as "no entry".

@@ 1
From **jose**:

- `jwtVerify` — checks a JWT's signature and standard claims;
- `createRemoteJWKSet` — fetches a key set from an address, and keeps it;
- `errors` — jose's error classes;
- `JWTPayload` and `JWTVerifyGetKey` — types: a token's claims, and "something that finds the right key for a token".

@@ 3
Our own error class.

@@ 5-6
`ALGORITHM` — the one allowed algorithm, as a constant that both the code and its readers can refer to. The doc comment says the rule.

@@ 7-8
`TOKEN_TYPE` — the type every age token declares in its header.

@@ 10
`Outcome` — a **union type** of three exact strings (§4.15): a variable of this type can only ever hold `"pass"`, `"fail"` or `"reject"`. TypeScript reports any other value as an error before the code ever runs.

@@ 12
`interface VerifyAgeTokenOptions` — the shape of the second argument. An **interface** describes an object: which properties it has, and their types.

@@ 13-14
`issuer` — the API's address, exactly as its discovery document states it.

@@ 15-16
`audience` — the website's own project ID.

@@ 17-18
`minAge` — the age *the website* requires. The token must speak about exactly this age.

@@ 19-20
`sessionId?` — the `?` makes it **optional**. Passing it is strongly recommended: the website knows which session the visitor just came back from (from `?session_id=` in the address), and the token must be about that one.

@@ 21-22
`keys?` — optional too: where to get public keys. Normal use leaves it out, and the keys are fetched from the issuer. Tests pass keys of their own.

@@ 23
The interface ends.

@@ 25-33
`interface AgeVerdict` — what the function returns. Most important is `allowed`: **the only field a website needs for its decision**. The others are for its records: the outcome, the session, the policy, whether it was a live check, and when the token expires — as a `Date` object.

@@ 52
**`verifiedClaims`** — check the token, and return its claims, or throw. `async` means it returns a **Promise** (§4.15): a value that arrives later, here once the keys are fetched and the signature checked.

@@ 53-54
`await jwtVerify(…)` — wait for jose's verdict. The keys: the ones passed in, or (`??` means "if that is missing, use this") the issuer's published ones (`remoteKeys(issuer)`). `const { payload } = …` takes just the `payload` property out of the result — this is called **destructuring**.

@@ 55-59
The rules jose must enforce, in addition to the signature:

- `issuer` and `audience` — the `iss` and `aud` claims must match exactly;
- `algorithms: [ALGORITHM]` — the **allow-list**: only Ed25519;
- `typ: TOKEN_TYPE` — the header's type must match;
- `requiredClaims` — these claims must be present at all. A token missing its expiry, its ID, its session or its outcome is refused outright, rather than read with gaps.

jose also checks `exp` (not expired) and `nbf` (not too early) automatically.

@@ 60-61
The checks passed: return the claims.

@@ 62-65
If jose refused the token, throw our own `AgeTokenError` instead. The message includes jose's short error code — such as `ERR_JWT_EXPIRED` — and `{ cause: error }` keeps jose's full error attached, for whoever is debugging.

@@ 66
Any *other* error — say, the network failed while fetching keys — is passed on unchanged. It is still an error, so the visitor still isn't let in.

@@ 67-68
The closing braces.

@@ 70-71
**`verifyAgeToken`** — the public function. It returns a `Promise<AgeVerdict>`: a verdict, once the checks are done.

@@ 72-74
First check the website's own input: `minAge` must be a whole number of at least 1. A typo such as `18.5` throws a `RangeError` at once, instead of quietly never matching any token.

@@ 75
Verify the token, and get its claims.

@@ 76
Take three claims out by destructuring: `outcome`, `sid` (the session) and `exp` (the expiry).

@@ 77-79
The outcome must be one of the three known values. jose only knows standard claims; this one is ours, so we check it ourselves.

@@ 80-82
The session must be text — and, if the website said which session it expects, exactly that one.

@@ 83-84
**The verdict.** `allowed` is true only if the outcome is `pass` **and** the claim named after the website's age — built by a template literal, such as `age_over_18` — is exactly `true`. `===` means "exactly equal, with no conversion": the text `"true"` or the number `1` would not count.

@@ 85-90
The record-keeping fields. `typeof claims.policy === "string" ? … : ""` is the **conditional operator** (`condition ? if-true : if-false`): use the policy if it is text, otherwise empty text. Token times are seconds since 1970, while JavaScript's `Date` counts milliseconds — hence `* 1000`.

@@ 91
The closing brace.

@@ 35
`keySets` — a **Map** (a dictionary that can hold any kind of key) from an API's address to its key fetcher. It lives as long as the website's server process, so the keys are fetched once and kept.

@@ 37-41
**`remoteKeys`** (exported since 9 Nov) — the comment says it: the public keys of the API at an address, fetched when first needed, kept, and fetched again for a key not seen yet. A token's keys come from its issuer by default; a server that reaches Dwarpal by another address — over a private network — passes these instead.

@@ 42-44
The address without any slash at its end (`replace(/\/+$/, "")`), so `http://api:8000/` and `http://api:8000` share one fetcher; then look in the map.

@@ 49-50
Return the fetcher.

@@ 45-48
Nothing for this address yet: create a fetcher for `<address>/.well-known/jwks.json` (jose's `createRemoteJWKSet`, which fetches and caches the key set) and remember it.
