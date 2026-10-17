"""Tests for training: label distributions, the loss, sampling, random changes, the model and one tiny run."""

from __future__ import annotations

import json
import pickle
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pytest
import timm
import torch
from hypothesis import given
from hypothesis import strategies as st
from safetensors.torch import save_file

from dwarpal_ml import data, train
from dwarpal_ml.data import Augment, FaceDataset, sampling_weights
from dwarpal_ml.manifest import Row
from dwarpal_ml.model import AgeModel, UnapprovedWeightsError, pretrained_weights
from dwarpal_ml.targets import (
    AGES,
    OPEN_BAND_TOP,
    age_loss,
    distance_to_band,
    expected_age,
    label_distribution,
)
from dwarpal_vision import decode_image

PORTRAIT = Path(__file__).resolve().parents[2] / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg"


def row(image_id: str, low: int, high: int | None, split: str = "train") -> Row:
    return Row(image_id, "d", "a.zip", image_id, low, high, None, "female", "g", "CC0", split)


@given(st.integers(0, 90), st.integers(0, 10))
def test_a_band_becomes_a_distribution_that_sums_to_one_and_peaks_in_the_band(low: int, width: int) -> None:
    target = label_distribution(low, low + width, None)
    assert target.shape == (AGES,)
    assert target.sum() == pytest.approx(1.0, abs=1e-5)
    assert low <= int(np.argmax(target)) <= low + width


@pytest.mark.parametrize(("low", "high"), [(0, 2), (3, 9), (10, 19), (20, 29), (60, 69)])
def test_most_of_a_real_band_stays_inside_it_with_soft_edges(low: int, high: int) -> None:
    inside = float(label_distribution(low, high, None)[low : high + 1].sum())
    assert 0.7 < inside < 0.95


def test_an_exact_age_peaks_at_that_age_and_an_open_band_stops_at_its_top() -> None:
    assert int(np.argmax(label_distribution(0, None, 16))) == 16
    open_band = label_distribution(70, None, None)
    assert open_band[70 : OPEN_BAND_TOP + 1].sum() > 0.8
    assert open_band[95:].sum() < 0.02


def test_the_distance_to_a_band_is_zero_inside_and_grows_outside() -> None:
    ages = torch.tensor([5.0, 15.0, 25.0])
    assert distance_to_band(ages, torch.tensor(10.0), torch.tensor(19.0)).tolist() == [5.0, 0.0, 6.0]


def test_the_loss_prefers_the_right_answer_to_a_wrong_one() -> None:
    target = torch.from_numpy(label_distribution(20, 29, None))[None]
    low, high = torch.tensor([20.0]), torch.tensor([29.0])
    right = torch.log(target + 1e-6)
    wrong = torch.log(torch.from_numpy(label_distribution(60, 69, None))[None] + 1e-6)
    assert float(age_loss(right, target, low, high)) < 0.01 < float(age_loss(wrong, target, low, high))
    assert float(expected_age(right)) == pytest.approx(24.5, abs=1.0)


def test_rare_bands_and_the_years_around_the_limits_are_shown_more_often() -> None:
    rows = [row("common", 30, 39)] * 9 + [row("rare", 60, 69), row("teen", 10, 19)]
    weights = sampling_weights(rows)
    assert weights.sum() == pytest.approx(1.0)
    assert weights[9] > weights[0]
    assert weights[10] == pytest.approx(2 * weights[9])


def test_random_changes_keep_the_size_and_repeat_with_the_same_seed() -> None:
    face = decode_image(PORTRAIT.read_bytes())
    first, second = Augment(seed=7)(face), Augment(seed=7)(face)
    assert first.shape == (224, 224, 3)
    assert first.dtype == np.uint8
    assert np.array_equal(first, second)
    assert not np.array_equal(first, Augment(seed=8)(face))


def faces_zip(folder: Path, rows: list[Row]) -> Path:
    jpeg = bytes(cv2.imencode(".jpg", cv2.resize(decode_image(PORTRAIT.read_bytes()), (256, 256)))[1].tobytes())
    with zipfile.ZipFile(folder / "faces.zip", "w") as archive:
        for item in rows:
            archive.writestr(item.image_id, jpeg)
    return folder / "faces.zip"


def test_a_sample_is_pixels_a_target_and_its_band(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [row("a", 10, 19), row("b", 20, 29, split="val")]
    monkeypatch.setattr(data, "usable_rows", lambda name: rows)
    dataset = FaceDataset("toy", "train", faces_zip(tmp_path, rows))
    assert len(dataset) == 1
    pixels, target, low, high = dataset[0]
    assert (pixels.shape, pixels.dtype) == ((3, 224, 224), torch.uint8)
    assert float(target.sum()) == pytest.approx(1.0, abs=1e-5)
    assert (float(low), float(high)) == (10.0, 19.0)
    sent = pickle.loads(pickle.dumps(dataset))  # noqa: S301 - our own object, as the loader sends it
    assert (sent.loaded, sent.archive) == (None, None)


def test_the_model_takes_plain_pixels_and_gives_one_score_per_age() -> None:
    model = AgeModel("resnet10t").eval()
    with torch.no_grad():
        logits = model(torch.randint(0, 256, (2, 3, 64, 64), dtype=torch.uint8))
    assert logits.shape == (2, AGES)


def test_the_learning_rate_warms_up_then_glides_to_zero() -> None:
    factors = [train.learning_rate_factor(step, 100, 10) for step in range(100)]
    assert factors[0] == pytest.approx(0.1)
    assert max(factors) == pytest.approx(1.0)
    assert factors[-1] < 0.01


def test_a_tiny_run_trains_records_and_saves(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [row(f"t{n}", 10 * (n % 7), 10 * (n % 7) + 9) for n in range(16)]
    rows += [row(f"v{n}", 20, 29, split="val") for n in range(4)]
    faces = faces_zip(tmp_path, rows)
    (tmp_path / "toy.csv").write_text("fingerprinted", encoding="utf-8")
    monkeypatch.setattr(data, "usable_rows", lambda name: rows)
    monkeypatch.setattr(train, "PROCESSED", tmp_path)
    monkeypatch.setattr(train, "MANIFESTS", tmp_path)
    faces.rename(tmp_path / "toy.zip")
    config = train.Config(dataset="toy", backbone="resnet10t", epochs=2, batch_size=4, image_size=64, workers=0)
    record = train.train(config, tmp_path / "run")
    saved = json.loads((tmp_path / "run" / "run.json").read_text(encoding="utf-8"))
    assert [epoch["epoch"] for epoch in saved["epochs"]] == [1, 2]
    assert saved["data"]["fingerprints"] == {"toy.csv": train.sha256_of(tmp_path / "toy.csv")}
    assert record["best"]["band_mae"] >= 0
    assert (tmp_path / "run" / "model.safetensors").is_file()


def register_with(folder: Path, file: Path, sha256: str) -> Path:
    entry = {"name": "toy", "use": "training", "timm": "resnet10t", "file": file.name, "sha256": sha256, "licence": "x"}
    (folder / "third_party.json").write_text(json.dumps({"models": [entry]}), encoding="utf-8")
    return folder / "third_party.json"


def test_only_registered_untampered_weights_are_used(tmp_path: Path) -> None:
    weights_file = tmp_path / "toy.safetensors"
    register = register_with(tmp_path, weights_file, "0" * 64)
    with pytest.raises(UnapprovedWeightsError, match="convnext_tiny"):
        pretrained_weights("convnext_tiny", register)
    with pytest.raises(FileNotFoundError, match="--training"):
        pretrained_weights("resnet10t", register)
    weights_file.write_bytes(b"not the pinned file")
    with pytest.raises(ValueError, match="fingerprint"):
        pretrained_weights("resnet10t", register)


def test_pretrained_weights_load_from_the_local_file_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    source = timm.create_model("resnet10t", num_classes=1000)
    weights_file = tmp_path / "toy.safetensors"
    save_file(source.state_dict(), str(weights_file))
    register = register_with(tmp_path, weights_file, train.sha256_of(weights_file))
    model = AgeModel("resnet10t", pretrained_weights("resnet10t", register))
    assert torch.equal(model.backbone.state_dict()["conv1.0.weight"], source.state_dict()["conv1.0.weight"])
    assert model.backbone.state_dict()["fc.weight"].shape == (AGES, 512)


def test_switches_on_the_command_line_are_true_or_false() -> None:
    assert train.parse([]).pretrained is False
    assert train.parse(["--pretrained", "--drop-path", "0.1"]) == train.Config(pretrained=True, drop_path=0.1)
