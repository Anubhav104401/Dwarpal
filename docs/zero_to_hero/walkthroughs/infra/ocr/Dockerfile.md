---
fingerprint: adda07eb720b1b37
---
The **OCR container**: Tesseract, packaged so the step-up check (§5.6.2) can read passports' machine-readable zones without installing anything on the computer. A *Dockerfile* is a recipe for a container image: start from a base image, run some steps, say what the container runs.

In production the inference service's own image will include Tesseract (Phase 8), and this container won't be needed.

@@ 1-3
What this image is for (Phase 6, decision D6b): **Tesseract**, a free OCR engine — software that turns a picture of text into text — kept in a container so that nothing has to be installed on the computer itself. The inference service hands it one picture at a time with `docker exec`.

@@ 4
Start from Debian 12 ("bookworm"), in its *slim* form — the smallest Debian that still has a package manager — pinned to the release of 20 October 2026, older than the seven-day cooldown (§4.6).

@@ 6-7
Why only English: an MRZ holds just capital letters, digits and `<`, and the reader limits Tesseract to those, so no other language's model is needed.

@@ 8-10
One `RUN` step, three commands joined with `&&` (each runs only if the one before succeeded) and split over lines with `\`:
- `apt-get update` — fetch Debian's current list of packages;
- `apt-get install --yes --no-install-recommends` — install Tesseract and its English model, without asking, and without the "recommended" extras;
- `rm -rf /var/lib/apt/lists/*` — delete that package list again, so the image doesn't carry it. Doing all three in one step keeps the image small.

@@ 12-13
`USER nobody` — run as an account with no rights at all. Tesseract needs no special access, and together with the compose file's settings (no network, read-only files, no privileges) a fault in it could reach nothing.

@@ 15-16
The container's main program does nothing — `sleep infinity` — and only keeps the container running, so `docker exec` can start `tesseract` inside it whenever a document needs reading.
