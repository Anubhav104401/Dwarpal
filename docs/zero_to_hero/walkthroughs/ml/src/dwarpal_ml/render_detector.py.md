---
fingerprint: 055b3891af2a2025
---
**The render detector** (liveness level 6, §5.9.4): MiniFASNet V2, retaught to tell a real face from a computer-rendered one on our own clips — preparing the crops, training, choosing a threshold, measuring against release gates, and exporting to ONNX.

@@ 1-10
The module's docstring: what the render detector is — MiniFASNet V2, the anti-spoofing network the service already runs, given a new last layer with two answers (*real*, *rendered*) and trained further on our own clips — and the four commands, in the order they are used.

@@ 12
The project-wide type-hint setting.

@@ 14-23
Command-line options, JSON, maths, the error stream, a stopwatch, the types of functions and lists, data classes, the date (for naming a run), paths, and the types for *any value* and for *anything with these methods*.

@@ 25-32
OpenCV (JPEG compression for augmenting), NumPy, ONNX Runtime (to prove the exported file answers alike), PyTorch with its layers and its data loading, and **safetensors** — a weights format that holds only numbers, so loading one can never run code.

@@ 34-40
Our own pieces: MiniFASNet's rebuild (§5.3) and the folder of third-party models; the release-gate checker and the rate-with-interval of the age model's evaluation (§5.2.5); the ONNX version the age model is exported with; the repository's root; the clips' folder, list, consents and split rule (`renders.py`); and the face finder, the image decoder and the crop MiniFASNet was trained on.

@@ 42-48
**Where things are**: MiniFASNet V2's weights (the 2.7-face-size network); the file of its tensors' shapes; its crop size; the position of the *rendered* answer; the prepared crops, the training runs and the release gates.

@@ 49-50
**`BPCER_TARGET`**: the threshold is set so that at most 5 % of real people's faces are called rendered. Refusing real people is the cost the detector must keep low.

@@ 51
How far the ONNX file's answers may differ from PyTorch's: one in ten thousand.

@@ 55
A picture: an array of bytes, height × width × 3 colours.

@@ 58-59
**`Detector`**: anything with a `detect` method that finds faces. The real face finder fits, and so does the tests' stand-in — a `Protocol` describes a shape, not a family.

@@ 62
The first part: the network.

@@ 65-67
**`base_state`**: the starting tensors. With `pretrained`, MiniFASNet V2's own weights…

@@ 68-71
…read as plain tensors only (`weights_only=True`, as everywhere in the project), with the `module.` prefix a multi-GPU wrapper added to every name removed.

@@ 72-73
Without them: an empty tensor of each recorded shape. MiniFASNet's rebuild reads only the shapes, so this builds the same network, which PyTorch fills with its usual random starting values — for training from scratch, and for tests on machines that never fetched the weights.

@@ 76-77
**`RenderNet`**: the network, with what it takes and gives.

@@ 79-83
MiniFASNet rebuilt, and given its trained weights if it starts from them (`strict`: every weight must fit).

@@ 84-85
Its last layer replaced: from the same 128 numbers it now gives two answers, not three. Everything before it keeps what MiniFASNet learnt about screens and prints, which is where training starts.

@@ 87-89
Pixels through the network: MiniFASNet's own `forward` ends with *softmax*, so the two answers are chances that add up to 1.

@@ 92
The second part: the data.

@@ 95-97
**`face_crops`**: every `every`-th frame of a clip (neighbouring frames are nearly the same picture)…

@@ 98-104
…decoded (with room for our own large PNG renders: `FRAME_BYTES`), searched for faces, and — when there is exactly one — cropped as MiniFASNet sees it. A frame with no face or two is skipped.

@@ 107-109
**`prepare`**: all clips' crops, gathered into one file per split.

@@ 110-112
First the clips are checked as `renders check` does; if any may not be kept — above all a real person's whose consent was withdrawn — nothing is prepared.

@@ 113
Per split, four lists: the crops, their labels, their kinds and their people.

@@ 114-116
For each clip, its frames in order, and their crops.

@@ 117-121
The clip's split comes from its person (`split_of`), so a person's crops all land together; each crop is labelled 1 if rendered and 0 if real, with its kind and person.

@@ 122-123
The folder for the crops, inside the data folder (so never in the repository).

@@ 124-131
Each split saved as one compressed NumPy file holding four arrays. `reshape` keeps an empty split's shape right.

@@ 132
How many crops each split received.

@@ 135-140
**`Split`**: one split's four arrays, as read back.

@@ 143-145
**`load_split`**: read one split's file.

@@ 148-150
**`augment`**: random changes a camera or a video call could make to a face, so the network learns what stays the same under them.

@@ 151-152
Half the time, the mirror image.

@@ 153-154
Brightness and contrast changed: every pixel multiplied by 0.7–1.3 and shifted by up to 25, kept within 0–255.

@@ 155-158
Half the time, JPEG compression at a random quality from 40 to 95, as a video call compresses its pictures.

@@ 159
A copy laid out plainly in memory, as PyTorch wants it.

@@ 162-166
**`Crops`**: a split as PyTorch's data loading wants it, changed at random only for training.

@@ 168-169
How many crops there are.

@@ 171-176
One crop: changed (for training), turned into numbers with the colours first (3 × 80 × 80), with its label.

@@ 179-182
**`balanced_weights`**: each crop's chance of being picked, 1 ÷ the number of crops with its label — so real and rendered crops are seen equally often, however many of each there are.

@@ 185
The third part: training.

@@ 188-195
**`Config`**: the training's settings — passes over the data, crops per step, how big a step, how much to pull weights towards zero, whether to start from MiniFASNet's weights, and the random seed.

@@ 198-204
**`scores_of`**: the network's *rendered* chance for every crop of a split, in batches of 256, without recording anything for learning (`no_grad`).

@@ 207-209
**`settle_batch_norm`**: batch normalisation keeps running averages of what each layer sees, used when the network answers outside training. After a short training they still lag far behind, and the network then answers almost the same for every face (found 3 Nov, in this module's own test). So they are measured again:

@@ 210-213
every batch-normalisation layer forgets its averages and switches to a plain average over all it sees…

@@ 214-220
…20 batches of training crops go through in training mode, learning nothing (`no_grad`)…

@@ 221-223
…and the layers go back to their usual running averages, with the network ready to answer.

@@ 226-231
**`balanced_error`**: at one threshold, the share of renders taken for real and the share of real faces taken for renders, averaged — so neither can hide behind the other's numbers.

@@ 234-235
**`train`**: train, keep the best epoch, record the run. `report` is where progress lines go (`print`, or a list in the tests).

@@ 236-238
A fixed random seed, the two splits it needs, and the network.

@@ 239-240
Crops drawn with the balanced weights, as many draws as there are crops per epoch, in batches.

@@ 241
**AdamW**, the usual optimiser, with weight decay.

@@ 242-243
The step size falls from the full rate to zero along half a cosine wave over the whole training.

@@ 244-246
A folder for this run, named by its start time; its history; the best error so far.

@@ 247-249
Each epoch: training mode, a stopwatch, the losses.

@@ 250-252
Each batch: the chances, and the **loss** — how surprised the network was by the right answers (the logarithm of the chance it gave them; `clamp_min` avoids the logarithm of 0).

@@ 253-257
Learn from it: clear the old gradients, compute new ones, take a step, move the step size on, note the loss.

@@ 258-260
After the epoch: settle the averages, measure the balanced error on the validation split, record both.

@@ 261-262
One line of progress.

@@ 263-265
The best epoch so far is saved (as safetensors); a later, worse one doesn't replace it.

@@ 266-268
The settings, the history and the best error into `run.json`, and the run's folder returned.

@@ 271-274
**`load_run`**: a run's best network, ready to answer. It is built from the shapes and then given every saved weight, so MiniFASNet's own file isn't needed.

@@ 277
The fourth part: evaluation.

@@ 280-281
**`threshold_for`**: the lowest threshold that calls at most `target` of the real crops rendered.

@@ 282-284
The real crops' scores, in order (none: a neutral 0.5).

@@ 285-286
How many may be called rendered, and the threshold just above the highest score that must stay real — so exactly those few top scores reach it (`nextafter`: the next number up).

@@ 289-291
**`measure`**: the two standard error rates of presentation-attack detection (ISO/IEC 30107-3).

@@ 292-293
Which crops are called rendered, and which really are.

@@ 294-298
The threshold; **APCER**, the share of renders taken for real; **BPCER**, the share of real faces taken for renders; APCER separately for each kind of render (on a screen, or injected). Each comes with its 95 % interval, from `rate`.

@@ 299-304
And how many different people, real and made-up, the numbers rest on.

@@ 307-308
**`evaluate`**: the threshold is chosen on the validation split, and the rates measured on the test split — people the threshold never saw either.

@@ 309-312
The run's network, both splits, the threshold, the measurement.

@@ 313-315
The release gates checked against it (`render_gates.toml`); everything written to `evaluation.json`.

@@ 318
The fifth part: export.

@@ 321-322
**`export`**: the network as an ONNX file the inference service can run.

@@ 323-326
Only after its evaluation passed every gate.

@@ 327-330
The network, and a folder for this version in the model registry.

@@ 331-341
The export: an example batch of 4 faces, named input and output, any number of faces from 1 to 64 at once, and the same ONNX version as the age model.

@@ 342-344
The file saved whole (no separate weights file).

@@ 345-347
Its answers compared with PyTorch's; a difference above the tolerance stops everything.

@@ 348-356
The **manifest**: the file, what goes in and comes out, and the threshold chosen on validation…

@@ 357-361
…where it came from: the run, the starting network and its licence, and the data's rules…

@@ 362-364
…its test results, and its use: **recorded only** — it decides nothing until it is measured on real attempts.

@@ 365-366
The manifest written beside the file, and the folder returned.

@@ 369-374
**`parity`**: eight batches of random pixels through PyTorch and through ONNX Runtime, and the largest difference between their answers.

@@ 377-378
**`main`**: the command line. Not run by the tests (`pragma: no cover`): it works on the owner's data.

@@ 379-389
The four commands and their options: how often to take a frame; how many epochs, and whether to start without MiniFASNet's weights; which run to evaluate or export, and under which version.

@@ 390-394
**prepare** with the real face finder.

@@ 395-396
**train**, printing the run's folder.

@@ 397-400
**evaluate**, printing the results; the exit code says whether every gate passed.

@@ 401-402
**export**.

@@ 403-406
A refusal (a clip that may not be kept, a gate that failed, a missing file) as one line, and failure.

@@ 407
Success.

@@ 409-410
Run as a program, `main`'s answer becomes the exit code.

@@ 52-53
**`FRAME_BYTES`**: how large a frame of our own may be — 16 MB. The service refuses uploads over 512 KB, which protects it from strangers; a rendered 1280 × 720 PNG is often larger, and found so when the first renders were cropped (4 Nov).
