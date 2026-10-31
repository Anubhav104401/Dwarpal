# @dwarpal/js

Dwarpal's browser SDK: open the age check in a modal over your page, or by redirect.

```ts
import { openAgeCheck } from "@dwarpal/js";

openAgeCheck(sessionUrl); // the verify link your server got from createSession
```

It holds no keys and sees no results: your server creates the session and verifies the age token. See the [browser SDK guide](../../docs/developers/browser-sdk.md) and [Integrating Dwarpal](../../docs/developers/README.md).
