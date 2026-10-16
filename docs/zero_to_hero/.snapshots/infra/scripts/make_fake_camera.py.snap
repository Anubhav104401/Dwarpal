"""Make the fake camera's video for the end-to-end test: the public-domain test portrait as a short Y4M clip.

uv run python infra/scripts/make_fake_camera.py e2e/.cache/fake-camera.y4m
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

WIDTH, HEIGHT, FRAMES, FPS = 640, 480, 30, 15
PORTRAIT = Path(__file__).resolve().parents[2] / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg"


def frame() -> bytes:
    portrait = cv2.imread(str(PORTRAIT))
    if portrait is None:
        raise SystemExit(f"cannot read the test portrait at {PORTRAIT}")
    canvas = np.full((HEIGHT, WIDTH, 3), 128, dtype=np.uint8)
    left = (WIDTH - HEIGHT) // 2
    canvas[:, left : left + HEIGHT] = cv2.resize(portrait, (HEIGHT, HEIGHT), interpolation=cv2.INTER_AREA)
    return bytes(cv2.cvtColor(canvas, cv2.COLOR_BGR2YUV_I420).tobytes())


def main(target: Path) -> None:
    planes = frame()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as video:
        video.write(f"YUV4MPEG2 W{WIDTH} H{HEIGHT} F{FPS}:1 Ip A1:1 C420jpeg\n".encode("ascii"))
        for _ in range(FRAMES):
            video.write(b"FRAME\n" + planes)
    print(f"wrote {FRAMES} frames to {target}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
