---
fingerprint: 45125b254f2055e1
---
**Face matching** for the step-up check (§5.6.2): is the live person in the selfie the person whose photo is on the document? Without this, anyone could show someone else's passport.

The model is **SFace**, from OpenCV's model zoo (decision D7b, accepted knowing that it was trained on face datasets collected without consent).

!!! kid "Explain like I'm six — a face's fingerprint"
    The computer can't look at two faces the way you do. Instead it measures each face in 128 ways and writes the numbers down, like a fingerprint made of numbers. Two photos of the same person give almost the same numbers; two different people give different ones. Then it throws the numbers away.

@@ 1-3
The module's docstring: compare two faces with **SFace** — is the person in the selfie the person on the document? Each face becomes 128 numbers in memory; the two are compared and dropped. Nothing is stored, and the numbers can't be turned back into a face.

@@ 5
The project-wide type-hint setting.

@@ 7-12
`threading` (for a lock), `Path`, OpenCV, NumPy and NumPy's array type.

@@ 14-15
The image type and the `Face` found by YuNet, the face detector — whose five landmarks (eyes, nose, mouth corners) SFace uses to line a face up.

@@ 17-19
**`SAME_PERSON`** — the similarity at or above which two faces count as the same person: 0.363, the threshold OpenCV publishes for SFace (with which it scores 99.4 % on LFW, a standard benchmark of celebrity photos).

!!! honest "Honest limitation"
    LFW's pairs are photos of similar quality. A document's printed, often years-old photo against a webcam selfie is harder, and this threshold isn't yet measured for that. Until it is, it's a starting point, not a calibrated number.

@@ 22-29
**`FaceMatcher`** — load SFace from its file (with a clear message if the file is missing), and a lock: the OpenCV model object isn't safe to use from two threads at once, and the inference service runs several.

@@ 31-33
**`embed`** — turn one face into its *embedding*: SFace's 128 numbers describing it.

@@ 34
OpenCV's SFace expects the face as YuNet describes it: one row of 15 numbers — the box (x, y, width, height), the five landmarks' x and y, and the detector's score.

@@ 35-37
Under the lock: `alignCrop` turns and scales the face so the eyes are level and in fixed places, cut to 112 × 112 pixels, as SFace was trained; `feature` runs the network; the result becomes a flat array of 128 numbers.

@@ 39-41
**`similarity`** — the **cosine similarity** of two embeddings: how closely they point the same way. Picture each embedding as an arrow in 128 dimensions: the same face points (nearly) the same way, giving close to 1; unrelated faces point in unrelated directions, giving about 0. It is the dot product divided by both lengths; the tiny `1e-12` avoids dividing by zero.
