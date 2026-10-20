---
fingerprint: cde3216d7a730a0b
---
The converter's test: the network rebuilt from the weights' shapes takes every stored weight, and it judges the test portrait — a genuine photograph — to be a real face. It needs the pinned weight files, which only `fetch_models.py --training` downloads; without them it is skipped, with that command as the reason.

@@ 1
The module docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-7
NumPy, pytest and PyTorch.

@@ 9-11
From the converter: the list of networks, the models folder and `load`. From the vision library: the face detector, the decoder and the crop.

@@ 13
Each network's weights file and crop size.

@@ 14
The test portrait, found from the models folder: two levels up is the repository's root.

@@ 17-19
Skip the test when the weights haven't been fetched, saying how to fetch them.

@@ 20-22
**Both networks rebuild exactly, and take a real photograph for a real face.** Find the portrait's face.

@@ 23-24
For each network: load it — strictly, so a mismatched rebuild fails right here.

@@ 25-27
The portrait's crop at the network's size, as the network expects it, and its three probabilities.

@@ 28-29
They add up to 1 (softmax is built in), and "a real face" gets more than 0.8.
