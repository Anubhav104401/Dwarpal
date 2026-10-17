---
fingerprint: a18b6a281ba47466
---
A small build step that puts MediaPipe's files where the browser can load them. It runs before the verify page's development server starts and before every production build (`package.json`).

Next.js serves everything in a project's `public/` folder as it is, at the site's own address. So this script copies two kinds of file into `public/mediapipe/`: MediaPipe's **WebAssembly** engine, from the installed package, and the **face model**, from the project's pinned model files (`models/third_party.json`).

`.mjs` means a JavaScript **module** run directly by Node.js — no TypeScript, no build of its own.

@@ 1-2
The comment says what the script does and when it runs, and that its output folder is generated — so it is listed in `.gitignore` and never committed.

@@ 4
Three file-system functions from Node.js, in their promise form (`fs/promises`), so they can be `await`ed: `copyFile`, `mkdir` (make a folder) and `stat` (look up a file's details — used here to see whether it exists).

@@ 6
Where the WebAssembly files are: inside the installed package. `new URL(…, import.meta.url)` builds a path **relative to this script's own location**, so the script works whichever folder it is run from. `import.meta.url` is the script's own address.

@@ 7
Where the face model is: `models/third_party/face_landmarker.task`, three folders up, at the repository's root, where `fetch_models.py` downloads it and checks its fingerprint.

@@ 8
Where everything goes: `public/mediapipe/`.

@@ 10
Make the `wasm/` folder inside it — and any missing folders above it (`recursive: true`). It is no error if it already exists.

@@ 11
The comment explains why there are four files: the same engine built twice. **SIMD** ("single instruction, multiple data") lets the processor work on several numbers at once; most browsers support it and get the faster build, and the rest get the other.

@@ 12-17
The four files: each build is a JavaScript loader (`.js`) and the engine itself (`.wasm`).

@@ 18-19
Copy each into `public/mediapipe/wasm/`.

@@ 21-24
Does the face model exist? `stat` succeeds if it does and fails if it doesn't; `.then(() => true, () => false)` turns the two cases into `true` or `false`.

@@ 25-26
If it does, copy it in.

@@ 27-32
If not — `fetch_models.py` hasn't been run yet — say so, with the command to fix it, and carry on: the verify page still works, only without live guidance. A warning rather than an error, so that a fresh checkout can still start the page.
