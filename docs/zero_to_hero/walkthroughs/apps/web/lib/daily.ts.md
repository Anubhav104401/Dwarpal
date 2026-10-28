---
fingerprint: 93e246d3fc611dcd
---
**The counts, day by day** (§5.5.2): the API sends a row only for a day, policy and outcome that had checks. A chart needs the opposite — every day of the window, in order, with nothing missing — so that a quiet day shows as a gap rather than vanishing and pulling its neighbours closer.

@@ 1-2
What this module does, and why the empty days matter.

@@ 4
**`OUTCOME_ORDER`** — the five ways a check can end, in one fixed order that the chart's colours, its legend, its table, the totals and the search menu all share. `as const` makes TypeScript keep the exact words rather than widening them to "any string".

@@ 6-10
**`DailyCount`** — one of the API's rows, without its policy: a day (written `YYYY-MM-DD`), an outcome and how many sessions ended that way.

@@ 12-16
**`Day`** — one bar of the chart: the day, its counts by outcome, and their total.

@@ 18
The number of milliseconds in a day (24 × 60 × 60 × 1,000). The underscores only make it easier to read.

@@ 20-21
**`everyDay`** — `days` entries starting at `since`, with the rows added in.

@@ 22-23
Read the first day as midnight in UTC (`Z`) — the API counts days in UTC, so mixing in the browser's own time zone could shift every bar by a day. A date that can't be read gives no days at all, rather than nonsense.

@@ 24-28
Make the empty window: for each position `i`, the day `i` days after the first — turned back into `YYYY-MM-DD` by taking the first ten characters of its ISO form — with no counts yet. Counting in milliseconds from UTC midnight crosses months and years correctly.

@@ 29
A **`Map`** from each day's text to its entry, so a row finds its day directly instead of searching the list.

@@ 30-32
For each row, find its day; a row outside the window (it can happen when "today" has moved on) is skipped.

@@ 33-34
Add its sessions to that outcome's count — `?? 0` starts a count that doesn't exist yet at 0 — and to the day's total. Two policies with the same outcome on the same day add up.

@@ 35-37
The whole window, empty days included.

@@ 39-46
**`shortDate`** — "28 Oct": the day number and the month's short name, in British English, read in UTC for the same reason as above.
