---
fingerprint: 123b174f47050a05
---
**Training**: gradient descent (§2.6), run on the GPU, with a written record of every run. Each run gets its own folder in `.runs/` (which Git ignores) holding two files:

- `model.safetensors` — the knobs of the best version so far;
- `run.json` — everything needed to understand or repeat the run: the settings, the exact code version, fingerprints of the data, the software and hardware, and the scores after every epoch.

```
uv run --package dwarpal-ml python -m dwarpal_ml.train --backbone convnext_atto --epochs 30 --workers 14

epoch   1/30  loss 2.7053  val band-MAE 8.637  in band 26.0%  672 img/s
…
epoch  30/30  loss 0.8867  val band-MAE 2.605  in band 49.3%  1106 img/s
run 20261016-231806-convnext_atto: best val band-MAE 2.605 at epoch 30
```

The design planned to track runs with **MLflow**, a popular tracking server. A plain JSON file per run does the same job at this stage, with nothing extra to install or run; MLflow can be added if runs ever need comparing by the hundred.

@@ 1-4
The docstring, with an example command.

@@ 6
The project-wide type-hint setting.

@@ 8-19
Standard-library tools: `argparse`, `hashlib` (fingerprints), `json`, `math`, `platform` (which Python and computer), `subprocess` (to ask Git which code is running), `sys`, `time`, the dataclass helpers, dates, `Path` and `Any`.

@@ 21-27
**timm**, **PyTorch**, `save_file` from **safetensors**, timm's optimiser builder and weight averager, PyTorch's network building blocks, and its data loader and weighted sampler.

`safetensors` is a file format for model weights, created by Hugging Face. PyTorch's own format (`.pt`) is built on Python's `pickle`, which can run arbitrary code when a file is loaded — a real risk with model files from elsewhere. A `.safetensors` file holds only numbers, so loading one can never run code.

@@ 29-34
From the ML package: the data, the manifests' folder, the model and its approved-weights lookup, the prepared faces, the repository's root, and the loss and measures.

@@ 36
`RUNS` — runs are recorded under `.runs/`.

@@ 37
`MEMORY_WARNING` — warn when training has used more than 92 % of the GPU's memory (`gpu_memory_share`, below).

@@ 40-55
**`Config`** — every setting of a run, with its default. Each one can be changed from the command line (`parse`, below), and all of them are written into the run record.

- `backbone` — which network design (§2.8);
- `pretrained` — start from the approved pretrained weights for that backbone (§2.10), or from random knobs;
- `drop_path` — the strength of stochastic depth (`model.py`); 0 switches it off;
- `epochs` — how many passes through the training faces;
- `batch_size` — 128 faces per step;
- `learning_rate`, `weight_decay`, `warmup_epochs` — the step size, the pull towards zero, and the gentle start (§2.6);
- `ema_decay` — how slowly the averaged copy follows the trained one (§2.15): each step it moves 0.1 % of the way;
- `image_size`, `workers` — the input size and the number of loader processes;
- `seed` — the starting point of the random numbers, so a run can be repeated;
- `limit` — use only this many faces per split (0 means all), for quick trials.

@@ 58
**`learning_rate_factor`** — how much of the full learning rate to use at a given step.

@@ 59-60
During warm-up, rise in a straight line from almost nothing to the full rate.

@@ 61-62
After it, glide down to zero along half a cosine wave: slowly at first, faster in the middle, gently at the end.

@@ 65-66
**`evaluate`** — score a model on the validation faces. `@torch.no_grad()` tells PyTorch not to prepare for a backward pass (§2.6), which saves memory and time.

@@ 67
`eval()` switches the model to evaluation behaviour (some layers, such as normalisation, behave differently while training).

@@ 68
Running totals.

@@ 69-71
For each batch: move the pixels, targets and bands to the GPU. `non_blocking=True` lets the copy overlap with other work.

@@ 72-73
Run the model under **autocast**: on the GPU, most calculations are done in **bfloat16**, a 16-bit number format with the same range as normal 32-bit numbers but less precision. Modern GPUs process it two to four times faster, and for neural networks the lost precision makes no measurable difference. On a computer without a GPU (as in CI), everything stays at full precision.

@@ 74
How far each predicted average age lies outside its band.

@@ 75-78
Add up the loss, the distances, the number of faces whose predicted age lands inside their band, and the number of faces.

@@ 79
Return three scores: the average loss, the **band-MAE** (average years outside the band; 0 is perfect) and the **in-band** share.

@@ 82-85
**`gpu_memory_share`** — the largest share of the GPU's memory PyTorch has held since training began (`max_memory_reserved`), as a fraction of the card's total. Without a GPU, 0.

@@ 88-89
**`sha256_of`** — a file's fingerprint (§X.5), for the run record.

@@ 92-96
**`git_state`** — which version of the code is running (`git rev-parse HEAD`) and whether it had uncommitted changes. A run made from uncommitted code can't be exactly reproduced, and the record says so. The `noqa` note tells the security linter that these are fixed commands, not built from outside input.

@@ 99-101
**`loader`** — PyTorch's **DataLoader**: it asks the dataset for examples in several processes at once and stacks them into batches.

@@ 102-110
The settings: 128 per batch; the sampler that picks faces with the right weights (training only); how many processes; keep the processes running between epochs (`persistent_workers`), since starting them is slow; put batches in memory the GPU can copy from directly (`pin_memory`); and in training, drop the last, incomplete batch, so every step sees a full 128.

@@ 113
**`train`** — one complete run.

@@ 114-116
Fix the random seed; let cuDNN, NVIDIA's library of network calculations, try several methods at the start and keep the fastest (`benchmark`); and use the GPU if there is one.

@@ 117-120
The training faces with random changes, the validation faces without, and their rows.

@@ 121-125
The **weighted sampler**: each epoch draws as many faces as there are, picking each with the probability from `sampling_weights` (§5.2.4). Drawing *with replacement* means some faces appear twice in an epoch and others not at all; over many epochs it evens out. It has its own seeded generator, so the order can be repeated.

@@ 126-128
The two loaders. The comment explains the split of processes: validation, without random changes, needs only a quarter as many.

@@ 130-131
If asked, look up the backbone's approved, fingerprint-checked weights — or stop with an error saying why there are none. Then build the model and move it to the GPU.

@@ 132
The **weight average** (§2.15), from timm. `use_warmup=True` lets it follow quickly at first, while the knobs are still far from good, and slowly later.

@@ 133
The **AdamW** optimiser (§2.6). timm's builder applies weight decay only to the knobs that should have it: the multiplying weights, not the small "add a constant" ones or the normalisation layers.

@@ 134-136
The total number of steps and of warm-up steps, and the **scheduler**, which sets the learning rate before every step using `learning_rate_factor`.

@@ 138-156
**The run record**, started before training: the settings, the start time, the code version, how many faces were used and the fingerprints of every data table they came from, the software and the device, which pretrained weights were used (name, fingerprint and licence, so a model's licence terms can always be traced), and the number of knobs (`numel` counts the numbers in each tensor).

@@ 157-159
Create the run's folder; no best score yet (`math.inf`, infinity, is worse than anything); no steps yet.

@@ 160-162
**The epochs.** Switch the model to training behaviour, and start the clock and the running totals.

@@ 163-165
For each batch: move everything to the GPU.

@@ 166-168
**Forward pass**: the model's answers, under autocast, and the loss.

@@ 169-170
**Backward pass**: clear the previous step's gradients, then compute new ones for every knob (backpropagation, §2.6).

@@ 171
**Gradient clipping**: if the gradients are unusually large all together, scale them down, so that one strange batch can't throw the knobs far off course.

@@ 172-173
Take the step, and move the learning rate on.

@@ 174-175
Count the step, and update the weight average.

@@ 176-177
Add to the running loss. `detach()` takes the plain number, without the record PyTorch keeps for the backward pass.

@@ 178-182
The epoch's duration, and the largest share of the GPU's memory used so far. Above 92 %, print a warning. This guard comes from experience (§5.2.4): when a Windows GPU runs out of memory, the driver doesn't stop with an error but quietly borrows ordinary memory, and training slows to a crawl. Then score the **averaged** model on validation.

@@ 183-192
Record the epoch: training loss, validation scores (rounded to four decimals), seconds, speed, and the memory share.

@@ 193-196
If this is the best validation band-MAE so far, save the averaged model's knobs (`state_dict`, every tensor by name) as `model.safetensors`, and note which epoch it was. Choosing the version by its validation score is what the validation split is for (§2.2); the test split is never used to choose.

@@ 197
Rewrite `run.json` after every epoch, so a run that stops halfway still leaves a full record of what it did.

@@ 198-203
Print one progress line.

@@ 204
Return the record.

@@ 207-215
**`parse`** — read the settings from the command line. Instead of listing each setting by hand, it goes through `Config`'s fields and adds an option for each: `epochs` becomes `--epochs`, `warmup_epochs` becomes `--warmup-epochs`, with the default's type (`type(field.default)`). A new setting needs only a new line in `Config`.

Yes-or-no settings need different handling, because `bool("False")` is `True` in Python — any non-empty text counts as true. So for those, `BooleanOptionalAction` creates a pair of switches instead: `--pretrained` and `--no-pretrained`.

@@ 218-223
**`main`** — name the run after the time (in UTC) and the backbone, train, and report the best epoch.

@@ 226-227
Run `main` when the module is started as a program. On Windows this guard is essential (see `prepare.py`).
