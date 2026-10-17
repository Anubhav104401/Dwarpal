---
fingerprint: d13c14330970cc78
---
**What the right answer looks like, and how wrong an answer is.** The model never answers with a single age. It answers with 101 numbers, one for each age from 0 to 100, which become a **probability distribution** — "probably 22, possibly 19 to 26" (§2.11). So the right answer for each training face must be a distribution too, and the **loss** must measure how far the model's distribution is from it (§2.5).

```
label "20-29"  ──► target: a soft hump over 20–29, edges spilling a little into 18–19 and 30–31
model output   ──► 101 scores ──softmax──► 101 probabilities
loss           =   how different the two distributions are (KL divergence)
               +   0.1 × how far the predicted average age lies outside 20–29
```

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-8
NumPy, PyTorch (§2.6), NumPy's array type, and PyTorch's `functional` module of ready-made calculations.

@@ 10
`AGES = 101` — one output for each age from 0 to 100.

@@ 11-13
**`OPEN_BAND_TOP`** — FairFace's oldest band is "70 and over", with no upper end. The target spreads it over 70–89. The comment explains why: real faces over 90 are rare, and a target reaching all the way to 100 would teach the model that a 75-year-old might well be 98.

@@ 14
`MEAN_WEIGHT = 0.1` — how much the second part of the loss counts, as the design specifies (Stage 3 §8.4).

@@ 16
All 101 ages as numbers, made once and reused. The leading `_` marks it as internal to this file.

@@ 19-20
**`spread`** — how uncertain an age label is, growing with age: 1 year for a baby, 1.6 at 15, 3 at 50. A face changes much faster at 5 than at 50, so a label of "5" is sharper than a label of "50". The formula comes from the design.

@@ 23
**`label_distribution`** — turn a label into the target distribution.

@@ 24-27
An exact age is treated as a band one year wide. An open band ends at `OPEN_BAND_TOP`.

@@ 28-30
For each age in the band, add a **bell curve** (a Gaussian) centred on it, with that age's spread; dividing by the spread keeps each curve's total the same, so wide and narrow ones count equally. A band becomes a smooth hump whose edges spill gently past the band's limits. That is deliberate: FairFace's bands are people's estimates, and the duplicate photos showed that people often disagree by one band (§5.2.3). For a real FairFace band, 72–88 % of the target lies inside the band.

@@ 31
Scale the hump so it adds up to 1, as a probability distribution must, and store it in the compact `float32` type.

@@ 34-35
**`distance_to_band`** — how many years an age lies outside a band: 0 inside it, otherwise the distance to the nearer end. `torch.clamp(…, min=0)` turns negative numbers into 0. This is the yardstick for every age-band measurement: it is the band version of the **mean absolute error** (MAE), the standard measure of age estimators (§2.12).

@@ 38-40
**`expected_age`** — the average age of a predicted distribution. `softmax` turns the model's 101 raw scores (**logits**) into probabilities that are positive and add up to 1; each age is multiplied by its probability, and the results added. `float()` does this sum at full precision even when the model computes in reduced precision (`train.py`).

@@ 43-45
**`age_loss`** — one number saying how wrong a batch of answers is. Training is the search for model settings that make this number small (§2.6).

@@ 46-47
The main part: the **Kullback–Leibler (KL) divergence** between the target and the predicted distribution — a standard measure of how badly one distribution stands in for another, which is 0 only when they are identical (§2.5). PyTorch's `kl_div` expects the prediction as *log*-probabilities (`log_softmax` computes them accurately in one step) and averages over the batch (`batchmean`).

@@ 48
The second part: how far, on average, each predicted *average age* lies outside its band. The KL part cares about the whole shape of the distribution; this part pulls its centre directly into the right band.

@@ 49
The loss: the KL part, plus a tenth of the distance part.
