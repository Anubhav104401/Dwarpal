---
fingerprint: fe484f591e185f7b
---
The **inference service's container image** (Phase 8, §5.8.2): the face pipeline, liveness, the age model's runtime, and — for the document check — Tesseract.

@@ 1-3
What this file makes — the inference service's container image — how to build it, and that the models are not inside it: they are mounted read-only when it runs, so an image can be rebuilt or shared without them.

@@ 5
**Stage 1, `build`** — start from the official Python 3.13 image, its *slim* Debian 12 form, pinned to an exact release (3.13.17) that was at least a week old.

@@ 15-18
The inference service's source, and the two libraries it uses: the contracts and the vision library.

@@ 19
Install the locked versions of the inference package and its dependencies — OpenCV, ONNX Runtime, NumPy — as copies, without developer tools.

@@ 21-26
**Stage 2.** Install **Tesseract** and its English model from Debian (in development it runs in its own container, §5.6.2; in production it lives here), delete apt's package lists so they don't bloat the image, and create the unprivileged user. One `RUN` step keeps it all in one image layer.

@@ 27
Copy in the installed environment.

@@ 28
The environment's programs on the path, unbuffered output, and the models' folder: `/models`, where Compose mounts them.

@@ 29-32
Run as the unprivileged user, in `/app`, listening on port 8001 — reached only by the API, on the private network.

@@ 6-8
uv, its image settings and the working folder, exactly as for the API (`services/api/Dockerfile`).

@@ 9-14
The workspace's description, the lockfile, and every member's own description: uv needs them all to read the shared lockfile.
