---
fingerprint: 479b9067ab251b96
---
**The home page's artwork** (§5.5.9): the brand's motif from the design — a face made of points of light inside a temple doorway, the place a dwarpal guards — drawn as SVG.

@@ 1-3
**`facePoints`** — where the points sit, and an empty list to fill.

@@ 4-6
Six rings, from the centre out; ring *n* has 8 × *n* points, so the points stay about evenly spaced as the rings grow.

@@ 7
Each point's angle around its ring; turning each ring a little (`ring * 0.4`) keeps the points from lining up in spokes.

@@ 8-12
The point's place on an oval 104 wide and 136 tall, centred at (120, 156): `cos` gives the across, `sin` the up and down, scaled by how far out the ring is. Rounded to one decimal place, so the server and the browser write exactly the same numbers.

@@ 13-16
The end of the loops; the points.

@@ 18
Worked out once, when the module loads, not each time the page is drawn.

@@ 20-25
What the artwork is, and why its one motion runs only for people who haven't asked their system for less; and, since the 3D hero (§5.5.10), that the 3D face takes the points' place where the browser can draw it.

@@ 26-28
The picture: 240 × 280 units, as wide as its place allows up to `max-w-72`; hidden from screen readers, since it is decoration and says nothing the text doesn't. `face` — whether to draw the face's points and line — is on unless the 3D face has replaced them.

@@ 29-35
The doorway: up the left side, a half circle over the top (`a92 92 …`, an arc of radius 92), and down the right — in saffron.

@@ 36-41
The threshold, a line across the bottom, dark on light and light on dark.

@@ 63-65
The end of the picture.

@@ 42-50
With a face: one circle per point, keyed by its place; the outer ring larger and saffron, the face's outline.

@@ 51-62
With a face, too: the line of light that passes over it, as a check would. Its group carries `animate-scan` (`globals.css`), only when motion is welcome (`motion-safe:`); otherwise the line rests across the middle.
