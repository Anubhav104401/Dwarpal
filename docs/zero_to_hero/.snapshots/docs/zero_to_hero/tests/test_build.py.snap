"""Tests for the Zero-to-Hero book builder: the checker of the book must itself be checked."""

from __future__ import annotations

from pathlib import Path

import pytest

import build
from build import Note, Place


def test_source_lines_drops_only_the_final_newline() -> None:
    assert build.source_lines("a\n\nb\n") == ["a", "", "b"]
    assert build.source_lines("a\nb") == ["a", "b"]


def test_fingerprint_is_stable_and_changes_with_any_edit() -> None:
    assert build.fingerprint("x = 1\n") == build.fingerprint("x = 1\n")
    assert build.fingerprint("x = 1\n") != build.fingerprint("x = 2\n")
    assert len(build.fingerprint("")) == 16


def test_parse_walkthrough_splits_header_intro_and_notes() -> None:
    text = "---\nfingerprint: abc\n---\nIntro.\n@@ 1\nOne.\n@@ 2-3\nTwo and three.\n"
    meta, intro, notes = build.parse_walkthrough(text)
    assert meta == {"fingerprint": "abc"}
    assert intro.strip() == "Intro."
    assert [(n.start, n.end, n.text.strip()) for n in notes] == [(1, 1, "One."), (2, 3, "Two and three.")]


def test_todo_and_empty_notes_do_not_count_as_explained() -> None:
    assert build.is_explained(Note(1, 1, "Real text."))
    assert not build.is_explained(Note(1, 1, "TODO"))
    assert not build.is_explained(Note(1, 1, "TODO(review) Old text."))
    assert not build.is_explained(Note(1, 1, "  \n"))


def test_segments_cover_every_line_exactly_once() -> None:
    parts, problems = build.segments([Note(3, 4, "b"), Note(1, 1, "a")], total=6)
    assert problems == []
    assert [(s, e, n is not None) for s, e, n in parts] == [(1, 1, True), (2, 2, False), (3, 4, True), (5, 6, False)]


def test_segments_reject_overlapping_and_out_of_range_notes() -> None:
    _, problems = build.segments([Note(1, 3, "a"), Note(2, 2, "b"), Note(5, 9, "c")], total=6)
    assert len(problems) == 2


def test_line_mapping_follows_moved_lines_and_skips_deleted_ones() -> None:
    mapping = build.line_mapping(["a", "b", "c"], ["new", "a", "c"])
    assert mapping == {1: Place(2, 2, edited=False), 3: Place(3, 3, edited=False)}


def test_line_mapping_lines_up_edited_blocks_side_by_side() -> None:
    grown = build.line_mapping(["a", "b", "c"], ["a", "B1", "B2", "c"])
    assert grown == {1: Place(1, 1, edited=False), 2: Place(2, 3, edited=True), 3: Place(4, 4, edited=False)}
    shrunk = build.line_mapping(["a", "b1", "b2", "c"], ["a", "B", "c"])
    assert shrunk[2] == shrunk[3] == Place(2, 2, edited=True)


def test_reanchor_moves_notes_and_flags_edited_code_for_review() -> None:
    old = ["import os", "x = 1", "y = 2"]
    new = ['"""Docstring."""', "import os", "x = 10", "y = 2"]
    text = "intro\n@@ 1\nImports os.\n@@ 2\nSets x.\n@@ 3\nSets y.\n"
    result, report = build.reanchor_text(text, build.line_mapping(old, new))
    assert result == "intro\n@@ 2\nImports os.\n@@ 3\nTODO(review) Sets x.\n@@ 4\nSets y.\n"
    assert len(report) == 1


def test_reanchor_drops_notes_whose_code_was_deleted() -> None:
    result, report = build.reanchor_text(
        "@@ 1\nA.\n@@ 2\nB.\n@@ 3\nC.\n", build.line_mapping(["a", "b", "c"], ["a", "c"])
    )
    assert result == "@@ 1\nA.\n@@ 2\nC.\n"
    assert report == ["@@ 2-2: its lines were deleted, so the note was dropped"]


def test_reanchor_keeps_an_edited_line_at_the_edge_of_a_note_covered() -> None:
    mapping = build.line_mapping(["a", "b", "c"], ["a", "B", "c"])
    result, report = build.reanchor_text("@@ 1-2\nA and b.\n@@ 3\nC.\n", mapping)
    assert result == "@@ 1-2\nTODO(review) A and b.\n@@ 3\nC.\n"
    assert report == ["@@ 1-2 -> 1-2: code changed, marked TODO(review)"]


def test_reanchor_keeps_notes_in_place_when_an_edit_keeps_the_line_count() -> None:
    mapping = build.line_mapping(["x", "a", "b", "c"], ["x", "A", "B", "C"])
    result, _ = build.reanchor_text("@@ 2\nA.\n@@ 3-4\nTODO(review) B and c.\n", mapping)
    assert result == "@@ 2\nTODO(review) A.\n@@ 3-4\nTODO(review) B and c.\n"


def test_a_walkthrough_must_be_placed_in_the_book_exactly_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("REPO_ROOT", "BOOK_DIR"):
        monkeypatch.setattr(build, name, tmp_path)
    monkeypatch.setattr(build, "WALK_DIR", tmp_path / "walkthroughs")
    for rel, text in [("a.py", "a = 1\n"), ("b.py", "b = 2\n"), ("abbr.md", ""), ("template.html", "{{BODY}}")]:
        build.write_text(tmp_path / rel, text)
    for rel in ("a.py", "b.py"):
        build.write_text(build.walk_file_for(rel), "---\nfingerprint: x\n---\n")
    build.write_text(tmp_path / "chapter.md", "!walk a.py\n\n!walk a.py\n\n!ledger\n")
    rules = {"include": ["**/*.py"], "exclude": [], "prune": ["walkthroughs"]}
    book = build.Book(
        {"chapters": ["chapter.md"], "abbreviations": "abbr.md", "title": "", "subtitle": "", "coverage": rules}
    )
    book.build()
    assert "a.py: its walkthrough is placed more than once" in book.problems
    assert "b.py: its walkthrough is not placed in any chapter (add a !walk line)" in book.problems


def test_reanchoring_twice_before_a_stamp_follows_both_edits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(build, "WALK_DIR", tmp_path / "walkthroughs")
    monkeypatch.setattr(build, "SNAP_DIR", tmp_path / "snapshots")
    source = tmp_path / "code.py"
    source.write_text("a\nb\n", encoding="utf-8")
    build.write_text(build.walk_file_for("code.py"), "---\nfingerprint: x\n---\n@@ 1\nA.\n@@ 2\nB.\n")
    build.write_text(build.snapshot_for("code.py"), "a\nb\n")
    for version in ("new\na\nb\n", "new\nnewer\na\nb\n"):
        source.write_text(version, encoding="utf-8")
        assert build.reanchor_walkthrough("code.py") == 0
    assert build.read_text(build.walk_file_for("code.py")).endswith("@@ 3\nA.\n@@ 4\nB.\n")
    assert build.read_text(build.snapshot_for("code.py")) == "new\nnewer\na\nb\n"
