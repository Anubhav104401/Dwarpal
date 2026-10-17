---
fingerprint: c698981041cba065
---
The package's **front door**. Code elsewhere can write `from dwarpal_contracts import FaceAnalysis` without knowing that the class actually lives in the module `face.py` inside the package. If the package is reorganised later, only this file changes, not every place that imports from it.

@@ 1
The docstring: data models shared across services, so their messages can never drift apart.

@@ 3-20
**Re-export the public names** from the `face` module. The parentheses let one `import` statement span several lines, one name per line, which keeps future changes easy to review.

- `MAX_FRAME_BYTES`, `MAX_FRAMES` — the size limits for one face attempt (added in Phase 1);
- `POLICY_AGES` — the ages the system reports probabilities for;
- `AgeEstimate`, `FaceAnalysis`, `FaceRequestMeta`, `FrameMeta`, `FrameReport` — the message shapes (all explained in `face.py`).

Added in Phase 3, for liveness: `POSES`, `Pose` and `Phase` (the head poses and capture phases), `Challenge` (what the server asked for), `ClientSignals` (what the browser reports about itself), and `Liveness`, `PoseCheck` and `LightCheck` (what the inference service found).

@@ 22-39
`__all__` lists the names that form the package's **public interface**. Tools and readers use it to see what is meant for outside use. It also tells Ruff that the imports above are used on purpose — re-exported — and not forgotten leftovers.

Look closely and you'll see that `MAX_FRAMES` and `MAX_FRAME_BYTES` swap places between the import above and this list. Both lists are kept sorted by Ruff, but by two different rules: the import sorter (`I001`) and the `__all__` sorter (`RUF022`) compare the underscore `_` with letters differently. The order has no effect on Python — and since Ruff fixes both lists automatically, no human ever has to think about it.
