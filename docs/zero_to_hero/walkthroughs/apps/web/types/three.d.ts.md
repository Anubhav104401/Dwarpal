---
fingerprint: daa3f6e7cd1ddb2a
---
Hand-written **type definitions** for the parts of three.js the hero uses (§5.5.10), so TypeScript can check the hero's code.

@@ 1-2
Why this file exists: three.js ships no type definitions, and the usual ones (`@types/three`) are a separate download not yet approved (D1b). So the few parts the hero uses are described here by hand.

@@ 3
`declare module "three"` — "when code imports `three`, these are the shapes it gets". TypeScript trusts this; it can't check it against three.js itself, so it is kept to what the hero uses.

@@ 4
The normal blending mode's number.

@@ 6-8
A colour, made from red, green and blue between 0 and 1.

@@ 10-12
A buffer attribute: a flat list of numbers, and how many make one item (3 for a position).

@@ 14-17
A geometry: attributes are set on it (and it returns itself, so calls can be chained), and it can free its memory.

@@ 19-21
A uniform: a shader input with a `value`.

@@ 23-34
A shader material: its uniforms, the two shaders' source, and the options the hero sets; it can free its memory.

@@ 36-38
Anything that can be placed in a scene can be turned (`rotation`).

@@ 40-42
Points: a geometry drawn with a material.

@@ 44-46
A scene, which things are added to (it returns itself).

@@ 48-53
A perspective camera: its view angle, proportions, nearest and furthest distance; its position; and the call that applies a change of proportions.

@@ 55-61
The renderer: made on a canvas, with options; its pixel density and size; drawing a scene through a camera; and freeing its memory.

@@ 62
The end of the declarations.
