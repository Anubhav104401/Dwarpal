---
fingerprint: 51e79f6aa11164f0
---
The hero's **3D scene** (decision D1): the face's points drawn with **three.js** and WebGL — the browser's way of using the graphics card. Its two small *shaders* run on the graphics card itself; the rest sets them up and animates them.

It is loaded only in the browser, only when the hero can animate (`face-hero.tsx`), and only once the page is idle, so it never slows the page's first appearance.

@@ 1-3
The module's comment: what the scene shows and when it is loaded — in the browser only, and only when it will be shown.

@@ 5-15
From **three.js** (decision D1), the pieces used: buffers to hand the points to the graphics card, a colour, a blending mode, a camera, a points object, a scene, a material written as shaders, and the renderer that draws with WebGL.

@@ 17
The face's points (`face-cloud.ts`).

@@ 19-20
**The vertex shader** — a small program, in the graphics card's language GLSL, run once per point on the graphics card. (`/* glsl */` only tells editors which language the text is.)

@@ 21-26
Its inputs: the scan line's height, how far the points are scattered, the points' size, and each point's own `seed`; and two values it passes on to the next shader (`varying`): how lit by the scan line the point is, and how bright its depth makes it.

@@ 27-29
Points nearer the viewer — the nose, the cheeks — are brighter than the eye hollows and the edges: that is what makes a cloud of points read as a face.

@@ 30-32
Scattering pushes each point outwards along its own direction, by its own amount; then the point is placed in the camera's view (`modelViewMatrix` turns the face and moves it in front of the camera).

@@ 33
`glow` — 1 on the scan line, fading to 0 within 0.12 of it.

@@ 34-36
The point's size on screen: larger when lit, smaller further away; and its position on screen (`projectionMatrix` applies the camera's perspective).

@@ 37
The end of the vertex shader.

@@ 39-44
**The fragment shader** — run once for every pixel of every point. Its inputs: the face's colour, the scan line's colour, and the two values passed on.

@@ 45-47
How far this pixel is from the point's centre; outside the circle, draw nothing (`discard`), so each point is round.

@@ 48-50
A soft edge, faded by depth or lit by the scan line, whichever is brighter; and the colour, moving from the face's to the line's as it is lit.

@@ 51
The end of the fragment shader.

@@ 53-54
**`rgb`** — the design's colours are written in OKLCH (§5.5.1), which three.js can't read. So the colour is painted into a one-pixel canvas — the browser converts it — and the pixel is read back as red, green and blue.

@@ 55-62
A 1 × 1 canvas and its 2D context (`willReadFrequently` tells the browser the pixel will be read back). Without one, a mid grey.

@@ 63-67
Paint the pixel, read its four values (red, green, blue, alpha, each 0–255), and scale the first three to 0–1.

@@ 69-72
**`token`** — a design token's value as the page has it, such as `--color-brand-500`; grey if it's missing.

@@ 74-75
**`startFaceScene`** — start drawing on the canvas; it returns a function that stops and frees everything.

@@ 76-77
The renderer, drawing on that canvas with a transparent background and smooth edges; at the screen's pixel density, but never more than double (very dense screens would cost much and show little).

@@ 79-83
The points, and a `seed` for each — a number from 0 to 0.6 that spreads evenly (multiples of the golden ratio's fraction), so points scatter by different amounts. Both are handed to the graphics card as attributes.

@@ 85-92
The shaders' inputs (*uniforms*), changed every frame: scan line, scatter, size; and the colours — the face a dark grey on a light page and a light grey on a dark one, the scan line saffron.

@@ 93-100
The material: the two shaders, transparent, not hiding what's behind it (`depthWrite: false`), blended normally.

@@ 101-104
The face as points, in a scene; a camera with a narrow 30° view, set back 5.2 units, so the face fills the canvas with a little room to turn and scatter.

@@ 106-116
Follow the canvas's size: resize the drawing, keep the camera's proportions right, and size the points to the canvas's height. A `ResizeObserver` calls this whenever the canvas changes size; and once now.

@@ 118-123
Draw only while the hero is on screen: an `IntersectionObserver` says whether the canvas is visible. No work for nobody.

@@ 125-131
The animation: `requestAnimationFrame` calls `draw` before each screen refresh, and `draw` asks for the next one first. Off screen or in a hidden tab, it skips the drawing.

@@ 132-135
Seconds since starting; the face turns gently left and right, and nods a little; the scan line passes up and down.

@@ 136-139
Every 9 seconds, in the last fifth: scatter out and gather back (half a sine wave), then draw the frame.

@@ 141
Start the animation.

@@ 143-151
The stop function: cancel the next frame, stop both observers, and free the graphics card's memory (`dispose`).

@@ 140
The end of `draw`.
