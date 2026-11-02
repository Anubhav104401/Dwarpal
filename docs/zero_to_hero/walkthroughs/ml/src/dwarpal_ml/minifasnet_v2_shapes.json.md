---
fingerprint: b35f22df299878ad
---
**MiniFASNet V2's shapes** (§5.9.4): the network's layout without its weights.

@@ 1-336
The name and shape of each of MiniFASNet V2's 334 tensors — `[32, 3, 3, 3]` is 32 filters, each 3 × 3 over 3 colours — written out once from the weights file (Apache-2.0) by a one-off script. Only shapes, no weights: enough to build the same network without the file, which `render_detector.base_state` does for training from scratch and for tests on machines that never fetched it.
