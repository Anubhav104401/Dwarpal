---
fingerprint: 9abd3e9b2fcdbeef
---
These are the **automatic tests** for the book builder. `build.py` is itself a checker — it decides whether the book is complete — so if it had a bug, it could report "100 % explained" when that isn't true. Testing the checker closes that gap.

Each test is a function whose name starts with `test_`. **pytest** finds and runs every such function. Inside, each `assert` states something that must be true; if it isn't, pytest reports exactly which line failed and what the values were.

!!! kid "Explain like I'm six"
    Before a referee runs a real match, someone checks the referee's whistle and stopwatch. These tests check the book-builder's tools with tiny, made-up examples where we already know the right answer.

@@ 1
The **module docstring**: what this file is for, in one sentence.

@@ 3
`from __future__ import annotations` — the same type-hint setting as in `build.py`, so both files behave identically.

@@ 5
`from pathlib import Path` — the `Path` type, used in the type hint of the last test's `tmp_path` folder.

@@ 7
`import pytest` — the test runner itself. These tests use it for one type name, `pytest.MonkeyPatch` (explained in the last test).

@@ 9-10
**Import the code under test.**

- `import build` works because `pyproject.toml` tells pytest to add `docs/zero_to_hero` to Python's search path (`pythonpath`, §5.0.2).
- `from build import Note, Place` also brings two classes in under their short names, because the tests create many of them.

@@ 13-15
**`source_lines` drops only the final newline.**

- `"a\n\nb\n"` (an empty line in the middle, and a final newline) must become three lines, keeping the empty middle one.
- Text without a final newline must lose nothing.

This protects the line numbering of every walkthrough.

@@ 18-21
**The fingerprint is stable and sensitive.**

- The same text always gives the same fingerprint.
- Changing one character (`1` → `2`) gives a different one.
- It is always 16 characters long, even for empty text.

@@ 24-29
**Parsing a walkthrough.** A tiny walkthrough with a header, an introduction and two notes (one single-line, one range) is parsed. Then:

- the header became a dict;
- the introduction text is right;
- each note has the right start, end and text.

The list comprehension on line 25 turns each `Note` into a simple tuple, so a single comparison checks everything at once.

@@ 32-36
**What counts as explained.** Real text counts. The skeleton placeholder `TODO`, the re-anchoring flag `TODO(review) …` and blank text do **not**. If any of these three lines ever broke, the coverage numbers would lie.

@@ 39-42
**Segments cover every line exactly once.** Two notes, given in the wrong order (lines 3–4 first, then line 1), on a 6-line file. The result must be, in order:

- line 1 (explained);
- line 2 (a gap);
- lines 3–4 (explained);
- lines 5–6 (a gap at the end).

`n is not None` turns each note into simply `True` or `False`, which keeps the expected value readable.

@@ 45-47
**Bad notes are rejected.** Lines 1–3 and line 2 overlap, and lines 5–9 run past the end of a 6-line file, so there must be exactly two problems. `_` discards the segments, which this test doesn't need.

@@ 50-52
**The line mapping follows moved lines and skips deleted ones.** Old file `a b c`; new file `new a c` — a line was added at the top, and `b` was deleted.

- `a` moved from line 1 to line 2, unedited;
- `c` stayed on line 3, unedited;
- `b` has no entry at all, because it has no place in the new file.

@@ 55-59
**Edited blocks are lined up side by side** (the "two rows of chairs" of `build.py`).

- *Grown:* `b` became two lines, `B1` and `B2`. Old line 2 now covers new lines 2–3, marked as edited, and `c` moved from 3 to 4.
- *Shrunk:* two lines, `b1` and `b2`, became one line `B`. Both old lines now point at new line 2, marked as edited. `shrunk[2] == shrunk[3] == Place(…)` is a **chained comparison**: it is true only when all three are equal.

@@ 62-68
**Re-anchoring moves notes and flags edited code.**

- A docstring line was added at the top, `x = 1` was edited into `x = 10`, and the other lines are unchanged.
- The note on `import os` moves from 1 to 2.
- The note on `y = 2` moves from 3 to 4.
- The note on the edited line moves to the code that replaced it (line 3), with its text marked `TODO(review)`.
- The report contains exactly one message: the one about the edited line.

@@ 71-76
**Notes on deleted code are dropped.** Old `a b c`, new `a c`. The note on `b`, whose code is gone, disappears from the result, and the report says so in exactly these words. The first argument is spread over three lines by the formatter because it is long.

@@ 79-83
**An edited line at the edge of a note stays covered.** The note explains lines 1–2, and only line 2 changed (`b` → `B`). The note must keep *both* lines, flagged for review.

An earlier version of the builder shrank such a note to line 1 alone, which silently left line 2 without an explanation. This test makes sure that never comes back.

@@ 86-89
**An edit that keeps the line count keeps every note in place.** Three lines in a row were edited, and there are still three. The note on line 2 and the note on lines 3–4 must stay exactly where they were, both flagged. This is the case where the "two rows of chairs" idea matters most: without it, both notes would be stretched over all three lines and would overlap.

The second note was *already* flagged before this run. The expected text shows that it doesn't get a second `TODO(review)` prefix.

@@ 92-107
**Every walkthrough must appear in the book exactly once.** The test builds a tiny book in a temporary folder:

- `monkeypatch` points the builder's project folder and book folder at `tmp_path` (lines 93–95);
- two source files, `a.py` and `b.py`, each get a walkthrough; an empty abbreviations file and a page template holding only the `{{BODY}}` placeholder complete the book (lines 96–99);
- the only chapter shows `a.py` **twice** and `b.py` **never**, then the ledger (line 100);
- the coverage rules count Python files and skip the walkthroughs folder (line 101).

After `build()`, both mistakes must be reported, in exactly these words.

@@ 110-122
**Re-anchoring twice before a stamp follows both edits.** This test runs the real `--reanchor` helper on real files, so it needs two pytest **fixtures** — ready-made helpers that pytest passes in when a test asks for them by name:

- `tmp_path` — a brand-new, empty temporary folder for this test only;
- `monkeypatch` — temporarily replaces values while the test runs, and puts the originals back afterwards.

Lines 93–95 point the builder's three folder settings at the temporary folder, so the test works in a sandbox and can never touch the real book.

Lines 96–99 set the scene: a two-line source file `a`, `b`, a walkthrough with one note per line, and a snapshot of that first version.

Lines 100–102 make two edits in a row — first a line `new` at the top, then another line `newer` below it — and re-anchor after each one.

The last two lines check the result: the notes moved twice, to lines 3 and 4, and the snapshot now holds the newest version. This is exactly the sequence that corrupted notes before the snapshot was moved forward on every re-anchor.
