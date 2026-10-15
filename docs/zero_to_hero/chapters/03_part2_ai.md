# Part 2 — AI from zero

!!! honest "Status of this part"
    This part is an **outline** today. Each section is written in full while the AI is actually built (roadmap Phase 2). The explanations will then use the project's *real* data, *real* training runs and *real* measured numbers, not made-up examples. The outline is here so you can see where the book is going.

**What you will be able to do after this part:** explain how a computer can learn to estimate age from a face; how we measure the mistakes it makes; why we trust some of its answers and not others; and how we make it fast and fair.

| Section | Question it answers |
| :-- | :-- |
| 2.1 What "learning" means for a machine | How can a program get better from examples instead of from rules a human wrote? |
| 2.2 Data, labels and datasets | What is a training example? Why do we split data into training, validation and test sets — and why is the test set kept locked away? |
| 2.3 Images as numbers | How does a photo become a grid of numbers (a *tensor*) that maths can work on? |
| 2.4 A model is a function with knobs | What are *parameters*, and why does a modern model have millions of them? |
| 2.5 Loss — measuring how wrong | Mean absolute error, cross-entropy, KL divergence — in pictures, not formulas first |
| 2.6 Gradient descent — walking downhill | How turning millions of knobs a tiny bit at a time makes the loss smaller |
| 2.7 Neural networks | Neurons, layers, activations — and what "deep" learning means |
| 2.8 Convolutional networks | Sliding "stencils" that find edges, then shapes, then faces |
| 2.9 Transformers and Vision Transformers | *Attention*: letting every patch of a face look at every other patch |
| 2.10 Pre-training and fine-tuning | Why we start from a model that has already seen millions of images |
| 2.11 Predicting a *distribution* instead of a number | Why "probably 22, possibly 19–26" is more useful and more honest than "22" |
| 2.12 Measuring mistakes | MAE, the confusion matrix, false-adult rate, thresholds, and why averages hide danger |
| 2.13 Calibration | Making "80 % sure" actually mean right 80 % of the time |
| 2.14 Risk control | Clopper–Pearson bounds and the conformal idea: turning test results into a guarantee |
| 2.15 Over-fitting and domain shift | Why a model can ace its exam and fail in real life (photos vs. webcams) |
| 2.16 Measuring fairness | Per-group error rates, gaps, and release gates |
| 2.17 Faces: detection, landmarks, alignment | Finding the face, finding the eyes and nose, straightening the picture |
| 2.18 Liveness and anti-spoofing models | How a model tells a real face from a photo of a face |
| 2.19 Making models fast | ONNX, quantisation, distillation — the same answers, in a fraction of the time |
