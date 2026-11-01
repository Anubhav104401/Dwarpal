# Tesseract OCR, for reading the machine-readable zone (MRZ) of passports and ID cards (Phase 6, decision D6b).
# On this project's computers it runs in a container rather than as a system-wide install; the inference service hands it
# one image at a time through `docker exec` (see `tesseract_command` in the inference service's settings).
FROM debian:bookworm-20261020-slim

# Debian's packaged Tesseract 5 with its English model only: the MRZ uses capital letters, digits and `<`, and the
# reader limits Tesseract to those characters.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Nothing here needs root, the network or a disk to write to: the compose file gives it none.
USER nobody

# Waits, doing nothing, for `docker exec` to run `tesseract` inside it.
CMD ["sleep", "infinity"]
