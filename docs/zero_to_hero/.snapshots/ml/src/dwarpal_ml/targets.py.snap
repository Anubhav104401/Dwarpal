"""What the model should answer for each label, and how wrong an answer is: label distributions and the loss."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray
from torch.nn import functional

AGES = 101
# FairFace's open band "70 and over" is spread over 70-89: older faces are rare, and a target reaching 100 would
# teach the model to expect them.
OPEN_BAND_TOP = 89
MEAN_WEIGHT = 0.1

_ages = np.arange(AGES, dtype=np.float64)


def spread(age: float) -> float:
    return 1.0 + 0.04 * age


def label_distribution(age_low: int, age_high: int | None, age_exact: int | None) -> NDArray[np.float32]:
    if age_exact is not None:
        low, high = age_exact, age_exact
    else:
        low, high = age_low, age_high if age_high is not None else OPEN_BAND_TOP
    target = np.zeros(AGES, dtype=np.float64)
    for age in range(low, min(high, AGES - 1) + 1):
        target += np.exp(-0.5 * ((_ages - age) / spread(age)) ** 2) / spread(age)
    return (target / target.sum()).astype(np.float32)


def distance_to_band(age: torch.Tensor, low: torch.Tensor, high: torch.Tensor) -> torch.Tensor:
    return torch.clamp(low - age, min=0) + torch.clamp(age - high, min=0)


def expected_age(logits: torch.Tensor) -> torch.Tensor:
    ages = torch.arange(logits.shape[-1], device=logits.device, dtype=torch.float32)
    return (logits.float().softmax(dim=-1) * ages).sum(dim=-1)


def age_loss(
    logits: torch.Tensor, target: torch.Tensor, low: torch.Tensor, high: torch.Tensor, mean_weight: float = MEAN_WEIGHT
) -> torch.Tensor:
    log_probabilities = functional.log_softmax(logits.float(), dim=-1)
    divergence = functional.kl_div(log_probabilities, target, reduction="batchmean")
    miss = distance_to_band(expected_age(logits), low, high).mean()
    return divergence + mean_weight * miss
