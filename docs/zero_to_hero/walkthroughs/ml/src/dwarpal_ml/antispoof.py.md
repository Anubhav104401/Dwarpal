---
fingerprint: b084f56f4d52e7f1
---
**Converting the anti-spoofing networks for serving.** The two MiniFASNet networks were published as **PyTorch weight files** (`.pth`). The inference service doesn't use PyTorch — it is 2 GB, and serving needs none of it — so this script turns them into **ONNX** files, the format the service already runs (§2.19), and proves the answers didn't change.

Two things make it unusual. First, the original project's model code isn't used: the network is **rebuilt from the shapes stored in the weight files**, and loading every weight with `strict=True` proves the rebuild matches — a single missing or misshapen layer would make loading fail. Second, safety: a `.pth` file is a Python *pickle*, a format that can carry code that runs when the file is opened. With `weights_only=True`, PyTorch reads plain numbers only and refuses anything else.

@@ 1-8
The module docstring: what it does, the command that runs it, and the two points above — the rebuild proved by strict loading, and reading the files as plain tensors only.

@@ 10
The project-wide type-hint setting.

@@ 12-13
`sys` (the exit code) and `Path`.

@@ 15-18
NumPy; ONNX Runtime, to run the converted files for the comparison; PyTorch and its building blocks, `nn`.

@@ 20-22
The repository's root folder; the face detector and decoder, to make a test crop from the portrait; and the anti-spoofing input size and crop from the vision library — so the comparison uses exactly the crop serving uses.

@@ 24
Where the models live.

@@ 25-29
`MODELS` — for each network, as the comment says: its weights file, the ONNX file to write, and the crop size it was trained on.

@@ 30-31
`HALVING` — the layers that halve the picture's size, as the comment shows: 80 → 40 → 20 → 10 → 5. The weights don't record a layer's **stride** (how far its filter steps), so the rebuild must know it.

@@ 32
`TOLERANCE` — the largest difference allowed between PyTorch's and ONNX Runtime's probabilities.

@@ 34
`State` — a name for the weights: a dict from layer names to tensors.

@@ 37-38
**`ConvBlock`** — a convolution, batch normalisation, and (except in projections) a **PReLU**: an activation like ReLU whose slope for negative values is itself learned. Its size comes from the stored weight.

@@ 40-42
The weight's shape gives the block's size: output channels, input channels per group, and the filter's size.

@@ 43
A **depthwise** convolution filters each channel on its own: its weight has one input channel per group, and as many groups as channels. Otherwise one group.

@@ 44-45
Padding, as the comment says: 3 × 3 filters get a 1-pixel border to keep the size; 1 × 1 filters need none; the final 5 × 5 filter takes none, shrinking 5 × 5 to 1 × 1.

@@ 46-48
The three parts. `bias=False`: these convolutions have no bias in the weights, since batch normalisation adds its own.

@@ 50-52
Run them in order; the PReLU only if there is one.

@@ 55-56
**`Squeeze`** — **squeeze-and-excitation**, used only in MiniFASNetV1SE: summarise each channel over the whole picture, and use the summary to strengthen or weaken that channel.

@@ 58-62
Its size comes from the weights: the number of channels, and the smaller number it squeezes them through. Two 1 × 1 convolutions, each with batch normalisation.

@@ 64-66
The summary: each channel's average over the picture (`mean` over height and width). Squeeze it, `relu`, expand it, and turn it into weights from 0 to 1 (`sigmoid`); multiply each channel by its weight.

@@ 69-70
**`DepthWise`** — the network's main building block, as the docstring says: expand with a 1 × 1 convolution, filter each channel on its own with a 3 × 3, project back with a 1 × 1, and optionally add the input back on (a **residual** connection).

@@ 72-77
The three convolutions, sized from their weights; the filtering one halves the picture if its layer is in `HALVING`.

@@ 78-79
A squeeze-and-excitation part, only where the weights have one.

@@ 80
Whether to add the input back.

@@ 82-87
Run the three, the squeeze-and-excitation if any, and add the input back when residual. (`result: torch.Tensor` gives the type checker the type that PyTorch leaves open.)

@@ 90-91
**`Stage`** — a run of residual blocks, as many as the weights hold.

@@ 93-96
Count the blocks: the distinct numbers in names like `conv_3.model.2.…`. Then build that many residual `DepthWise` blocks, in order, as one `nn.Sequential`.

@@ 98-100
Run them in turn.

@@ 103-104
**`MiniFASNet`** — the whole network, as the docstring says: pixels in (blue-green-red, 0–255, 80 × 80); the three classes' probabilities out, index 1 being a real face.

@@ 106-117
Its layers, in order, each built from its stored weights: a halving convolution, a depthwise one, then halving blocks and stages taking the picture down to 5 × 5, and a final pair that turns it into 512 numbers.

@@ 118-121
Then a **linear** layer down to an embedding (128 numbers), batch normalisation, and the final linear layer to the three classes. Their sizes come from the weights' shapes.

@@ 123-127
Run everything in order; flatten the 512 × 1 × 1 result into a row; and turn the three scores into probabilities with **softmax** — the probabilities are built into the model, so the ONNX file returns them directly.

@@ 130-132
**`load`** — read a weights file **as plain tensors only** (`weights_only=True`), on the processor. PyTorch's files can contain *pickled* Python objects, which can run code when loaded, so Semgrep warns about `torch.load` (Phase 7); with `weights_only=True` pickled code is refused, so the warning doesn't apply, and the comment says so.

@@ 133-134
As the comment says, the weights were saved from a multi-GPU wrapper that prefixes every name with `module.`; remove it.

@@ 135-137
Build the network from the weights' shapes, load every weight **strictly** — the proof that the rebuild is exact — and switch to evaluation mode (`eval`), which fixes batch normalisation to its learned averages.

@@ 140-147
**`convert`** — export to ONNX, as in Phase 2's export (`export.py`): one example input of the right shape, named input and output, the newer exporter (`dynamo=True`), and everything saved in one file.

@@ 150-151
**`parity`** — run the ONNX file with ONNX Runtime on some crops, and compare with PyTorch.

@@ 152-157
For each crop: the same pixels for both, as the networks expect them; the largest difference between the two answers.

@@ 158
The largest difference over all crops.

@@ 161-163
**`main`** — a real crop to compare on: the test portrait's face.

@@ 164-165
A seeded random generator for extra test crops, and whether everything passed so far.

@@ 166-168
For each network: load it strictly and convert it.

@@ 169-171
The comparison crops: the portrait's face at the network's crop size, and eight crops of random noise — the answers must agree on anything, not just faces.

@@ 172-174
Compare, remember whether it passed, and print the result. On the first conversion the gaps were 5.5 × 10⁻⁷ and 5.6 × 10⁻⁸: the same answers.

@@ 175
Exit with `1` if either comparison failed.

@@ 178-179
Run `main` when the file is run as a program.
