---
fingerprint: a4751f53974099b9
---
`build.py` is the **book binder**. It reads the settings, chapters, walkthroughs and template, and writes one finished HTML file. It also checks that every code line in the project has an explanation that is still up to date, and it keeps explanations attached to the right lines when code changes.

The file has four regions, top to bottom:

1. **Preparation** (lines 1–42): a description, the tools it borrows (imports) and fixed settings (constants).
2. **Small helpers** (lines 45–197): data containers, and short functions that each do one job. Most of them are **pure** — they only turn inputs into outputs, without touching files — which makes them easy to test (see `tests/test_build.py`, §5.0.7).
3. **The `Book` class** (lines 200–343): the main machine. It renders walkthroughs, scans the project, builds the ledger and assembles the page.
4. **Commands** (lines 346–401): the helper commands `--new`, `--stamp` and `--reanchor`, and `main()`, which decides what to do when you run the file.

!!! kid "Explain like I'm six"
    Think of a school project folder. `build.py` collects all the loose pages and checks that each one has a matching explanation. It puts a red sticker on any page that is out of date. Then it slides everything into a nice binder cover (the template) and adds a checklist page at the back (the ledger). And if someone adds new pages in the middle, it moves every sticky note to follow its page.

@@ 1-11
**The docstring.** Text between triple quotes (`"""`) at the very top of a file is that file's **docstring**: a description for humans. Python stores it but does not run it. It explains the purpose in two sentences, then shows the five ways to run the program. `PATH` is a placeholder meaning "put a file path here".

@@ 13
`from __future__ import annotations` makes Python treat every *type hint* in this file (labels like `-> str` or `Note | None`) as plain text that is never evaluated when the file loads. Python 3.14 already behaves this way by default. The line keeps the behaviour identical on Python 3.13, which the project uses, and costs nothing.

@@ 15
`import argparse` brings in Python's built-in **argument parser**. It reads the extra words typed after the program name on the command line (like `--strict`), checks them, and prints a help page for `--help`. It is used in `main()`.

@@ 16
`import difflib` brings in Python's built-in tools for **comparing sequences** — the same idea as the "diff" view in code-review tools. It is used by `line_mapping` (line 148) to work out where lines moved after an edit.

@@ 17
`import hashlib` brings in Python's collection of **hash functions**, including SHA-256, the "magic blender" that makes fingerprints (§X.5).

@@ 18
`import html` gives two small tools for HTML text:

- `html.escape` turns characters that mean something in HTML (`<`, `>`, `&`, quotes) into safe codes, so text is *shown* rather than treated as tags;
- `html.unescape` does the reverse.

@@ 19
`import os` gives tools for talking to the **o**perating **s**ystem. We use `os.walk`, which visits every folder and file under a starting folder.

@@ 20
`import re` gives **regular expressions**: a mini-language for describing text patterns. It is used for the `@@` note markers, the `!walk` directives and the fingerprint line.

@@ 21
`import sys` gives access to the running Python itself. We use `sys.exit` on the last line to hand an **exit code** back to whoever started the program: 0 for success, 1 for failure.

@@ 22
`import tomllib` is Python's built-in reader for TOML files, used to read `book.toml`.

@@ 23
`from dataclasses import dataclass` brings in one specific tool, the `@dataclass` decorator. `from X import Y` takes just `Y` out of module `X`.

@@ 24
`from datetime import UTC, datetime` brings in tools for dates and times. `UTC` is Coordinated Universal Time. We stamp the book with its build time in UTC, so the stamp means the same thing everywhere.

The very first version of this line imported `timezone` and wrote `timezone.utc`. The **Ruff linter** (§4.3) pointed out that modern Python offers the shorter alias `UTC`, so the line was updated.

@@ 25
`from pathlib import Path, PurePosixPath`:

- `Path` represents a file or folder location as an *object*. It has useful abilities (`.read_bytes()`, `.is_file()`, `.parent`, joining with `/`) and handles Windows `\` and Linux `/` correctly.
- `PurePosixPath` is a path that always uses forward slashes and never touches the disk. We use it for pattern matching that must behave the same on every operating system.

@@ 26
`from typing import Any` imports the special type `Any`, meaning "a value of any kind". The settings read from `book.toml` mix text, lists and nested tables, so their type is "a dict whose keys are strings and whose values could be anything": `dict[str, Any]`.

The type checker (mypy, §4.3) insisted on that precise label.

@@ 28
`import markdown` imports **Python-Markdown**, pinned in the project's `pyproject.toml` (§5.0.2). This is the first import that isn't built into Python, so it sits in its own group after a blank line. Standard library first, third-party second is a Python style rule that Ruff enforces.

@@ 29
`from pygments import highlight` imports the main function of **Pygments**. You give it source code, a *lexer* (which knows the language) and a *formatter* (which knows the output format), and it gives back highlighted text.

@@ 30
`from pygments.formatters import HtmlFormatter` imports the formatter that produces HTML, such as `<span class="k">def</span>`.

@@ 31
`from pygments.lexers import TextLexer, get_lexer_for_filename` — a **lexer** chops code into labelled pieces called *tokens* (this is a keyword, this is a string…).

- `get_lexer_for_filename` picks the right lexer from a file name.
- `TextLexer` is the fallback for files Pygments doesn't recognise.

@@ 32
`from pygments.util import ClassNotFound` imports the **exception** (error signal) Pygments raises when it has no lexer for a file name. We need its name so we can catch it on line 192.

@@ 34
`BOOK_DIR = Path(__file__).resolve().parent` answers "where is this book folder?":

- `__file__` is the path of the file being run;
- `.resolve()` makes it a full, absolute path;
- `.parent` steps up to the folder containing it: `…/docs/zero_to_hero`.

Names in CAPITALS are **constants**: set once, never changed.

!!! why "Why not just use the current folder?"
    You might run `build.py` from anywhere — the project root, the book folder, an automated test machine. Working out locations from `__file__` makes the program find its files no matter where it was started.

@@ 35
`REPO_ROOT = BOOK_DIR.parents[1]` — `.parents` is the chain of folders above a path: `[0]` is `docs`, and `[1]` is the **project root**. Every project-relative path, like `docs/zero_to_hero/build.py`, is measured from here.

@@ 36
`WALK_DIR = BOOK_DIR / "walkthroughs"` — with `Path` objects, `/` means **join paths**, not divide. This is the folder holding every walkthrough file.

@@ 37
`SNAP_DIR = BOOK_DIR / ".snapshots"` — the folder holding a **snapshot** (an exact copy) of each source file as it was when its walkthrough was last stamped. The name starts with a dot to mark it as a tool's private folder. It is deliberately excluded from coverage scans, linting and type checking (`book.toml`, `pyproject.toml`), because it contains *copies* of code, not code.

@@ 38
`NOTE_MARK = re.compile(r"^@@ *(\d+)(?: *- *(\d+))? *$")` is the pattern that recognises a note marker line, such as `@@ 12` or `@@ 12-14`. `re.compile` prepares the pattern once for fast reuse. The `r` makes a **raw string**, which keeps backslashes as typed.

| Piece | Means |
| :-- | :-- |
| `^` | the start of the line |
| `@@` | two literal `@` signs |
| ` *` | zero or more spaces |
| `(\d+)` | one or more digits, **captured** as group 1 (the start line) |
| `(?: … )?` | an optional, uncaptured group containing… |
| ` *- *(\d+)` | …a dash with optional spaces, and more digits captured as group 2 (the end line) |
| ` *$` | optional trailing spaces, then the end of the line |

@@ 39
`DIRECTIVE = re.compile(…, re.MULTILINE)` is the pattern for chapter directives such as `!walk docs/zero_to_hero/build.py` or `!ledger`:

- `(walk|ledger)` captures either word (`|` means "or");
- `(?: +(\S+))?` optionally captures a path made of non-space characters (`\S+`).

`re.MULTILINE` makes `^` and `$` mean the start and end of *each line*, which matters because the whole chapter is searched at once.

@@ 40
`FINGERPRINT_LINE` finds the `fingerprint: …` line in a walkthrough's header, so `--stamp` can replace it. `.*` means "any characters, any number of them".

@@ 41
`EXTENSIONS` lists the Python-Markdown extensions to switch on:

- `extra` — tables, footnotes, abbreviations, definition lists, fenced code;
- `admonition` — the `!!!` boxes;
- `sane_lists` — keeps numbered and bulleted lists from merging;
- `codehilite` — colours fenced code blocks with Pygments.

@@ 42
`EXT_CONFIG` holds settings for those extensions, as a **dict**. For `codehilite`:

- `css_class: "hl"` matches the colour rules in the template;
- `guess_lang: False` means "don't guess the language of unlabelled code blocks" — wrong colours are worse than none.

@@ 45-49
**`Note` — a container for one explanation.** `@dataclass` is a **decorator**: it writes the boring parts of the class for us, such as the code that builds a `Note` from three values. The three **fields** are:

- `start` — first line number explained;
- `end` — last line number;
- `text` — the explanation, in Markdown.

`Note(12, 14, "…")` means "lines 12 to 14 are explained by this text".

@@ 52
`type Segment = tuple[int, int, Note | None]` is a **type alias** — a short name for a longer type. It uses the `type` statement added in Python 3.12. A *segment* is a stretch of lines: a start number, an end number, and either the `Note` explaining it or `None` if nothing does. The alias makes the function signatures below much easier to read.

@@ 55-61
**`Coverage` — the score card for one file:**

- `path` — the file;
- `lines` — total lines;
- `required` — non-blank lines, which need explaining;
- `explained` — how many required lines have an explanation;
- `stale` — `True` if the code changed after it was explained.

@@ 63-65
`percent` is the share of required lines explained, out of 100. `@property` lets us read it like a field (`cov.percent`), although it is calculated fresh each time, so it can never be out of date.

The **conditional expression** `A if condition else B` guards against dividing by zero: a file with nothing to explain counts as 100 % explained.

@@ 67-69
`complete` is `True` only when **every** required line is explained **and** the file hasn't changed since.

@@ 72-73
**`read_text` — read any file safely:**

1. `read_bytes()` reads the raw bytes.
2. `.decode("utf-8")` turns them into text **using UTF-8 explicitly** — this prevents the mojibake of §0.2.
3. `.replace("\r\n", "\n")` converts Windows line endings to `\n`, so a file has the same fingerprint on every operating system.

@@ 76-78
**`write_text` — write any file safely:**

- `path.parent.mkdir(parents=True, exist_ok=True)` first creates the folder the file goes in, and any missing folders above it, without complaining if they already exist.
- It then writes the text as UTF-8 with Linux-style newlines (`newline="\n"`), so the file is byte-for-byte identical on Windows and Linux.

Every file this program writes goes through this one function, so those two promises hold everywhere.

@@ 81-82
**`fingerprint` — the magic blender:**

1. Encode the text as bytes.
2. Blend it with SHA-256.
3. Write the result as hexadecimal (`hexdigest`).
4. Keep the first 16 characters (`[:16]` is a **slice**). That is still 2⁶⁴ possibilities.

@@ 85-86
**`walk_file_for`** gives the walkthrough's location for a project file: the walkthroughs folder mirrors the project, with `.md` added (`docs/zero_to_hero/build.py` → `walkthroughs/docs/zero_to_hero/build.py.md`). `f"{rel}.md"` is an **f-string**: `{rel}` is replaced by the value of `rel`.

@@ 89-90
**`snapshot_for`** gives the location of a project file's snapshot. It mirrors the project inside `.snapshots`, adding `.snap` to the name (`tasks.py` → `.snapshots/tasks.py.snap`).

!!! warn "Careful — why the `.snap` ending matters"
    The first design kept each copy's original name. Then the snapshot of `.gitignore` would itself be a file called `.gitignore`, and Git obeys `.gitignore` files in every folder. The snapshot of `pyproject.toml` might be mistaken for a real project by tools that search for one. Adding `.snap` makes every copy **inert**: no tool recognises it as anything special.

@@ 93-95
**`repo_relative`** turns whatever path the user typed into a project-relative one.

- If the typed path is absolute, use it; otherwise glue it onto `Path.cwd()`, the terminal's current folder.
- Then make it absolute (`resolve`), cut off the project root (`relative_to`), and write it with forward slashes (`as_posix`).

@@ 98-102
**`source_lines` — split text into lines.** `split("\n")` cuts at every newline. A tidy file ends with a newline, which leaves one empty string at the end — not a real line — so `lines[-1]` (the last item) is removed with `.pop()` when it is empty. Without this, every file would seem to have one extra line.

@@ 105
**`parse_walkthrough` — read a walkthrough's text into its three parts.** It returns a **tuple** of:

1. a dict of header settings;
2. the introduction text;
3. a list of `Note`s.

It receives the *text*, not a file path, so it never touches the disk. That makes it a pure function that tests can feed with any text they like.

@@ 106
`meta` (short for *metadata*, "data about data") starts as an empty dict for the header values.

@@ 107-108
**The header.** If the text begins with three dashes, there is a header.

- `text[4:]` skips those four characters (the dashes plus the newline).
- `.partition("\n---\n")` splits the rest at the first closing dash line into three pieces: before, the separator itself, and after.
- **Tuple unpacking** assigns the three pieces at once. `_` is the conventional name for "a value we don't need". `text` becomes everything after the header.

@@ 109-111
For each header line, split at the first `:` into key and value, trim the spaces from both (`.strip()`) and store them. So `fingerprint: 3f9a…` becomes `meta["fingerprint"] == "3f9a…"`.

@@ 112-113
Two empty lists to fill: `intro` for the introduction's lines, and `notes` for the `Note`s.

@@ 114
Walk through the body one line at a time. The `for` loop runs its indented block once per line.

@@ 115
Try the marker pattern on this line. `.match` returns a *match object* for a marker, or `None` otherwise.

@@ 116-118
**If the line is a marker**, start a new note.

- `mark[1]` is the captured start number; `int(...)` turns `"12"` into `12`.
- `mark[2] or start` uses the end number if there is one, otherwise the start (`or` gives its left side if that is "truthy", else its right side).

@@ 119-120
**Otherwise, if a note has already started**, this line belongs to the latest note (`notes[-1]`). `+=` adds it, plus the newline that `split` removed.

@@ 121-122
**Otherwise** — before the first marker — the line belongs to the introduction.

@@ 123
Return the three parts, gluing the introduction's lines back together with newlines.

@@ 126-128
**`is_explained`** checks that a note's text is non-empty **and** doesn't start with `TODO`. This covers both the `TODO` skeletons from `--new` and the `TODO(review)` flags from `--reanchor`.

!!! why "Why treat TODO as 'not explained'?"
    If placeholders counted, a freshly generated skeleton would show 100 % coverage, and the honesty check would be fooled by its own helper.

@@ 131
**`segments` — chop a file into consecutive stretches**, each covered by one note or by none. It returns two things: the list of `Segment`s, and a list of problems found (bad notes).

In the first version of the book this was a method that wrote problems straight into the `Book`. Turning it into a separate function that *returns* its problems made it possible to test on its own.

@@ 132-134
`result` and `problems` start empty. `cursor` is a finger pointing at the first line not yet assigned to a stretch; it starts at line 1.

@@ 135
Visit the notes **in order of their first line**. `sorted(...)` returns a sorted copy. `key=lambda n: n.start` says what to sort by: a **lambda** is a tiny unnamed function, here "given a note `n`, give back `n.start`".

@@ 136-138
**Reject impossible notes.** A note is bad if it starts before the cursor (it overlaps the previous note), ends before it starts, or ends beyond the last line. Bad notes are recorded as problems and skipped with `continue` ("go straight to the next item"). Overlaps are forbidden so that each line has exactly one explanation and coverage can't be double-counted.

@@ 139-140
**A gap before this note?** The lines between the cursor and the note's start have no note. Record them as a stretch with `None` in the note position.

@@ 141-142
Record the note's own stretch, then move the cursor to just after it.

@@ 143-144
**A gap at the end?** If the cursor hasn't passed the last line, the tail of the file has no notes. Record it as one more stretch.

@@ 145
Return both lists. Together the stretches cover every line exactly once, in order.

@@ 148
**`line_mapping` — where did each old line go?** Given the lines of the old version (the snapshot) and of the new version, it returns a dict from *old line number* to *new line number*. It covers only lines that are unchanged.

@@ 149
Start the dict with two invisible **sentinels** — markers placed just outside the real lines:

- "line 0" before the start maps to new line 0;
- "one past the last old line" maps to "one past the last new line".

They mean the search for "the nearest surviving line above or below" (lines 169–170) always finds something, even at the very top or bottom of a file.

@@ 150
`difflib.SequenceMatcher(a=old, b=new, autojunk=False)` compares the two lists of lines. `.get_matching_blocks()` returns runs of lines that appear in both, in the same order. Each block says "`size` lines starting at old position `a` match new position `b`".

`autojunk=False` switches off a speed shortcut that ignores very common lines. In code, common lines such as blank lines and lone closing brackets matter.

@@ 151-152
For every line inside each matching block, record "old number → new number". The `+ 1`s convert difflib's positions, which count from 0, into line numbers, which count from 1.

@@ 153
Return the finished mapping.

@@ 156
**`reanchor_text` — move every note in a walkthrough to its lines' new numbers.** It receives the walkthrough's text and the mapping. It returns the new text, plus a report of everything that needs a human's attention.

@@ 157-159
`output` collects the lines of the new walkthrough, and `report` the messages. Two on/off switches are written on one line (`dropping = review = False` sets both):

- `dropping` — "skip the text of the current note, because its code is gone";
- `review` — "the next line of text needs a `TODO(review)` label".

@@ 160
Go through the walkthrough line by line.

@@ 161
Is this line a note marker?

@@ 162
If it is…

@@ 163
…read its start and end line numbers. A single-line marker uses the start number for both.

@@ 164
`kept` is the list of **new** positions of this note's old lines, keeping only lines that survived unchanged (`if n in mapping`).

@@ 165-167
**Some lines survived.** The note moves to span from the lowest to the highest surviving position.

It needs review if any of its lines disappeared, *or* if new lines were inserted in the middle of its range. In both cases the count of kept lines differs from the size of the range.

Example: a note on lines 10–14 whose block gained a line in the middle now spans 10–15, with five kept lines in a range of six. Its explanation can't cover the new line without someone checking.

@@ 168-171
**No lines survived unchanged** — typically because the line was edited, and difflib sees an edited line as "one removed, one added". Rather than throw the explanation away, find:

- the nearest surviving line **above** the note — the largest old number below `start`, mapped to its new position, plus 1;
- the nearest surviving line **below** — the smallest old number above `end`, mapped, minus 1.

Whatever now sits *between* them is the code that replaced the note's code, so the note moves there, always marked for review. `default=max(mapping)` covers a malformed note that pointed beyond the file.

@@ 172
If the stretch between the neighbours is empty (low is past high), the code wasn't replaced — it was simply **deleted**.

@@ 173-175
Then the note is dropped: record a report message, and skip the marker (`continue`). The `dropping` switch makes the following lines (the note's text) be skipped too.

@@ 176-177
If the note needs review, say so in the report, showing its old and new ranges.

@@ 178
Write the new marker: a single number if the note now covers one line, otherwise a range.

@@ 179-180
A text line while `dropping` is on belongs to a dropped note, so skip it.

@@ 181-183
The first non-blank text line after a marker that needs review gets the prefix `TODO(review)`, which makes `is_explained` treat the note as unexplained. Then the switch turns off, so only that first line is prefixed.

@@ 184-185
Every other line is copied unchanged.

@@ 186
Return the rebuilt walkthrough text and the report.

@@ 189
**`highlight_lines` — colour a file and return one HTML string per line.**

@@ 190-193
**`try` / `except`.** Ask Pygments for the lexer matching the file name. If it doesn't know the name, it raises `ClassNotFound`; we catch that and fall back to plain text.

`stripnl=False` is vital: by default Pygments drops blank lines at the start and end, which would shift every line number.

@@ 194
**Highlight, then split.** `nowrap=True` means "just the coloured spans, no surrounding box". Pygments closes and reopens its colour tags at every line break, so splitting at `"\n"` gives one valid HTML piece per line.

@@ 195-196
**Safety net.** If highlighting produced *fewer* lines than the file has, don't trust it. Fall back to the plain lines, escaped so that `<` displays correctly. Wrong colours are acceptable; wrong line numbers are not.

@@ 197
Return exactly `count` lines. The slice drops the extra empty item left by the final newline.

@@ 200
**`class Book:`** — a **class** is a blueprint for an object that bundles *data* with *behaviour*. A `Book` remembers the settings, every file's score card and the problems found. Its methods do the work.

@@ 201
`__init__` runs when a `Book` is created: `Book(config)`. `self` is the new object, and `config` is the dict read from `book.toml` — typed `dict[str, Any]` (see line 26).

@@ 202-206
The `Book`'s memory:

- `config` — the settings;
- `coverage` — a dict from file path to its score card;
- `problems` — a list of human-readable problem messages;
- `abbreviations` — the hover definitions, read once;
- `note_md` — one Markdown converter for walkthrough notes, created once and reused for hundreds of notes.

@@ 208-210
**`note_html` — convert one note's Markdown to HTML.** `.reset()` clears the converter's memory of the previous note so notes never leak into each other. The abbreviation definitions are attached after a blank line, then the note is converted.

@@ 212
**`render_walkthrough` — the heart of the book.** It returns the HTML of one file's whole walkthrough, and records the file's score card.

@@ 213
Work out the source file's path and its walkthrough's path in one line (tuple unpacking).

@@ 214-216
**Missing pieces.** If either file is missing, record a problem and return a red warning instead of crashing. One missing explanation shouldn't stop the whole book from building, but it must be visible.

@@ 217-218
Read the source file and split it into lines.

@@ 219
Read the walkthrough file and parse it into its three parts.

@@ 220
Highlight the source: one coloured HTML string per line.

@@ 221
**Which lines need explaining?** A **set comprehension** collects the numbers of non-blank lines. `enumerate(lines, 1)` counts from 1, because humans number lines from 1.

@@ 222-223
`explained` will collect the numbers of lines that turn out to be explained (`set()` makes an empty set; `{}` would make a dict). `rows` will collect the HTML of each row.

@@ 224-225
**Cut the file into stretches** with `segments` (line 131). Any problems it found are added to the book's list, each prefixed with the file's path so the message says *which* walkthrough is broken. `+=` on a list appends all the new items.

@@ 226
Go through the stretches in order, unpacking each into `start`, `end` and `note`.

@@ 227
`range(start, end + 1)` gives the line numbers in this stretch. `range` stops *before* its second number, hence the `+ 1`.

@@ 228
**The code side of the row**: for each line number, a line-number label followed by that line's highlighted HTML, joined with newlines.

`code[n - 1]` uses `n - 1` because Python lists count from **0** while line numbers count from **1** — the classic "off-by-one" trap.

@@ 229-231
**Case 1 — a real explanation.** Mark the lines as explained; the row gets the normal style, and the note is converted to HTML.

@@ 232-233
**Case 2 — no explanation, but there is code here.** The row gets the `missing` style (a red bar) and a red "Not explained yet." message.

@@ 234-235
**Case 3 — only blank lines.** Nothing to explain: a compact `blank` row with no explanation box.

@@ 236-237
Build the row's HTML in two steps — first the code box, then the note box and the closing tags — and add it to `rows`. Two short steps keep each line within the 120-character limit that Ruff checks.

@@ 238
**Stale?** The fingerprint recorded in the walkthrough's header must equal a fresh fingerprint of the code. A missing fingerprint (`None`) also counts as stale.

@@ 239-240
**Record the score.** `required & explained` is the **intersection** of the two sets: lines that are both required and explained. Blank lines inside a multi-line note don't inflate the count.

@@ 241
The red **"code changed since explained"** badge if stale, otherwise nothing.

@@ 242-245
**The header bar**: the file's path, its line count and its coverage. The parentheses let one string span several lines; Python glues adjacent strings together automatically. `{cov.percent:.0f}` formats the number with no decimal places.

@@ 246
The file's introduction, converted from Markdown and wrapped in its own box.

@@ 247
**Assemble the walkthrough**: a `<section>` holding the header bar, the introduction and every row.

@@ 249
**`scan_sources` — find every file in the project that must be explained.**

@@ 250-251
`rules` is the `[coverage]` group from `book.toml`; `found` collects matching paths.

@@ 252
**`os.walk(REPO_ROOT)`** visits the project root and every folder beneath it. For each folder it gives the folder's path, its sub-folder names and its file names.

@@ 253
**Pruning.** The list of sub-folders is replaced *in place* with a sorted copy that leaves out the names in `prune`.

`dirs[:] = …` changes the very list `os.walk` will use to decide where to go next. Plain `dirs = …` would make a new list that `os.walk` never sees. Sorting makes the ledger's order the same on every computer.

@@ 254
For each file name in this folder, in sorted order…

@@ 255
…build its project-relative path with forward slashes, as a `PurePosixPath`.

@@ 256
**Does it match any `include` pattern?** `any(...)` is `True` if at least one pattern matches. It stops at the first match.

@@ 257-258
**Keep it** if it was wanted and matches no `exclude` pattern.

@@ 259
Return the list of every file that must be explained.

@@ 261-262
**`ledger_html` — build the coverage table at the back of the book.** `rows` holds one table row per file.

@@ 263
For every file the scan says must be explained…

@@ 264
…check whether it has a walkthrough file.

@@ 265-266
**It has a walkthrough, but no chapter has shown it yet** — render it anyway, purely so its coverage is counted. A file can't dodge the ledger by not being mentioned in a chapter.

@@ 267-270
**It has no walkthrough at all.**

- Count its lines anyway and record a score card with zero explained, so the totals honestly include it.
- `sum(1 for x in lines if x.strip())` adds 1 for every non-blank line.
- Also record a problem.

!!! real "Real world — a bug this fixed"
    The first version skipped files without walkthroughs when adding up totals. The very first build therefore announced "0/0 lines explained (100.0 %)" — a perfect score for doing nothing. **A check that can report success when nothing was done is worse than no check.**

@@ 271
Fetch this file's score card. One of the branches above guarantees it exists.

@@ 272-280
**Choose the status label and its colour** with a chain of conditional expressions, read top to bottom:

- complete → green;
- otherwise stale → red;
- otherwise has a walkthrough → amber "in progress";
- otherwise → red "not explained".

Ruff's formatter spread the chain over several lines so each condition is easy to see.

@@ 281-285
Add the table row: path, line count, explained/required with the percentage, and the coloured status pill.

@@ 286-287
The heading row, then the whole table, wrapped in a box that scrolls sideways on narrow screens.

@@ 288
Return a **Total** line followed by the table.

@@ 290-294
**`totals` — one line summarising the whole project's coverage.** Add up the required and explained lines across every score card, work out the percentage (guarding against dividing by zero), and format the line. `:,` adds thousands separators and `.1f` shows one decimal place.

@@ 296-297
**`build` — assemble the whole book.** `blocks` remembers each directive found in the chapters: a placeholder name → (kind, argument).

@@ 299-302
**`park` — a function inside a function.** It is called for every directive found:

1. invent a unique placeholder such as `ZTHBLOCK3X`;
2. remember what the directive asked for;
3. return the placeholder surrounded by blank lines, to replace the directive in the chapter.

!!! key "Key idea — why park directives?"
    Walkthrough HTML must **not** go through the Markdown converter, which would mangle the code. So each directive is swapped for a harmless word, everything is converted, and then the real HTML is swapped back in (lines 311–312). The blank lines make Markdown wrap the placeholder in its own `<p>…</p>`, which is exactly what we search for.

@@ 304
**Read every chapter in the order `book.toml` gives, parking its directives.** A **list comprehension**; `DIRECTIVE.sub(park, text)` replaces each directive with whatever `park` returns.

@@ 305-307
**The main Markdown converter**, with our extensions plus `toc`. `toc` gives every heading an `id` you can link to, and records the headings for the sidebar.

- `[*EXTENSIONS, "toc"]` builds a new list: everything in `EXTENSIONS`, then `"toc"`. The `*` spreads a list's items.
- `{**EXT_CONFIG, …}` does the same for dicts.

@@ 308
**Convert the whole book in one go**, with the abbreviations attached once at the end. Converting everything together lets `toc` make every heading's `id` unique across all chapters.

@@ 309
**Render every parked walkthrough** — a dict comprehension keeping only `walk` blocks.

@@ 310
**Render the ledger last** (`|=` merges entries into the dict), so every walkthrough shown in a chapter already has its score card.

@@ 311-312
**Swap the real HTML back in** for each `<p>placeholder</p>`.

@@ 313
**Make wide tables scrollable on phones** by wrapping each table in a `tw` box.

@@ 314
**Get the list of headings for the sidebar.** The `toc` extension attaches `toc_tokens` to the converter *while the program runs*, so the type checker — which reads the code beforehand — can't know it exists. `getattr(md, "toc_tokens", [])` reads the attribute by name, and gives an empty list if it is missing. The label `list[dict[str, Any]]` tells mypy what we expect to get.

@@ 315
Hand the body and headings to `page()`.

@@ 317-318
**`page` — pour everything into the template.** `links` collects one sidebar link per heading.

@@ 320-324
**`visit` — turn the tree of headings into flat sidebar links.** For each heading:

1. make its name safe (unescape, then escape exactly once);
2. add a link whose class (`h1`, `h2`, `h3`) lets the CSS indent it;
3. **call itself** on the heading's children.

A function that calls itself is using **recursion**, the natural way to walk a tree.

@@ 326
Start the walk from the top-level headings.

@@ 327
**Count the words**: replace every HTML tag with a space (`re.sub`), find every run of word characters (`re.findall`), and count them.

@@ 328
Read the template.

@@ 329-335
**The values for the template's blanks**:

- the escaped title and subtitle;
- the word count and coverage totals;
- the build time (`strftime` formats a date as text);
- the sidebar links.

@@ 336-337
**Fill the blanks**: replace `{{NAME}}` with each value. The placeholder is built with `+` because inside an f-string, `{{` means a single literal `{`, which would make an f-string version unreadable.

@@ 338
**Insert the body last — on purpose.** The book *contains* text like `{{TITLE}}` (in the template's walkthrough, for example). If the body went in first, the loop above would wrongly replace those mentions too.

@@ 340-343
**`report` — the summary printed in the terminal**: the totals, then one indented line per problem. The `·` dot is swapped for `|` because some Windows terminals can't print it.

@@ 346-347
**`new_walkthrough` — the `--new` helper.** Find where the file's walkthrough should go.

@@ 348-350
**Never overwrite.** If a walkthrough already exists, refuse and return `1` (failure). One mistyped command must never destroy hours of written explanations.

@@ 351
Read the source file.

@@ 352
**One `TODO` note per non-blank line**: a marker with the line number, then `TODO`. The author replaces each `TODO`, merging neighbouring lines into ranges where that reads better.

@@ 353
**The header**: the file's current fingerprint between dashes, and a `TODO` for the introduction.

@@ 354
Write the walkthrough: the header followed by all the notes.

@@ 355
Save the first **snapshot** of the source, so `--reanchor` works from day one.

@@ 356-357
Report where the file was created, and return `0` (success).

@@ 360-366
**`stamp_walkthrough` — the `--stamp` helper**, run after the explanations have been checked against the current code:

1. find the walkthrough and read the current source;
2. replace the walkthrough's `fingerprint:` line with a fresh one (`count=1` changes only the first match);
3. save a fresh snapshot;
4. report and return success.

Stamping is deliberately manual: the builder can *notice* that code changed, but only a person can confirm the explanation still matches.

@@ 369-378
**`reanchor_walkthrough` — the `--reanchor` helper.**

1. Find the snapshot and the walkthrough. If either is missing, explain what's needed and return `1`.
2. Build the line mapping from the snapshot (the old version) to the current file.
3. Rewrite the walkthrough with `reanchor_text`, and save it.
4. Print the file name followed by every report line. `[f"…", *report]` builds one list from a first item plus all of `report`'s items.

It never stamps: moved notes still need a human's approval.

@@ 381
**`main` — what happens when you run `build.py`.** It returns an exit code.

@@ 382
Create the argument parser, with a description for the help text.

@@ 383
`--strict` is an on/off switch (`store_true`).

@@ 384-386
`--new`, `--stamp` and `--reanchor` each take a path (shown as `PATH` in the help text).

@@ 387
**Read what was actually typed.** Unknown options stop the program with a helpful message.

@@ 388
**A dict from option name to the function that handles it.** Functions are values in Python, so they can be stored in a dict like anything else.

@@ 389-391
**Dispatch.** For each helper command: if its option was given (`getattr(args, name)` reads the attribute whose name is in `name`), convert the path to project-relative form, run the function, and return its exit code. Nothing else runs.

The first version used three separate `if` blocks. The dict makes adding a fourth command a one-line change.

@@ 392
**Normal build.** Read `book.toml` and parse it.

@@ 393
Create the `Book`.

@@ 394
**Build and save** the page, at the path named by `output` in the settings.

@@ 395
Print the report.

@@ 396
**Is anything incomplete?** `True` if at least one file isn't fully explained, or is stale.

@@ 397
**The exit code.** In `--strict` mode any problem or incomplete file means failure (`1`); otherwise success (`0`). Robots such as CI read this number (§4.6).

@@ 400-401
**The entry point.** When a file is run directly, Python sets `__name__` to `"__main__"`; when it is imported, `__name__` is the module's name. So `main()` runs only when you run the file — the tests can `import build` without building the book.
