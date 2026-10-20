"""Convert the pinned MiniFASNet anti-spoofing weights (PyTorch) to ONNX for serving, proving the answers don't change.

uv run --package dwarpal-ml python -m dwarpal_ml.antispoof

The repository's own model code isn't needed: the network is rebuilt from the shapes stored in the weight files, and
loading every weight strictly proves the rebuild matches. The files are read as plain tensors only (`weights_only`), so
nothing inside them can run.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import onnxruntime
import torch
from torch import nn

from dwarpal_ml.register import ROOT
from dwarpal_vision import FaceDetector, decode_image
from dwarpal_vision.antispoof import SIZE, crop

THIRD_PARTY = ROOT / "models" / "third_party"
# Weights file → ONNX file, and the crop size the network was trained on.
MODELS = (
    ("minifasnet_v2_2.7.pth", "minifasnet_v2_2.7.onnx", 2.7),
    ("minifasnet_v1se_4.0.pth", "minifasnet_v1se_4.0.onnx", 4.0),
)
# The layers that halve the picture's size: 80 → 40 → 20 → 10 → 5.
HALVING = {"conv1", "conv_23.conv_dw", "conv_34.conv_dw", "conv_45.conv_dw"}
TOLERANCE = 1e-4

type State = dict[str, torch.Tensor]


class ConvBlock(nn.Module):
    """A convolution, batch normalisation and (except in projections) a PReLU, sized from its stored weight."""

    def __init__(self, weight: torch.Tensor, stride: int, prelu: bool) -> None:
        super().__init__()
        out_c, per_group, k, _ = weight.shape
        groups = out_c if per_group == 1 and k > 1 else 1
        # 1 x 1 and the final 5 x 5 (which shrinks 5 x 5 to 1 x 1) use no padding; 3 x 3 keeps the size.
        padding = 1 if k == 3 else 0
        self.conv = nn.Conv2d(per_group * groups, out_c, k, stride, padding, groups=groups, bias=False)
        self.bn = nn.BatchNorm2d(out_c)
        self.prelu = nn.PReLU(out_c) if prelu else None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.bn(self.conv(x))
        return self.prelu(x) if self.prelu is not None else x


class Squeeze(nn.Module):
    """Squeeze-and-excitation: reweigh the channels by a summary of the whole picture (MiniFASNetV1SE only)."""

    def __init__(self, state: State, prefix: str) -> None:
        super().__init__()
        channels, reduced = state[prefix + "fc2.weight"].shape[0], state[prefix + "fc1.weight"].shape[0]
        self.fc1, self.bn1 = nn.Conv2d(channels, reduced, 1, bias=False), nn.BatchNorm2d(reduced)
        self.fc2, self.bn2 = nn.Conv2d(reduced, channels, 1, bias=False), nn.BatchNorm2d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        summary = x.mean(dim=(2, 3), keepdim=True)
        return x * torch.sigmoid(self.bn2(self.fc2(torch.relu(self.bn1(self.fc1(summary))))))


class DepthWise(nn.Module):
    """Expand (1 x 1), filter each channel on its own (3 x 3), project back (1 x 1); optionally add the input back."""

    def __init__(self, state: State, prefix: str, residual: bool) -> None:
        super().__init__()
        self.conv = ConvBlock(state[prefix + "conv.conv.weight"], 1, True)
        stride = 2 if prefix + "conv_dw" in HALVING else 1
        self.conv_dw = ConvBlock(state[prefix + "conv_dw.conv.weight"], stride, True)
        self.project = ConvBlock(state[prefix + "project.conv.weight"], 1, False)
        has_se = prefix + "se_module.fc1.weight" in state
        self.se_module = Squeeze(state, prefix + "se_module.") if has_se else None
        self.residual = residual

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.project(self.conv_dw(self.conv(x)))
        if self.se_module is not None:
            y = self.se_module(y)
        result: torch.Tensor = x + y if self.residual else y
        return result


class Stage(nn.Module):
    """A run of residual blocks, as many as the weights hold."""

    def __init__(self, state: State, prefix: str) -> None:
        super().__init__()
        count = len({key.split(".")[2] for key in state if key.startswith(prefix + "model.")})
        self.model = nn.Sequential(*[DepthWise(state, f"{prefix}model.{i}.", True) for i in range(count)])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        result: torch.Tensor = self.model(x)
        return result


class MiniFASNet(nn.Module):
    """Pixels (blue-green-red, 0-255, 80 x 80) in; probabilities of the three classes out (index 1: a real face)."""

    def __init__(self, state: State) -> None:
        super().__init__()
        self.conv1 = ConvBlock(state["conv1.conv.weight"], 2, True)
        self.conv2_dw = ConvBlock(state["conv2_dw.conv.weight"], 1, True)
        self.conv_23 = DepthWise(state, "conv_23.", False)
        self.conv_3 = Stage(state, "conv_3.")
        self.conv_34 = DepthWise(state, "conv_34.", False)
        self.conv_4 = Stage(state, "conv_4.")
        self.conv_45 = DepthWise(state, "conv_45.", False)
        self.conv_5 = Stage(state, "conv_5.")
        self.conv_6_sep = ConvBlock(state["conv_6_sep.conv.weight"], 1, True)
        self.conv_6_dw = ConvBlock(state["conv_6_dw.conv.weight"], 1, False)
        embedding, features = state["linear.weight"].shape
        self.linear = nn.Linear(features, embedding, bias=False)
        self.bn = nn.BatchNorm1d(embedding)
        self.prob = nn.Linear(embedding, state["prob.weight"].shape[0], bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        for stage in (self.conv1, self.conv2_dw, self.conv_23, self.conv_3, self.conv_34, self.conv_4, self.conv_45):
            x = stage(x)
        x = self.conv_6_dw(self.conv_6_sep(self.conv_5(x)))
        return torch.softmax(self.prob(self.bn(self.linear(x.flatten(1)))), dim=1)


def load(path: Path) -> MiniFASNet:
    raw = torch.load(path, map_location="cpu", weights_only=True)
    # The weights were saved from a multi-GPU wrapper, which prefixes every name with "module.".
    state = {name.removeprefix("module."): tensor for name, tensor in raw.items()}
    model = MiniFASNet(state)
    model.load_state_dict(state, strict=True)
    return model.eval()


def convert(model: MiniFASNet, target: Path) -> None:
    example = torch.zeros(1, 3, SIZE, SIZE)
    program = torch.onnx.export(
        model, (example,), input_names=["pixels"], output_names=["probabilities"], dynamo=True, verbose=False
    )
    if program is None:
        raise RuntimeError("the ONNX exporter returned nothing")
    program.save(str(target), external_data=False)


def parity(model: MiniFASNet, target: Path, patches: list[np.ndarray]) -> float:
    session = onnxruntime.InferenceSession(str(target), providers=["CPUExecutionProvider"])
    gaps = []
    for patch in patches:
        pixels = np.ascontiguousarray(patch.astype(np.float32).transpose(2, 0, 1)[None])
        with torch.no_grad():
            reference = model(torch.from_numpy(pixels)).numpy()
        gaps.append(float(np.abs(reference - session.run(None, {"pixels": pixels})[0]).max()))
    return max(gaps)


def main() -> int:
    image = decode_image((ROOT / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg").read_bytes())
    face = FaceDetector(THIRD_PARTY / "face_detection_yunet_2023mar.onnx").detect(image)[0]
    rng = np.random.default_rng(0)
    ok = True
    for weights, onnx_file, scale in MODELS:
        model = load(THIRD_PARTY / weights)
        convert(model, THIRD_PARTY / onnx_file)
        patches = [crop(image, face.box, scale)] + [
            rng.integers(0, 256, (SIZE, SIZE, 3), dtype=np.uint8) for _ in range(8)
        ]
        gap = parity(model, THIRD_PARTY / onnx_file, patches)
        ok = ok and gap <= TOLERANCE
        print(f"{onnx_file}: largest probability gap {gap:.2e} (tolerance {TOLERANCE:.0e})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
