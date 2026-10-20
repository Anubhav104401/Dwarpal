"""Tests for the anti-spoofing converter: the network rebuilt from its weights' shapes takes every stored weight."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from dwarpal_ml.antispoof import MODELS, THIRD_PARTY, load
from dwarpal_vision import FaceDetector, decode_image
from dwarpal_vision.antispoof import crop

WEIGHTS = [(THIRD_PARTY / weights, scale) for weights, _, scale in MODELS]
PORTRAIT = THIRD_PARTY.parents[1] / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg"


@pytest.mark.skipif(
    not all(path.is_file() for path, _ in WEIGHTS), reason="fetched by: uv run infra/scripts/fetch_models.py --training"
)
def test_both_networks_rebuild_exactly_and_take_a_real_photograph_for_a_real_face() -> None:
    image = decode_image(PORTRAIT.read_bytes())
    face = FaceDetector(THIRD_PARTY / "face_detection_yunet_2023mar.onnx").detect(image)[0]
    for path, scale in WEIGHTS:
        model = load(path)
        pixels = torch.from_numpy(crop(image, face.box, scale).astype(np.float32).transpose(2, 0, 1)[None])
        with torch.no_grad():
            probabilities = model(pixels).numpy()[0]
        assert abs(float(probabilities.sum()) - 1.0) < 1e-5
        assert probabilities[1] > 0.8
