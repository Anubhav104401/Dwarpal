---
fingerprint: 6bb59f3f71746a30
---
The tests for `daily.ts`: the window is complete, rows are added up correctly, and dates are written as the console shows them.

@@ 1
The test functions from Vitest.

@@ 3
The two functions under test.

@@ 5-6
**The first test**: every day of the window, policies added together, rows outside the window ignored.

@@ 7-12
Three days from 27 October, and four rows: two for the same day and outcome (as two policies would give), one on the third day, and one the day after the window ends.

@@ 14
All three days are there, in order — including the 28th, which had no rows.

@@ 15
Their totals: 3 (the two rows added), 0 for the empty day, 4; the row from the 30th was left out.

@@ 16
The first day's counts hold one outcome, `pass`, with the two rows added together.

@@ 17
End of the first test.

@@ 19-22
**The second**: a window that starts on 31 October runs on to 1 November; and an empty or unreadable first day gives no days, not 30 broken ones.

@@ 23
End of the group.

@@ 25-29
`shortDate` writes 28 October as "28 Oct".
