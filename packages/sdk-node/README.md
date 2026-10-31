# @dwarpal/node

Dwarpal's server SDK for Node.js 24: create age-verification sessions, read their results, and verify the signed age tokens and webhooks.

```ts
import { DwarpalClient, verifyAgeToken } from "@dwarpal/node";

const dwarpal = new DwarpalClient({ apiKey: process.env.DWARPAL_API_KEY!, baseUrl: "https://api.dwarpal.example" });
const session = await dwarpal.createSession({ policy: "uk_osa_18", returnUrl: "https://shop.example/age-check/complete" });
```

Keep the API key on your server. See the [Node.js SDK guide](../../docs/developers/node-sdk.md) and [Integrating Dwarpal](../../docs/developers/README.md).
