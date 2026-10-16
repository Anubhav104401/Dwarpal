---
fingerprint: f3e51c2c38c2f863
---
The SDK's **front door** — the file that `package.json`'s `exports` points to (after building, as `dist/index.js`). It contains no code of its own: it gathers the public parts of the other files, so a website writes one import:

```ts
import { DwarpalClient, verifyAgeToken } from "@dwarpal/node";
```

Anything *not* listed here stays private to the SDK, such as the helper functions inside `client.ts`. This is the same idea as the Python packages' `__init__.py` files (§5.1.1).

@@ 1-9
From `client.ts`: the `DwarpalClient` class, and the **types** that describe its inputs and outputs. The word `type` in front of a name says "this is only a type": it exists while TypeScript checks the code, and disappears completely from the JavaScript that runs. The project's settings (`verbatimModuleSyntax`) require that word, so it is always clear which imports cost nothing at run time.

The `.js` ending in `"./client.js"` looks odd in a TypeScript file, but it names the file *as Node.js will see it* after building (see `tsconfig.json`).

@@ 10
From `errors.ts`: both error classes. They are real values (classes), so they have no `type` in front.

@@ 11-18
From `token.ts`: the verification function, the two constants it checks against (`ALGORITHM`, `TOKEN_TYPE`), and its types.
