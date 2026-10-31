# @dwarpal/react

Dwarpal for React 19: a button that opens the age check, and a hook to open it yourself. Built on [`@dwarpal/js`](../sdk-js).

```tsx
import { VerifyAgeButton } from "@dwarpal/react";

<VerifyAgeButton createSession={createAgeCheck}>Verify my age</VerifyAgeButton>;
```

`createAgeCheck` asks your server for a new session and returns its `url`. See the [browser SDK guide](../../docs/developers/browser-sdk.md).
