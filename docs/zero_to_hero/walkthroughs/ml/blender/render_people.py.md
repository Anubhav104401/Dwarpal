---
fingerprint: 1a003c97b56545c3
---
**Rendering made-up people** (decision D23, §5.9.4): a script that runs inside Blender, builds random adults with MPFB and MakeHuman's CC0 assets, and films them doing the liveness challenge under three lights.

@@ 1-10
The module's docstring: it renders made-up adults doing the liveness challenge, runs **inside Blender** (not in the project's own Python) with MPFB and MakeHuman's CC0 assets installed, and shows the command. Each person comes from a seed, adults only; a camera circles the head through the challenge's movements under three lights, and the frames go where `renders inject` and `renders film` expect them.

@@ 12
The project-wide type-hint setting.

@@ 14-21
Command-line options, importing a module by its name, JSON, maths, random numbers, the argument list, paths, and the type for *any value* (Blender's objects have no type hints).

@@ 23-24
**`bpy`**: Blender's own Python interface — everything Blender can do, a script can do through it. **`Vector`**: Blender's 3D vector, from its maths module.

@@ 26-28
The repository's root, where the renders go, and the name Blender gives the MPFB extension once installed (from the `user_default` repository).

@@ 29-30
**Adults only**: of MakeHuman's age anchors (baby, child, young, middle age, old), only the three adult ones may be drawn. No render may look like a child (ADR-0021).

@@ 31
The three lights: soft from the front, from the side, and a dim room.

@@ 32-34
30 frames a second, of which every third is rendered; 1280 × 720, a webcam's usual size.

@@ 35-37
**The challenge's movements**: at each second, how far the head is turned and lifted. Ahead for a second, 35° one way and back, 35° the other way and back, 18° up and back — six seconds, as the verify page asks. The head itself never moves: the camera circles it the other way, which the camera sees the same, and needs no skeleton.

@@ 38-40
The camera's distance (an arm's length, as a laptop's webcam), its lens (a webcam's wide view), and how far behind the eyes the head turns.

@@ 43-44
**`mpfb`**: one of MPFB's modules, by name. MPFB is installed as an extension, so its modules are found under Blender's extension package, not by a plain `import`.

@@ 47-51
**`person_spec`**: MPFB's own default for random people (its *phenotype* spec)…

@@ 52
…limited to the adult ages…

@@ 53-57
…always dressed: the system pack's clothes are whole outfits, so the full-body slot always draws one, and the upper- and lower-body slots, which would find nothing, are off…

@@ 58-59
…with random face and body details (MPFB's default detail spec over every section of its targets, except the measurements)…

@@ 60-71
…and how to build the person: in metres, without extra helpers or a skeleton, with one level of smoothing when rendered.

@@ 74-79
**`empty_scene`**: a new, empty scene, at the frame rate, size and file format above.

@@ 80-82
Frames 1 to 180 (six seconds), every third rendered: 10 a second still follows every movement, and the detector's crops use every fifth frame anyway.

@@ 83-89
**EEVEE**, Blender's fast renderer: thousands of frames are needed, and its name has changed between Blender versions, so both are tried.

@@ 90
32 samples per pixel: smooth enough, and fast.

@@ 93-95
**`head_centre`**: where the head turns — 8 cm behind the middle of the eyes.

@@ 96-97
The eyes are their own object, which MPFB marks with the type *Eyes*; its marks find them whatever the mesh is called. (The body mesh carries hidden helper shapes, which made measuring it unreliable.)

@@ 98-99
The middle of the eyes' bounding box, moved back towards the neck.

@@ 102-104
**`make_person`**: one random person, by MPFB's own randomiser and builder.

@@ 105-107
The spec, a random-number generator started from the seed (not for anything secret, so the linter's warning is silenced), and the person's body proportions drawn from it.

@@ 108-109
The person built — body, skin, eyes, hair, eyebrows, outfit — with warnings ignored; the head's centre and the proportions are returned.

@@ 112-113
**`backdrop`**: a plain wall behind the person, as a room behind a webcam user.

@@ 114-117
A plane 20 m wide (so the camera never sees past its edge when it swings to the side), 1.4 m behind the head, stood upright.

@@ 118-122
A new material of a random, muted colour for it.

@@ 125-126
**`camera_rig`**: the camera, on an arm from the head's centre.

@@ 127-129
The arm: an empty object at the head's centre (an *empty* has a place but no shape).

@@ 130-133
A camera with the webcam's lens, attached to the arm.

@@ 134-138
In front of the face — at arm's length plus the distance back to the turning point — looking back at it; it is the scene's camera.

@@ 139-143
One keyframe per movement: the arm is turned (and tilted for the look-up), and Blender moves smoothly between keyframes. Turning the arm left makes the head seem to turn right, and both turns are asked for, so the direction doesn't matter; for a lifted chin the camera must drop, to see more of the chin's underside.

@@ 146-148
**`light`**: one of the three lights. The previous light goes first.

@@ 149-152
The world (what is seen and lit where nothing else is), with its background node.

@@ 153-158
Each light: where it stands from the face, its power, and how much light the room gives besides.

@@ 159
The room's light.

@@ 160-165
An area light (soft, like a window or a lamp's shade), 80 cm across, placed and turned to face the head.

@@ 168-170
**`render_person`**: one person, all its lights — or, for a preview, only some lights and frames.

@@ 171-174
A new scene, the person, the wall (its colour from the next seed), the camera.

@@ 175-177
Their folder, and `person.json` beside the frames: the seed and the drawn proportions, so a person can be made again and checked.

@@ 178-184
For each light: the light, then the whole animation, each frame saved as `0001.png`, `0004.png`, … (`####` is filled with the frame's number).

@@ 185-189
A preview renders only the frames asked for.

@@ 192-193
**`main`**: Blender passes its own options too; a script's come after `--`.

@@ 194-202
The options: the first person's number, how many, where to write, which lights, and which frames for a preview.

@@ 203-206
Each person in turn. The seed is 1000 plus the person's number, so `render-007` is always the same made-up person.

@@ 207
Success.

@@ 210-211
Run as a script, `main`'s answer becomes the exit code.
