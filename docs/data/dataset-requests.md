# Asking dataset authors for terms — drafts for the owner to send

**Decision:** [ADR-0021](../adr/0021-render-detector-data.md) (D22, 2 Nov 2026: "make our own, and ask"). These are
drafts: **the owner sends them**, from their own address, after checking each contact on the dataset's own page (no
address here is guessed). Record each answer in the table at the end; anything allowed goes into the licence register
(`ml/datasets.toml`) before it is downloaded.

## 1. SynthASpoof

**To:** the corresponding author of *SynthASpoof: Developing Face Presentation Attack Detection Based on Privacy-friendly
Synthetic Data* (Meiling Fang, Marco Huber, Naser Damer; [arXiv 2303.02660](https://arxiv.org/abs/2303.02660)) — the
address is in the paper's PDF.

> **Subject:** SynthASpoof — terms for use in a deployed age-assurance service
>
> Dear Dr Fang,
>
> I run Dwarpal, an open-source (Apache-2.0) age-assurance service that protects minors online without storing anyone's
> face: <https://github.com/Anubhav104401/Dwarpal>. Its liveness checks include a presentation-attack model, and we are
> building a detector for computer-rendered faces.
>
> SynthASpoof is the closest dataset to what we need, and it is made of synthetic identities, which fits our privacy
> rules. I couldn't find the licence of the dataset itself (the paper is CC BY-NC-SA 4.0). Could you tell me its terms,
> and in particular whether a model trained on it may be used in a service that might be run commercially? If that is
> not allowed by default, would you consider a licence for it, and on what conditions?
>
> We would of course cite the paper, and I am happy to share our evaluation results.
>
> Kind regards,
> [name], Dwarpal

## 2. Deepfake Synthetic-20K

**To:** the dataset's submitter, through its page on [IEEE DataPort](https://ieee-dataport.org/documents/deepfake-synthetic-20k-dataset)
(the page's contact link, or the address in its documentation).

> **Subject:** Deepfake Synthetic-20K — use in a deployed service under CC BY 4.0?
>
> Dear authors,
>
> I run Dwarpal, an open-source (Apache-2.0) age-assurance service: <https://github.com/Anubhav104401/Dwarpal>. We are
> building a detector for computer-generated faces in its liveness check.
>
> IEEE DataPort lists Deepfake Synthetic-20K under CC BY 4.0, while its description mentions academic use. Could you
> confirm which applies — in particular, whether a model trained on it may be used in a service that might be run
> commercially, with attribution?
>
> Thank you,
> [name], Dwarpal

## Answers

| Dataset | Sent on | Answer | Allowed use | In the register |
| :-- | :-- | :-- | :-- | :-- |
| SynthASpoof | — | — | — | — |
| Deepfake Synthetic-20K | — | — | — | — |
