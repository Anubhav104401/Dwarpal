---
fingerprint: 25f82a5d94cbfda2
---
The home page's **hero** (decision D1): the doorway artwork with a 3D face of points inside it. It decides whether the 3D face may run at all, loads it only when the page is idle, and falls back to the still artwork otherwise.

@@ 1
A **client component**: it runs in the browser, where WebGL and animation live.

@@ 3-5
React's effect, reference and state hooks, and the still artwork.

@@ 7-17
**`canAnimate`** — two questions. Has the person asked their system for less motion (`prefers-reduced-motion`)? Then no. Otherwise, can this browser make a WebGL 2 drawing context? If making one fails or throws, no.

@@ 19-23
**`FaceHero`** — the hero, and how it degrades: the still artwork first; the 3D face only where it can run, only once the browser is idle; and anything that goes wrong leaves the still artwork.

@@ 24-26
A reference to the canvas, and whether the 3D face is running.

@@ 28-31
After the page appears: nothing at all for a browser that shouldn't animate.

@@ 32-33
The stop function, once the scene runs; and a flag for a page left before the scene arrived.

@@ 34-44
**`begin`** — fetch the scene's code (`import()` loads it as a separate file, only now), start it on the canvas, and show it. If the page was left meanwhile, do nothing; if loading fails, the still artwork stays.

@@ 45-46
Wait for a quiet moment (`requestIdleCallback`, at most 2.5 seconds), so the 3D code never competes with the page's first paint or first input. Safari has no `requestIdleCallback`: there, a timer of 1.2 seconds.

@@ 47-53
On leaving the page: cancel whichever wait it was, and stop the scene.

@@ 55-57
The still artwork, without its points once the 3D face runs.

@@ 58-61
The canvas in the face's box inside the doorway — the artwork's proportions in percentages — hidden from screen readers as decoration, and invisible until the scene runs.

@@ 62-64
The end of the component.
