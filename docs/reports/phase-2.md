# Phase 2 report — ML core

**Dates:** from 16 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** ✅ steps 1–7 done; open questions below; CI green on GitHub since 2 Nov (`03f3f5b`)

**Goal (from the roadmap):** replace the stub age model with a trained, calibrated one whose thresholds carry a statistical guarantee per age and group.

## What is built so far

| Area | Delivered |
| :-- | :-- |
| Licence register | `ml/datasets.toml`: four datasets with licence, permitted use, citation and label kind; owner approval with a date; SHA-256-pinned files. Approved: **FairFace** (CC BY 4.0), wide-margin (padding 1.25) images. **UTKFace** (non-commercial research, in-the-wild images, 1.39 GB pinned) approved 2026-10-17 for exact-age evaluation and calibration only. Not approved: APPA-REAL, IMDB-Clean. New register fields: `age_source`, `subject` |
| Fetch | `dwarpal_ml.fetch`: refuses unapproved or unpinned datasets; https only; downloads to `.part`, keeps a file only if its fingerprint matches |
| Manifest | `dwarpal_ml.manifest`: one row shape for every dataset; fixed hash-based splits (train/val/calib 80/10/10 of FairFace's train; its official val is the test set); summary printout |
| Risk control | `dwarpal_ml.risk`: one-sided Clopper–Pearson bound (SciPy); τ_pass = lowest line keeping every (exact age N−5…N−1 × group) cell within ε; τ_fail = highest line keeping adults N+3+ failed ≤ 1 % per group, capped below τ_pass; refusals for missing ages, small cells (149 per cell for ε = 2 %), and scores of exactly 0 or 1 |
| Face preparation | `dwarpal_ml.prepare`: every image through the serving vision library (decode → YuNet → central face → quality record → align to 256×256 at serving framing); 64-bit DCT perceptual hash; reproducible output zip; 24 processes |
| Duplicate removal | `dwarpal_ml.dedup`: Hamming sieve (≤ 10 bits, vectorised blocks) → fine-detail confirmation (64×64 grey minus Gaussian blur σ 2, correlation ≥ 0.6) → union-find groups → keep the copy in the most protected split (test > calib > val > train) |
| Training | `targets.py` (σ(a)=1+0.04a label distributions; bands as sums of Gaussians, open band to 89; loss = KL + 0.1·distance of E[age] to band); `data.py` (usable rows; 1/√count sampling, ×2 for bands touching 10–25; OpenCV augmentation: one-warp geometry, colour, webcam damage); `model.py` (timm backbone, 101 logits, normalisation inside the model); `train.py` (AdamW, warm-up + cosine, bf16 autocast, grad clip 1.0, EMA, best-by-val-band-MAE, `run.json` with config, git state, data fingerprints, environment) |
| Supply chain | uv `exclude-newer = "7 days"` (rolling cooldown, like pnpm); six pins stepped back (fastapi 0.143.0, hypothesis 6.168.5, markdown 3.11, numpy 2.5.3, pydantic 2.14.0, pydantic-settings 2.15.0); PyTorch 2.14.1 from PyTorch's indexes: CUDA 13.0 on Windows, CPU on Linux |
| Evaluation | `evaluate.py`: band-MAE/in-band per band, group, sex; clear minors (band entirely < N) rated ≥ N and clear adults (band ≥ N+3) rated < N at N = 13, 16, 18, 21, with two-sided Clopper–Pearson 95 % intervals; ECE of P(age ≥ b) at FairFace band edges, before/after temperature fitted on val; worst/best group ratios; logits cached per run; **test split locked after one evaluation** |
| Gates | `ml/gates.toml` (provisional, FairFace-measurable): band-MAE ≤ 2.0; children < 10 rated 18+ upper ≤ 5 %; worst group's upper ≤ 10 %; group band-MAE ratio ≤ 1.25; mean ECE ≤ 0.05 |
| Exact-age calibration | UTKFace adapter (tar.gz repacked to zip; labels from file names; calib/test 50/50); `subject = "only"` preparation (photos with a second clear face set aside); dataset photos decoded with roomier limits then shrunk to 1,920 px; `dedup --against fairface`; risk control with per-age fallback (`by_group`); `calibrate.py`: strictest certifiable budget from 2 % to 20 %, every refusal recorded, decisions checked on the test half once |
| Export and serving | `export.py`: model + temperature + softmax exported to ONNX (opset 18, dynamic batch 1–64); parity vs PyTorch; serving-path drift; CPU latency; registry manifest `models/registry/age/age-convnext-tiny-2026.10.17/manifest.json` (thresholds at certified budgets, provenance, licences, checks; `calibrated: false`, non-commercial research only). Shared `dwarpal_vision.to_model_input`. Inference `OnnxAgeBackend` (fingerprint-checked, fail closed), `DWARPAL_INFERENCE_AGE_BACKEND=onnx`; stub remains the default |
| Book | Part 2 §2.1, 2.2, 2.4–2.8, 2.10–2.17, 2.19 written in full; §5.2.1–5.2.7 with every new file walked through |

## What was measured

| Check | Result |
| :-- | :-- |
| FairFace manifest | 97,698 images · train 69,469 · val 8,654 · calib 8,621 · test 10,954 · groups from 10,425 to 18,612 |
| ML tests | 24 passed (9 risk control, 8 data, 7 preparation and dedup; Hypothesis properties included) |
| Face preparation | 97,698 images → 97,645 faces, 53 without a face; 45 s on 24 processes; 1.7 GB of aligned faces. Quality flags recorded (not removed): not frontal 32,818, multiple faces 23,489, blurry 10,319, dark 9,167, small 8,703 |
| Duplicates | 123,774 sieve pairs → 467 copies removed; 233 would have leaked into evaluation (train → test 75, train → calib 65, train → val 60, between evaluation splits 33) |
| Usable faces | train 69,012 · val 8,625 · calib 8,600 · test 10,941 |
| Constant baseline (val) | always 29: band-MAE 8.55, in band 29 % |
| ConvNeXt-Atto, from scratch (val) | 3.4 M parameters, 30 epochs, 32 min at ~1,100 img/s: **band-MAE 2.61**, in band 49 %; per band 1.46 (20–29) to 5.21 (70+); per group 2.35–3.05 (Black highest); P(≥18) ≥ 0.5 for 4.5 % of ages 3–9 and 1.7 % of ages 0–2; train/val loss 0.89/1.07, still improving at epoch 30 |
| **ResNet-26d, from scratch (val) — baseline** | 14.2 M parameters, 30 epochs, 63 min at ~555 img/s: **band-MAE 2.28**, in band 52 %; per band 1.27 (20–29) to 4.00 (70+); per group 2.05–2.63 (Black highest); P(≥18) ≥ 0.5 for 3.5 % of ages 3–9 and 1.1 % of ages 0–2; train/val loss 0.81/0.98, still improving at epoch 30 |
| **ConvNeXt-Tiny, ImageNet-pretrained (val) — best** | `convnext_tiny.in12k_ft_in1k` (Apache-2.0, pinned), 27.9 M parameters, batch 64, lr 1.5e-4, warm-up 1, drop-path 0.1, 15 epochs, 54 min at ~320 img/s, 59 % GPU memory: **band-MAE 1.84 at epoch 6**, in band 55 %; per band 0.94 (3–9) to 3.33 (70+); per group 1.72–2.02 (Black highest); P(≥18) ≥ 0.5 for 1.7 % of ages 3–9 and 0.6 % of ages 0–2; over-fits after epoch 6 (val loss 0.86 → 1.08, train 0.72 → 0.29) |
| **ConvNeXt-Tiny on the locked test split** (evaluated once) | 10,941 faces, temperature 0.884 (fitted on val): band-MAE **1.83**, in band 55.7 %; children < 10 rated 18+ **1.74 %** (27/1,553; 95 % up to 2.52 %); adults 30+ rated < 18 0.65 %; ECE 0.0188 → 0.0177; group band-MAE 1.68–2.04 (ratio 1.21); by sex 1.95 (f) / 1.72 (m); at 13: 10.6 % of children < 10 rated 13+. **Gates: 4 pass, 1 fails** — worst group (Middle Eastern, 6/126 = 4.8 %) upper bound 10.08 % > 10 % |
| UTKFace data | 24,079 photos (8 malformed names and 22 ages > 100 skipped) → 23,477 faces (519 several faces, 83 none) → 539 copies removed (533 within UTKFace, 324 of them with a different age; 6 copies of FairFace photos) → calib 11,301 · test 11,637. Teens 13/14/15/16/17: 82/164/180/253/159 in all; smallest group cells 1–15 |
| **ConvNeXt-Tiny on UTKFace (exact ages)** | Test MAE **4.96 years** (0–12: 1.6, 13–17: 3.3, 18–24: 2.9, 60+: 9.6). Certified per age only (no group cell reaches 149): **18 → 7.5 %**, τ_pass 0.964, τ_fail 0.384; 21 → 7.5 %; 13 and 16 → 15 %. Test half at 18: 13–17 passed **2.9 %** (12/416, up to 5.0 %; 13: 0 %, 14: 0 %, 15: 3.7 %, 16: 2.7 %, 17: 6.4 %), under-13 0.4 %; adults 18–20: 13 % pass / 77 % step-up / 9 % fail; 21–24: 30 % pass; 25–29: 56 %; 30+: 94 %. Every age within its certified budget |
| Export checks | Parity: largest probability gap 8.3e-7 over 512 faces (tolerance 1e-4). Serving path vs training path: 0.16 years mean (0.45 p95), 0.003 in P(18+). CPU, 1 thread, 5 faces: p50 668 ms, p95 697 ms (NFR-05: ≤ 1.5 s per submission on 4 vCPU). Whole service pipeline, 5 frames, 4 threads: 239 ms |

## Findings

- FairFace's label file writes its top band `more than 70`, not `70+` as documented; the manifest refused it until the spelling was added.
- **Tight crops were unusable for our alignment.** FairFace's padding-0.25 images left about a third of each aligned face as stretched edge pixels — unlike any webcam frame — and made strangers' perceptual hashes collide. The owner approved the padding-1.25 version (2.1 GB, `033bb5c7…`); faces not found fell from 151 to 53.
- **Duplicate limits were set by inspection.** Whole-thumbnail correlation could not separate copies from aligned strangers (strangers up to 0.95). Fine-detail correlation is bimodal (bulk 0–0.35, copies near 1); every inspected pair ≥ 0.6 was the same photo. Sieve 10 found 31 more confirmed copies than sieve 8.
- **Label noise.** 189 of 467 duplicate pairs (40 %) give the same photo different age bands (175 one band apart, 14 two or more).
- **ConvNeXt V2 weights are non-commercial** (CC BY-NC 4.0); Apache-2.0 alternatives exist (timm ConvNeXt, DINOv2). The owner approved PyTorch but no pretrained weights, so the first models are trained from scratch.
- **The guarantee holds on unseen exact ages, but only per age and loosely.** UTKFace's teenagers are too few for per-group cells; at 18 the strictest certifiable budget is 7.5 % (NFR-01 target: 2 % per age and group). The test half stayed within every certified budget. The cost falls on young adults: most 18–24-year-olds are sent to step-up.
- **UTKFace's labels are noisy**: estimated (DEX + human check); 61 % of within-dataset duplicate copies carry a different age; strong heaping at 26.
- **First test-split result: one gate fails.** Middle Eastern children < 10: 6/126 rated 18+ (val: 1/81); girls 2.5 % vs boys 1.2 %; limit 13 weak (10.6 %) because FairFace's 10–19 band can't separate 10 from 13. Recorded unchanged; the test split is locked for this model.
- **Pretrained weights help a lot**: ConvNeXt-Tiny (ImageNet) beat the from-scratch ResNet-26d after a single epoch (2.15 vs 2.28) and reached 1.84. Its weights' licence is Apache-2.0, but they were trained on ImageNet (research-only terms) — recorded in the register as an open legal question.
- **Silent GPU memory spill on Windows**: at batch 128 ConvNeXt-Tiny exceeded 8 GB and the driver spilled ~2.2 GB into system memory (GPU 100 % busy at 32 W, epoch > 10 min) instead of failing. Batch 64 uses 59 %. Training now records peak memory per epoch and warns above 92 %.
- **Data loading was the first bottleneck**: torchvision ColorJitter (hue) cost 17 ms/face; replaced by OpenCV (27 → 7.5 ms). Windows spawn serialised 14 loader processes (78 s) because each received the full row list; sending only (dataset, split) cut start-up to 11 s.
- The first `calibrate` refused a model that separates ages perfectly ("can't separate"). Fixed by capping τ_fail below τ_pass, which is always safe; found while writing the book's explanation of the test.

## Open questions for the owner

1. **More exact-age data.** UTKFace allows per-age certification at 7.5 % for 18; NFR-01's 2 % per age *and* group needs ≥ 149 teenagers per age per group in the calibration half alone — several thousand teenagers in all, with documented (not estimated) ages. Candidates: APPA-REAL, IMDB-Clean (licences to check), AgeDB/LAGENDA (on request), or consented collection.
2. **Per-cell or simultaneous confidence.** ADR-0006 promises 95 % confidence *per cell*. With ~35 cells, a guarantee for all cells at once (Bonferroni: δ/35 per cell) needs about 325 people per cell for ε = 2 %, instead of 149.
3. **ImageNet-trained weights.** ConvNeXt-Tiny's weights are Apache-2.0, but whether ImageNet's research-only terms reach trained weights is legally unsettled; to judge before any commercial launch.
4. **Policies vs certified budgets.** API presets all ask for 2 %; the model certifies 7.5 % (18, 21) and 15 % (13, 16), so with its manifest every preset is `policy_not_supported` until either better data certifies 2 % or the owner adds presets at the certified budgets (test mode only).
5. **Release gates.** `ml/gates.toml` values are proposals; the group gate's 10 % and the use of upper bounds need the owner's confirmation, and the exact-age gates of NFR-01/NFR-04 replace them once exact-age data is approved.
6. **Laptop heat.** Long runs keep the RTX 4070 at ~86 °C and ~80–100 W. Options: shorter runs (8 epochs suffice for the pretrained recipe), a cooling pad / performance fan profile, or a GPU power cap (an owner decision).
