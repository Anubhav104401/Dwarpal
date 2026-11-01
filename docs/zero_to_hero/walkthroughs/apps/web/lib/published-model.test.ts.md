---
fingerprint: 5c68a1d0a93df32c
---
Tests of `lib/published-model.ts`.

@@ 1-3
Vitest's tools, and the two functions under test.

@@ 5-19
A made-up answer in the API's shape: an 18+ line with bounds and a band of adults, and a 13+ line never measured.

@@ 21
The group.

@@ 22-33
**Reading**: the dataset, the measured line in camelCase, and the unmeasured line with no bounds and no bands.

@@ 35-38
**Refusing**: nothing, or something without a version, is not a model.

@@ 40-46
**Asking**: a stand-in for `fetch` that notes the address it was asked and answers with a chosen status.

@@ 47-49
It asks `/v1/model` at the API's address and reads the answer; a failing status means no figures.

@@ 50-53
And an API that can't be reached means no figures, not an error.

@@ 54-55
The end.
