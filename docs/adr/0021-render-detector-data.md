# ADR-0021: The render detector's data — made by us, real faces only with consent

- **Status:** Accepted — 2026-11-02 (the owner's decision D22: "make our own, and ask")

## Context
Liveness level 6 needs a classifier that tells a real face in front of the camera from a computer-rendered one. No
dataset found allows training a model for a service *and* shows renders filmed by a camera
([render-detector-datasets.md](../reports/render-detector-datasets.md)). [ADR-0013](0013-no-biometric-storage.md) keeps
the **service** from storing any face; a training set is a different thing and needs its own rules.

## Decision
- **Renders are ours.** Made-up people only, built in Blender with MakeHuman's CC0 assets (MPFB). Blender's output and
  CC0 assets carry no restriction, so a model trained on them could serve a launch. No render may be made to look like
  a real, identifiable person.
- **Two kinds of attack:** a render *shown on a screen and filmed by a camera* (`screen_render`), and the render's own
  frames, as a virtual camera would *inject* them (`injected_render`).
- **Real faces only with written consent** (`real`): the owner first, then volunteers (O4), each with a signed
  [consent form](../data/consent-form.md) and an entry in a consent register. A clip of a real person is accepted
  only while that person's consent stands; withdrawing it deletes their clips and, at the next training, removes them
  from the model's data.
- **Where the data lives:** under `.datasets/render-detector/` on the owner's machine (on an encrypted disk), never in the
  repository, never uploaded, never part of an image or the service. No real person's frame is ever published, in the
  book or anywhere else.
- **Splits by person:** a person, real or made-up, is in exactly one of training, validation and test, so the test
  measures people the model has never seen.
- **In parallel, ask:** the authors of SynthASpoof and Deepfake Synthetic-20K are asked for terms that allow use in a
  service ([requests](../data/dataset-requests.md)); anything they allow is added to the licence register first.

## Consequences
- **Good:** every example's terms are known and ours; the model could ship.
- **Cost:** a small, narrow set at first (few people, cameras and rooms); filming takes the owner's time; the real side
  grows only as fast as volunteers come.
- **Not covered:** a real-time face swap of a real person (the swap tools found are research-only).

## Alternatives considered
Microsoft's research-only renders (no use in a service), waiting for a dataset (nothing found), and scraping
renders from the web (no consent, unknown licences) — rejected.
