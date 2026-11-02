"""The render detector's own data (ADR-0021): clips of real, consenting people and of made-up people rendered by us.

Everything lives in .datasets/render-detector/, never in the repository: the clips, their list (clips.csv) and the
consent register (consent.toml). See docs/data/render-detector-protocol.md.

uv run --package dwarpal-ml python -m dwarpal_ml.renders check
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
import tomllib
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Literal, cast, get_args

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_ml.register import ROOT

DATA = ROOT / ".datasets" / "render-detector"

type Kind = Literal["real", "screen_render", "injected_render"]
KINDS: tuple[Kind, ...] = get_args(Kind.__value__)
# Who may appear in each kind: a consenting person, or one of our made-up people.
IDENTITY = {"real": re.compile(r"person-\d{3}"), "screen_render": re.compile(r"render-\d{3}")}
IDENTITY["injected_render"] = IDENTITY["screen_render"]
NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,39}")
IMAGES = (".png", ".jpg", ".jpeg")
# Camera frames dropped while the first rendered frame is on screen: the camera adjusts its exposure to the screen.
SETTLE = 15

type Frame = NDArray[np.uint8]
type Show = Callable[[Frame], None]
type Grab = Callable[[], Frame | None]


@dataclass(frozen=True)
class Clip:
    clip_id: str
    kind: Kind
    identity: str
    camera: str
    setting: str
    consent: str = ""

    @property
    def rendered(self) -> bool:
        return self.kind != "real"


@dataclass(frozen=True)
class Consent:
    id: str
    identity: str
    given_on: str
    withdrawn_on: str = ""

    @property
    def standing(self) -> bool:
        return not self.withdrawn_on


def read_clips(folder: Path = DATA) -> list[Clip]:
    path = folder / "clips.csv"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as source:
        return [Clip(**row) for row in csv.DictReader(source)]  # type: ignore[arg-type]


def write_clips(clips: Iterable[Clip], folder: Path = DATA) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "clips.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=[f.name for f in fields(Clip)])
        writer.writeheader()
        writer.writerows(asdict(clip) for clip in sorted(clips, key=lambda c: c.clip_id))


def load_consents(folder: Path = DATA) -> dict[str, Consent]:
    path = folder / "consent.toml"
    if not path.is_file():
        return {}
    entries = tomllib.loads(path.read_text(encoding="utf-8")).get("consent", [])
    return {
        str(e["id"]): Consent(str(e["id"]), str(e["identity"]), str(e["given_on"]), str(e.get("withdrawn_on", "")))
        for e in entries
    }


def consent_problem(kind: Kind, identity: str, consent: str, consents: dict[str, Consent]) -> str | None:
    """Why a clip of this kind, person and consent may not be kept, or None if it may."""
    if kind not in KINDS:
        return f"unknown kind {kind!r}"
    if not IDENTITY[kind].fullmatch(identity):
        return f"{kind} clips belong to {IDENTITY[kind].pattern}, not {identity!r}"
    if kind != "real":
        return f"a rendered clip has no consent to give, not {consent!r}" if consent else None
    given = consents.get(consent)
    if given is None:
        return f"no consent {consent!r} in the register"
    if given.identity != identity:
        return f"consent {consent} was given by {given.identity}, not {identity}"
    if not given.standing:
        return f"consent {consent} was withdrawn on {given.withdrawn_on}"
    return None


def problems(clips: list[Clip], consents: dict[str, Consent], folder: Path = DATA) -> list[str]:
    found = []
    for clip in clips:
        problem = consent_problem(clip.kind, clip.identity, clip.consent, consents)
        if problem is not None:
            found.append(f"{clip.clip_id}: {problem}")
        if not any((folder / "clips" / clip.clip_id).glob("frame_*")):
            found.append(f"{clip.clip_id}: no frames")
    return found


def split_of(identity: str) -> str:
    """Training, validation or test, decided by the person alone: nobody is ever in two splits."""
    bucket = int(hashlib.sha256(identity.encode()).hexdigest(), 16) % 100
    return "train" if bucket < 70 else "validation" if bucket < 85 else "test"


def next_clip_id(clips: list[Clip], identity: str, kind: Kind) -> str:
    taken = sum(1 for c in clips if c.identity == identity and c.kind == kind)
    return f"{identity}-{kind.replace('_', '-')}-{taken + 1:03d}"


def record(
    frames: Iterable[NDArray[np.uint8]],
    kind: Kind,
    identity: str,
    camera: str,
    setting: str,
    consent: str = "",
    folder: Path = DATA,
) -> Clip:
    """Keep one clip's frames as JPEGs, after checking that it may be kept at all."""
    for name, value in (("camera", camera), ("setting", setting)):
        if not NAME.fullmatch(value):
            raise ValueError(f"--{name} must be short, lower-case letters, digits and dashes")
    problem = consent_problem(kind, identity, consent, load_consents(folder))
    if problem is not None:
        raise ValueError(problem)
    clips = read_clips(folder)
    clip = Clip(next_clip_id(clips, identity, kind), kind, identity, camera, setting, consent)
    target = folder / "clips" / clip.clip_id
    target.mkdir(parents=True)
    count = 0
    try:
        for count, frame in enumerate(frames, start=1):
            cv2.imwrite(str(target / f"frame_{count:04d}.jpg"), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if count == 0:
            raise ValueError("no frames were recorded")
    except BaseException:
        # Whatever stopped the filming, no half-written clip is left behind.
        shutil.rmtree(target, ignore_errors=True)
        raise
    write_clips([*clips, clip], folder)
    return clip


def inject(folder: Path = DATA) -> list[Clip]:
    """Add each rendered sequence (renders/<identity>/<light>/) as an injected clip, as a virtual camera feeds it."""
    clips = read_clips(folder)
    done = {(c.identity, c.setting) for c in clips if c.kind == "injected_render"}
    added = []
    for sequence in sorted((folder / "renders").glob("*/*")):
        identity, light = sequence.parent.name, sequence.name
        images = sorted(p for p in sequence.iterdir() if p.suffix.lower() in IMAGES)
        if not images or (identity, light) in done:
            continue
        problem = consent_problem("injected_render", identity, "", {})
        if problem is not None or not NAME.fullmatch(light):
            raise ValueError(f"{sequence}: {problem or 'the light set-up must be a short lower-case name'}")
        clip = Clip(next_clip_id(clips, identity, "injected_render"), "injected_render", identity, "none", light)
        target = folder / "clips" / clip.clip_id
        target.mkdir(parents=True)
        for index, image in enumerate(images, start=1):
            shutil.copyfile(image, target / f"frame_{index:04d}{image.suffix.lower()}")
        clips.append(clip)
        added.append(clip)
    write_clips(clips, folder)
    return added


def withdraw(consent_id: str, folder: Path = DATA) -> int:
    """Delete every clip filmed under a consent that has been withdrawn in the register."""
    given = load_consents(folder).get(consent_id)
    if given is None or given.standing:
        raise ValueError(f"mark consent {consent_id} withdrawn (withdrawn_on) in consent.toml first")
    clips = read_clips(folder)
    gone = [c for c in clips if c.consent == consent_id]
    for clip in gone:
        shutil.rmtree(folder / "clips" / clip.clip_id, ignore_errors=True)
    write_clips([c for c in clips if c.consent != consent_id], folder)
    # The prepared crops (dwarpal_ml.render_detector) hold faces too: all of them go, to be prepared again.
    shutil.rmtree(folder / "crops", ignore_errors=True)
    return len(gone)


def read_frame(path: Path) -> Frame:
    """One rendered frame, as OpenCV reads it; a file it can't read is refused by name."""
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"{path} isn't a readable picture")
    return cast("Frame", image)


def played(sequence: Path, show: Show, grab: Grab, settle: int = SETTLE) -> Iterator[Frame]:
    """A rendered sequence shown on a screen and filmed in step: each rendered frame is shown, then one camera frame is
    taken of it. The first is shown a little longer, and what the camera sees meanwhile is dropped."""
    images = sorted(p for p in sequence.iterdir() if p.suffix.lower() in IMAGES)
    if not images:
        raise ValueError(f"{sequence} holds no rendered frames")
    first = read_frame(images[0])
    for _ in range(settle):
        show(first)
        grab()
    for path in images:
        show(read_frame(path))
        frame = grab()
        if frame is None:
            break
        yield frame


def film(sequence: Path, show: Show, grab: Grab, camera: str, setting: str, folder: Path = DATA) -> Clip:
    """A `screen_render` clip of the made-up person whose sequence it is (renders/<identity>/<light>/)."""
    return record(played(sequence, show, grab), "screen_render", sequence.parent.name, camera, setting, "", folder)


def full_screen(device: int) -> tuple[Show, Grab, Callable[[], None]]:  # pragma: no cover - needs a screen and webcam
    """A full-screen window to show frames in, a webcam to grab them from, and a way to close both."""
    capture = cv2.VideoCapture(device)
    if not capture.isOpened():
        raise ValueError(f"camera {device} can't be opened")
    cv2.namedWindow("dwarpal-render", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("dwarpal-render", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def show(image: Frame) -> None:
        cv2.imshow("dwarpal-render", image)
        cv2.waitKey(1)

    def grab() -> Frame | None:
        ok, frame = capture.read()
        return cast("Frame", frame) if ok else None

    def close() -> None:
        capture.release()
        cv2.destroyAllWindows()

    return show, grab, close


def camera_frames(index: int, seconds: float) -> Iterable[NDArray[np.uint8]]:  # pragma: no cover - needs a webcam
    capture = cv2.VideoCapture(index)
    if not capture.isOpened():
        raise ValueError(f"camera {index} can't be opened")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    try:
        for _ in range(round(seconds * fps)):
            ok, frame = capture.read()
            if not ok:
                break
            yield cast("NDArray[np.uint8]", frame)
    finally:
        capture.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dwarpal-ml renders", description="The render detector's own data")
    parser.add_argument("--folder", type=Path, default=DATA)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="every clip may be kept and has frames")
    commands.add_parser("split", help="clips per split and kind")
    commands.add_parser("inject", help="add rendered sequences as injected clips")
    filming = commands.add_parser("record", help="film one clip from a webcam")
    filming.add_argument("--kind", choices=KINDS, required=True)
    filming.add_argument("--identity", required=True)
    filming.add_argument("--camera", required=True, help="a short name for the camera, e.g. laptop")
    filming.add_argument("--setting", required=True, help="room and light, e.g. study-dim")
    filming.add_argument("--consent", default="", help="the consent ID, for a real person")
    filming.add_argument("--device", type=int, default=0, help="the webcam's number")
    filming.add_argument("--seconds", type=float, default=6.0)
    showing = commands.add_parser("film", help="show a rendered sequence full-screen and film it in step")
    showing.add_argument("sequence", type=Path, help="renders/<identity>/<light>/")
    showing.add_argument("--camera", required=True)
    showing.add_argument("--setting", required=True, help="the screen, room and light, e.g. phone-study-dim")
    showing.add_argument("--device", type=int, default=0)
    leaving = commands.add_parser("withdraw", help="delete the clips of a withdrawn consent")
    leaving.add_argument("consent")
    args = parser.parse_args(argv)
    folder: Path = args.folder
    try:
        if args.command == "record":
            frames = camera_frames(args.device, args.seconds)
            clip = record(frames, args.kind, args.identity, args.camera, args.setting, args.consent, folder)
            print(f"recorded {clip.clip_id}")
        elif args.command == "film":  # pragma: no cover - needs a screen and webcam
            show, grab, close = full_screen(args.device)
            try:
                clip = film(args.sequence, show, grab, args.camera, args.setting, folder)
            finally:
                close()
            print(f"recorded {clip.clip_id}")
        elif args.command == "inject":
            print(f"added {len(inject(folder))} injected clips")
        elif args.command == "withdraw":
            print(f"deleted {withdraw(args.consent, folder)} clips")
        elif args.command == "split":
            counts = Counter((split_of(c.identity), c.kind) for c in read_clips(folder))
            for (split, kind), count in sorted(counts.items()):
                print(f"{split:<11} {kind:<16} {count}")
        else:
            found = problems(read_clips(folder), load_consents(folder), folder)
            print("\n".join(found) if found else "every clip may be kept")
            return 1 if found else 0
    except ValueError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
