---
fingerprint: f109478a9d98c735
---
The tests for the dashboard's face-check figures (`figures.ts`).

@@ 1
The test functions from Vitest.

@@ 3
The functions under test.

@@ 5-6
**`bandText`**: seconds up to a minute, minutes after, and "or more" for the last band.

@@ 7-10
A band within a minute, one ending at exactly a minute, one in minutes (with "1.5"), and the open-ended last band.

@@ 11-12
End of the test and the group.

@@ 14-15
**`withinTarget`**: a band meets the 15-second target only if all of it does.

@@ 16-22
The band ending at 15 does; the band from 15 to 20 doesn't; the last band, with no end, never does.

@@ 23-24
End of the test and the group.

@@ 26-28
**`share`**: 400 decided checks — 300 passes, 99 step-ups and a single rejection.

@@ 29-34
Passes 75 %; step-ups 24.75 %, rounded to 25 %; the one rejection "under 1 %", not "0 %"; and an outcome that never happened, honestly 0 %.

@@ 35
Before anything is decided, a dash.

@@ 36-37
End of the test and the group.
