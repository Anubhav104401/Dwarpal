"""Tests for the licence register, the fetch refusals and the unified manifest."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from dwarpal_ml import manifest, register
from dwarpal_ml.fetch import fetch
from dwarpal_ml.register import Dataset, DatasetFile, load_register


def test_the_register_pins_every_approved_file_and_marks_research_only_data() -> None:
    datasets = load_register()
    assert datasets["fairface"].approved
    assert all(len(f.sha256) == 64 and f.url.startswith("https://") for f in datasets["fairface"].files)
    assert datasets["utkface"].age_labels == "exact"
    assert not datasets["imdb-clean"].approved
    assert "non-commercial" in datasets["utkface"].licence


def test_unapproved_or_unpinned_datasets_are_never_fetched(capsys: pytest.CaptureFixture[str]) -> None:
    assert not fetch(load_register()["imdb-clean"])
    pinned_nothing = Dataset("x", "X", "CC0", "any", "-", "exact", "-", "central", approved=True, files=())
    assert not fetch(pinned_nothing)
    assert "refused" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("text", "expected"), [("0-2", (0, 2)), ("10-19", (10, 19)), ("70+", (70, None)), ("more than 70", (70, None))]
)
def test_age_ranges_are_read_in_every_spelling(text: str, expected: tuple[int, int | None]) -> None:
    assert manifest.parse_age_range(text) == expected


def test_splits_are_fixed_and_roughly_80_10_10() -> None:
    ids = [f"fairface/train/{n}.jpg" for n in range(20_000)]
    splits = [manifest.split_for(i, "train") for i in ids]
    assert splits == [manifest.split_for(i, "train") for i in ids]
    assert 0.78 < splits.count("train") / len(ids) < 0.82
    assert 0.09 < splits.count("calib") / len(ids) < 0.11
    assert manifest.split_for("fairface/val/1.jpg", "val") == "test"


def test_fairface_rows_come_from_the_labels_and_skip_missing_images(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(register, "RAW", tmp_path)
    folder = tmp_path / "fairface"
    folder.mkdir()
    with zipfile.ZipFile(folder / "fairface-img-margin125-trainval.zip", "w") as images:
        images.writestr("train/1.jpg", b"jpeg")
        images.writestr("val/1.jpg", b"jpeg")
    header = "file,age,gender,race,service_test\n"
    (folder / "fairface_label_train.csv").write_text(
        header + "train/1.jpg,10-19,Female,Indian,True\ntrain/2.jpg,20-29,Male,White,False\n", encoding="utf-8"
    )
    (folder / "fairface_label_val.csv").write_text(
        header + "val/1.jpg,more than 70,Male,Black,False\n", encoding="utf-8"
    )
    entry = Dataset(
        "fairface",
        "FairFace",
        "CC BY 4.0",
        "any",
        "-",
        "ranges",
        "-",
        "central",
        True,
        (DatasetFile("f", "u", "s", 0),),
    )
    rows = list(manifest.fairface_rows(entry))
    assert [(r.member, r.age_low, r.age_high, r.sex, r.split) for r in rows] == [
        ("train/1.jpg", 10, 19, "female", manifest.split_for("fairface/train/1.jpg", "train")),
        ("val/1.jpg", 70, None, "male", "test"),
    ]
    written = manifest.write_manifest(rows, tmp_path / "out.csv")
    assert (
        (tmp_path / "out.csv").read_text(encoding="utf-8").splitlines()[2].endswith(",70,,,male,Black,CC BY 4.0,test")
    )
    assert len(written) == 2
