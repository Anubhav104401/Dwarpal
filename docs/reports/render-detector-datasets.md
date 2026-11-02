# Datasets for the render detector — options for the owner

**Asked:** 2 Nov 2026 (the owner chose "look for a dataset") · **Unblocks:** liveness level 6 (Phase 9): telling a
real face in front of the camera from a computer-rendered one — a game-engine avatar, or a face swapped onto someone
else live. **Nothing has been downloaded.** Each option below needs your decision, and most need you to accept terms
yourself (an account, or a signed agreement), which I can't do.

## What the detector needs

Two kinds of example, each with many people, cameras and rooms:

1. **Real faces in front of a camera** — we have the owner's own captures (Phase 3) and the public test sets used for
   the PAD model, but not enough people (O4).
2. **Rendered or swapped faces shown to, or fed into, a camera** — none in the project.

A licence that allows training a model **that Dwarpal then uses in a service** is the hard part. Dwarpal's code is
Apache-2.0 and public; whether the service itself will be run commercially is yours to say, and it decides most of
the answers below.

## What I found

| Dataset | What it is | Licence | Fit |
| :-- | :-- | :-- | :-- |
| [DigiFace-1M](https://github.com/microsoft/DigiFace1M) (Microsoft) | 1.2 M rendered faces of 110 k made-up people, from a graphics pipeline; no real person in it | **Non-commercial research** only | Good *rendered* examples, but stills, not filmed by a camera; no commercial use |
| [Face Synthetics](https://github.com/microsoft/FaceSynthetics) (Microsoft) | 100 k rendered faces, 512 × 512, ~32 GB (samples of 100 and 1,000 images: 34 MB, 320 MB) | **Non-commercial research** only | As DigiFace-1M |
| [SynthASpoof](https://arxiv.org/abs/2303.02660) | 25 k synthetic "real" faces and 78.8 k attacks made by showing them to cameras | The dataset's own licence isn't stated where I looked (the paper is CC BY-NC-SA 4.0); its authors would have to be asked | Closest in kind (attacks filmed by a camera), but the attacks are prints and replays, not renders |
| [Deepfake-Eval-2024](https://huggingface.co/datasets/nuriachandra/Deepfake-Eval-2024/blob/main/README.md) | Deepfakes collected from social media in 2024 | CC BY-SA 4.0; its card says commercial use is allowed, training generators isn't | Real-world swaps, but videos posted online, not live to a camera; the share-alike terms reach what is made from it |
| [Deepfake Synthetic-20K](https://ieee-dataport.org/documents/deepfake-synthetic-20k-dataset) | 20 k StyleGAN-2 faces | Listed as CC BY 4.0, but described for academic use: ask the publisher | Generated stills, not renders shown to a camera |
| FaceForensics++, Celeb-DF, DFDC, and sets derived from them ([RLDF](https://arxiv.org/html/2610.21438v1), [SynthForensics](https://arxiv.org/pdf/2602.04939)) | The usual face-swap benchmarks | Research only, or CC BY-NC; the source videos keep their own limits | Not usable for a service |
| Face anti-spoofing sets ([CelebA-Spoof, HiFiMask, WMCA, SiW-M](https://iapr-tc4.org/face-datasets/)) | Prints, replays, masks | Each owner's agreement, mostly research only; SiW-M reported unavailable; CelebA-Spoof scraped from the web | Masks, not renders |

**Summary:** no dataset I found allows training a model for use in a commercial service *and* contains rendered faces
filmed by a camera. The [face-analysis models](https://www.insightface.ai/) often used to make swaps are research-only
too, so making swaps ourselves with them isn't open either.

## Options

1. **Research only, for now.** If Dwarpal stays a non-commercial project, DigiFace-1M or Face Synthetics (start with the
   1,000-image sample, 320 MB) shown on a screen to our cameras would give a first measurement. You'd accept
   Microsoft's licence; a model trained this way couldn't later serve a commercial launch without retraining.
2. **Ask.** Write to SynthASpoof's and Deepfake Synthetic-20K's authors for terms that allow use in a service. Slow,
   but the best fit if they agree.
3. **Make our own, with consent.** Render made-up faces with an engine whose licence allows it (three.js is already
   approved; Blender is GPL, and its output is ours), and film them on screens and through a virtual camera; add
   consented volunteers for the real side (O4). Narrow at first, but every example would be ours to use.
4. **Keep deferring.** The PAD model already refuses screen replays and prints; a rendered face shown on a screen should look
   like any other screen replay to it (not yet measured). What isn't covered is a render fed straight into the browser through a *virtual camera*, which
   no image model catches well — it needs signals from the device instead (planned: none yet).

My suggestion is **3, starting small**, plus **2** in parallel: it keeps every example ours, and it's the only route
that ends with a model a launch could use.
