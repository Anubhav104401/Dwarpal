---
fingerprint: a4d0e03ec573b720
---
The tests for the palette's search (`places.ts`).

@@ 1
The test functions from Vitest.

@@ 3
The function under test, the fixed places, and the type of a place.

@@ 5-10
Two places of the kind the palette adds: an organisation and one of its projects.

@@ 12-15
Nothing typed but spaces: every place, in the order given.

@@ 17-18
Every word must match, in any order and any case: "CELLARS project" finds only the project, whose hint names its organisation.

@@ 19
The hint counts too: "recovery" finds the *Security* page, whose hint mentions recovery codes.

@@ 20
A word that matches nothing leaves nothing.

@@ 21
End of the test.

@@ 23-28
A place whose name starts with the first word comes first: given the project before the organisation, "amber" still puts *Amber Cellars* ahead of the project that merely mentions it.

@@ 29
End of the group.
