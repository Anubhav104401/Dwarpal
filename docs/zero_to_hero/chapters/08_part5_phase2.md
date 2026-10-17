## 5.2 Phase 2 — the ML core

Phase 1 left a stand-in where the age model belongs. Phase 2 builds the real one, and everything a trustworthy model needs around it: data that may lawfully be used, a fixed and fair division of that data, safety lines with a provable guarantee, and measurements of how the model treats different groups of people.

It is built in this order, and this chapter grows in the same order:

| Step | What | Section |
| :-: | :-- | :-- |
| 1 | Data: the licence register, the fetch command, the unified manifest | §5.2.1 ✅ |
| 2 | Risk control: choosing the safety lines | §5.2.2 ✅ |
| 3 | Face preparation: detecting and aligning every face, finding duplicates | §5.2.3 ✅ |
| 4 | Training the age model | §5.2.4 ✅ |
| 5 | Evaluation and fairness | §5.2.5 ✅ |
| 6 | Exact ages and the safety lines: UTKFace, calibration | §5.2.6 ✅ |
| 7 | Export to ONNX, and the model's manifest | §5.2.7 ✅ |

The ML code lives in the `ml/` package, created empty in Phase 0 (§5.0.2). It now uses **httpx** for downloads, **SciPy** for statistics, the project's own vision library, so that training prepares faces exactly as serving does, and **PyTorch** with **timm** for training (its `pyproject.toml` walkthrough, in §5.0.2, describes them all). Data never enters the repository: downloads and manifests live in `.datasets/`, which Git ignores.

### 5.2.1 Data — the register, the fetch and the manifest

The background is in §2.2: what labels and splits are, and why datasets have licences. Three pieces of code put it into practice:

```
ml/datasets.toml        the licence register: which datasets, which licences, approved by whom, pinned files
        │
        ▼
dwarpal_ml.fetch        downloads an approved dataset's files; keeps a file only if its fingerprint matches
        │                 → .datasets/raw/fairface/  (578 MB of face images + 2 label files)
        ▼
dwarpal_ml.manifest     one row per image, the same columns for every dataset, with a fixed split
                          → .datasets/manifest/fairface.csv  (97,698 rows)
```

The project's owner approved one dataset for now: **FairFace**, under the CC BY 4.0 licence (use for any purpose, with credit). Three exact-age datasets are listed in the register but not approved, because their licences allow research use only (ADR-0018).

#### The licence register

!walk ml/datasets.toml

!walk ml/src/dwarpal_ml/register.py

#### The fetch command

!walk ml/src/dwarpal_ml/fetch.py

#### The unified manifest

!walk ml/src/dwarpal_ml/manifest.py

#### Tests for the data side

!walk ml/tests/test_data.py

!!! real "Real world — what the data showed"
    - **The documentation was wrong.** FairFace's documentation says its oldest age band is written `70+`; its label file actually says `more than 70`. The manifest refused the unknown spelling instead of guessing, which is how it was found. Refusing what you don't understand turns a silent mistake into a visible one.
    - **The numbers.** 97,698 faces: 69,469 for training, 8,654 for validation, 8,621 for calibration and 10,954 for the final test. They are spread fairly evenly across the seven groups (from 10,425 to 18,612 faces each), which is what FairFace was built for.
    - **What it can't do.** Only 10,284 faces fall in the band "10-19", and that band holds children *and* adults together. FairFace can teach a model to see age; it can't prove where the line between 17 and 18 falls. That needs exact ages, from a dataset the owner hasn't approved yet (§2.14).

### 5.2.2 Risk control — choosing the safety lines

The background is in §2.14: the Clopper–Pearson bound, cells, and how a bound becomes a line. This code is the calculation itself. It works on any list of `(age, group, score)` triples, so it was written and tested *before* any model exists, on made-up populations. When the trained model scores the calibration split, the same code chooses its lines.

!walk ml/src/dwarpal_ml/risk.py

!walk ml/tests/test_risk.py

!!! real "Real world — a mistake the book caught"
    The first version of `calibrate` refused to answer when the highest safe fail line came out above the pass line, reporting that the model "can't separate" the ages. Its test used children who all scored 0.9 and adults who all scored 0.95, and the test passed.

    Explaining that test for this book showed that the expected result was wrong. Those scores describe a model that separates the ages *perfectly*, and the right answer was two lines in the gap, not a refusal. Each line had been chosen without looking at the other, but a fail line can always be lowered safely, so it is now capped just below the pass line. This is exactly why the book explains every line: putting code into plain words is a review.

!!! try "Try it yourself"
    Run the ML tests (no download needed):

    `uv run pytest ml/tests`

    Then, in Python (`uv run --package dwarpal-ml python`), ask the bound some questions:

    ```python
    from dwarpal_ml.risk import clopper_pearson_upper, minimum_cell_size
    clopper_pearson_upper(6, 600)   # 0.0196… — the jar from §3.3
    clopper_pearson_upper(7, 600)   # 0.0218… — one more child, and the line must move
    minimum_cell_size(0.02)         # 149
    ```

### 5.2.3 Face preparation — the same faces the service sees

The background is in §2.17: finding a face, finding its landmarks, and straightening it. This step runs every FairFace image through the vision library built in Phase 1 — the very code that handles webcam frames — and then removes repeated photos.

```
manifest ──► dwarpal_ml.prepare   97,698 images → 97,645 aligned faces (53 without a face)      45 s on 24 cores
         ──► dwarpal_ml.dedup     123,774 candidate pairs → 502 confirmed → 467 copies removed    about 1 min
         ──► usable faces:        train 69,012 · val 8,625 · calib 8,600 · test 10,941
```

#### Preparing the faces

!walk ml/src/dwarpal_ml/prepare.py

#### Removing duplicates

!walk ml/src/dwarpal_ml/dedup.py

#### The tests

!walk ml/tests/test_prepare.py

!!! real "Real world — the smeared foreheads"
    The first run used FairFace's tightly cropped images, and the numbers looked fine: a face in 99.8 % of them. Only *looking* at the aligned faces showed the problem. Our alignment frames a face with room for hair and forehead, but the tight crops had cut those off, so the missing parts were filled by stretching the edge pixels: a third of each face was smeared streaks. A model trained on those would have learned from pictures unlike any webcam frame.

    FairFace also publishes a version with a much wider margin. The owner approved its download (2.1 GB, the same 97,698 photos, the same licence), it replaced the tight crops in the register, and the faces came out clean. Faces not found fell from 151 to 53.

    The smears had a second effect: they made strangers' fingerprints look alike, which is how they were noticed in the first place. Measure, then **look**: a number can say "99.8 % fine" about pictures that are a third garbage.

!!! real "Real world — choosing the duplicate limits by eye"
    There is no textbook value for "how similar is the same photo", so the limits were chosen from FairFace itself, by looking at pairs of faces.

    - **The first check failed.** Comparing small, whole grey versions of two faces gave a smooth range of scores, with no gap between copies and strangers. Faces of different people scored 0.95 out of 1, because after alignment every face has its features in the same places.
    - **Fine detail separated them.** Comparing only fine detail (each face minus a blurred copy of itself) split the pairs cleanly: most scored between 0 and 0.35, very few between 0.5 and 0.6, and a separate cluster sat near 1. Every pair looked at from 0.6 upwards was the same photo — including colour and grey copies. Below 0.5 they were almost all strangers.
    - **The sieve was widened.** Allowing 10 differing bits instead of 8 found 31 more confirmed copies (502 instead of 471) for six times as many pairs to check: still about a minute's work. The extra pairs scoring 0.5–0.6 included strangers, which is why the confirmation limit is 0.6, not 0.5.

!!! real "Real world — what the duplicates revealed"
    467 copies were removed. 233 of them would have **leaked into evaluation**: 75 training copies of test photos, 65 of calibration photos, 60 of validation photos, and 33 more between the evaluation splits themselves.

    The copies also measured something unexpected: **how consistent FairFace's age labels are.** In 189 of the 467 pairs (40 %), the two copies of the *same photo* carry different age bands: 175 one band apart, 14 two or more. FairFace's ages are people's estimates from looking at photos, and this shows how often such estimates disagree. It is one more reason why the safety lines must be set on data with exact, documented ages (§2.14).

!!! try "Try it yourself"
    With FairFace fetched and its manifest built (§5.2.1), and the face-detector model downloaded:

    `uv run --package dwarpal-ml python -m dwarpal_ml.prepare fairface`

    `uv run --package dwarpal-ml python -m dwarpal_ml.dedup fairface`

    Then open `.datasets/processed/fairface.zip` and look at some of the faces — every one with its eyes in the same place.

### 5.2.4 Training the age model

The background is in Part 2: what learning is (§2.1), models and their knobs (§2.4), the loss (§2.5), gradient descent (§2.6), neural and convolutional networks (§2.7–2.8), predicting a distribution (§2.11), and over-fitting (§2.15). This step puts them together:

```
usable faces ─► data.py     weighted sampling, random changes, webcam damage    ┐  14 loader processes,
                                                                                ┘  ~1,500 faces a second
             ─► model.py    pixels → timm backbone → 101 scores                 ┐  GPU, bfloat16,
             ─► targets.py  label → target distribution; KL + band distance     │  AdamW, warm-up + cosine,
             ─► train.py    30 epochs; averaged weights scored on validation    ┘  weight averaging
             ─► .runs/<time>-<backbone>/   run.json + model.safetensors
```

#### Choices made before writing any code

- **Which backbone weights may be used.** The design named ConvNeXt V2 as a candidate, but its published weights are licensed for non-commercial use only (CC BY-NC 4.0), while FairFace itself allows commercial use. Apache-2.0 alternatives were found (timm's own ConvNeXt, DINOv2) and offered to the owner, who approved PyTorch but no pretrained weights for now. So these first models learn **from scratch** (§2.10): a harder start, and an honest baseline for pretrained models later.
- **A cooldown for Python packages.** Adding PyTorch brought in new libraries, three of them only days old. uv can now refuse any release younger than a week, as pnpm already does for JavaScript, and that rule is now on (root `pyproject.toml`). It also caught six earlier pins, which were stepped back by a release each.
- **The right PyTorch for each computer**: the CUDA build on the Windows development laptop, the small CPU build on Linux, where CI runs (`ml/pyproject.toml`).

#### The targets and the loss

!walk ml/src/dwarpal_ml/targets.py

#### The data

!walk ml/src/dwarpal_ml/data.py

#### The model

!walk ml/src/dwarpal_ml/model.py

#### The training loop

!walk ml/src/dwarpal_ml/train.py

#### The tests

!walk ml/tests/test_train.py

!!! real "Real world — making the GPU wait less"
    The first trial runs managed 261 faces a second, with the GPU mostly idle. Two fixes, each found by measuring rather than guessing:

    - **Slow random changes.** Timing every step of preparing one face showed torchvision's colour change taking 17 milliseconds — mostly its hue adjustment — and its rotation another 4. All the changes were rewritten with OpenCV: zoom, turn and shift as one warp, and colour as simple arithmetic, dropping hue shifts, which don't occur in real faces anyway. From 27 to 7.5 milliseconds a face.
    - **Slow start-up.** The first epoch of every run took minutes. The loader's 14 processes were starting one at a time, 17 seconds apart: on Windows each had to receive the full list of 69,000 faces before the next could start, and couldn't receive it until it had finished loading PyTorch. Sending each only "FairFace, training split" let all 14 start at once: from 78 seconds to 11.

    Now the loader prepares about 1,500 faces a second, more than the GPU can use, which is how it should be.

!!! real "Real world — the first model"
    **ConvNeXt-Atto**, 3.4 million knobs, trained from scratch for 30 epochs (32 minutes):

    | Measure (validation, 8,625 faces) | Guessing "29" for everyone | ConvNeXt-Atto |
    | :-- | --: | --: |
    | Band-MAE (years outside the band) | 8.55 | **2.61** |
    | Predicted age inside the band | 29 % | **49 %** |

    It is best for faces in their twenties (1.5 years outside the band, on average) and worst for older faces (4–5 years), which are rare in the training data. Between groups, band-MAE ranges from 2.35 to 3.05; the largest gap, for faces labelled Black, is a fairness finding for step 5 to measure properly.

    The number that matters most for Dwarpal: children under 10 were given at least a 50 % chance of being 18 or over in 4.5 % of cases. That is why nothing in the system ever passes someone at 50 %: the safety lines are set by risk control (§2.14), on calibration data with exact ages.

!!! real "Real world — the second model, and the baseline"
    **ResNet-26d**, 14.2 million knobs, trained the same way (63 minutes, at half the speed):

    | Measure (validation) | Constant guess | ConvNeXt-Atto | **ResNet-26d** |
    | :-- | --: | --: | --: |
    | Band-MAE | 8.55 | 2.61 | **2.28** |
    | Predicted age inside the band | 29 % | 49 % | **52 %** |
    | Ages 3–9 given P(18+) ≥ 50 % | — | 4.5 % | **3.5 %** |
    | Band-MAE, best to worst group | — | 2.35–3.05 | **2.05–2.63** |

    ResNet-26d is better on every measure, and becomes the baseline that pretrained models will have to beat. Both models were still improving slowly at their last epoch, and their training loss sat only a little below their validation loss: neither had begun to over-fit (§2.15), so longer training might squeeze out a little more. A pretrained backbone (§2.10) is the likelier big step.

    Each run's `run.json` records that it was made from uncommitted code — true, since this step was still being written. Runs for a release will be made from a commit.

!!! real "Real world — starting from pretrained weights"
    The owner then approved one set of pretrained weights: timm's **ConvNeXt-Tiny**, trained on ImageNet-12k and ImageNet-1k (Apache-2.0, 114 MB, 28 million knobs). They were pinned in the model register with their fingerprint and licence, and fetched by the project's own downloader (`fetch_models.py --training`). Fine-tuning used the gentler recipe for pretrained models: a learning rate eight times lower, a one-epoch warm-up, stochastic depth, and 15 epochs.

    The first attempt crawled. ConvNeXt-Tiny at 128 faces a batch needed more than the laptop GPU's 8 GB, and on Windows the driver doesn't fail with "out of memory": it quietly borrows ordinary memory, which is many times slower. The GPU showed 100 % busy but drew a third of its usual power, waiting on memory. At 64 faces a batch (with the learning rate halved to match), it used 59 % of the memory and ran at full speed. Training now records each epoch's memory use, and warns above 92 % (`train.py`).

    | Measure (validation) | ResNet-26d, from scratch | **ConvNeXt-Tiny, pretrained** |
    | :-- | --: | --: |
    | Band-MAE | 2.28 | **1.84** |
    | Predicted age inside the band | 52 % | **55 %** |
    | Ages 3–9 given P(18+) ≥ 50 % | 3.5 % | **1.7 %** |
    | Ages 0–2 given P(18+) ≥ 50 % | 1.1 % | **0.6 %** |
    | Band-MAE, best to worst group | 2.05–2.63 | **1.72–2.02** |
    | Best epoch, training time | 30 of 30, 63 min | **6 of 15**, 54 min |

    After **one** epoch it was already better than the from-scratch model after thirty — the value of starting from a backbone that already knows how to see (§2.10). It is now the best model, and the one the next steps evaluate.

!!! real "Real world — over-fitting, caught in the act"
    The pretrained model shows what §2.15 describes, epoch by epoch:

    | Epoch | 1 | 3 | 5 | 6 | 8 | 10 | 12 | 15 |
    | :-- | --: | --: | --: | --: | --: | --: | --: | --: |
    | Training loss | 1.41 | 0.93 | 0.78 | 0.72 | 0.58 | 0.45 | 0.35 | 0.29 |
    | Validation loss | 0.95 | 0.88 | **0.86** | 0.86 | 0.89 | 0.94 | 1.02 | 1.08 |
    | Validation band-MAE | 2.15 | 1.91 | 1.86 | **1.84** | 1.87 | 1.92 | 2.00 | 2.04 |

    Up to epoch 5 or 6, both losses fall together: the model is learning about ageing. After that, the training loss keeps falling while the validation loss *rises*: the model is memorising its 69,000 training faces, and getting worse at new ones. Because training keeps the version with the best validation score, the saved model is the one from epoch 6, before the memorising set in. The next run of this recipe can stop at about 8 epochs — half the time, and half the heat.

### 5.2.5 Evaluation and fairness

The background is in Part 2: measuring mistakes (§2.12), calibration (§2.13) and fairness (§2.16). This step builds one evaluation protocol for every model, writes the release gates down *before* the test results are seen, and opens the test split for the first time — once.

```
model + validation faces ─► logits ─► temperature fitted (validation only)
model + test faces       ─► logits ─► accuracy · clear minors/adults at 13, 16, 18, 21 · calibration · fairness
                                    ─► evaluation-test.json  ─► every gate in ml/gates.toml: PASS / FAIL
```

#### The release gates

!walk ml/gates.toml

#### The protocol

!walk ml/src/dwarpal_ml/evaluate.py

#### The tests

!walk ml/tests/test_evaluate.py

!!! real "Real world — the first exam"
    **ConvNeXt-Tiny**, pretrained and fine-tuned (§5.2.4), evaluated on the locked test split: 10,941 faces it had never seen, and nobody had looked at.

    | Measure | Validation | **Test** |
    | :-- | --: | --: |
    | Band-MAE | 1.86 | **1.83** |
    | Inside the band | 55.6 % | **55.7 %** |
    | Children under 10 rated 18+ (more likely than not) | 1.49 % (18 of 1,208) | **1.74 %** (27 of 1,553), up to 2.52 % |
    | Adults 30+ rated under 18 | 0.66 % | **0.65 %** |
    | Calibration error (after temperature 0.88) | 0.017 | **0.018** |
    | Worst-to-best group band-MAE | 1.17 | **1.21** |

    Validation and test agree closely: choosing the best epoch and the temperature on validation did not flatter the model.

    **Four of the five gates pass. One fails.** Of 126 Middle Eastern children under 10 in the test split, 6 (4.8 %) were rated more likely than not to be 18 or over. With so few children, the true rate could plausibly be as high as 10.1 %, just over the provisional 10 % gate. On validation, the same group had 1 of 81. Two other patterns stand out: girls were misjudged more often than boys (2.5 % against 1.2 %), and the age limit 13 is the model's weak point — 10.6 % of children under 10 were rated 13 or over, because FairFace's single 10–19 band can't teach the difference between 10 and 13.

    This result stays exactly as measured. The test split has now been used for this model, and the code refuses to evaluate it again: changing something and re-taking the exam until it passes would make the exam meaningless. The next model must do better on its own first attempt — through more and better data (exact ages, more children of every group), and through the risk-controlled thresholds of §2.14, which are stricter than the plain 50 % line used here.

!!! try "Try it yourself"
    Evaluate any trained run on validation as often as you like:

    `uv run --package dwarpal-ml python -m dwarpal_ml.evaluate .runs/<run>`

    The results are in `evaluation-val.json` in the run's folder. Then, once you are sure, the exam: add `--split test`. Try it a second time to see the lock.

### 5.2.6 Exact ages and the safety lines

Everything so far was measured with FairFace's age bands, which can't tell a 15-year-old from a 19-year-old. Setting the safety lines (§2.14) needs **exact ages**. The owner approved **UTKFace** for this, under the project's research-only first version: over 24,000 photos, each labelled with an exact age. It is used only to *measure*, never to train: half of it for setting the lines, half for checking them.

```
UTKFace ─► fetch (3 files, 1.39 GB) ─► manifest (repack to one zip; labels from file names; calib/test halves)
        ─► prepare (clearest face; photos with a second clear face set aside)
        ─► dedup --against fairface (copies within UTKFace, and of photos the model learned from)
        ─► calibrate: lines certified on the calib half ─► decisions checked on the test half, once
```

Three things about UTKFace shaped the code:

- **The labels are estimated.** UTKFace's ages were proposed by an age-estimation algorithm (DEX) and checked by a person. They are not ages from documents. The register records this (`age_source`), and every calibration result carries the note.
- **The labelled person isn't always alone, or in the middle.** FairFace centred each photo on its subject; UTKFace's in-the-wild photos don't. So the register gained a `subject` rule: for UTKFace, take the clearest face, and set the photo aside if a second clear face appears (519 photos).
- **Some photos are bigger than any webcam frame.** The vision library refuses uploads over 512 KB or 1,920 pixels, rightly for a service. Dataset preparation now decodes with roomier limits, then shrinks each photo to the service's largest size.

Changes to files walked through earlier are explained in their walkthroughs (`ml/datasets.toml`, `register.py`, `manifest.py`, `prepare.py`, `dedup.py`, `risk.py`, `evaluate.py`, the vision library's `decode.py`, and their tests).

#### Calibration

!walk ml/src/dwarpal_ml/calibrate.py

!walk ml/tests/test_calibrate.py

!!! real "Real world — what UTKFace showed before any model looked at it"
    - **Teenagers are scarce.** UTKFace has 82 faces aged 13, 164 aged 14, 180 aged 15, 253 aged 16 and 159 aged 17 — and only 4 Asian 13-year-olds. Risk control needs 149 people per age-and-group cell to certify 2 % (§2.14). Only one cell in the whole dataset reaches that. So the promise can be certified **per age, but not per group**, and only at a looser budget than 2 %.
    - **Repeated photos disagree about age.** Duplicate removal found 533 extra copies of photos *within* UTKFace, and 324 of them (61 %) carry a different age from the copy that was kept — the same photo, labelled with two ages. Estimated labels are noisy, even when checked.
    - **Age heaping.** 2,206 faces are labelled exactly 26, but only 616 are labelled 27: a sign of estimated, rounded labels.
    - Only 6 UTKFace photos were copies of FairFace photos — removed, so the model is never tested on a face it learned from.

!!! real "Real world — the safety lines, on exact ages"
    ConvNeXt-Tiny (§5.2.4), trained on FairFace only, calibrated on UTKFace's calibration half (11,301 faces) and checked on its test half (11,637 faces, opened once). Exact-age error on these new faces: **4.96 years** on average (1.6 for children under 13, 3.3 for teenagers, 9.6 over 60).

    | Limit | Strictest budget the data certifies | Pass line τ | Teenagers passed on the test half (ages N−5 to N−1) |
    | :-- | :-- | --: | :-- |
    | **18** | **7.5 %, per age** | 0.964 | 2.9 % (12 of 416; up to 5.0 %) — by age: 13: 0 %, 14: 0 %, 15: 3.7 %, 16: 2.7 %, 17: 6.4 % |
    | 21 | 7.5 %, per age | 0.927 | 1.3 % (7 of 520) |
    | 16 | 15 %, per age | 0.761 | 7.6 % (25 of 327) |
    | 13 | 15 %, per age | 0.809 | 4.1 % (16 of 392) |

    On faces that played no part in choosing the lines, every age's pass rate stayed inside its certified budget: the guarantee held. At 18, children under 13 passed 0.4 % of the time (7 of 1,741).

    **The price is paid by adults.** At the 18 line, only 13 % of 18–20-year-olds and 30 % of 21–24-year-olds pass straight away; most are sent to step-up. From 30 upwards, 94 % pass. That is exactly the trade risk control is built to make: with a model this uncertain about teenagers, it keeps children out by sending more adults to a document check — never by letting more children through.

    **What these lines are not.** They are not yet good enough to serve: the design's target is 2 % per age *and* group (NFR-01), and the data supports only 7.5 % per age; the ages are estimates; and the per-group pass rates are measurements on a few dozen teenagers each (3 of 50 Black teenagers passed at 18, for example), not guarantees. More exact-age data of every group — and a better model — are what will move all three.

!!! try "Try it yourself"
    With UTKFace fetched, its manifest built and its faces prepared and deduplicated, calibrate any trained run:

    `uv run --package dwarpal-ml python -m dwarpal_ml.calibrate .runs/<run> utkface`

    Read `calibration-utkface.json` in the run's folder to see every budget that was refused, and why.

### 5.2.7 From trained model to served model

The last step turns the trained, calibrated model into what the inference service runs (§2.19), proves that nothing changed on the way, and gives the model a manifest in the registry.

```
.runs/<run>/ ─► export.py ─► models/registry/age/age-convnext-tiny-2026.10.17/model.onnx      (110 MB, not in Git)
                         ─►                                           …/manifest.json   (thresholds, provenance, checks)
inference service ─► DWARPAL_INFERENCE_AGE_BACKEND=onnx ─► OnnxAgeBackend: fingerprint check ─► ONNX Runtime
API               ─► DWARPAL_AGE_MANIFEST=registry/age/age-convnext-tiny-2026.10.17/manifest.json
```

Both services still default to the stand-in model. Switching to the trained one is two settings, and only for test mode: the manifest says `calibrated: false`, because the thresholds don't yet meet the release standard (§5.2.6), and the API refuses live sessions with such a model.

#### One conversion for training's checks and for serving

!walk libs/vision/src/dwarpal_vision/batch.py

#### The export

!walk ml/src/dwarpal_ml/export.py

#### The manifest

!walk models/registry/age/age-convnext-tiny-2026.10.17/manifest.json

The inference service's changes — the ONNX backend, its settings, and its tests — are explained in their walkthroughs (`services/inference/src/dwarpal_inference/backends.py`, `settings.py`, `main.py`, `tests/test_inference.py`), alongside the vision library's new export and test.

!!! real "Real world — the served model"
    - **Parity**: the ONNX file and PyTorch agree to within 0.0000008 on every probability of 512 validation faces.
    - **The service's way of aligning** (straight from the photo, at 224 pixels) against training's (at 256, then shrunk): 0.16 years apart on average, and 0.003 in the probability of being 18 or over.
    - **Speed on the processor**: a burst of 5 faces in 0.67 s typical, 0.70 s slow case, on a single thread. Through the whole service pipeline — decode, detect, check quality, align, estimate — a 5-frame burst took 239 ms with 4 threads.
    - **The export crashed once, on an emoji.** PyTorch's exporter prints progress messages containing ✅, which the Windows console's old character set can't display. Turned off; the lesson is that tools are tested on someone else's computer.
    - **A real verdict.** Through the service, the test portrait — an astronaut photographed in her forties — was estimated at 25.4 years, with P(18 or over) = 0.937. At the 18 line of 0.964, the system would send her to step-up: not a pass, not a refusal. That is the strict line doing its job while the model is uncertain.

!!! try "Try it yourself"
    With the model exported, start the inference service with it:

    `DWARPAL_INFERENCE_AGE_BACKEND=onnx uv run --package dwarpal-inference uvicorn dwarpal_inference.main:create_app --factory --port 8001`

    and the API with its manifest (`DWARPAL_AGE_MANIFEST=registry/age/age-convnext-tiny-2026.10.17/manifest.json`), then use a **test** key in the demo shop (§5.1.5). A live key is refused: the model isn't calibrated to the release standard yet.
