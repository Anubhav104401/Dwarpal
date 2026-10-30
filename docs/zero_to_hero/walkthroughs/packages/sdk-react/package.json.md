---
fingerprint: 879c10064164cf96
---
The package description of **`@dwarpal/react`**: the browser SDK as **React** pieces — a button, and a *hook* for websites built with React, as the design asks (`<VerifyAgeButton/>`, `useDwarpal()`). Its lines follow `@dwarpal/js`'s; the differences are its dependencies.

@@ 1-6
The opening brace; name, version and description; never published by accident; ES modules.

@@ 7-15
The package itself as its only export, built into `dist/`, the only folder that would be packed.

@@ 16-20
Build, check and test, as in the other SDKs.

@@ 21-23
**`dependencies`** — the browser SDK, from this repository: the React pieces only wrap it.

@@ 24-26
**`peerDependencies`** — React 19 or newer, but *the website's own copy*. A website's page must have exactly one React; a component library that brought its own would load a second, and React's hooks break when two copies meet. So the package only says which versions it works with.

@@ 27-35
For development: the shared settings; React's and React DOM's type descriptions; React and React DOM themselves (the same 19.3.0 as the apps — the tests need a React to run, and `react-dom` draws a component as HTML); the compiler and the test runner.

@@ 36
The closing brace.
