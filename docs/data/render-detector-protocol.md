# Making the render detector's data — the protocol

**Decision:** [ADR-0021](../adr/0021-render-detector-data.md) (D22, 2 Nov 2026) · **Tool:** `uv run --package dwarpal-ml
python -m dwarpal_ml.renders` · **Where the data lives:** `.datasets/render-detector/` on the owner's machine, never in the
repository.

The detector answers one question about a face in front of the camera: **was it rendered by a computer?** It learns from
three kinds of clip:

| Kind | What it is | Label |
| :-- | :-- | :-: |
| `real` | A consenting person in front of a webcam, doing the liveness challenge as anyone would | real |
| `screen_render` | A made-up person rendered in Blender, played full-screen on a monitor or phone and filmed by a webcam | rendered |
| `injected_render` | The same render's frames themselves, as a virtual camera would feed them to the browser | rendered |

## First set: small on purpose

A first set is meant to tell us whether the idea works, not to ship:

- **Made-up people:** 40, varied in age (adults only: no render may look like a child), skin tone, sex, hair, glasses
  and beard. Each one gets an identity such as `render-007`.
- **Each render:** a 6-second clip of the challenge's movements: look ahead, turn left, turn right, look up, and back.
  Three lighting set-ups (soft front light, one side light, a dim room) → 120 clips.
- **Filming (`screen_render`):** each clip played on at least two screens (the laptop's own, a phone), filmed by at least
  two cameras (the laptop's webcam, a USB webcam), in two rooms → 480 clips at most. Vary the distance, the angle and
  the brightness.
- **Injected (`injected_render`):** the 120 clips' own frames, scaled to the webcam's size, with and without the
  compression a video call adds.
- **Real (`real`):** the owner first: 20 clips across the same cameras, rooms and lights. Volunteers later (O4), each
  with a signed [consent form](consent-form.md).

Splits are by person, decided by the tool: about 70 % training, 15 % validation and 15 % test. Nobody, real or rendered,
appears in two splits.

## Steps

1. **Software** (needs the owner's approval to download, decision D23): Blender 5.2 LTS, the MPFB extension
   and MakeHuman's CC0 system assets.
2. **Make the people.** In MPFB, start from a random human, vary it, and check that it doesn't look like anyone real.
   Save it as `render-NNN.blend`.
3. **Animate and render** the challenge's movements, 30 frames a second, 1280 × 720, as a PNG sequence per clip, into
   `.datasets/render-detector/renders/render-NNN/<light>/`.
4. **Import the injected clips:** `python -m dwarpal_ml.renders inject` copies every rendered sequence in as an
   `injected_render` clip.
5. **Film the screen clips:** point a webcam at the screen (a monitor, or a phone mirroring the computer), then
   `python -m dwarpal_ml.renders film .datasets/render-detector/renders/render-NNN/<light> --camera <name> --setting <screen-room-light>`.
   It shows the sequence full-screen and takes one camera frame per rendered frame, in step; the first frame stays up
   half a second while the camera adjusts to the screen.
6. **Film the real clips:** first add the person to the consent register (below), then
   `python -m dwarpal_ml.renders record --kind real --identity person-NNN --consent <consent id> ...`. The tool refuses
   a real clip without a standing consent.
7. **Check** with `python -m dwarpal_ml.renders check`: every clip has a known kind, every real clip a standing consent,
   no rendered clip claims a consent. Then `split`.

## The consent register

`.datasets/render-detector/consent.toml`, kept with the data and never committed. One entry per signed form (the paper
or the signed PDF is filed by the owner, not here):

```toml
[[consent]]
id = "c-001"
identity = "person-001"
given_on = 2026-11-03
withdrawn_on = ""          # a date here withdraws it
```

**Withdrawing:** put the date in `withdrawn_on`, then run `python -m dwarpal_ml.renders withdraw c-001`: it deletes that
person's clips. `check` fails while any clip of a withdrawn consent remains.

## What isn't covered yet

- A real-time face swap of a real person: the tools found are research-only.
- Phones as the camera, and more than one room per volunteer: later sets.
- How well the detector works: nothing is trained yet; the model will meet the same release gates as the others.
