---
fingerprint: fdb068e2d685e313
---
These are the **automatic tests** for the book builder. `build.py` is itself a checker — it decides whether the book is complete — so if it had a bug, it could report "100 % explained" when that isn't true. Testing the checker closes that gap.

Each test is a function whose name starts with `test_`. **pytest** finds and runs every such function. Inside, each `assert` states something that must be true; if it isn't, pytest reports exactly which line failed and what the values were.

!!! kid "Explain like I'm six"
    Before a referee runs a real match, someone checks the referee's whistle and stopwatch. These tests check the book-builder's tools with tiny, made-up examples where we already know the right answer.

@@ 1
The **module docstring**: what this file is for, in one sentence.

@@ 3
`from __future__ import annotations` — the same type-hint setting as in `build.py`, so both files behave identically.

@@ 5-6
**Import the code under test.**

- `import build` works because `pyproject.toml` tells pytest to add `docs/zero_to_hero` to Python's search path (`pythonpath`, §5.0.2).
- `from build import Note` also brings the `Note` class in under its short name, because the tests create many notes.

@@ 9-11
**`source_lines` drops only the final newline.**

- `"a\n\nb\n"` (an empty line in the middle, and a final newline) must become three lines, keeping the empty middle one.
- Text without a final newline must lose nothing.

This protects the line numbering of every walkthrough.

@@ 14-17
**The fingerprint is stable and sensitive.**

- The same text always gives the same fingerprint.
- Changing one character (`1` → `2`) gives a different one.
- It is always 16 characters long, even for empty text.

@@ 20-25
**Parsing a walkthrough.** A tiny walkthrough with a header, an introduction and two notes (one single-line, one range) is parsed. Then:

- the header became a dict;
- the introduction text is right;
- each note has the right start, end and text.

The list comprehension on line 25 turns each `Note` into a simple tuple, so a single comparison checks everything at once.

@@ 28-32
**What counts as explained.** Real text counts. The skeleton placeholder `TODO`, the re-anchoring flag `TODO(review) …` and blank text do **not**. If any of these three lines ever broke, the coverage numbers would lie.

@@ 35-38
**Segments cover every line exactly once.** Two notes, given in the wrong order (lines 3–4 first, then line 1), on a 6-line file. The result must be, in order:

- line 1 (explained);
- line 2 (a gap);
- lines 3–4 (explained);
- lines 5–6 (a gap at the end).

`n is not None` turns each note into simply `True` or `False`, which keeps the expected value readable.

@@ 41-43
**Bad notes are rejected.** Lines 1–3 and line 2 overlap, and lines 5–9 run past the end of a 6-line file, so there must be exactly two problems. `_` discards the segments, which this test doesn't need.

@@ 46-48
**The line mapping follows moved lines.** Old file `a b c`; new file `new a c` — a line was added at the top and `b` was deleted.

- `a` moved from 1 to 2.
- `c` moved from 3 to 3.
- `b` has no entry.
- The two sentinels are `0 → 0` and `4 → 4` (one past the end).

@@ 51-57
**Re-anchoring moves notes and flags edited code.**

- A docstring line was added at the top, `x = 1` was edited into `x = 10`, and the other lines are unchanged.
- The note on `import os` moves from 1 to 2.
- The note on `y = 2` moves from 3 to 4.
- The note on the edited line moves to the code that replaced it (line 3), with its text marked `TODO(review)`.
- The report contains exactly one message: the one about the edited line.

@@ 60-65
**Notes on deleted code are dropped.** Old `a b c`, new `a c`. The note on `b`, whose code is gone, disappears from the result, and the report says so in exactly these words. The first argument is spread over three lines by the formatter because it is long.
