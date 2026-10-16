---
fingerprint: 21cc3733298c5a59
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

@@ 55-59
**`Place` — where one old line ended up in the new version.** It has three fields:

- `first` and `last` — the new line numbers that the old line now covers. Usually they are equal. When an edit turned one line into several, the old line's place stretches over all of them;
- `edited` — whether the line's code changed, rather than just moved.

`frozen=True` makes every `Place` read-only once it is made. A `Place` is a *fact* about two versions of a file, and nothing should quietly change it later.

@@ 62-68
**`Coverage` — the score card for one file:**

- `path` — the file;
- `lines` — total lines;
- `required` — non-blank lines, which need explaining;
- `explained` — how many required lines have an explanation;
- `stale` — `True` if the code changed after it was explained.

@@ 70-72
`percent` is the share of required lines explained, out of 100. `@property` lets us read it like a field (`cov.percent`), although it is calculated fresh each time, so it can never be out of date.

The **conditional expression** `A if condition else B` guards against dividing by zero: a file with nothing to explain counts as 100 % explained.

@@ 74-76
`complete` is `True` only when **every** required line is explained **and** the file hasn't changed since.

@@ 79-80
**`read_text` — read any file safely:**

1. `read_bytes()` reads the raw bytes.
2. `.decode("utf-8")` turns them into text **using UTF-8 explicitly** — this prevents the mojibake of §0.2.
3. `.replace("\r\n", "\n")` converts Windows line endings to `\n`, so a file has the same fingerprint on every operating system.

@@ 83-85
**`write_text` — write any file safely:**

- `path.parent.mkdir(parents=True, exist_ok=True)` first creates the folder the file goes in, and any missing folders above it, without complaining if they already exist.
- It then writes the text as UTF-8 with Linux-style newlines (`newline="\n"`), so the file is byte-for-byte identical on Windows and Linux.

Every file this program writes goes through this one function, so those two promises hold everywhere.

@@ 88-89
**`fingerprint` — the magic blender:**

1. Encode the text as bytes.
2. Blend it with SHA-256.
3. Write the result as hexadecimal (`hexdigest`).
4. Keep the first 16 characters (`[:16]` is a **slice**). That is still 2⁶⁴ possibilities.

@@ 92-93
**`walk_file_for`** gives the walkthrough's location for a project file: the walkthroughs folder mirrors the project, with `.md` added (`docs/zero_to_hero/build.py` → `walkthroughs/docs/zero_to_hero/build.py.md`). `f"{rel}.md"` is an **f-string**: `{rel}` is replaced by the value of `rel`.

@@ 96-97
**`snapshot_for`** gives the location of a project file's snapshot. It mirrors the project inside `.snapshots`, adding `.snap` to the name (`tasks.py` → `.snapshots/tasks.py.snap`).

!!! warn "Careful — why the `.snap` ending matters"
    The first design kept each copy's original name. Then the snapshot of `.gitignore` would itself be a file called `.gitignore`, and Git obeys `.gitignore` files in every folder. The snapshot of `pyproject.toml` might be mistaken for a real project by tools that search for one. Adding `.snap` makes every copy **inert**: no tool recognises it as anything special.

@@ 100-102
**`repo_relative`** turns whatever path the user typed into a project-relative one.

- If the typed path is absolute, use it; otherwise glue it onto `Path.cwd()`, the terminal's current folder.
- Then make it absolute (`resolve`), cut off the project root (`relative_to`), and write it with forward slashes (`as_posix`).

@@ 105-109
**`source_lines` — split text into lines.** `split("\n")` cuts at every newline. A tidy file ends with a newline, which leaves one empty string at the end — not a real line — so `lines[-1]` (the last item) is removed with `.pop()` when it is empty. Without this, every file would seem to have one extra line.

@@ 112
**`parse_walkthrough` — read a walkthrough's text into its three parts.** It returns a **tuple** of:

1. a dict of header settings;
2. the introduction text;
3. a list of `Note`s.

It receives the *text*, not a file path, so it never touches the disk. That makes it a pure function that tests can feed with any text they like.

@@ 113
`meta` (short for *metadata*, "data about data") starts as an empty dict for the header values.

@@ 114-115
**The header.** If the text begins with three dashes, there is a header.

- `text[4:]` skips those four characters (the dashes plus the newline).
- `.partition("\n---\n")` splits the rest at the first closing dash line into three pieces: before, the separator itself, and after.
- **Tuple unpacking** assigns the three pieces at once. `_` is the conventional name for "a value we don't need". `text` becomes everything after the header.

@@ 116-118
For each header line, split at the first `:` into key and value, trim the spaces from both (`.strip()`) and store them. So `fingerprint: 3f9a…` becomes `meta["fingerprint"] == "3f9a…"`.

@@ 119-120
Two empty lists to fill: `intro` for the introduction's lines, and `notes` for the `Note`s.

@@ 121
Walk through the body one line at a time. The `for` loop runs its indented block once per line.

@@ 122
Try the marker pattern on this line. `.match` returns a *match object* for a marker, or `None` otherwise.

@@ 123-125
**If the line is a marker**, start a new note.

- `mark[1]` is the captured start number; `int(...)` turns `"12"` into `12`.
- `mark[2] or start` uses the end number if there is one, otherwise the start (`or` gives its left side if that is "truthy", else its right side).

@@ 126-127
**Otherwise, if a note has already started**, this line belongs to the latest note (`notes[-1]`). `+=` adds it, plus the newline that `split` removed.

@@ 128-129
**Otherwise** — before the first marker — the line belongs to the introduction.

@@ 130
Return the three parts, gluing the introduction's lines back together with newlines.

@@ 133-135
**`is_explained`** checks that a note's text is non-empty **and** doesn't start with `TODO`. This covers both the `TODO` skeletons from `--new` and the `TODO(review)` flags from `--reanchor`.

!!! why "Why treat TODO as 'not explained'?"
    If placeholders counted, a freshly generated skeleton would show 100 % coverage, and the honesty check would be fooled by its own helper.

@@ 138
**`segments` — chop a file into consecutive stretches**, each covered by one note or by none. It returns two things: the list of `Segment`s, and a list of problems found (bad notes).

In the first version of the book this was a method that wrote problems straight into the `Book`. Turning it into a separate function that *returns* its problems made it possible to test on its own.

@@ 139-141
`result` and `problems` start empty. `cursor` is a finger pointing at the first line not yet assigned to a stretch; it starts at line 1.

@@ 142
Visit the notes **in order of their first line**. `sorted(...)` returns a sorted copy. `key=lambda n: n.start` says what to sort by: a **lambda** is a tiny unnamed function, here "given a note `n`, give back `n.start`".

@@ 143-145
**Reject impossible notes.** A note is bad if it starts before the cursor (it overlaps the previous note), ends before it starts, or ends beyond the last line. Bad notes are recorded as problems and skipped with `continue` ("go straight to the next item"). Overlaps are forbidden so that each line has exactly one explanation and coverage can't be double-counted.

@@ 146-147
**A gap before this note?** The lines between the cursor and the note's start have no note. Record them as a stretch with `None` in the note position.

@@ 148-149
Record the note's own stretch, then move the cursor to just after it.

@@ 150-151
**A gap at the end?** If the cursor hasn't passed the last line, the tail of the file has no notes. Record it as one more stretch.

@@ 152
Return both lists. Together the stretches cover every line exactly once, in order.

@@ 155
**`line_mapping` — where did each old line go?** It receives the lines of the old version (the snapshot) and of the new version. It returns a dict from each *old line number* to that line's `Place` in the new version.

@@ 156
Start with an empty dict. The annotation `dict[int, Place]` tells the type checker what it will hold.

@@ 157
`difflib.SequenceMatcher(a=old, b=new, autojunk=False)` compares the two lists of lines. `.get_opcodes()` then describes the change as a list of **operations** that turn the old version into the new one. Each operation is five values:

- `tag` — what happened: `"equal"` (these lines are unchanged), `"replace"` (these old lines became those new lines), `"delete"` (these old lines are gone) or `"insert"` (these new lines are brand new);
- `i1`, `i2` — where the operation starts and stops in the old list;
- `j1`, `j2` — the same in the new list.

Positions count from 0, and the stop position is *not* included — Python's usual **half-open** ranges, exactly like `range(i1, i2)`.

| Old lines | New lines | Operations |
| :-- | :-- | :-- |
| `a`, `b`, `c` | `a`, `B`, `c` | equal `a` · replace `b` → `B` · equal `c` |
| `a`, `b`, `c` | `new`, `a`, `c` | insert `new` · equal `a` · delete `b` · equal `c` |

`autojunk=False` switches off a speed shortcut that ignores very common lines. In code, common lines such as blank lines and lone closing brackets matter.

@@ 158-159
**Deleted** old lines have no new place, and **inserted** new lines have no old line to come from, so both kinds of operation are skipped (`continue`). A note whose lines were all deleted therefore finds no places, and is dropped later. New lines that nobody has explained yet show up in the book as *not explained*.

@@ 160
For every old line in an `equal` or `replace` block — `k` counts 0, 1, 2… through the block…

@@ 161
…line it up with the new line in the same position of the new block. If the new block is *shorter*, `min(…)` stops at its last line, so the leftover old lines all point there.

@@ 162
The **last** old line of the block also takes any *extra* new lines: if the new block is longer, its `last` stretches to the block's final line (`j2 - 1`). Every other old line covers exactly one new line.

!!! kid "Explain like I'm six — two rows of chairs"
    Put the old row of chairs and the new row side by side, lined up from the left. Chair 1 faces chair 1, chair 2 faces chair 2, and so on. If the new row is longer, the last old chair looks after every leftover new chair. If it is shorter, the extra old chairs all face the last new one.

For an `equal` block both rows have the same length, so every line simply faces its twin.

@@ 163
Record the place. The `+ 1`s convert difflib's positions, which count from 0, into line numbers, which count from 1. In `edited=tag == "replace"`, the `==` *compares*, and its answer — `True` or `False` — is what gets stored: a line is edited exactly when it came from a `replace` block.

For example, with old lines `a`, `b`, `c` and new lines `a`, `B1`, `B2`, `c`, the mapping is: 1 → `Place(1, 1, edited=False)`, 2 → `Place(2, 3, edited=True)`, 3 → `Place(4, 4, edited=False)`. `tests/test_build.py` checks exactly these values.

@@ 164
Return the finished mapping.

@@ 167
**`reanchor_text` — move every note in a walkthrough to its lines' new places.** It receives the walkthrough's text and the mapping. It returns the new text, plus a report of everything that needs a human's attention.

@@ 168-170
`output` collects the lines of the new walkthrough, and `report` the messages. Two on/off switches are written on one line (`dropping = review = False` sets both):

- `dropping` — "skip the text of the current note, because its code is gone";
- `review` — "the next line of text needs a `TODO(review)` label".

@@ 171
Go through the walkthrough line by line.

@@ 172
Is this line a note marker?

@@ 173
If it is…

@@ 174
…read its start and end line numbers. A single-line marker uses the start number for both.

@@ 175
`places` collects the new places of the note's old lines. Lines with no place — deleted ones — are left out by `if n in mapping`.

@@ 176-179
**No places at all** means every line the note explained was deleted. Then the note is dropped: record a report message, and skip the marker (`continue`). The `dropping` switch makes the lines that follow — the note's text — be skipped too.

@@ 180
The note's new range runs from the smallest `first` to the largest `last` among its places. The values are fed to `min` and `max` by **generator expressions**: `p.first for p in places` produces the numbers one by one, without building a list first.

@@ 181
The note **needs review** if either:

- its **size** changed — lines were inserted inside it, or some of its lines were deleted. `high - low` is how far apart the new ends are, and `end - start` how far apart the old ones were, so comparing the two compares the sizes;
- or any of its lines was **edited** (`any(…)` is true if at least one place says so).

A note whose lines only *moved* passes both tests: it follows them silently, and no human is needed.

@@ 182-183
If the note needs review, say so in the report, showing its old and new ranges.

@@ 184
Write the new marker: a single number if the note now covers one line, otherwise a range.

@@ 185-186
A text line while `dropping` is on belongs to a dropped note, so skip it.

@@ 187-189
The first non-blank text line after a marker that needs review gets the prefix `TODO(review)`, which makes `is_explained` treat the note as unexplained. A line that already starts with `TODO` is left as it is, so running `--reanchor` twice can never produce a doubled prefix. Then the switch turns off, so only the first line is touched.

@@ 190-191
Every other line is copied unchanged.

@@ 192
Return the rebuilt walkthrough text and the report.

@@ 195
**`highlight_lines` — colour a file and return one HTML string per line.**

@@ 196-199
**`try` / `except`.** Ask Pygments for the lexer matching the file name. If it doesn't know the name, it raises `ClassNotFound`; we catch that and fall back to plain text.

`stripnl=False` is vital: by default Pygments drops blank lines at the start and end, which would shift every line number.

@@ 200
**Highlight, then split.** `nowrap=True` means "just the coloured spans, no surrounding box". Pygments closes and reopens its colour tags at every line break, so splitting at `"\n"` gives one valid HTML piece per line.

@@ 201-202
**Safety net.** If highlighting produced *fewer* lines than the file has, don't trust it. Fall back to the plain lines, escaped so that `<` displays correctly. Wrong colours are acceptable; wrong line numbers are not.

@@ 203
Return exactly `count` lines. The slice drops the extra empty item left by the final newline.

@@ 206
**`class Book:`** — a **class** is a blueprint for an object that bundles *data* with *behaviour*. A `Book` remembers the settings, every file's score card and the problems found. Its methods do the work.

@@ 207
`__init__` runs when a `Book` is created: `Book(config)`. `self` is the new object, and `config` is the dict read from `book.toml` — typed `dict[str, Any]` (see line 26).

@@ 208-212
The `Book`'s memory:

- `config` — the settings;
- `coverage` — a dict from file path to its score card;
- `problems` — a list of human-readable problem messages;
- `abbreviations` — the hover definitions, read once;
- `note_md` — one Markdown converter for walkthrough notes, created once and reused for hundreds of notes.

@@ 214-216
**`note_html` — convert one note's Markdown to HTML.** `.reset()` clears the converter's memory of the previous note so notes never leak into each other. The abbreviation definitions are attached after a blank line, then the note is converted.

@@ 218
**`render_walkthrough` — the heart of the book.** It returns the HTML of one file's whole walkthrough, and records the file's score card.

@@ 219
Work out the source file's path and its walkthrough's path in one line (tuple unpacking).

@@ 220-222
**Missing pieces.** If either file is missing, record a problem and return a red warning instead of crashing. One missing explanation shouldn't stop the whole book from building, but it must be visible.

@@ 223-224
Read the source file and split it into lines.

@@ 225
Read the walkthrough file and parse it into its three parts.

@@ 226
Highlight the source: one coloured HTML string per line.

@@ 227
**Which lines need explaining?** A **set comprehension** collects the numbers of non-blank lines. `enumerate(lines, 1)` counts from 1, because humans number lines from 1.

@@ 228-229
`explained` will collect the numbers of lines that turn out to be explained (`set()` makes an empty set; `{}` would make a dict). `rows` will collect the HTML of each row.

@@ 230-231
**Cut the file into stretches** with `segments` (line 131). Any problems it found are added to the book's list, each prefixed with the file's path so the message says *which* walkthrough is broken. `+=` on a list appends all the new items.

@@ 232
Go through the stretches in order, unpacking each into `start`, `end` and `note`.

@@ 233
`range(start, end + 1)` gives the line numbers in this stretch. `range` stops *before* its second number, hence the `+ 1`.

@@ 234
**The code side of the row**: for each line number, a line-number label followed by that line's highlighted HTML, joined with newlines.

`code[n - 1]` uses `n - 1` because Python lists count from **0** while line numbers count from **1** — the classic "off-by-one" trap.

@@ 235-237
**Case 1 — a real explanation.** Mark the lines as explained; the row gets the normal style, and the note is converted to HTML.

@@ 238-239
**Case 2 — no explanation, but there is code here.** The row gets the `missing` style (a red bar) and a red "Not explained yet." message.

@@ 240-241
**Case 3 — only blank lines.** Nothing to explain: a compact `blank` row with no explanation box.

@@ 242-243
Build the row's HTML in two steps — first the code box, then the note box and the closing tags — and add it to `rows`. Two short steps keep each line within the 120-character limit that Ruff checks.

@@ 244
**Stale?** The fingerprint recorded in the walkthrough's header must equal a fresh fingerprint of the code. A missing fingerprint (`None`) also counts as stale.

@@ 245-246
**Record the score.** `required & explained` is the **intersection** of the two sets: lines that are both required and explained. Blank lines inside a multi-line note don't inflate the count.

@@ 247
The red **"code changed since explained"** badge if stale, otherwise nothing.

@@ 248-251
**The header bar**: the file's path, its line count and its coverage. The parentheses let one string span several lines; Python glues adjacent strings together automatically. `{cov.percent:.0f}` formats the number with no decimal places.

@@ 252
The file's introduction, converted from Markdown and wrapped in its own box.

@@ 253
**Assemble the walkthrough**: a `<section>` holding the header bar, the introduction and every row.

@@ 255
**`scan_sources` — find every file in the project that must be explained.**

@@ 256-257
`rules` is the `[coverage]` group from `book.toml`; `found` collects matching paths.

@@ 258
**`os.walk(REPO_ROOT)`** visits the project root and every folder beneath it. For each folder it gives the folder's path, its sub-folder names and its file names.

@@ 259
**Pruning.** The list of sub-folders is replaced *in place* with a sorted copy that leaves out the names in `prune`.

`dirs[:] = …` changes the very list `os.walk` will use to decide where to go next. Plain `dirs = …` would make a new list that `os.walk` never sees. Sorting makes the ledger's order the same on every computer.

@@ 260
For each file name in this folder, in sorted order…

@@ 261
…build its project-relative path with forward slashes, as a `PurePosixPath`.

@@ 262
**Does it match any `include` pattern?** `any(...)` is `True` if at least one pattern matches. It stops at the first match.

@@ 263-264
**Keep it** if it was wanted and matches no `exclude` pattern.

@@ 265
Return the list of every file that must be explained.

@@ 267-268
**`ledger_html` — build the coverage table at the back of the book.** `rows` holds one table row per file.

@@ 269
For every file the scan says must be explained…

@@ 270
…check whether it has a walkthrough file.

@@ 271-273
**It has a walkthrough, but no chapter has shown it yet** — render it anyway, so its coverage is counted, *and* record a problem: an explanation that exists but never appears in the book helps nobody.

!!! real "Real world — a gap this closed"
    In Phase 1, 34 new walkthroughs were written before the chapter that shows them — and the strict check still passed, because it only asked whether each file was *explained*, not whether the explanation was *shown*. A check that passes while the reader sees nothing is a gap, so this line now makes it fail.

@@ 274-277
**It has no walkthrough at all.**

- Count its lines anyway and record a score card with zero explained, so the totals honestly include it.
- `sum(1 for x in lines if x.strip())` adds 1 for every non-blank line.
- Also record a problem.

!!! real "Real world — a bug this fixed"
    The first version skipped files without walkthroughs when adding up totals. The very first build therefore announced "0/0 lines explained (100.0 %)" — a perfect score for doing nothing. **A check that can report success when nothing was done is worse than no check.**

@@ 278
Fetch this file's score card. One of the branches above guarantees it exists.

@@ 279-287
**Choose the status label and its colour** with a chain of conditional expressions, read top to bottom:

- complete → green;
- otherwise stale → red;
- otherwise has a walkthrough → amber "in progress";
- otherwise → red "not explained".

Ruff's formatter spread the chain over several lines so each condition is easy to see.

@@ 288-292
Add the table row: path, line count, explained/required with the percentage, and the coloured status pill.

@@ 293-294
The heading row, then the whole table, wrapped in a box that scrolls sideways on narrow screens.

@@ 295
Return a **Total** line followed by the table.

@@ 297-301
**`totals` — one line summarising the whole project's coverage.** Add up the required and explained lines across every score card, work out the percentage (guarding against dividing by zero), and format the line. `:,` adds thousands separators and `.1f` shows one decimal place.

@@ 303-304
**`build` — assemble the whole book.** `blocks` remembers each directive found in the chapters: a placeholder name → (kind, argument).

@@ 306-309
**`park` — a function inside a function.** It is called for every directive found:

1. invent a unique placeholder such as `ZTHBLOCK3X`;
2. remember what the directive asked for;
3. return the placeholder surrounded by blank lines, to replace the directive in the chapter.

!!! key "Key idea — why park directives?"
    Walkthrough HTML must **not** go through the Markdown converter, which would mangle the code. So each directive is swapped for a harmless word, everything is converted, and then the real HTML is swapped back in (lines 311–312). The blank lines make Markdown wrap the placeholder in its own `<p>…</p>`, which is exactly what we search for.

@@ 311
**Read every chapter in the order `book.toml` gives, parking its directives.** A **list comprehension**; `DIRECTIVE.sub(park, text)` replaces each directive with whatever `park` returns.

@@ 312-314
**The main Markdown converter**, with our extensions plus `toc`. `toc` gives every heading an `id` you can link to, and records the headings for the sidebar.

- `[*EXTENSIONS, "toc"]` builds a new list: everything in `EXTENSIONS`, then `"toc"`. The `*` spreads a list's items.
- `{**EXT_CONFIG, …}` does the same for dicts.

@@ 315
**Convert the whole book in one go**, with the abbreviations attached once at the end. Converting everything together lets `toc` make every heading's `id` unique across all chapters.

@@ 316-318
**Each walkthrough must be shown exactly once.** `walked` lists the file named by every `!walk` directive, in order. `repeated` collects the files that appear more than once: the braces build a **set**, which keeps each file once, and `sorted` fixes the order. Each one becomes a problem. Showing the same file twice makes the book longer for no gain, and usually means a `!walk` line was meant to name a different file.

@@ 319
**Render every parked walkthrough** — a dict comprehension keeping only `walk` blocks.

@@ 320
**Render the ledger last** (`|=` merges entries into the dict), so every walkthrough shown in a chapter already has its score card.

@@ 321-322
**Swap the real HTML back in** for each `<p>placeholder</p>`.

@@ 323
**Make wide tables scrollable on phones** by wrapping each table in a `tw` box.

@@ 324
**Get the list of headings for the sidebar.** The `toc` extension attaches `toc_tokens` to the converter *while the program runs*, so the type checker — which reads the code beforehand — can't know it exists. `getattr(md, "toc_tokens", [])` reads the attribute by name, and gives an empty list if it is missing. The label `list[dict[str, Any]]` tells mypy what we expect to get.

@@ 325
Hand the body and headings to `page()`.

@@ 327-328
**`page` — pour everything into the template.** `links` collects one sidebar link per heading.

@@ 330-334
**`visit` — turn the tree of headings into flat sidebar links.** For each heading:

1. make its name safe (unescape, then escape exactly once);
2. add a link whose class (`h1`, `h2`, `h3`) lets the CSS indent it;
3. **call itself** on the heading's children.

A function that calls itself is using **recursion**, the natural way to walk a tree.

@@ 336
Start the walk from the top-level headings.

@@ 337
**Count the words**: replace every HTML tag with a space (`re.sub`), find every run of word characters (`re.findall`), and count them.

@@ 338
Read the template.

@@ 339-345
**The values for the template's blanks**:

- the escaped title and subtitle;
- the word count and coverage totals;
- the build time (`strftime` formats a date as text);
- the sidebar links.

@@ 346-347
**Fill the blanks**: replace `{{NAME}}` with each value. The placeholder is built with `+` because inside an f-string, `{{` means a single literal `{`, which would make an f-string version unreadable.

@@ 348
**Insert the body last — on purpose.** The book *contains* text like `{{TITLE}}` (in the template's walkthrough, for example). If the body went in first, the loop above would wrongly replace those mentions too.

@@ 350-353
**`report` — the summary printed in the terminal**: the totals, then one indented line per problem. The `·` dot is swapped for `|` because some Windows terminals can't print it.

@@ 356-357
**`new_walkthrough` — the `--new` helper.** Find where the file's walkthrough should go.

@@ 358-360
**Never overwrite.** If a walkthrough already exists, refuse and return `1` (failure). One mistyped command must never destroy hours of written explanations.

@@ 361
Read the source file.

@@ 362
**One `TODO` note per non-blank line**: a marker with the line number, then `TODO`. The author replaces each `TODO`, merging neighbouring lines into ranges where that reads better.

@@ 363
**The header**: the file's current fingerprint between dashes, and a `TODO` for the introduction.

@@ 364
Write the walkthrough: the header followed by all the notes.

@@ 365
Save the first **snapshot** of the source, so `--reanchor` works from day one.

@@ 366-367
Report where the file was created, and return `0` (success).

@@ 370-376
**`stamp_walkthrough` — the `--stamp` helper**, run after the explanations have been checked against the current code:

1. find the walkthrough and read the current source;
2. replace the walkthrough's `fingerprint:` line with a fresh one (`count=1` changes only the first match);
3. save a fresh snapshot;
4. report and return success.

Stamping is deliberately manual: the builder can *notice* that code changed, but only a person can confirm the explanation still matches.

@@ 379-390
**`reanchor_walkthrough` — the `--reanchor` helper.**

1. Find the snapshot and the walkthrough. If either is missing, explain what's needed and return `1`.
2. Read the current source, and build the line mapping from the snapshot (the old version) to it.
3. Rewrite the walkthrough with `reanchor_text`, and save it.
4. **Move the snapshot forward** to the current source. From now on, the snapshot is the version that the walkthrough's line numbers refer to.
5. Print the file name followed by every report line. `[f"…", *report]` builds one list from a first item plus all of `report`'s items.

It never stamps: the fingerprint still belongs to the last *approved* version, so the strict check keeps failing until a person has reviewed the moved notes.

!!! real "Real world — a bug this step fixed"
    The first version did not do step 4. Re-anchoring twice before a stamp then went wrong: the second run compared the *stamped* version with the newest one, and moved notes that had already been moved once. The builder's own tests now include exactly that case.

@@ 393
**`main` — what happens when you run `build.py`.** It returns an exit code.

@@ 394
Create the argument parser, with a description for the help text.

@@ 395
`--strict` is an on/off switch (`store_true`).

@@ 396-398
`--new`, `--stamp` and `--reanchor` each take a path (shown as `PATH` in the help text).

@@ 399
**Read what was actually typed.** Unknown options stop the program with a helpful message.

@@ 400
**A dict from option name to the function that handles it.** Functions are values in Python, so they can be stored in a dict like anything else.

@@ 401-403
**Dispatch.** For each helper command: if its option was given (`getattr(args, name)` reads the attribute whose name is in `name`), convert the path to project-relative form, run the function, and return its exit code. Nothing else runs.

The first version used three separate `if` blocks. The dict makes adding a fourth command a one-line change.

@@ 404
**Normal build.** Read `book.toml` and parse it.

@@ 405
Create the `Book`.

@@ 406
**Build and save** the page, at the path named by `output` in the settings.

@@ 407
Print the report.

@@ 408
**Is anything incomplete?** `True` if at least one file isn't fully explained, or is stale.

@@ 409
**The exit code.** In `--strict` mode any problem or incomplete file means failure (`1`); otherwise success (`0`). Robots such as CI read this number (§4.6).

@@ 412-413
**The entry point.** When a file is run directly, Python sets `__name__` to `"__main__"`; when it is imported, `__name__` is the module's name. So `main()` runs only when you run the file — the tests can `import build` without building the book.
