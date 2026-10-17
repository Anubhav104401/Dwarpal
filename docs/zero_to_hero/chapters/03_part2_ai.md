# Part 2 — AI from zero

!!! honest "Status of this part"
    This part is being written **while the AI is actually built** (roadmap Phase 2), so its explanations can use the project's *real* data, *real* training runs and *real* measured numbers, not made-up examples. Sections marked ✅ in the table are written in full below; the rest are still an outline, so you can see where the book is going.

**What you will be able to do after this part:** explain how a computer can learn to estimate age from a face; how we measure the mistakes it makes; why we trust some of its answers and not others; and how we make it fast and fair.

| Section | Question it answers |
| :-- | :-- |
| 2.1 What "learning" means for a machine ✅ | How can a program get better from examples instead of from rules a human wrote? |
| 2.2 Data, labels and datasets ✅ | What is a training example? Why do we split data into training, validation and test sets — and why is the test set kept locked away? |
| 2.3 Images as numbers | How does a photo become a grid of numbers (a *tensor*) that maths can work on? |
| 2.4 A model is a function with knobs ✅ | What are *parameters*, and why does a modern model have millions of them? |
| 2.5 Loss — measuring how wrong ✅ | Mean absolute error, cross-entropy, KL divergence — in pictures, not formulas first |
| 2.6 Gradient descent — walking downhill ✅ | How turning millions of knobs a tiny bit at a time makes the loss smaller |
| 2.7 Neural networks ✅ | Neurons, layers, activations — and what "deep" learning means |
| 2.8 Convolutional networks ✅ | Sliding "stencils" that find edges, then shapes, then faces |
| 2.9 Transformers and Vision Transformers | *Attention*: letting every patch of a face look at every other patch |
| 2.10 Pre-training and fine-tuning ✅ | Why we start from a model that has already seen millions of images |
| 2.11 Predicting a *distribution* instead of a number ✅ | Why "probably 22, possibly 19–26" is more useful and more honest than "22" |
| 2.12 Measuring mistakes ✅ | MAE, the confusion matrix, false-adult rate, thresholds, and why averages hide danger |
| 2.13 Calibration ✅ | Making "80 % sure" actually mean right 80 % of the time |
| 2.14 Risk control ✅ | Clopper–Pearson bounds and the conformal idea: turning test results into a guarantee |
| 2.15 Over-fitting and domain shift ✅ | Why a model can ace its exam and fail in real life (photos vs. webcams) |
| 2.16 Measuring fairness ✅ | Per-group error rates, gaps, and release gates |
| 2.17 Faces: detection, landmarks, alignment ✅ | Finding the face, finding the eyes and nose, straightening the picture |
| 2.18 Liveness and anti-spoofing models | How a model tells a real face from a photo of a face |
| 2.19 Making models fast | ONNX, quantisation, distillation — the same answers, in a fraction of the time |

## 2.1 What "learning" means for a machine

An ordinary program is a list of rules a person wrote: *if the password matches, let them in*. Nobody can write the rules for "how old does this face look". People can do it, but can't say how: we notice skin, the shape of the jaw, the eyes, the hair, all at once, without being able to list the rules.

**Machine learning** turns the problem round. Instead of writing the rules, we write a program with a great many adjustable settings, show it examples together with the right answers, and let a mathematical procedure adjust the settings until the program's answers match the examples. The examples are the **training data** (§2.2); the program with its settings is the **model**; the adjusting is **training**.

!!! kid "Explain like I'm six — learning to throw at a target"
    Nobody can tell you exactly how hard to throw a ball so it lands in a bucket. But you can throw, see where it lands — too far, too short — and adjust a little. After a hundred throws you're good at it, though you still couldn't write down the rule. Machine learning does the same: try, measure how far off it was, adjust a little, and repeat — millions of times.

The test of whether it worked is never the examples it learned from. It is new examples it has never seen: that is what the validation and test splits are for (§2.2).

## 2.2 Data, labels and datasets

A program that *learns* is not given rules. It is given **examples**, and it works out the rules itself (§2.1). For age estimation, one example is a photo of a face together with the answer we want for it — the person's age. The answer is called the **label**. A **dataset** is a large collection of labelled examples, gathered and published by researchers so that others can learn from it and compare their results.

### Kinds of labels

Not every dataset labels age the same way, and the difference matters a great deal for this project:

| Kind | Example | What it can teach |
| :-- | :-- | :-- |
| **Exact age** | "17" | Everything: the model can learn to tell 17 from 18 |
| **Age band** | "10-19" | Rough age only: a 13-year-old and a 19-year-old get the *same* label |
| **Apparent age** | "people guessed 21" | What a person *looks* like — which is what a camera can actually see |

The first dataset this project uses, **FairFace**, has age bands only. It is excellent for teaching a model the broad shape of ageing, and its 97,698 faces are deliberately balanced across seven groups of people. But its band "10-19" puts children and adults together, so it can never prove anything about 15-year-olds in particular. That needs exact ages (§2.14).

### Splitting the data: practice, homework, the safety check and the exam

Imagine a teacher who hands out the exam questions as homework. Every student would score full marks, and the marks would mean nothing. Machine learning has the same trap: a model tested on photos it has already learned from looks far better than it really is. So, before anything is learned, the data is divided into **splits**, and each split has one job:

| Split | Like… | Its job |
| :-- | :-- | :-- |
| **train** | the textbook | the examples the model learns from |
| **validation** (`val`) | practice tests | checking progress while learning, and choosing between settings |
| **calibration** (`calib`) | the safety inspection | setting the safety lines (§2.14) — never used for learning |
| **test** | the final exam | measured once, at the end; nobody looks at it before |

The test split is kept **locked away**: if people look at test results while still making choices, their choices slowly bend towards the test, and the test stops being a fair exam. This project uses FairFace's *own* validation set as its test set, because it was chosen by FairFace's authors — nothing we did could have influenced it.

!!! kid "Explain like I'm six — a fair way to pick teams"
    Picking teams by drawing names from a hat is fair, but if you draw again tomorrow, the teams change. We want teams that are fair *and* never change. So each photo's name is put through a fingerprint machine (§X.5), which turns it into a number that looks random but is always the same for the same name. Numbers 0–79 go to the textbook, 80–89 to the practice tests, and 90–99 to the safety inspection. Tomorrow, next year, on any computer: the same photo always lands in the same place.

!!! honest "Honest limitation — the same person twice"
    Splitting by photo keeps each *photo* in one split, but a dataset can contain the same photo twice, or two photos of the same person. If one lands in training and the other in testing, the test is slightly too easy. The project removes repeated photos across all splits (§5.2.3): FairFace had 467, of which 233 would have leaked into evaluation. Different photos of one person can't be found that way, and FairFace doesn't record who is who, so for this dataset that risk remains, and is stated.

### Datasets have licences

A dataset is someone else's work, published under a **licence** — the rules for using it (§0.16). Some allow any use with credit; others allow research only. A model *learns from* its data, so the data's terms follow the model: a model trained on "research only" photos is a research-only model. That's why the project keeps a **licence register** (`ml/datasets.toml`, §5.2.1) listing every dataset, its licence, and whether the project's owner has approved it — and why nothing is downloaded until they have.

## 2.4 A model is a function with knobs

A **function** takes something in and gives something out. Our age model takes in a picture — 224 × 224 pixels × 3 colours, so 150,528 numbers (§0.1) — and gives out 101 numbers, one for each age from 0 to 100.

Between input and output is a long chain of simple calculations: multiply, add, keep only the positive part, and again. Each multiplication uses a number that isn't fixed by the design but can be adjusted. These adjustable numbers are the model's **parameters** (also called **weights**) — the knobs. The models trained in this project have 3.4 million (ConvNeXt-Atto) and 14 million (ResNet-26d). A brand-new model has its knobs set at random, so its answers are random. Training sets them.

A model's **design** — which calculations, in which order — is called its **architecture**. A well-known architecture used as the main body of a model, with a small task-specific part on top, is called a **backbone**. Ours come from the timm library (§5.2.4).

## 2.5 Loss — measuring how wrong

To improve, the model needs a single number that says how wrong it is: the **loss**. Small is good; zero would be perfect. Choosing the loss means choosing what "wrong" means, so it is one of the most important decisions in a project.

Simple choices first. If the model gave one age, the obvious loss would be the **absolute error**: answer 25 for a 22-year-old, and the loss is 3. Averaged over many faces, that is the **mean absolute error (MAE)**, the standard score for age estimation.

But our model gives a whole **distribution** (§2.11), and the right answer is a distribution too: for the label "20-29", a soft hump over those years (`targets.py`). The standard way to compare two distributions is the **Kullback–Leibler divergence**: roughly, how much extra surprise you'd suffer if you expected the model's distribution but the truth was the target. It is 0 when they match, and grows the more probability the model puts in the wrong places — especially where the target says "almost impossible".

The project's loss adds the two ideas: the KL divergence, plus a tenth of how many years the predicted average age lies outside the labelled band. The first shapes the whole distribution; the second pulls its centre into place.

## 2.6 Gradient descent — walking downhill

Imagine every possible setting of the model's millions of knobs as a point in a vast landscape, with the loss as the height of the ground. Training means finding a low point. You can't see the landscape — it has millions of directions — but at any point you can feel which way the ground slopes. That slope is the **gradient**, and calculus gives a way to compute it for every knob at once, in one pass backwards through the chain of calculations (**backpropagation**). Then: take a small step downhill, measure again, step again. That is **gradient descent**.

Three practical details, all in `train.py`:

- **Mini-batches.** Measuring the loss over all 69,000 training faces for every step would be slow. Instead each step uses a **batch** of 128 random faces: a slightly noisy but much cheaper estimate of the slope. One pass through the data is an **epoch**; our runs take 30 epochs, about 16,000 steps.
- **The step size** — the **learning rate** — matters enormously. Too big and training overshoots and bounces around; too small and it crawls. The usual recipe, used here: start small and grow (**warm-up**, for the first 2 epochs, while the random knobs settle), then shrink smoothly to zero along a cosine curve, so the final steps are tiny and precise.
- **AdamW.** Plain gradient descent uses one step size for every knob. **Adam** gives each knob its own, based on how steep and how consistent its slope has been — the standard choice today. The "W" adds **weight decay**: a gentle pull of every knob towards zero, so that no knob grows huge to fit a few odd examples.

!!! kid "Explain like I'm six — down a foggy hill"
    You're on a hill in thick fog and want to reach the valley. You can't see it, but you can feel the slope under your feet. So: feel the slope, take a step downhill, feel again, step again. Big steps at first, tiny careful steps at the end so you don't walk past the bottom. That's all training is — just with millions of directions instead of four.

## 2.7 Neural networks

A **neural network** is a particular kind of model, loosely inspired by brain cells. Its unit, the **neuron**, takes several numbers in, multiplies each by a weight, adds them up, and passes the total through a simple bend — most often "if negative, make it zero" (**ReLU**). Without the bend, any chain of multiply-and-add would collapse into one big multiply-and-add, which can only draw straight lines; with it, a network can bend its answers to fit almost anything.

Neurons are arranged in **layers**: each layer's outputs are the next layer's inputs. "**Deep** learning" just means many layers. The first layers of a vision network learn simple things — edges, spots of colour; later layers combine them into textures, then parts (an eye, a wrinkle), then whole-face properties such as apparent age. Nobody tells it to do this: it is simply what turns out to reduce the loss.

Two more pieces appear in every modern network. **Normalisation** layers keep each layer's numbers in a sensible range, which makes training far more stable. **Residual connections** let each block of layers add a correction to its input rather than replace it, which makes very deep networks trainable.

## 2.8 Convolutional networks

A photo has 150,528 numbers. Connecting every one of them to every neuron of the next layer would need billions of weights, and would ignore the obvious: what matters in a picture is *local* patterns, and a pattern means the same thing wherever it appears.

A **convolution** uses this. It slides a small stencil — say 3 × 3 pixels — across the whole picture, computing the same weighted sum at every position. A stencil whose weights are learned becomes a detector: one for horizontal edges, one for a particular texture. The same few weights are reused everywhere, which makes convolutional networks small and efficient. Stack many such layers, shrinking the picture step by step, and the stencils of later layers effectively see larger and larger areas — from edges to features to a whole face.

The project compares two convolutional backbones (§5.2.4):

- **ResNet-26d** — a 26-layer **ResNet**, the family that introduced residual connections in 2015 and became the standard workhorse of computer vision; "d" is an improved variant from the paper *Bag of Tricks for Image Classification*.
- **ConvNeXt-Atto** — the smallest **ConvNeXt** (2022), a convolutional network modernised with ideas borrowed from transformers (§2.9): larger stencils, fewer bends, different normalisation.

## 2.10 Pre-training and fine-tuning

Teaching a network to see from nothing takes enormous amounts of data. That is why most vision models start from a backbone that was first trained on a huge general collection — usually **ImageNet**, 1.3 million photos of a thousand kinds of things — and then **fine-tune** it on the task at hand. The pretrained backbone already knows edges, textures, shapes and faces; fine-tuning only has to teach it what age looks like. With 69,000 training faces, starting from a pretrained backbone typically gives far better results than starting from random knobs.

Pretrained weights are files someone else made, and they come with their own licences — some forbid commercial use, as for the original ConvNeXt V2 weights (§5.2.4). Like datasets, they need checking and the owner's approval. For the first training runs none were approved, so the project's first models learned from FairFace alone, **from scratch**: a harder start, and an honest baseline. Then the owner approved one set, ConvNeXt-Tiny trained on ImageNet: after a single epoch of fine-tuning it already beat the best from-scratch model after thirty, and it finished about a fifth better (§5.2.4).

## 2.11 Predicting a *distribution* instead of a number

A model could answer with one number: "22". But a face alone often can't settle whether someone is 17 or 19, and a single number hides that doubt. Our model answers with **101 probabilities**, one for each age from 0 to 100, adding up to 1: perhaps 2 % for 17, 9 % for 20, 14 % for 22, and so on.

The 101 raw outputs of the network (**logits**) can be any numbers. The **softmax** function turns them into probabilities: it raises *e* to the power of each (making them all positive, and exaggerating the differences), then divides by the total (making them add up to 1).

From the distribution we can read everything the system needs:

- the **expected age** — each age times its probability, added up;
- the **spread** — how uncertain the model is;
- most importantly, the **probability of being at least N**: add up the probabilities of all ages from N to 100. This number, `P(age ≥ 18)`, is what the safety lines of §2.14 are set on.

## 2.12 Measuring mistakes

A single score can hide the mistakes that matter. Dwarpal measures a model several ways, because each answers a different question.

**How far off, on average?** The standard score for age estimation is the **mean absolute error (MAE)**: the average number of years between the estimate and the true age. FairFace gives age *bands*, not ages, so the project uses **band-MAE**: how many years the estimate lies *outside* the labelled band, 0 if it is inside. The best model so far scores 1.83 on the test split.

**Which mistakes are dangerous?** For an age check, errors are not equal. A 30-year-old estimated at 34 harms nobody; a 9-year-old estimated at 19 is the failure the whole system exists to prevent. So mistakes are counted separately for the cases that matter:

| | Truly under the limit | Truly over the limit |
| :-- | :-- | :-- |
| **Rated over** | ❌ the **safety** error: a child let through | ✅ |
| **Rated under** | ✅ | the **convenience** error: an adult sent to step-up |

A table like this is called a **confusion matrix**. The safety error at a given threshold is what the design calls **FAR-minor** (false adult rate for minors).

**Why averages hide danger.** A model can have an excellent average and still fail a small group badly: if it is wrong about 9-year-olds 10 % of the time but 9-year-olds are 1 % of the test faces, the overall score barely notices. So every measure is also reported per age band, per group and per sex — and the gates (§2.16) look at the *worst* of them, not the average.

**Every rate gets an interval.** "18 of 1,208 children" is 1.49 %, but a different 1,208 children might have given 1.2 % or 2 %. Each rate is reported with its 95 % Clopper–Pearson interval (§2.14) — for 18 of 1,208, from 0.9 % to 2.3 % — and gates are checked against the upper end, the cautious one.

## 2.13 Calibration

A model that says "80 % sure" should be right about 80 % of the time. If, of all the faces it called 80 % likely to be over 18, only 60 % really were, its probabilities are **overconfident** — and any threshold set on them would be set on a false sense of certainty. A model whose stated probabilities match reality is **well calibrated**.

To measure it: put the forecasts into bins (0–10 %, 10–20 %, …), compare each bin's average forecast with how often the event really happened, and add up the gaps, weighting each bin by how many forecasts fell in it. That is the **expected calibration error (ECE)**: 0 is perfect, and 0.05 means "off by about 5 percentage points".

FairFace can't say whether a face in the band 10–19 is over 18. But it can say, for *every* face, whether it is over 20, 30 or 40, because its bands never straddle those ages. So calibration is measured at each band edge. The best model's error is about 0.018 — already close to honest.

Modern networks are often a little overconfident, and there is a standard fix: **temperature scaling**. Dividing all the logits by one number *T* before the softmax spreads the probabilities out (*T* > 1) or sharpens them (*T* < 1), without changing which age is most likely. *T* is chosen on the validation split to make the true answers as unsurprising as possible. For our model it came out at 0.88 — slightly *under*-confident, so slightly sharpened — and the calibration error fell from 0.0188 to 0.0177 on the test split. Calibration matters doubly here, because the safety lines of §2.14 are set on these probabilities.

## 2.14 Risk control — turning test results into a guarantee

§3.3 told the story of the jar of 600 photos: 6 children got through, and "the worst the real rate could plausibly be" came out at 1.96 %. This section explains where that number comes from, and how the project uses it to set its safety lines.

### The problem: a test is only a sample

Suppose we show the model 600 photos of 17-year-olds, and 6 would pass. The rate *in this jar* is 1 %. But another jar of 600 different 17-year-olds might give 4 passes, or 10. What we want to know is the rate for *all* 17-year-olds like these — and that number we can never measure directly. We can only reason about what it *could* be, given what we saw.

### The worst plausible rate

The question is turned around: **if the true rate were p, how surprising would our result be?** If the true rate were 5 %, seeing only 6 passes in 600 (we would expect 30) would be wildly unlikely — so 5 % is not plausible. If the true rate were 1.5 %, seeing 6 would be quite normal. Somewhere in between is the highest rate at which our result is still not too surprising. "Not too surprising" is set by the **confidence level**: at 95 % confidence, we call a result too surprising if a rate p would produce it — or anything better — less than 5 % of the time.

That highest plausible rate is the **Clopper–Pearson upper bound**, after the two statisticians who described it in 1934. For 6 out of 600 it is **1.96 %**. For 7 out of 600, 2.18 %.

For readers who like formulas: if the true rate is p, the number of passes out of n behaves like coin tosses with a coin that lands "pass" with chance p — what statisticians call a **binomial distribution**. The Clopper–Pearson upper bound is the value of p at which the chance of seeing k or fewer passes falls to exactly δ (5 %). There is no simple formula for it in general, but it equals a point of another well-known curve, the **beta distribution**, which the SciPy library computes precisely (`risk.py`, §5.2.2).

One case does have a simple formula, and it is a useful one. With **zero** passes out of n, the chance of seeing zero when the rate is p is (1 − p) multiplied by itself n times, so the bound is 1 − δ^(1/n). To prove a rate of at most 2 % with nobody getting through, you therefore need **149 people**; with 148, even a perfect result can't prove it. To prove 1 % takes 299. *Less evidence forces more caution.*

!!! why "Why this method, and not a simpler one?"
    The simplest-looking approach — "1 % passed, so the rate is about 1 %" — ignores luck completely. Textbook "± margin" formulas use a bell-curve shortcut that is badly wrong for rare events and small groups, which is exactly our situation: they can even promise a rate *below* zero. Clopper–Pearson works from the exact coin-toss maths, and errs only on the cautious side. For a safety promise, cautious is right.

### From a bound to a safety line

The model gives each face a score: how likely the person is to be at least the minimum age. A **pass line** turns scores into decisions: at or above the line, pass. Raising the line lets fewer people through. The project chooses:

1. **The pass line:** the *lowest* line at which, for **every exact age** from N−5 to N−1 and **every group** of people, the Clopper–Pearson bound of the pass rate is within the website's **risk budget** (for example, 2 %). Each age in each group is called a **cell**, and every cell must keep the promise — because an average hides danger: a model could let in hardly any 13-year-olds and far too many 17-year-olds, and still average under 2 %.
2. **The fail line:** the *highest* line at which clear adults (N+3 and over) in every group are failed outright at most 1 % of the time — kept below the pass line.
3. Between the lines, **step-up**: a document check instead of a guess.

A weaker model doesn't make the system less safe. It makes the lines move apart, so more people are sent to step-up. Safety stays fixed; the cost shows up as inconvenience, where it can be measured and improved.

!!! honest "Honest limitation — what exactly is promised"
    - The promise is about photos **like the calibration photos**. Webcams are different (§3.3), which is why the system also refuses poor frames, trains on "webcam-style" photos, and watches its live pass rates.
    - The 95 % confidence applies to **each cell on its own**. With around 35 cells (5 ages × 7 groups), the chance that *at least one* cell's real rate is above its bound is higher than 5 %. Making the promise hold for all cells at once is possible — by giving each cell a smaller share of the 5 % — but it needs more than twice as many people per cell. That is a decision for the project's owner, and it is recorded as an open question in the Phase 2 report (`docs/reports/phase-2.md`).
    - Exact ages are needed. FairFace's age bands can't certify anything about a single age, so calibration waits for an exact-age dataset to be approved.
## 2.15 Over-fitting and domain shift

A model with millions of knobs can do something unhelpful: memorise its training faces instead of learning about ageing. Its training loss keeps falling while its answers on new faces stop improving or get worse. That is **over-fitting**, and it is exactly what the validation split watches for: the model is judged after every epoch on 8,625 faces it never trains on, and the version kept is the one that did best there (`train.py`). Our pretrained model did exactly this: its validation loss was lowest at epoch 5 and then rose for ten epochs while its training loss kept falling — the table in §5.2.4 shows it epoch by epoch.

Three defences are used in training:

- **Data augmentation**: every time a face is shown, it is randomly zoomed, turned, shifted, mirrored, recoloured and roughened (`data.py`). The model can't memorise a picture it never sees twice in the same form.
- **Weight decay** (§2.6) keeps knobs from growing large to fit a few odd faces.
- **Weight averaging (EMA)**: alongside the knobs being trained, a second copy keeps a slowly moving average of them. The average is smoother than any single moment of training and usually does better on new data, so it is the copy that gets evaluated and saved.

**Domain shift** is the same problem one level up: a model can do well on new photos *from the same collection* and still disappoint on a different kind of picture. FairFace's photos come from the internet; Dwarpal's come from webcams and phones — darker, blurrier, more compressed. The webcam-style damage in the augmentation is there to narrow that gap, and the quality checks at serving time refuse pictures too far outside it.

## 2.16 Measuring fairness

An age estimator can be accurate on average and still be worse for some people than for others: for darker skin in poor light, for women wearing makeup, for faces underrepresented in the training data. In an age check, that would mean some children are let through more often than others, or some adults sent to step-up more often. Fairness can't be assumed; it has to be measured, group by group, and published.

Dwarpal measures, for every group the test data labels (FairFace has seven ethnic groups and two sexes):

- **accuracy per group**, and the **ratio of the worst to the best**;
- **safety per group**: the share of each group's children rated more likely than not to be over 18, with its interval.

**Release gates** turn these into rules: limits written down *before* looking at a model's test results, which every model must meet before it serves anyone (`ml/gates.toml`). Writing them first matters: once the results are in view, it is very tempting to find reasons why a slightly worse number is fine.

Two honest difficulties come with group measurements:

- **Small groups make wide intervals.** FairFace's test split has 126 Middle Eastern children under 10. With 6 of them misjudged, the true rate could plausibly be anywhere from 1.8 % to 10.1 %. Gates on groups must use the upper bound — and more data per group is the only real cure.
- **Group labels are coarse.** Seven ethnic labels assigned by annotators can't describe how diverse faces really are, and skin tone, lighting and camera matter as much as any label. The labels are used because they are what the data offers, not because they are the right categories for people.

## 2.17 Faces: detection, landmarks, alignment

Before a model can estimate anyone's age, three questions must be answered about a picture: *is there a face, where is it, and which way is it turned?* The answers turn a photo of a whole scene into a small, standard picture of one face — and the age model only ever sees that.

### Detection: is there a face, and where?

A **face detector** is itself a small neural network, trained on many thousands of photos where people had drawn boxes around faces. Shown a new picture, it answers with a **box** around each face it finds, a **score** for how sure it is (from 0 to 1), and five **landmarks**: the centres of both eyes, the tip of the nose, and the two corners of the mouth. The project uses **YuNet** (§3.3, Choice 5): it takes a few milliseconds per picture on an ordinary processor, and its licence allows any use.

When a picture holds several faces, something must decide which one counts. At serving time the rule is strict: a second clear face is a reason to ask for a new picture. In a dataset like FairFace, where every image was made by centring it on the labelled person, the face **nearest the middle** is the one the label describes (§5.2.3).

### Alignment: the same face, the same way, every time

People tilt their heads, stand near or far, and appear anywhere in the frame. A model could learn to cope with all of that, but it learns far more easily if every face arrives the same way round. **Alignment** moves the picture so that the five landmarks land as close as possible to five fixed positions — a **template**: eyes level and at a fixed distance apart, nose in the middle, mouth below.

The movement allowed is a **similarity transform**: turning, resizing and shifting, but never stretching (§4.9), so a face never gets thinner or wider than it really is. The best one is found by a method that fits the five points as closely as possible while ignoring a point that is badly off (*least median of squares*), then applied to every pixel.

!!! kid "Explain like I'm six — passport photos"
    Imagine a pile of holiday photos: people far away, close up, tilted, off to one side. Now imagine turning them all into passport photos: same size, head straight, eyes on the same line. Comparing faces is much easier with the passport photos. Alignment makes passport photos automatically, using the eyes, nose and mouth as guides.

### One recipe for training and serving

The most important rule of this whole section is simple: **the faces a model learns from must be prepared exactly like the faces it will judge.** If training faces were framed more tightly, or stretched differently, or had parts filled in that live faces don't, the model would be tested on pictures unlike the ones it studied — and its measured accuracy would no longer describe the real system. That is why one library, `dwarpal_vision`, does detection and alignment for both training and serving, and why Phase 2 replaced a dataset version whose crops were too tight for that recipe (§5.2.3).

!!! honest "Honest limitation"
    The detector can miss faces, especially very dark, very small or sharply turned ones. In FairFace it found a face in all but 53 of 97,698 photos, but those 53 are not a random sample: missed faces are more often the hard cases. A missed face at serving time asks the person to try again with better light, so nobody is silently judged on a bad picture.
