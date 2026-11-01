---
fingerprint: 3560e81ab6a85aa2
---
Unit tests for **preparing the document photo** (§5.6.3): the size it is drawn at, and the order of JPEG qualities tried.

@@ 1-3
Vitest's tools, and the pure parts under test: the size calculation, the side limit and the list of qualities. (`prepareDocument` needs a real browser's canvas; the browser test exercises it.)

@@ 5-9
**Test — a large photo is scaled down so its longer side fits, keeping its shape**: landscape and portrait, both to 2000 on the long side, 1500 on the other.

@@ 11-13
**Test — a small photo is never enlarged.**

@@ 15-17
**Test — no side is ever drawn at zero pixels**, however thin the picture: a canvas side of zero would draw nothing.

@@ 20-24
**Test — the qualities are tried from the best down**: the list equals itself sorted in descending order.

@@ 18
The end of the size tests.
