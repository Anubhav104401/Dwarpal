---
fingerprint: f3f3f8f66811e9a5
---
The tests for the dashboard's face-check figures (`figures.ts`).

@@ 1
The test functions from Vitest.

@@ 3
The functions under test. Since 9 Nov also `documentFigures`.

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

@@ 39-40
**Test — the ID-document figures** (9 Nov).

@@ 41-42
Forty reached: twenty passed by the document and four by an Age Pass, five failed and one was rejected — so 75 % finished, 60 % passed (the Age Passes too), and 25 % left.

@@ 43-48
Two reached in the 30 days but three ended in them (one was reached the day before): every share stops at 100 %, and nobody left.

@@ 49-51
Nothing reached: a dash for each.
