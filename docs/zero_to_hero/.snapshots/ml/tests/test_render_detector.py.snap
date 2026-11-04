"""Tests for the render detector: crops only from clips that may be kept, a network that learns, honest thresholds,
and an export that needs passing gates and answers as PyTorch does."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
import torch

from dwarpal_ml import render_detector as rd
from dwarpal_ml import renders
from dwarpal_vision import Face, RenderDetector
from dwarpal_vision.antispoof import crop

SPLITS = ("train", "validation", "test")


class OneFace:
    """Stands in for the face finder: one face in the middle of every picture."""

    def detect(self, image: np.ndarray) -> list[Face]:
        height, width = image.shape[:2]
        box = (width / 4, height / 4, width / 2, height / 2)
        return [Face(box=box, landmarks=np.zeros((5, 2), dtype=np.float32), score=0.9)]


def people(prefix: str, per_split: int) -> list[str]:
    """IDs that fill every split with `per_split` people each."""
    chosen: dict[str, list[str]] = {split: [] for split in SPLITS}
    for number in range(1000):
        identity = f"{prefix}-{number:03d}"
        bucket = chosen[renders.split_of(identity)]
        if len(bucket) < per_split:
            bucket.append(identity)
    return [identity for split in SPLITS for identity in chosen[split]]


def frames(rendered: bool, count: int, rng: np.random.Generator) -> list[np.ndarray]:
    """Real faces as fine, random texture; renders as smooth gradients — a difference a small network learns fast."""
    pictures: list[np.ndarray] = []
    for _ in range(count):
        if rendered:
            ramp = np.linspace(rng.uniform(40, 120), rng.uniform(140, 220), 160)
            picture: np.ndarray = np.repeat(np.repeat(ramp[None, :, None], 160, axis=0), 3, axis=2)
        else:
            picture = rng.integers(0, 256, (160, 160, 3))
        pictures.append(picture.astype(np.uint8))
    return pictures


@pytest.fixture(scope="module")
def clips(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("render-data")
    real, made_up = people("person", 3), people("render", 3)
    register = "".join(
        f'[[consent]]\nid = "c-{i:03d}"\nidentity = "{identity}"\ngiven_on = 2026-11-03\n'
        for i, identity in enumerate(real)
    )
    (folder / "consent.toml").write_text(register, encoding="utf-8")
    rng = np.random.default_rng(0)
    for i, identity in enumerate(real):
        renders.record(frames(False, 12, rng), "real", identity, "laptop", "study", f"c-{i:03d}", folder)
    for identity in made_up:
        renders.record(frames(True, 12, rng), "screen_render", identity, "laptop", "study", "", folder)
    return folder


def test_crops_are_prepared_per_split_and_never_from_a_clip_that_may_not_be_kept(clips: Path) -> None:
    counts = rd.prepare(OneFace(), clips, every=1)
    assert counts == {"test": 72, "train": 72, "validation": 72}
    test = rd.load_split("test", clips / "crops")
    assert test.pixels.shape == (72, 80, 80, 3)
    assert set(test.labels) == {0, 1} and set(test.kinds) == {"real", "screen_render"}
    assert not set(test.people) & set(rd.load_split("train", clips / "crops").people)

    broken = clips / "clips" / renders.read_clips(clips)[0].clip_id
    hidden = broken.with_name("hidden")
    broken.rename(hidden)
    try:
        with pytest.raises(ValueError, match="renders check"):
            rd.prepare(OneFace(), clips, every=1)
    finally:
        hidden.rename(broken)


def test_a_large_rendered_png_is_cropped_like_any_frame(tmp_path: Path) -> None:
    # Speckle doesn't compress: a 640 x 640 PNG of it is over a megabyte, twice the service's upload limit.
    big = tmp_path / "0001.png"
    cv2.imwrite(str(big), np.random.default_rng(2).integers(0, 256, (640, 640, 3), dtype=np.uint8))
    assert big.stat().st_size > 1024 * 1024
    assert [c.shape for c in rd.face_crops([big], OneFace(), every=1)] == [(80, 80, 3)]


def test_the_network_starts_from_minifasnet_shapes_and_answers_two_chances() -> None:
    model = rd.RenderNet(rd.base_state(pretrained=False), pretrained=False).eval()
    with torch.no_grad():
        chances = model(torch.zeros(4, 3, 80, 80))
    assert chances.shape == (4, 2)
    assert torch.allclose(chances.sum(dim=1), torch.ones(4))


def test_augmenting_keeps_the_crop_a_crop() -> None:
    rng = np.random.default_rng(1)
    patch = rng.integers(0, 256, (80, 80, 3), dtype=np.uint8)
    changed = [rd.augment(patch, rng) for _ in range(10)]
    assert all(c.shape == (80, 80, 3) and c.dtype == np.uint8 for c in changed)
    assert any(not np.array_equal(c, patch) for c in changed)
    assert rd.balanced_weights(np.array([0, 0, 0, 1])) == [1 / 3, 1 / 3, 1 / 3, 1.0]


def test_the_threshold_refuses_at_most_the_target_share_of_real_people() -> None:
    real = np.linspace(0.0, 0.99, 100)
    scores = np.concatenate([real, np.full(10, 0.999)])
    labels = np.array([0] * 100 + [1] * 10)
    threshold = rd.threshold_for(scores, labels, target=0.05)
    assert np.mean(real >= threshold) <= 0.05
    assert np.mean(real >= np.nextafter(threshold, 0) - 0.01) > 0.05
    assert rd.balanced_error(scores, labels, threshold) <= 0.025


def test_training_without_real_faces_is_refused(tmp_path: Path) -> None:
    rendered_only = {
        "pixels": np.zeros((2, 80, 80, 3), np.uint8),
        "labels": np.array([1, 1]),
        "kinds": np.array(["injected_render"] * 2),
        "people": np.array(["render-001"] * 2),
    }
    for name in ("train", "validation"):
        np.savez_compressed(tmp_path / f"{name}.npz", **rendered_only)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="both real and rendered"):
        rd.train(rd.Config(epochs=1, pretrained=False), tmp_path, tmp_path / "runs")


def test_training_learns_evaluating_measures_and_exporting_needs_the_gates(clips: Path, tmp_path: Path) -> None:
    rd.prepare(OneFace(), clips, every=1)
    lines: list[str] = []
    run = rd.train(rd.Config(epochs=4, batch_size=16, pretrained=False), clips / "crops", tmp_path, lines.append)
    assert len(lines) == 4 and (run / "model.safetensors").is_file()

    strict = tmp_path / "strict.toml"
    strict.write_text('[[gate]]\nname = "people"\nmetric = "test.people.real"\nmin = 50\n', encoding="utf-8")
    results = rd.evaluate(run, clips / "crops", strict)
    assert results["test"]["people"] == {"real": 3, "rendered": 3}
    assert results["test"]["apcer"]["rate"] <= 0.1 and results["test"]["bpcer"]["rate"] <= 0.1
    with pytest.raises(ValueError, match="gates failed: people"):
        rd.export(run, "0.0.1", tmp_path / "registry")

    easy = tmp_path / "easy.toml"
    easy.write_text('[[gate]]\nname = "people"\nmetric = "test.people.real"\nmin = 1\n', encoding="utf-8")
    rd.evaluate(run, clips / "crops", easy)
    target = rd.export(run, "0.0.1", tmp_path / "registry")
    assert (target / "render.onnx").is_file()
    assert '"use": "recorded only"' in (target / "manifest.json").read_text(encoding="utf-8")

    # The inference service's wrapper, through OpenCV, answers as the trained network does.
    picture = frames(True, 1, np.random.default_rng(5))[0]
    face = OneFace().detect(picture)[0]
    served = RenderDetector(target / "render.onnx").rendered(picture, face)
    patch = crop(picture, face.box, rd.SCALE).astype(np.float32).transpose(2, 0, 1)[None]
    with torch.no_grad():
        trained = float(rd.load_run(run)(torch.from_numpy(np.ascontiguousarray(patch)))[0, rd.RENDERED])
    assert abs(served - trained) < 1e-4
    with pytest.raises(FileNotFoundError):
        RenderDetector(tmp_path / "missing.onnx")
