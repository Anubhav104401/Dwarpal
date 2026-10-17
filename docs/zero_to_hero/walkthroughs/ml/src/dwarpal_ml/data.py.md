---
fingerprint: 2898865482874f95
---
**Feeding the model.** Training shows the model its faces in batches of 128, over and over: one pass through all of them is an **epoch**. This file decides which faces are usable, how often each is shown, what random changes are made to it each time, and how it becomes numbers for PyTorch.

```
usable faces (manifest − no face − duplicates)
     │  sampling_weights: rare bands, and the years around the age limits, shown more often
     ▼
for each face:  decode (256×256) → Augment: zoom/turn/shift/flip → colour → webcam damage → 224×224
                                  (validation: just shrink to 224×224, no randomness)
     ▼
(pixels, target distribution, band low, band high)  → a batch of 128 → the GPU
```

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-10
Standard-library tools: `csv`, `zipfile`, `Counter`, `dataclass` and `field`, `Path`, and `Any` ("any type").

@@ 12-16
OpenCV, NumPy, PyTorch, NumPy's array type, and PyTorch's `Dataset`, the standard shape for "a list of training examples".

@@ 18-20
From the ML package: manifests and the target distributions. From the vision library: the `Image` type and the decoder.

@@ 22
`INPUT_SIZE = 224` — the model sees faces at 224×224 pixels, the framing the service uses.

@@ 23-24
**`FOCUS`** — ages 10 to 25, where the age limits that matter (13, 16, 18, 21) all lie. Bands touching these years are shown twice as often (`FOCUS_BOOST`), as the design specifies: a model that is merely good on average, but vague around 18, would be no use.

@@ 26
`Sample` — the four things one training example consists of: pixels, target distribution, and the band's lower and upper ends.

@@ 29
**`usable_rows`** — the faces training may use.

@@ 30-31
Every face that preparation found and aligned (§5.2.3).

@@ 32-33
Every copy that duplicate removal took out.

@@ 34-35
The manifest's rows, minus both. For FairFace: 97,178 faces.

@@ 38-41
**`band_of`** — a row's age band as two numbers. An exact age is a one-year band; the open band "70 and over" ends at 100.

@@ 44
**`sampling_weights`** — how likely each face is to be picked when a batch is drawn. FairFace's training split has 20,392 faces in their twenties but only 684 aged 70 and over; drawn evenly, the model would hardly ever see old faces and could do well by mostly guessing "twenties".

@@ 45-47
Count the faces in each band, and give each face a weight of 1 ÷ √(its band's size). Dividing by the size itself would show every band equally often — but then each of the 684 older faces would be seen 30 times as often as each face in its twenties, and the model would start memorising those few. The square root is a common middle way: rare bands are shown more, but not so much that their few faces wear out.

@@ 48-49
Double the weight of faces whose band touches ages 10–25.

@@ 50
Scale the weights to add up to 1.

@@ 53-54
**`fit`** — for validation: shrink the 256×256 face to 224×224. Because preparation used the service's framing, only larger (§5.2.3), this gives exactly the face the service would see.

@@ 57-58
**`Augment`** — random changes for training (**data augmentation**, §2.15). Each time a face is shown it looks slightly different, so the model can't simply memorise 69,000 particular pictures; it has to learn what ageing looks like. The changes are ones a real face really goes through — a slightly different pose, other light, another camera — never ones that would change how old someone looks.

@@ 60-63
The output size, an optional fixed seed (for tests), and the random-number generator, created later.

@@ 65-71
**`rng`** — the generator, created on first use. The comment explains why: the loader starts several processes, each with a copy of this object. A generator made beforehand would be copied too, and every process would then make the *same* random changes. Created inside each process from PyTorch's per-process seed (`torch.initial_seed()`), each gets its own.

@@ 73-74
**`chance`** — true with the given probability: `chance(0.3)` is true about 3 times in 10.

@@ 76-77
The full change: geometry, then colour, then webcam damage.

@@ 79
**`geometry`** — zoom, turn, shift and maybe mirror, all at once.

@@ 80-82
Zoom between 92 % and 108 % (while shrinking 256 to 224), and turn up to 10° either way.

@@ 83
`getRotationMatrix2D` builds the **affine matrix** (§4.9) that turns and zooms about the picture's centre.

@@ 84-85
Shift the result so the centre of the face lands at the centre of the 224×224 output, plus a random nudge of up to 4 % in each direction.

@@ 86-88
Apply all of it in one step. Doing the zoom, turn and shift as a single warp is much faster than doing them one after another — the first version used separate steps and spent most of its time there (§5.2.4). Where the turn uncovers a corner, `BORDER_REFLECT_101` fills it with a mirror image of the nearby pixels.

@@ 89-91
Half the time, mirror the face left to right: a mirrored face is just as old.

@@ 93
**`colour`** — different light and cameras.

@@ 94-95
Work in decimals, and compute the **grey** version of each pixel (the standard weights for blue, green and red: the eye is most sensitive to green).

@@ 96
**Saturation**: move each pixel towards or away from its own grey, by 70 % to 130 %: from washed-out to vivid colour.

@@ 97
**Contrast**: stretch or squash all values around the average brightness.

@@ 98
**Brightness**: scale everything by 70 % to 130 %.

@@ 99
Keep the values within 0–255, and return to whole numbers.

@@ 101
**`webcam`** — damage a webcam does, each kind with its own probability. Training on such damage is how the model is prepared for the gap between dataset photos and live frames (§3.3).

@@ 102-106
Half the time, change the **gamma** — the curve from dark to light — between 0.6 and 1.4: like a camera that brightens shadows or a dim room. A lookup table (`LUT`) maps each of the 256 possible values to its new value at once.

@@ 107-108
A third of the time, blur slightly, like a camera slightly out of focus.

@@ 109-110
One time in five, **motion blur**, like a hand moving the phone.

@@ 111-112
A third of the time, shrink and enlarge again, like a low-resolution camera.

@@ 113-115
A third of the time, add **sensor noise**: random speckle of strength 2 to 10, like a camera in poor light.

@@ 116-118
Half the time, save as JPEG at a quality between 30 and 90 and decode again, like a frame compressed for upload.

@@ 119
Return the result as a tidy block of whole numbers.

@@ 121
**`motion_blur`** — smear the picture along a line.

@@ 122-124
A **kernel**: a small square grid of 3 to 9 pixels with a single horizontal line of ones across its middle.

@@ 125-126
Turn that line to a random angle.

@@ 127
`filter2D` slides the kernel over the picture, replacing each pixel by the average of the pixels along the line — a smear in that direction. Dividing by the kernel's total keeps the overall brightness unchanged.

@@ 129-134
**`downscale`** — shrink to between a quarter and 60 % of the size (never below 8 pixels), then enlarge back: the fine detail is lost, as with a cheap camera.

@@ 137-139
**`to_tensor`** — turn OpenCV's blue-green-red picture into red-green-blue, and rearrange it from *height, width, colour* into PyTorch's *colour, height, width* (`permute`). The pixels stay whole numbers from 0 to 255; the model scales them itself (`model.py`).

@@ 142-145
**`FaceDataset`** — the faces of one split, in the shape PyTorch's loader expects. The docstring records a lesson from the first full training run (§5.2.4). The loader starts its helper processes one after another, and on Windows each must receive everything it is sent before the next can start. When each was sent the full list of 69,000 rows, the next process waited until the previous one had finished loading PyTorch: 14 processes took over a minute to start. Now each is sent only a short description, reads the rows itself, and all start together in about 11 seconds.

@@ 147-152
The description: the dataset's name, the split, the zip of prepared faces, the random changes (none for validation), the output size, and an optional limit on how many faces to use (for quick trials).

@@ 153-154
Two things each process fills in for itself: the rows, once read, and the open zip file. `field(default=None, repr=False)` gives them a starting value of "nothing yet" and leaves them out when the object is printed.

@@ 156-161
**`rows`** — the split's usable faces, read on first use and then remembered.

@@ 163-164
`__getstate__` — what Python sends when it copies this object to another process (**pickling**). Everything except the rows and the open file, which each process makes for itself.

@@ 166-167
`__len__` — how many examples there are.

@@ 169
`__getitem__` — example number `index`, called by the loader processes.

@@ 170-172
The first time, inside each loader process: keep OpenCV to one thread (the processes already share out the cores), and open the zip.

@@ 173-175
Read and decode the face, then either change it randomly (training) or just shrink it (validation).

@@ 176-178
Return the pixels, the target distribution, and the band's two ends as tensors.
