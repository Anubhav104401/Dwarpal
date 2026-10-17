---
fingerprint: c46c710b3485917a
---
Tests for training. A real run takes most of an hour on a GPU, so these test the pieces separately, and finish with one **tiny run**: 16 faces, a very small network (`resnet10t`), 64×64 pixels, two epochs, on the processor. It proves the whole loop works — loading, training, scoring, recording, saving — in seconds, on any computer, including CI's, which has no GPU.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-8
`json` (to read the run record), `pickle` (to copy the dataset as the loader does), `zipfile` and `Path`.

@@ 10-17
OpenCV, NumPy, pytest, timm, PyTorch, Hypothesis, and `save_file` from safetensors (to write a small weights file for a test).

@@ 19-31
The code under test, and the vision library's decoder.

@@ 33
The test portrait (§5.2.3).

@@ 36-37
**`row`** — a helper that makes a manifest row with a band and a split.

@@ 40-45
**Every band becomes a proper distribution.** For any band Hypothesis invents (starting from 0 to 90, 1 to 11 years wide): 101 numbers, adding up to 1, with the highest one inside the band.

@@ 48-51
**FairFace's real bands keep most of their weight inside**, between 70 % and 95 %: mostly inside, with soft edges. The first version of this test demanded 90 %, and failed; measuring showed 72–88 %, exactly as designed — wider labels for older ages spill further (§5.2.4).

@@ 54-58
An exact age of 16 peaks at 16; the open band "70 and over" stays mostly within 70–89, with under 2 % beyond 95.

@@ 61-63
**Distance to a band**: 5 below it is 5, inside is 0, 6 above is 6.

@@ 66-72
**The loss prefers the right answer.** A model output equal to the target (as log-probabilities) gives a loss near 0; one that says "60s" for a face labelled "20s" gives a large loss. And the expected age of "20s" is about 24.5, the middle of the band.

@@ 75-80
**Sampling.** Nine faces in their thirties, one in its sixties, one teenager. The weights add up to 1; the rare sixties face is shown more often than each thirties face; and the teenager, equally rare but in the focus years, twice as often as the sixties face.

@@ 83-89
**Random changes**: the result is 224×224 whole-number pixels; the same seed gives exactly the same changes (so a problem can be replayed); a different seed gives different ones.

@@ 92-97
**`faces_zip`** — a helper that writes a zip of "prepared faces", every one the portrait at 256×256.

@@ 100-104
**A sample.** The dataset is given only a name and a split, and reads its rows itself (here, made-up rows supplied in place of the real ones by `monkeypatch`). Of the two rows, one is in `train`, so the training split has one face.

@@ 105-108
Its sample: 3×224×224 whole-number pixels, a target adding up to 1, and the band 10–19.

@@ 109-110
**What a loader process receives.** Copying the dataset the way the loader does (`pickle`) sends neither the rows nor the open file: only the short description (§5.2.4). The `noqa` note tells the security linter that this unpickles our own object, not outside data.

@@ 113-117
**The model takes plain pixels**: two random 64×64 pictures of whole numbers go in, and 101 scores per picture come out.

@@ 120-124
**The learning-rate schedule**, over 100 steps with 10 of warm-up: it starts at a tenth, reaches the full rate, and ends near zero.

@@ 127-129
**The tiny run.** Sixteen training faces spread over seven bands, and four validation faces.

@@ 130-135
Make the zip, a stand-in data table to fingerprint, and point the code at them instead of the real folders.

@@ 136-137
Train `resnet10t` for two epochs, four faces per batch, at 64×64 pixels, with no loader processes.

@@ 138-142
The record lists both epochs and the fingerprint of the data table; a best epoch was chosen; and the model's knobs were saved.

@@ 145-148
**`register_with`** — a helper that writes a small model register with one training entry, for `resnet10t`, pointing at a given file with a given fingerprint.

@@ 151-153
**Only registered, untampered weights are used.** A register whose entry expects a fingerprint of all zeros.

@@ 154-155
A backbone the register doesn't mention is refused, by name.

@@ 156-157
A registered backbone whose file hasn't been downloaded is refused, and the message says to run the fetcher with `--training`.

@@ 158-160
A file whose fingerprint doesn't match is refused.

@@ 163-164
**Weights load from the local file only.** `HF_HUB_OFFLINE=1` forbids the Hugging Face library from using the network at all: if loading tried to download anything, this test would fail.

@@ 165-168
Make a small "pretrained" network with 1,000 outputs, save its weights to a file, and register that file with its real fingerprint.

@@ 169-171
Build an age model from it: the first layer's weights are exactly the file's, and the final layer has been replaced by a fresh one with 101 outputs.

@@ 174-176
**Yes-or-no switches** work: without `--pretrained` the setting is false; with it, true — and `--drop-path 0.1` is read as a number.
