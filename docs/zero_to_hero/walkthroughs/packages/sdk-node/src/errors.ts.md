---
fingerprint: 8a41486bbada58bc
---
The SDK's two kinds of error. A website's code can tell them apart with `instanceof`, and react differently: an `AgeTokenError` means "don't let this person in"; a `DwarpalApiError` carries the API's own explanation.

This is the first TypeScript file in the book walked through line by line; §4.15 explains the language.

@@ 1
A **doc comment**: `/** … */` just before something describes it. Editors show it when you hover over a use of `DwarpalApiError`. It says that `code` is for programs and `message` for people — the same split as the API's problem details (§4.13).

@@ 2
`export class DwarpalApiError extends Error` — a **class** (a blueprint for objects) that **extends** JavaScript's built-in `Error`: it is an error in every way, plus what's added below. `export` makes it importable from other files.

@@ 3
`override readonly name = "DwarpalApiError"` — every error has a `name`, shown in error messages and logs. `override` says on purpose: "I am replacing the `name` that `Error` already has" — with the project's strict settings, TypeScript insists on that word, so a replacement can never happen by accident. `readonly` means it can't be changed after the object is made.

@@ 4-6
Three more **fields**, each with its type:

- `status` — the HTTP status code, a `number`;
- `code` — the API's stable code, a `string`;
- `requestId` — the request's ID from the `X-Request-Id` header, or `null` if there wasn't one. `string | null` reads "a string or null".

@@ 8
The **constructor** — the function that runs when a new error is made with `new DwarpalApiError(…)`. It takes the four values, each with its type.

@@ 9
`super(message)` — first run `Error`'s own constructor, which stores the human message. A class that extends another must call `super` before using `this`.

@@ 10-12
Store the other three values on the new object. `this` means "the object being made".

@@ 13-14
The closing braces of the constructor and the class.

@@ 16
The doc comment for the second error: an age token that failed any check.

@@ 17-19
`AgeTokenError` needs nothing beyond its own name: the message says what went wrong, and `cause` (set where it is thrown, in `token.ts`) holds the original error from jose, for debugging.
