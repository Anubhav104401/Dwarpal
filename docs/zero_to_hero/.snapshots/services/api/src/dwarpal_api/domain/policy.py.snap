"""Verification policies (which age, how strict) and the age model's calibrated thresholds for them."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path


class UnknownPolicyError(LookupError):
    """No preset policy has this name."""


class UncalibratedPolicyError(LookupError):
    """The active age model has no thresholds for this policy's age and risk budget."""


@dataclass(frozen=True)
class Policy:
    id: str
    min_age: int
    risk_budget: float
    max_face_attempts: int = 3
    token_ttl_s: int = 600


PRESETS: dict[str, Policy] = {
    policy.id: policy
    for policy in (
        Policy("uk_osa_18", 18, 0.02),
        Policy("eu_dsa_18", 18, 0.02),
        Policy("in_dpdp_18", 18, 0.02),
        Policy("au_smma_16", 16, 0.02),
        Policy("us_21", 21, 0.02),
        Policy("teen_13", 13, 0.02),
    )
}


def get_policy(policy_id: str) -> Policy:
    try:
        return PRESETS[policy_id]
    except KeyError:
        raise UnknownPolicyError(policy_id) from None


@dataclass(frozen=True)
class Thresholds:
    tau_pass: float
    tau_fail: float


@dataclass(frozen=True)
class ModelManifest:
    name: str
    version: str
    serves: str
    calibrated: bool
    thresholds: dict[tuple[int, float], Thresholds]

    def serves_model(self, model_version: str) -> bool:
        return fnmatchcase(model_version, self.serves)

    def thresholds_for(self, policy: Policy) -> Thresholds:
        try:
            return self.thresholds[(policy.min_age, policy.risk_budget)]
        except KeyError:
            message = f"model {self.version} has no thresholds for age {policy.min_age} at risk {policy.risk_budget}"
            raise UncalibratedPolicyError(message) from None


def load_manifest(path: Path) -> ModelManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    thresholds = {
        (int(row["min_age"]), float(row["risk_budget"])): Thresholds(float(row["tau_pass"]), float(row["tau_fail"]))
        for row in data["thresholds"]
    }
    for value in thresholds.values():
        if not 0.0 <= value.tau_fail < value.tau_pass <= 1.0:
            raise ValueError(f"invalid thresholds in {path}: {value}")
    return ModelManifest(data["name"], data["version"], data["serves"], bool(data["calibrated"]), thresholds)
