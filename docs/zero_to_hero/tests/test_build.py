"""Tests for the Zero-to-Hero book builder: the checker of the book must itself be checked."""

from __future__ import annotations

import build
from build import Note


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


def test_line_mapping_follows_moved_lines_and_skips_changed_ones() -> None:
    mapping = build.line_mapping(["a", "b", "c"], ["new", "a", "c"])
    assert mapping == {0: 0, 1: 2, 3: 3, 4: 4}


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
