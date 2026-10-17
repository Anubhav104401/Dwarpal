"""Liveness challenges: a random order of head poses and a random run of screen colours, new for every attempt."""

from __future__ import annotations

import random
import secrets
from collections.abc import Sequence

from dwarpal_contracts import POSES, Challenge, Pose

# Calm, clearly different colours. None is a saturated red, and each is shown for STEP_MS, so the screen changes
# fewer than two times a second: well below the three flashes a second that WCAG 2.3.1 warns about.
PALETTE = ("#3c78ff", "#20c8a0", "#ffd23c", "#c060ff", "#f0f0f0")
# Three or four poses. Turns are the strong proof (a flat picture can't turn); looking up is hard to measure from five
# landmarks, so it appears at most once, and every challenge still holds at least two turns.
POSE_STEPS = (3, 4)
MAX_LOOK_UPS = 1
COLOUR_STEPS = 4
STEP_MS = 600

_unpredictable = secrets.SystemRandom()


def sequence[T](options: Sequence[T], length: int, rng: random.Random) -> list[T]:
    chosen = [rng.choice(options)]
    while len(chosen) < length:
        chosen.append(rng.choice([option for option in options if option != chosen[-1]]))
    return chosen


def pose_sequence(length: int, rng: random.Random) -> list[Pose]:
    chosen: list[Pose] = []
    while len(chosen) < length:
        allowed = [
            pose
            for pose in POSES
            if (not chosen or pose != chosen[-1]) and (pose != "look_up" or chosen.count("look_up") < MAX_LOOK_UPS)
        ]
        chosen.append(rng.choice(allowed))
    return chosen


def new_challenge(rng: random.Random = _unpredictable) -> Challenge:
    return Challenge(
        poses=pose_sequence(rng.choice(POSE_STEPS), rng),
        colours=sequence(PALETTE, COLOUR_STEPS, rng),
        step_ms=STEP_MS,
    )
