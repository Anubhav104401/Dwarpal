---
fingerprint: 15276bf3494f75cd
---
The browser SDK's **front door**: it gathers the public parts of the other files, so a website writes one import — `import { openAgeCheck } from "@dwarpal/js"`. As in `@dwarpal/node`'s, `type` marks the names that are only types.

@@ 1
From `link.ts`: the link check, the origin check and the checked link's type.

@@ 2
From `open.ts`: `openAgeCheck` and the types of its options and result.

@@ 3-10
From `protocol.ts`: the message types, the sender's name, the reader and the session ID's shape — exported so the verify page uses exactly the same ones.
