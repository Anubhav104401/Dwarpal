"""Tests for the render detector's own data: consent first, people never split, withdrawal deletes."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from dwarpal_ml import renders


def frames(count: int = 3) -> list[np.ndarray]:
    return [np.full((8, 8, 3), index * 40, dtype=np.uint8) for index in range(count)]


def consent(folder: Path, *, withdrawn: str = "") -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "consent.toml").write_text(
        f'[[consent]]\nid = "c-001"\nidentity = "person-001"\ngiven_on = 2026-11-03\nwithdrawn_on = "{withdrawn}"\n',
        encoding="utf-8",
    )


def test_a_real_person_is_filmed_only_under_their_own_standing_consent(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no consent"):
        renders.record(frames(), "real", "person-001", "laptop", "study-dim", "", tmp_path)
    consent(tmp_path)
    with pytest.raises(ValueError, match="given by person-001"):
        renders.record(frames(), "real", "person-002", "laptop", "study-dim", "c-001", tmp_path)
    clip = renders.record(frames(), "real", "person-001", "laptop", "study-dim", "c-001", tmp_path)
    assert clip.clip_id == "person-001-real-001"
    assert len(list((tmp_path / "clips" / clip.clip_id).glob("frame_*.jpg"))) == 3
    assert renders.problems(renders.read_clips(tmp_path), renders.load_consents(tmp_path), tmp_path) == []


def test_renders_belong_to_made_up_people_and_carry_no_consent(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="render-"):
        renders.record(frames(), "screen_render", "person-001", "laptop", "study", "", tmp_path)
    with pytest.raises(ValueError, match="no consent to give"):
        renders.record(frames(), "screen_render", "render-001", "laptop", "study", "c-001", tmp_path)
    with pytest.raises(ValueError, match="--camera"):
        renders.record(frames(), "screen_render", "render-001", "Laptop Cam", "study", "", tmp_path)
    with pytest.raises(ValueError, match="no frames"):
        renders.record([], "screen_render", "render-001", "laptop", "study", "", tmp_path)
    clip = renders.record(frames(), "screen_render", "render-001", "laptop", "study", "", tmp_path)
    assert clip.rendered


def test_rendered_sequences_are_added_once_as_injected_clips(tmp_path: Path) -> None:
    sequence = tmp_path / "renders" / "render-004" / "side-light"
    sequence.mkdir(parents=True)
    for index in range(2):
        (sequence / f"{index:04d}.png").write_bytes(b"png")
    (sequence / "notes.txt").write_text("ignored", encoding="utf-8")
    added = renders.inject(tmp_path)
    assert [(c.clip_id, c.kind, c.setting) for c in added] == [
        ("render-004-injected-render-001", "injected_render", "side-light")
    ]
    assert len(list((tmp_path / "clips" / added[0].clip_id).iterdir())) == 2
    assert renders.inject(tmp_path) == []


def test_withdrawing_consent_deletes_that_persons_clips_and_check_catches_leftovers(tmp_path: Path) -> None:
    consent(tmp_path)
    clip = renders.record(frames(), "real", "person-001", "laptop", "study", "c-001", tmp_path)
    renders.record(frames(), "screen_render", "render-001", "laptop", "study", "", tmp_path)
    with pytest.raises(ValueError, match="withdrawn_on"):
        renders.withdraw("c-001", tmp_path)
    consent(tmp_path, withdrawn="2026-11-04")
    assert renders.main(["--folder", str(tmp_path), "check"]) == 1
    (tmp_path / "crops").mkdir()
    (tmp_path / "crops" / "train.npz").write_bytes(b"faces")
    assert renders.withdraw("c-001", tmp_path) == 1
    assert not (tmp_path / "clips" / clip.clip_id).exists()
    assert not (tmp_path / "crops").exists()
    assert [c.identity for c in renders.read_clips(tmp_path)] == ["render-001"]
    assert renders.main(["--folder", str(tmp_path), "check"]) == 0


def test_a_person_lands_in_one_split_only_and_the_splits_are_roughly_seventy_fifteen_fifteen() -> None:
    people = [f"render-{n:03d}" for n in range(1000)]
    assert all(renders.split_of(p) == renders.split_of(p) for p in people)
    shares = {s: sum(renders.split_of(p) == s for p in people) for s in ("train", "validation", "test")}
    assert 640 < shares["train"] < 760 and 110 < shares["validation"] < 190 and 110 < shares["test"] < 190


def test_a_render_is_filmed_in_step_with_the_screen_after_the_camera_settles(tmp_path: Path) -> None:
    sequence = tmp_path / "renders" / "render-007" / "side-light"
    sequence.mkdir(parents=True)
    for index in range(4):
        cv2.imwrite(str(sequence / f"{index:04d}.png"), np.full((8, 8, 3), index * 60, dtype=np.uint8))
    shown: list[int] = []

    def show(image: np.ndarray) -> None:
        shown.append(int(image[0, 0, 0]))

    def grab() -> np.ndarray:
        # The camera sees whatever is on the screen.
        return np.full((8, 8, 3), shown[-1], dtype=np.uint8)

    clip = renders.film(sequence, show, grab, "laptop", "phone-study", tmp_path)
    assert shown == [0] * renders.SETTLE + [0, 60, 120, 180]
    assert (clip.kind, clip.identity) == ("screen_render", "render-007")
    kept = sorted((tmp_path / "clips" / clip.clip_id).glob("frame_*.jpg"))
    assert [int(renders.read_frame(p)[0, 0, 0]) for p in kept] == pytest.approx([0, 60, 120, 180], abs=2)

    with pytest.raises(ValueError, match="render-"):
        renders.film(tmp_path / "renders", show, grab, "laptop", "study", tmp_path)
    shown.clear()
    nothing = tmp_path / "renders" / "render-008" / "dim"
    nothing.mkdir(parents=True)
    with pytest.raises(ValueError, match="no rendered frames"):
        renders.film(nothing, show, grab, "laptop", "study", tmp_path)
    assert shown == []
    assert [p.name for p in (tmp_path / "clips").iterdir()] == [clip.clip_id]  # nothing half-written left
