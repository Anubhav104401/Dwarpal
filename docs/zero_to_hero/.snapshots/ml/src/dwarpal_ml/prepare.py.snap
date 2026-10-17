"""Face preparation: find, straighten and crop every face with the code that serves, and fingerprint each one.

uv run --package dwarpal-ml python -m dwarpal_ml.prepare fairface
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path

import cv2
import numpy as np

from dwarpal_ml.manifest import MANIFESTS, Row, read_manifest, write_table
from dwarpal_ml.register import RAW, ROOT, dataset
from dwarpal_vision import DecodeError, FaceDetector, align_face, assess, decode_image
from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face

PROCESSED = RAW.parent / "processed"
DETECTOR = ROOT / "models" / "third_party" / "face_detection_yunet_2023mar.onnx"
SIZE = 256
JPEG_QUALITY = 95
CHUNK = 500
# A fixed timestamp for every file in the output zip, so the same faces always make the same bytes.
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class Prepared:
    image_id: str
    status: str
    faces: int = 0
    detector_score: float = 0.0
    eye_distance_px: float = 0.0
    brightness: float = 0.0
    sharpness: float = 0.0
    yaw_ratio: float = 0.0
    flags: str = ""
    phash: str = ""


def central_face(image: Image, faces: list[Face]) -> Face:
    height, width = image.shape[:2]

    def distance(face: Face) -> float:
        x, y, w, h = face.box
        return math.hypot(x + w / 2 - width / 2, y + h / 2 - height / 2)

    return min(faces, key=distance)


def perceptual_hash(image: Image) -> int:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    low = cv2.dct(small)[:8, :8].flatten()
    bits = low > np.median(low[1:])
    return int.from_bytes(np.packbits(bits).tobytes(), "big")


def prepare_one(detector: FaceDetector, data: bytes, image_id: str) -> tuple[Prepared, bytes]:
    try:
        image = decode_image(data)
    except DecodeError:
        return Prepared(image_id, "undecodable"), b""
    faces = detector.detect(image)
    if not faces:
        return Prepared(image_id, "no_face"), b""
    face = central_face(image, faces)
    quality = assess(image, [face, *(other for other in faces if other is not face)])
    try:
        aligned = align_face(image, face, size=SIZE)
    except ValueError:
        return Prepared(image_id, "unalignable", faces=len(faces)), b""
    encoded = cv2.imencode(".jpg", aligned, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])[1]
    prepared = Prepared(
        image_id=image_id,
        status="ok",
        faces=quality.faces,
        detector_score=round(quality.detector_score, 4),
        eye_distance_px=round(quality.eye_distance_px, 2),
        brightness=round(quality.brightness, 4),
        sharpness=round(quality.sharpness, 2),
        yaw_ratio=round(quality.yaw_ratio, 4),
        flags="|".join(quality.flags),
        phash=f"{perceptual_hash(aligned):016x}",
    )
    return prepared, encoded.tobytes()


def prepare_chunk(folder: Path, rows: list[Row], model: Path = DETECTOR) -> list[tuple[Prepared, bytes]]:
    cv2.setNumThreads(1)
    detector = FaceDetector(model)
    results = []
    with ExitStack() as stack:
        archives: dict[str, zipfile.ZipFile] = {}
        for row in rows:
            if row.archive not in archives:
                archives[row.archive] = stack.enter_context(zipfile.ZipFile(folder / row.archive))
            results.append(prepare_one(detector, archives[row.archive].read(row.member), row.image_id))
    return results


def prepare(rows: list[Row], folder: Path, target: Path, workers: int) -> list[Prepared]:
    chunks = [rows[start : start + CHUNK] for start in range(0, len(rows), CHUNK)]
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    prepared: list[Prepared] = []
    with ProcessPoolExecutor(workers) as pool, zipfile.ZipFile(partial, "w", zipfile.ZIP_STORED) as out:
        for done, results in enumerate(pool.map(prepare_chunk, repeat(folder), chunks), 1):
            for item, jpeg in results:
                prepared.append(item)
                if jpeg:
                    out.writestr(zipfile.ZipInfo(item.image_id, date_time=ZIP_TIME), jpeg)
            print(f"\r{len(prepared):,}/{len(rows):,} images", end="", flush=True)
            if done == len(chunks):
                print()
    partial.replace(target)
    return prepared


def summary(prepared: list[Prepared]) -> str:
    statuses = Counter(item.status for item in prepared)
    flags = Counter(flag for item in prepared for flag in item.flags.split("|") if flag)
    lines = [f"{len(prepared):,} images: " + ", ".join(f"{name} {count:,}" for name, count in statuses.most_common())]
    lines.append("quality flags (recorded, not removed): " + ", ".join(f"{n} {c:,}" for n, c in flags.most_common()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml prepare", description="Align and fingerprint a dataset's faces")
    parser.add_argument("name", help="a dataset with a manifest in .datasets/manifest/")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    args = parser.parse_args(argv)
    entry = dataset(args.name)
    if not entry.approved:
        print(f"refused  {entry.name}: not approved in ml/datasets.toml")
        return 1
    rows = read_manifest(MANIFESTS / f"{entry.name}.csv")
    prepared = prepare(rows, entry.folder, PROCESSED / f"{entry.name}.zip", args.workers)
    write_table(Prepared, prepared, MANIFESTS / f"{entry.name}.faces.csv")
    print(summary(prepared))
    return 0


if __name__ == "__main__":
    sys.exit(main())
