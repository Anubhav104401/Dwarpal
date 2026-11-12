"""Build the Zero-to-Hero book.

Markdown chapters plus line-by-line walkthroughs of the project's source files
are turned into ONE self-contained HTML file.

    python build.py                  build the book
    python build.py --strict         build, then fail if any source line is unexplained or stale
    python build.py --new PATH       write a walkthrough skeleton for a source file
    python build.py --stamp PATH     after reviewing a walkthrough, record PATH's fingerprint and a snapshot
    python build.py --reanchor PATH  move a walkthrough's line numbers to follow edits made since its last snapshot
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import html
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.util import ClassNotFound

BOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOOK_DIR.parents[1]
WALK_DIR = BOOK_DIR / "walkthroughs"
SNAP_DIR = BOOK_DIR / ".snapshots"
NOTE_MARK = re.compile(r"^@@ *(\d+)(?: *- *(\d+))? *$")
DIRECTIVE = re.compile(r"^!(walk|ledger)(?: +(\S+))? *$", re.MULTILINE)
FINGERPRINT_LINE = re.compile(r"^fingerprint:.*$", re.MULTILINE)
EXTENSIONS = ["extra", "admonition", "sane_lists", "codehilite"]
EXT_CONFIG = {"codehilite": {"css_class": "hl", "guess_lang": False}}


@dataclass
class Note:
    start: int
    end: int
    text: str


type Segment = tuple[int, int, Note | None]


@dataclass(frozen=True)
class Place:
    first: int
    last: int
    edited: bool


@dataclass
class Coverage:
    path: str
    lines: int
    required: int
    explained: int
    stale: bool

    @property
    def percent(self) -> float:
        return 100.0 if self.required == 0 else 100.0 * self.explained / self.required

    @property
    def complete(self) -> bool:
        return self.explained == self.required and not self.stale


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def walk_file_for(rel: str) -> Path:
    return WALK_DIR / f"{rel}.md"


def snapshot_for(rel: str) -> Path:
    return SNAP_DIR / f"{rel}.snap"


def repo_relative(arg: str) -> str:
    path = Path(arg) if Path(arg).is_absolute() else Path.cwd() / arg
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def source_lines(text: str) -> list[str]:
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return lines


def parse_walkthrough(text: str) -> tuple[dict[str, str], str, list[Note]]:
    meta: dict[str, str] = {}
    if text.startswith("---\n"):
        header, _, text = text[4:].partition("\n---\n")
        for line in header.splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    intro: list[str] = []
    notes: list[Note] = []
    for line in text.split("\n"):
        mark = NOTE_MARK.match(line)
        if mark:
            start = int(mark[1])
            notes.append(Note(start, int(mark[2] or start), ""))
        elif notes:
            notes[-1].text += line + "\n"
        else:
            intro.append(line)
    return meta, "\n".join(intro), notes


def is_explained(note: Note) -> bool:
    body = note.text.strip()
    return bool(body) and not body.startswith("TODO")


def segments(notes: list[Note], total: int) -> tuple[list[Segment], list[str]]:
    result: list[Segment] = []
    problems: list[str] = []
    cursor = 1
    for note in sorted(notes, key=lambda n: n.start):
        if note.start < cursor or note.end < note.start or note.end > total:
            problems.append(f"note @@ {note.start}-{note.end} overlaps or is out of range")
            continue
        if note.start > cursor:
            result.append((cursor, note.start - 1, None))
        result.append((note.start, note.end, note))
        cursor = note.end + 1
    if cursor <= total:
        result.append((cursor, total, None))
    return result, problems


def line_mapping(old: list[str], new: list[str]) -> dict[int, Place]:
    mapping: dict[int, Place] = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if tag not in ("equal", "replace"):
            continue
        for k in range(i2 - i1):
            first = j1 + min(k, j2 - j1 - 1)
            last = j2 - 1 if k == i2 - i1 - 1 else first
            mapping[i1 + k + 1] = Place(first + 1, last + 1, edited=tag == "replace")
    return mapping


def reanchor_text(text: str, mapping: dict[int, Place]) -> tuple[str, list[str]]:
    output: list[str] = []
    report: list[str] = []
    dropping = review = False
    for line in text.split("\n"):
        mark = NOTE_MARK.match(line)
        if mark:
            start, end = int(mark[1]), int(mark[2] or mark[1])
            places = [mapping[n] for n in range(start, end + 1) if n in mapping]
            dropping = not places
            if dropping:
                report.append(f"@@ {start}-{end}: its lines were deleted, so the note was dropped")
                continue
            low, high = min(p.first for p in places), max(p.last for p in places)
            review = high - low != end - start or any(p.edited for p in places)
            if review:
                report.append(f"@@ {start}-{end} -> {low}-{high}: code changed, marked TODO(review)")
            output.append(f"@@ {low}" if low == high else f"@@ {low}-{high}")
        elif dropping:
            continue
        elif review and line.strip():
            output.append(line if line.startswith("TODO") else f"TODO(review) {line}")
            review = False
        else:
            output.append(line)
    return "\n".join(output), report


def highlight_lines(text: str, filename: str, count: int) -> list[str]:
    try:
        lexer = get_lexer_for_filename(filename, stripnl=False)
    except ClassNotFound:
        lexer = TextLexer(stripnl=False)
    lines = highlight(text, lexer, HtmlFormatter(nowrap=True)).split("\n")
    if len(lines) < count:
        return [html.escape(line) for line in source_lines(text)]
    return lines[:count]


class Book:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.coverage: dict[str, Coverage] = {}
        self.problems: list[str] = []
        self.abbreviations = read_text(BOOK_DIR / config["abbreviations"])
        self.note_md = markdown.Markdown(extensions=EXTENSIONS, extension_configs=EXT_CONFIG)

    def note_html(self, text: str) -> str:
        self.note_md.reset()
        return self.note_md.convert(text + "\n\n" + self.abbreviations)

    def render_walkthrough(self, rel: str) -> str:
        source, walk = REPO_ROOT / rel, walk_file_for(rel)
        if not source.is_file() or not walk.is_file():
            self.problems.append(f"no source file or no walkthrough for {rel}")
            return f'<p class="todo">Walkthrough for <code>{html.escape(rel)}</code> is missing.</p>'
        text = read_text(source)
        lines = source_lines(text)
        meta, intro, notes = parse_walkthrough(read_text(walk))
        code = highlight_lines(text, source.name, len(lines))
        required = {n for n, line in enumerate(lines, 1) if line.strip()}
        explained: set[int] = set()
        rows: list[str] = []
        parts, problems = segments(notes, len(lines))
        self.problems += [f"{rel}: {p}" for p in problems]
        for start, end, note in parts:
            numbers = range(start, end + 1)
            code_html = "\n".join(f'<span class="ln">{n}</span>{code[n - 1]}' for n in numbers)
            if note and is_explained(note):
                explained.update(numbers)
                kind, side = "wrow", self.note_html(note.text)
            elif required.intersection(numbers):
                kind, side = "wrow missing", '<p class="todo">Not explained yet.</p>'
            else:
                kind, side = "wrow blank", ""
            row = f'<div class="{kind}"><pre class="hl"><code>{code_html}</code></pre>'
            rows.append(f'{row}<div class="wnote">{side}</div></div>')
        stale = meta.get("fingerprint") != fingerprint(text)
        cov = Coverage(rel, len(lines), len(required), len(required & explained), stale)
        self.coverage[rel] = cov
        badge = '<span class="pill bad">code changed since explained</span>' if stale else ""
        head = (
            f'<div class="whead"><code>{html.escape(rel)}</code>'
            f"<span>{cov.lines} lines · {cov.percent:.0f}% explained</span>{badge}</div>"
        )
        intro_html = f'<div class="wintro">{self.note_html(intro)}</div>'
        return f'<section class="walk">{head}{intro_html}{"".join(rows)}</section>'

    def scan_sources(self) -> list[str]:
        rules = self.config["coverage"]
        found: list[str] = []
        for folder, dirs, files in os.walk(REPO_ROOT):
            dirs[:] = sorted(d for d in dirs if d not in rules["prune"])
            for name in sorted(files):
                rel = PurePosixPath(Path(folder, name).relative_to(REPO_ROOT).as_posix())
                wanted = any(rel.full_match(p) for p in rules["include"])
                if wanted and not any(rel.full_match(p) for p in rules["exclude"]):
                    found.append(str(rel))
        return found

    def ledger_html(self) -> str:
        rows: list[str] = []
        for rel in self.scan_sources():
            has_walk = walk_file_for(rel).is_file()
            if rel not in self.coverage and has_walk:
                self.render_walkthrough(rel)
                self.problems.append(f"{rel}: its walkthrough is not placed in any chapter (add a !walk line)")
            elif rel not in self.coverage:
                lines = source_lines(read_text(REPO_ROOT / rel))
                self.coverage[rel] = Coverage(rel, len(lines), sum(1 for x in lines if x.strip()), 0, False)
                self.problems.append(f"{rel}: no walkthrough yet")
            cov = self.coverage[rel]
            label, tone = (
                ("complete", "ok")
                if cov.complete
                else ("stale", "bad")
                if cov.stale
                else ("in progress", "warn")
                if has_walk
                else ("not explained", "bad")
            )
            rows.append(
                f"<tr><td><code>{html.escape(rel)}</code></td><td>{cov.lines}</td>"
                f"<td>{cov.explained}/{cov.required} ({cov.percent:.0f}%)</td>"
                f'<td><span class="pill {tone}">{label}</span></td></tr>'
            )
        head = "<tr><th>File</th><th>Lines</th><th>Explained (non-blank)</th><th>Status</th></tr>"
        table = f'<div class="tw"><table><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'
        return f"<p><strong>Total:</strong> {self.totals()}</p>{table}"

    def totals(self) -> str:
        required = sum(c.required for c in self.coverage.values())
        explained = sum(c.explained for c in self.coverage.values())
        percent = 100.0 if required == 0 else 100.0 * explained / required
        return f"{len(self.coverage)} files · {explained:,}/{required:,} lines explained ({percent:.1f}%)"

    def build(self) -> str:
        blocks: dict[str, tuple[str, str]] = {}

        def park(match: re.Match[str]) -> str:
            key = f"ZTHBLOCK{len(blocks)}X"
            blocks[key] = (match[1], match[2] or "")
            return f"\n\n{key}\n\n"

        chapters = [DIRECTIVE.sub(park, read_text(BOOK_DIR / c)) for c in self.config["chapters"]]
        md = markdown.Markdown(
            extensions=[*EXTENSIONS, "toc"], extension_configs={**EXT_CONFIG, "toc": {"toc_depth": "1-3"}}
        )
        body = md.convert("\n\n".join(chapters) + "\n\n" + self.abbreviations)
        walked = [arg for kind, arg in blocks.values() if kind == "walk"]
        repeated = sorted({rel for rel in walked if walked.count(rel) > 1})
        self.problems += [f"{rel}: its walkthrough is placed more than once" for rel in repeated]
        fragments = {k: self.render_walkthrough(arg) for k, (kind, arg) in blocks.items() if kind == "walk"}
        fragments |= {k: self.ledger_html() for k, (kind, _) in blocks.items() if kind == "ledger"}
        for key, fragment in fragments.items():
            body = body.replace(f"<p>{key}</p>", fragment)
        body = body.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
        toc_tokens: list[dict[str, Any]] = getattr(md, "toc_tokens", [])
        return self.page(body, toc_tokens)

    def page(self, body: str, toc_tokens: list[dict[str, Any]]) -> str:
        links: list[str] = []

        def visit(tokens: list[dict[str, Any]]) -> None:
            for token in tokens:
                name = html.escape(html.unescape(token["name"]))
                links.append(f'<a class="h{token["level"]}" href="#{token["id"]}">{name}</a>')
                visit(token["children"])

        visit(toc_tokens)
        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", body)))
        page = read_text(BOOK_DIR / "template.html")
        values = {
            "TITLE": html.escape(self.config["title"]),
            "SUBTITLE": html.escape(self.config["subtitle"]),
            "META": f"{words:,} words · {self.totals()}",
            "BUILT": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "TOC": "\n".join(links),
        }
        for key, value in values.items():
            page = page.replace("{{" + key + "}}", value)
        return page.replace("{{BODY}}", body)

    def report(self) -> str:
        lines = [f"book: {self.totals()}".replace("·", "|")]
        lines += [f"  problem: {p}" for p in self.problems]
        # A file can also be incomplete without a "problem": explained once, then changed. Name those too.
        named = "\n".join(self.problems)
        for cov in self.coverage.values():
            if not cov.complete and cov.path not in named:
                changed = ", code changed since explained" if cov.stale else ""
                lines.append(f"  incomplete: {cov.path} ({cov.explained}/{cov.required} lines explained{changed})")
        return "\n".join(lines)


def new_walkthrough(rel: str) -> int:
    target = walk_file_for(rel)
    if target.exists():
        print(f"{target} already exists")
        return 1
    text = read_text(REPO_ROOT / rel)
    marks = [f"@@ {n}\nTODO\n" for n, line in enumerate(source_lines(text), 1) if line.strip()]
    header = f"---\nfingerprint: {fingerprint(text)}\n---\nTODO: what this file is for.\n\n"
    write_text(target, header + "\n".join(marks))
    write_text(snapshot_for(rel), text)
    print(f"created {target}")
    return 0


def stamp_walkthrough(rel: str) -> int:
    target = walk_file_for(rel)
    text = read_text(REPO_ROOT / rel)
    write_text(target, FINGERPRINT_LINE.sub(f"fingerprint: {fingerprint(text)}", read_text(target), count=1))
    write_text(snapshot_for(rel), text)
    print(f"stamped {target}")
    return 0


def reanchor_walkthrough(rel: str) -> int:
    snapshot, target = snapshot_for(rel), walk_file_for(rel)
    if not snapshot.is_file() or not target.is_file():
        print(f"{rel}: needs a walkthrough and a snapshot (made by --new or --stamp)")
        return 1
    current = read_text(REPO_ROOT / rel)
    mapping = line_mapping(source_lines(read_text(snapshot)), source_lines(current))
    text, report = reanchor_text(read_text(target), mapping)
    write_text(target, text)
    write_text(snapshot, current)
    print("\n".join([f"re-anchored {target}", *report]))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Zero-to-Hero book.")
    parser.add_argument("--strict", action="store_true", help="fail on unexplained, stale or missing walkthroughs")
    parser.add_argument("--new", metavar="PATH", help="create a walkthrough skeleton for PATH")
    parser.add_argument("--stamp", metavar="PATH", help="record PATH's fingerprint and snapshot in its walkthrough")
    parser.add_argument("--reanchor", metavar="PATH", help="move PATH's notes to follow edits since its last snapshot")
    args = parser.parse_args()
    commands = {"new": new_walkthrough, "stamp": stamp_walkthrough, "reanchor": reanchor_walkthrough}
    for name, command in commands.items():
        if getattr(args, name):
            return command(repo_relative(getattr(args, name)))
    config = tomllib.loads(read_text(BOOK_DIR / "book.toml"))
    book = Book(config)
    write_text(BOOK_DIR / config["output"], book.build())
    print(book.report())
    incomplete = any(not c.complete for c in book.coverage.values())
    return 1 if args.strict and (book.problems or incomplete) else 0


if __name__ == "__main__":
    sys.exit(main())
