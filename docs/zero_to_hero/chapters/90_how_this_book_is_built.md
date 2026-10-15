# Part X — How this book is built

This part is placed near the end, but you can read it any time. It shows the *line-by-line format* used for the whole project. And it is the first real code in the project, so it is explained exactly like everything else will be.

## X.1 Why a program builds this book

The book you are reading is a single HTML file. We could have typed that HTML by hand, but three problems would appear quickly:

1. **It would be huge and painful to edit.** Thousands of lines of HTML tags around every sentence.
2. **It would drift away from the code.** When a code file changes, nothing would tell us that its explanation is now wrong.
3. **"Every line is explained" would be a promise nobody could check.**

So the book is *generated*. We write chapters in a simple text format (Markdown) and explanations in small *walkthrough* files. A Python program, `build.py`, then assembles them into the HTML file. While doing so it checks the coverage and freshness of every explanation.

!!! kid "Explain like I'm six"
    Instead of hand-copying a whole book every time one page changes, you keep each page separately and let a machine bind them into a book. The machine also checks each page against the thing it describes and puts a red sticker on any page that's out of date.

## X.2 The pieces

All of these live in `docs/zero_to_hero/`:

| File or folder | What it is |
| :-- | :-- |
| `book.toml` | The settings: the book's title, the order of the chapters, and which project files must be explained |
| `chapters/*.md` | The chapters, written in Markdown |
| `walkthroughs/…/*.md` | One explanation file per code file, mirroring the project's folders. The explanation of `docs/zero_to_hero/build.py` lives at `walkthroughs/docs/zero_to_hero/build.py.md` |
| `abbreviations.md` | Short definitions that appear when you hover over words like API |
| `template.html` | The empty "shell" of the page — styles, sidebar, buttons — with blanks for the content |
| `build.py` | The program that puts it all together |
| `tests/test_build.py` | Automatic tests for `build.py` (the checker is itself checked) |
| `.snapshots/…` | A copy of each source file as it was when its walkthrough was last stamped. Used to move notes when code changes (§X.6) |
| `zero_to_hero.html` | **The result** — the book you are reading |

The two libraries the builder needs (Python-Markdown and Pygments) are pinned in the project's root `pyproject.toml`, in a group called `docs` (§5.0.2). In the very first version of the book they were listed in a separate `requirements.txt`. That file was removed when the project gained its uv workspace, so the versions are written in exactly one place.

## X.3 Markdown in sixty seconds

Markdown is a way of writing formatted text using ordinary symbols. A converter turns it into HTML.

| You write | You get |
| :-- | :-- |
| `# Title` | A big heading (`##` smaller, `###` smaller still) |
| `**bold**` and `*italic*` | **bold** and *italic* |
| `` `code` `` | `code` |
| `- item` on separate lines | A bulleted list |
| `1. step` on separate lines | A numbered list |
| `[text](https://example.com)` | A link |
| Lines with vertical bars (\|) between cells | A table (like this one) |
| Three back-ticks, a language name, the code, three back-ticks | A highlighted code block |
| `!!! kid "Title"` followed by indented lines | One of the coloured boxes (an *admonition*) |

## X.4 How a walkthrough file works

A walkthrough file has three parts.

**1. A header** between two lines of three dashes, recording the code file's **fingerprint** at the moment it was explained:

```
---
fingerprint: 3f9a1c0be27d4e51
---
```

**2. An introduction** — ordinary Markdown describing the whole file.

**3. Notes.** Each note starts with a line containing two `@` signs and a line number (like `@@ 12`) or a range (like `@@ 12-14`). The explanation of those lines follows in Markdown:

```
@@ 1
This line ...

@@ 2-4
These three lines ...
```

Inside a chapter, a line that contains only the word `!walk` followed by a file path tells the builder: *"put the line-by-line walkthrough of this file here"*. A line containing only `!ledger` inserts the coverage table.

## X.5 Fingerprints

How can a program notice that a file changed since it was explained? It can't keep a copy of every old version. Instead it keeps a **fingerprint**.

!!! kid "Explain like I'm six — the magic blender"
    Imagine a magic blender. You drop in any amount of text — one word or a whole book — and it always pours out a short code like `3f9a1c0be27d4e51`. Two magic rules:

    - the **same** text always gives the **same** code;
    - change even **one letter**, and the code comes out **completely different**.

    So to know whether a file changed, you don't need the old file — only the old code.

The blender is a real algorithm called **SHA-256**, a *cryptographic hash function* used everywhere in computer security, including in Git and HTTPS certificates. SHA-256 produces 64 hexadecimal characters (digits `0–9` and letters `a–f`). We keep the first 16. That is still 2⁶⁴ ≈ 18 quintillion possibilities — far more than enough to notice an edit.

## X.6 Coverage and the ledger

For each code file the builder:

1. counts the **non-blank** lines (blank lines have nothing to explain);
2. marks the lines covered by a note that has real text — a note that is empty, or still says `TODO`, does not count;
3. shows any uncovered line in the book with a red bar and the words *"Not explained yet"*;
4. compares the recorded fingerprint with a fresh one, and shows a red **"code changed since explained"** badge if they differ.

Then it walks the whole project folder, finds every code file, and prints the [Coverage ledger](#coverage-ledger). Files with no walkthrough at all appear there as **not explained**. Nothing can hide.

### When code changes: re-anchoring

Notes are pinned to **line numbers**. Add one line at the top of a file and every note below it now points one line too high. In the first days of this book, fixing that meant renumbering notes by hand — slow and error-prone.

So the builder learned a trick. Whenever a walkthrough is **stamped**, the builder also saves a **snapshot**: a copy of the source file exactly as it was explained. Later, `--reanchor` compares the snapshot with the current file and works out where every unchanged line has moved:

- a note whose lines are all **unchanged** simply moves with them — no human needed;
- a note whose lines were **edited** moves to the new code that replaced them, and its text is prefixed with `TODO(review)`. It then counts as *not explained* until someone re-reads it and removes the prefix;
- a note whose lines were **deleted** is dropped, and the command prints what was dropped.

!!! kid "Explain like I'm six — seats in a theatre"
    Imagine a theatre where every seat has a name card. The theatre adds two new rows at the front. Every old seat now has a new number, but the *people* haven't changed — so you move each name card to its person's new seat number. If someone swapped seats with a stranger, you put a sticky note on their card: *"please check this one"*.

How does the builder know which lines are "the same"? Python's built-in **difflib** module finds the longest runs of lines that appear in both versions, in the same order — the same idea behind the "diff" view of any code-review tool.

!!! key "Key idea"
    Moving notes is automatic. **Approving** them is not: only a person can confirm that an explanation still matches the code. That is why `--reanchor` never stamps, and why changed notes are marked `TODO(review)`.

## X.7 Building the book yourself

!!! try "Try it yourself"
    With **uv** installed (§4.2), open a terminal in the project folder and run:

    1. `uv sync` — installs Python 3.13 and every tool the project needs (only needed once).
    2. `uv run tasks.py book` — builds the book in **strict** mode and prints a one-line summary.

    Then open `docs/zero_to_hero/zero_to_hero.html` in any browser.

**Strict** mode makes the builder **fail** if anything is unexplained or stale. The project's automatic checks (CI, §4.6) run exactly this on every change, so the book can never fall behind the code.

Three helper commands keep walkthroughs in step with the code:

- `build.py --new path/to/file.py` creates a walkthrough skeleton with an empty `TODO` note for every non-blank line, and a first snapshot;
- `build.py --reanchor path/to/file.py` moves the notes to follow edits made since the last stamp (§X.6);
- `build.py --stamp path/to/file.py` records the file's current fingerprint and snapshot, after its explanations have been reviewed.

## X.8 Python words you'll meet in `build.py`

`build.py` is the first Python program in this project. Its walkthrough explains every line, but a few words come up again and again, so here they are first.

| Word | Meaning | Tiny example |
| :-- | :-- | :-- |
| **variable** | A name that refers to a value | `title = "Dwarpal"` |
| **string** (`str`) | Text, in quotes | `"hello"` |
| **integer** (`int`), **float** | Whole numbers; numbers with a decimal point | `42`, `98.5` |
| **boolean** (`bool`) | `True` or `False` | `stale = False` |
| **None** | "Nothing here" | `result = None` |
| **list** | An ordered, changeable collection | `["a", "b"]` |
| **tuple** | An ordered collection that can't be changed | `(3, 7)` |
| **dict** | Labelled values, looked up by key | `{"title": "Dwarpal"}` |
| **set** | A collection with no duplicates and no order; fast "is it in here?" checks | `{1, 2, 3}` |
| **function** (`def`) | A named, reusable recipe. It takes inputs (*parameters*) and gives back an output (`return`) | `def double(x): return x * 2` |
| **class** | A blueprint for making objects that bundle data and functions together. Functions inside a class are called **methods** | `class Book: ...` |
| **object / instance** | One thing made from a class | `book = Book(config)` |
| **`self`** | Inside a method, "the object this method belongs to" | `self.title` |
| **module / import** | A file of Python code; `import` brings another module's tools into this file | `import re` |
| **`if` / `elif` / `else`** | Decisions | `if age >= 18: ...` |
| **`for` loop** | Repeat something for each item in a collection | `for line in lines: ...` |
| **comprehension** | A one-line way to build a list, set or dict from a loop | `[x * 2 for x in numbers]` |
| **f-string** | A string with values slotted in, marked by `f` before the quote | `f"{count} lines"` |
| **type hint** | A label saying what kind of value is expected. Python itself ignores it; tools and humans use it | `def read_text(path: Path) -> str:` |
| **exception** | An error signal that stops the normal flow; `try`/`except` catches it | `try: ... except ClassNotFound: ...` |
| **decorator** | A line starting with `@` that wraps or modifies the function or class below it | `@dataclass` |
| **indentation** | Python uses spaces at the start of a line to show what belongs inside what. Four spaces = one level | (everywhere) |

!!! warn "Careful — indentation is not decoration in Python"
    In many languages spacing is just for looks. In Python, **indentation is part of the meaning**: the lines indented under an `if` are the lines that run only when the condition is true. Get it wrong and the program means something different, or refuses to run.

## X.9 The code, line by line

### X.9.1 `book.toml` — the settings

!walk docs/zero_to_hero/book.toml

### X.9.2 `build.py` — the book binder

!walk docs/zero_to_hero/build.py

### X.9.3 `template.html` — the page shell

!walk docs/zero_to_hero/template.html

The builder's own tests (`tests/test_build.py`) are walked through in §5.0.7, alongside the other Phase 0 files.
