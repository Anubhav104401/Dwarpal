"""Render made-up adults doing the liveness challenge, for the render detector's data (ADR-0021, protocol steps 2-3).

Runs inside Blender 5.2 with the MPFB extension and MakeHuman's CC0 system assets installed (decision D23):

    blender --background --python ml/blender/render_people.py -- --first 1 --count 40

Each person is drawn at random by MPFB from a seed — adults only — and filmed by a camera that circles the head
through the challenge's movements (look ahead, left, right, up), under three lights. The frames go to
.datasets/render-detector/renders/render-NNN/<light>/, ready for `renders inject` and `renders film`.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / ".datasets" / "render-detector" / "renders"
MPFB = "bl_ext.user_default.mpfb"
# MakeHuman's adult ages only: no render may look like a child.
ADULT_AGES = ["young", "middleage", "old"]
LIGHTS = ("front-soft", "side", "dim")
FPS = 30
STEP = 3
WIDTH, HEIGHT = 1280, 720
# The challenge, as the camera sees it: (second, turn, look up), in degrees. The camera circles the head the opposite
# way, which looks the same from the camera, without rigging a neck.
MOVES = [(0.0, 0, 0), (1.0, 0, 0), (1.8, 35, 0), (2.6, 0, 0), (3.4, -35, 0), (4.2, 0, 0), (5.0, 0, 18), (6.0, 0, 0)]
DISTANCE = 0.55  # metres from the face: a laptop's webcam at arm's length
LENS = 26.0  # millimetres on a 36 mm sensor: a webcam's wide view
BEHIND_EYES = 0.08  # metres from the eyes back to where the head turns (MPFB's people face -Y)


def mpfb(module: str) -> Any:
    return importlib.import_module(f"{MPFB}.{module}")


def person_spec() -> dict[str, Any]:
    """MPFB's default randomisation, limited to adults, with face-shape details on and no rig."""
    service = mpfb("services").RandomizationService
    builder = mpfb("ui.new_human.randomize.characterbuilder")
    spec: dict[str, Any] = service.get_default_phenotype_spec()
    spec["phenotype"]["attributes"]["age"]["allowed"] = ADULT_AGES
    # The system pack's clothes are whole outfits ("...suit"): always one, as a webcam user is dressed.
    clothes = spec["assets"]["clothes"]
    clothes["full_body"].update({"enabled": True, "chance": 100})
    for slot in ("upper_body", "lower_body"):
        clothes[slot]["enabled"] = False
    sections = [name for name in builder._parse_detail_sections() if name != "measure"]
    spec["details"] = service.get_default_detail_spec(sections)
    spec["creation"] = {
        "scale_factor": "METER",
        "detailed_helpers": False,
        "extra_vertex_groups": True,
        "mask_helpers": True,
        "rig": "NONE",
        "auto_generate_rigify": False,
        "meta_rig_action": "hide",
        "add_subdiv_modifier": True,
        "subdiv_render_levels": 1,
    }
    return spec


def empty_scene() -> None:
    bpy.ops.wm.read_homefile(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
    scene.render.image_settings.file_format = "PNG"
    scene.frame_start, scene.frame_end = 1, round(MOVES[-1][0] * FPS)
    # Every third frame: 10 a second still follows every movement, and the detector's crops use every fifth anyway.
    scene.frame_step = STEP
    # EEVEE is fast enough for thousands of frames on a laptop; its name changed between Blender versions.
    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 32


def head_centre(basemesh: Any) -> Vector:
    """Where the head turns: 8 cm behind the middle of the eyes. The eyes are their own object, so this holds whatever
    the person's height (the body mesh itself carries hidden helper shapes that would mislead a measurement)."""
    objects = mpfb("services").ObjectService
    eyes = objects.find_object_of_type_amongst_nearest_relatives(basemesh, "Eyes", only_children=True)
    corners = [eyes.matrix_world @ Vector(corner) for corner in eyes.bound_box]
    return sum(corners, Vector()) / len(corners) + Vector((0.0, BEHIND_EYES, 0.0))


def make_person(seed: int) -> tuple[Vector, dict[str, Any]]:
    service = mpfb("services").RandomizationService
    builder = mpfb("ui.new_human.randomize.characterbuilder")
    spec = person_spec()
    rng = random.Random(seed)  # noqa: S311 - a seed, so a person can be made again; nothing secret
    macro = service.randomize_macro_info_dict(spec, rng)
    basemesh = builder.build_character(spec, macro, rng, lambda *_: None, builder.build_discovery_context())
    return head_centre(basemesh), macro


def backdrop(centre: Vector, rng: random.Random) -> None:
    """A plain wall behind the person, in a random muted colour, as a room behind a webcam user."""
    # 20 m wide, so the camera never sees past its edge when it swings to the side.
    place = (centre.x, centre.y + 1.4, centre.z)
    bpy.ops.mesh.primitive_plane_add(size=20, location=place, rotation=(math.pi / 2, 0, 0))
    wall = bpy.context.object
    material = bpy.data.materials.new("wall")
    material.use_nodes = True
    shade = [rng.uniform(0.15, 0.7) for _ in range(3)]
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*shade, 1.0)
    wall.data.materials.append(material)


def camera_rig(centre: Vector) -> Any:
    """A camera on an arm from the head's centre: turning the arm circles the camera around the face."""
    pivot = bpy.data.objects.new("pivot", None)
    pivot.location = centre
    bpy.context.collection.objects.link(pivot)
    camera_data = bpy.data.cameras.new("webcam")
    camera_data.lens = LENS
    camera = bpy.data.objects.new("webcam", camera_data)
    camera.parent = pivot
    # MPFB's people face -Y: the camera stands in front, looking back at the face.
    camera.location = (0.0, -DISTANCE - BEHIND_EYES, 0.0)
    camera.rotation_euler = (math.pi / 2, 0.0, 0.0)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    for second, turn, look_up in MOVES:
        # Lifting the chin shows the camera more of its underside: the camera drops (a positive turn about X).
        pivot.rotation_euler = (math.radians(look_up), 0.0, math.radians(-turn))
        pivot.keyframe_insert("rotation_euler", frame=1 + round(second * FPS))
    return pivot


def light(kind: str, centre: Vector) -> None:
    for item in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(item)
    world = bpy.context.scene.world or bpy.data.worlds.new("world")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    # (where the light stands, relative to the face; its power in watts; the room's own light)
    place, power, ambient = {
        "front-soft": (Vector((0.3, -1.2, 0.4)), 60.0, 0.35),
        "side": (Vector((1.2, -0.2, 0.2)), 80.0, 0.08),
        "dim": (Vector((-0.6, -1.0, 0.8)), 12.0, 0.03),
    }[kind]
    background.inputs["Strength"].default_value = ambient
    data = bpy.data.lights.new(kind, type="AREA")
    data.energy, data.size = power, 0.8
    lamp = bpy.data.objects.new(kind, data)
    lamp.location = centre + place
    lamp.rotation_euler = (centre - lamp.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(lamp)


def render_person(
    number: int, seed: int, out: Path, lights: tuple[str, ...] = LIGHTS, frames: list[int] | None = None
) -> None:
    empty_scene()
    centre, macro = make_person(seed)
    backdrop(centre, random.Random(seed + 1))  # noqa: S311 - as above
    camera_rig(centre)
    folder = out / f"render-{number:03d}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "person.json").write_text(json.dumps({"seed": seed, "macro": macro}, indent=2), encoding="utf-8")
    scene = bpy.context.scene
    for kind in lights:
        light(kind, centre)
        if frames is None:
            scene.render.filepath = str(folder / kind / "####")
            bpy.ops.render.render(animation=True)
            continue
        # A preview: only the frames asked for.
        for frame in frames:
            scene.frame_set(frame)
            scene.render.filepath = str(folder / kind / f"{frame:04d}")
            bpy.ops.render.render(write_still=True)


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="render_people", description="Render made-up adults")
    parser.add_argument("--first", type=int, default=1, help="the first person's number (render-NNN)")
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--lights", default=",".join(LIGHTS), help="which lights, e.g. front-soft")
    parser.add_argument("--frames", default="", help="a preview of only these frames, e.g. 1,55,151")
    args = parser.parse_args(argv)
    lights = tuple(args.lights.split(","))
    frames = [int(f) for f in args.frames.split(",")] if args.frames else None
    for number in range(args.first, args.first + args.count):
        # The seed comes from the number, so a person can be rendered again exactly.
        render_person(number, 1000 + number, args.out, lights, frames)
        print(f"rendered render-{number:03d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
