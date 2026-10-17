// Puts MediaPipe's WebAssembly files and the pinned face model into public/mediapipe/, where the browser loads them.
// Run before `next dev` and `next build`. The folder is generated, so Git ignores it.

import { copyFile, mkdir, stat } from "node:fs/promises";

const wasm = new URL("../node_modules/@mediapipe/tasks-vision/wasm/", import.meta.url);
const model = new URL("../../../models/third_party/face_landmarker.task", import.meta.url);
const target = new URL("../public/mediapipe/", import.meta.url);

await mkdir(new URL("wasm/", target), { recursive: true });
// Two builds of the same engine: the browser picks the faster one (SIMD) when it can, and the other when it can't.
for (const name of [
  "vision_wasm_internal.js",
  "vision_wasm_internal.wasm",
  "vision_wasm_nosimd_internal.js",
  "vision_wasm_nosimd_internal.wasm",
]) {
  await copyFile(new URL(name, wasm), new URL(`wasm/${name}`, target));
}

const present = await stat(model).then(
  () => true,
  () => false,
);
if (present) {
  await copyFile(model, new URL("face_landmarker.task", target));
} else {
  console.warn(
    "mediapipe: models/third_party/face_landmarker.task is missing (run `uv run infra/scripts/fetch_models.py`);" +
      " the verify page will work without live guidance.",
  );
}
