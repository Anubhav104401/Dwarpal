---
fingerprint: be872e81ae6a9578
---
**The daily chart** (§5.5.2): a project's finished checks per day, for 30 days, as bars stacked by outcome. It is plain HTML and CSS — each bar a column of coloured blocks whose heights are proportions — so it needs no chart library, stays sharp at any width, and every part of it can be reached by a screen reader or a keyboard. The design follows a few rules: one fixed colour per outcome, checked for colour-blind readers; a legend; thin gaps between blocks; each day's exact numbers on hover or focus; and the same numbers as a table.

@@ 1
It reacts to the pointer, so it runs in the browser (§5.5.1).

@@ 3
`useState`, to remember which day is being looked at.

@@ 5
From `daily.ts`: the type of a day, the shared order of outcomes, and the short date format.

@@ 7-15
**`COLOUR`** — each outcome's colour, as Tailwind classes: one for light pages and a slightly different one for dark ones (`dark:`), each picked to stand out on its own background. The five were checked with a colour validator: neighbouring colours stay distinguishable for the common kinds of colour blindness, and in dark mode every one has at least 3:1 contrast with the panel. In light mode three of them don't reach 3:1 against white, which is why the chart always comes with a table.

@@ 17
`step_up` is shown as "step up".

@@ 19-20
**`DailyChart`** — takes the days made by `everyDay`.

@@ 21
Which day is under the pointer or has the keyboard's focus — none at first.

@@ 22
The tallest day's total, which becomes the full height of the chart. `Math.max(1, …)` avoids dividing by zero when every day is empty.

@@ 23
All the checks in the window, for the chart's spoken description.

@@ 24
The day whose numbers to show, if any.

@@ 25-28
Where to show them: the middle of that day's bar, as a percentage of the chart's width. In the left half, the box starts 12 pixels to the right of it; in the right half, it ends 12 pixels to its left — so it never covers the bar being read, nor runs off the edge.

@@ 29-31
The first and last days, for the labels underneath; with no days at all, draw nothing.

@@ 33-34
A **`figure`** — HTML's element for a self-contained picture with a caption. The test ID lets tests find it.

@@ 35-42
**The legend**: a small coloured square and the outcome's name for each of the five, in the shared order. The squares are hidden from screen readers (`aria-hidden`): the name says it all.

@@ 44
The bars and the hover box share a box, so the hover box can be placed over the bars (`relative` here, `absolute` below).

@@ 45-50
The bars sit in a **`fieldset`** — a group with a spoken name — that says what the chart shows: how many checks, over which days, and the busiest day's number. The days line up at the bottom (`items-end`) with a 2-pixel gap between them; a faint line marks the top (the busiest day's height) and a stronger one the bottom. Moving the pointer out of the chart clears the hover box.

@@ 51-60
**One button per day.** A button isn't needed to click on — it is there so that a keyboard can reach each day too. Its spoken label is the day and its total. The button fills the chart's full height (a tall target is easier to hover than a thin bar), is shaded while it is the one being looked at, and becomes the active day when the pointer enters it or it receives focus.

@@ 61-64
The bar itself: as tall as this day's share of the busiest day. Its blocks stack from the bottom up (`flex-col-reverse`), with 2-pixel gaps; its top corners are rounded and anything poking past them is clipped (`overflow-hidden`).

@@ 65-71
One block per outcome that happened that day, in the shared order, so `pass` is always at the bottom. Each block's height is its count, by way of `flexGrow`: the blocks share the bar's height in proportion to their counts. `min-h-px` keeps a block of one visible.

@@ 72-75
The end of the bar, the button, the list and the group.

@@ 76
The busiest day's number at the top left — the only scale the chart needs, since exact numbers are on hover and in the table.

@@ 77-81
**The hover box**, only while a day is active: placed beside its bar (`beside`), never catching the pointer itself (`pointer-events-none`), with a border and a light shadow.

@@ 82-84
The day and its total, with "check" or "checks".

@@ 85-93
Then each outcome of that day, with its coloured square, name and number.

@@ 94-96
The end of the box and of the shared area.

@@ 98-101
The caption: the first day at the left and the last at the right.

@@ 103-104
**The table**, folded away in a `details` element: "Show as a table" opens it. It gives every number as text — for anyone who can't tell the colours apart, uses a screen reader, or simply wants the figures.

@@ 105-116
A header row: Day, the five outcomes in the shared order, and All.

@@ 117-120
One row per day that had checks — the empty days add nothing to a table.

@@ 121-129
The day, its count for each outcome (0 where there was none), and its total in bold.

@@ 130-136
The end of the rows, the table, the fold, the figure and the function.
