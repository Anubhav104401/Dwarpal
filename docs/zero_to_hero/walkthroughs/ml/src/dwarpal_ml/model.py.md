---
fingerprint: c6b4edbcb3b17017
---
**The age model itself**: a **backbone** — a ready-designed neural network from the timm library (§2.7–2.8) — with 101 outputs, one per age. The wrapper adds two things.

1. **It takes plain pixels** and prepares them itself. Most vision models expect their input scaled in a particular way, and if training scales pictures one way and the service another, the model quietly sees the wrong numbers — a classic and hard-to-spot mistake. With the scaling *inside* the model, it travels with the model into the exported file (Phase 2, step 6), and the service only has to hand over a face's pixels.
2. **It can start from pretrained weights** (§2.10) — but only from weights in the project's model register (`models/third_party.json`): pinned to an exact file, with a recorded licence, approved by the owner, downloaded by the project's own fetcher, and checked against their fingerprint before use. Nothing is ever downloaded from inside training.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-8
`hashlib` (fingerprints), `json` (the register), `dataclass` and `Path`.

@@ 10-12
**timm** (PyTorch Image Models) — a library of hundreds of well-tested vision network designs, maintained by Ross Wightman and Hugging Face under the Apache 2.0 licence; PyTorch; and `nn`, PyTorch's building blocks for networks.

@@ 14-15
The repository's root folder, and the number of outputs.

@@ 17
`MODELS` — the `models/` folder, which holds the register and the downloaded files.

@@ 18-20
**`MEAN` and `STD`** — the average and the spread of the red, green and blue values in **ImageNet**, the 1.3-million-photo collection most vision models are first trained on. Scaling pixels by them gives numbers centred around 0, which networks learn from most easily, and a pretrained backbone expects exactly these numbers, because it learned with them.

@@ 23-24
**`UnapprovedWeightsError`** — asked to start from weights the register doesn't approve.

@@ 27-32
**`Weights`** — one approved set of pretrained weights: its name in the register, the local file, its fingerprint and its licence (copied into the run record).

@@ 35
**`pretrained_weights`** — find the approved weights for a backbone, or refuse.

@@ 36-40
Go through the register's entries and take the first one that is for **training** and names this backbone (its `timm` field). A model file for serving, such as the face detector, can never be picked up by mistake.

@@ 41-42
`for … else`: the `else` part runs only if the loop finished without `break` — that is, if nothing matched. Then refuse, naming the backbone.

@@ 43-44
The file must be present: if not, the message says how to download it.

@@ 45-46
And it must still match its pinned fingerprint. A file that was changed or swapped since it was fetched is refused.

@@ 47
Return the approved weights.

@@ 50-51
**`AgeModel`** — a PyTorch **module**, the base type for every network. The docstring states the contract: pixels in, as numbers 0–255 in red-green-blue order, arranged as *batch, colour, height, width*; 101 scores out.

@@ 53-54
Type declarations for the two stored constants (below), so the type checker knows they are tensors.

@@ 56-57
Build the model: from a backbone name, optional approved weights, and optional **stochastic depth** (`drop_path`, below). `super().__init__()` sets up PyTorch's own bookkeeping first.

@@ 58-64
**Create the backbone** by name, such as `resnet26d` or `convnext_tiny.in12k_ft_in1k`:

- `pretrained` — whether to start from weights; `pretrained_cfg_overlay={"file": …}` tells timm to load them from our local, checked file instead of fetching them from the internet;
- `num_classes=AGES` — 101 outputs. The pretrained file has 1,000 outputs (for ImageNet's 1,000 kinds of things); timm notices the difference and gives the new model a fresh, untrained final layer, keeping everything else. Of the file's 182 tensors, the 180 that make up the backbone are loaded exactly; the 2 of the old final layer are replaced;
- `drop_path_rate` — stochastic depth: during training, each block of layers is skipped at random now and then, so the network can't rely too much on any single block. ConvNeXt was designed to be trained with it. During evaluation nothing is skipped.

@@ 65-66
Store the averages and spreads, scaled from the 0–1 range to the 0–255 range of pixels, and shaped `(1, 3, 1, 1)` so that PyTorch applies each colour's value to every pixel of that colour (**broadcasting**, as in §5.2.3). `register_buffer` makes them part of the model — saved with it and moved to the GPU with it — without being settings that training changes.

@@ 68
**`forward`** — what the model does with a batch of pixels. PyTorch calls it when the model is used like a function: `model(pixels)`.

@@ 69
Convert the pixels to decimal numbers and scale them.

@@ 70
Run the backbone. `channels_last` rearranges the numbers in memory so that each pixel's three colours sit side by side, the layout the GPU's matrix units process fastest; it changes nothing about the result.

@@ 71
Return the 101 scores for each face.
