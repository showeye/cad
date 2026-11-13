# Fala (The Wave)

A hand-cranked kinetic souvenir: a terrace of Silesian familoks on ground that rolls like a
wave. Everything for this product lives in this folder.

## Status (2026-11-13, end of the fourth session)

**Step 3 of the brief, the motion proof, is written up and waits for the client's review:
`docs/motion-proof.md`. Stop here until the client has answered it. The work of the third
and fourth sessions is not committed.**

What exists:

- `projects/fala` is a `cadkit` package (`fala`, version 0.4.0, variant `nikisz`): the whole
  moving system as 23 named solids. Base, rear panel, corkscrew cam with its gear, pinion,
  handwheel, knob, eight sleds, eight houses and the steel axle. The mechanism is real
  geometry with every fit a parameter; the houses are plain Nikisz volumes on real ground
  blocks. Size 224 x 67 x 93 mm.
- `docs/motion-proof.md`: the report for the client, with the two films (the wave, and the
  bare mechanism), the evidence for each thing the brief asks of this step, what is not as
  it should be yet, and seven decisions to confirm.
- `docs/motion-proof-checks.json`: every figure the report quotes, written by
  `tools/motion_proof.py checks`.
- 27 tests pass, none is expected to fail.

What the model shows (details and method in the report):

- No part runs into another at 72 positions through one pass of the wave.
- A force model (`_statics.py`): every house rides by its own weight up to a friction of
  0.25; the cam takes the houses along up to 0.55; the handwheel needs about 0.1 N.
- Nothing of the mechanism is in view from the front, three-quarter views or above
  (`_hidden.py`, full sweep: 12 positions, 152 directions).
- No line of sight passes between the walls of two houses (`_gaps.py`).
- Every part goes in along a clear path. A house goes in while its sled stands on the crest
  of the wave; a third of a turn of the handwheel brings the next one up.

What the fourth session did, without changing the geometry:

- **The houses can be put in from above.** This was the open defect. The cause was the
  path, not the parts: at one fixed crank angle neighbours lean differently, and the facade
  plates and block edges of the house already in place lean into the way. On the crest the
  house is upright and its left neighbour leans away.
- **The full visibility sweep was run on the final geometry: clean.**
- **The gaps between houses were measured,** which found two things for the client
  (open points 2 and 3 in the design notes): a slit of sky up to 1.9 mm at the stepped
  roofline, and a 0.5 mm slot at pavement level that lets light through when the eye is
  level with the pavement.
- The films and stills were rendered and the report written. `cadkit` gained extra films
  per model (`films` in the presentation) and `visibility.through`.

Next, after the client's answers:

1. Apply what the client decides (the seven decisions at the end of the report). If the
   pavement-level slot is to be closed now, that is a change to the ground block: bump the
   version, regenerate the snapshot, rerun `tools/motion_proof.py checks`.
2. Step 4 of the brief, the test prints: parts that measure friction on the U1's own
   surfaces and check the riskiest fits, plus one sample house section. The design notes
   list ideas ("Ideas for the test prints").

Decisions this work rests on, to confirm with the client (also in the report):

- **Look 1 "Nikisz" and drive A "corkscrew".** The approval is recorded only on the branch
  `projects/fala/codex` (2026-11-13). The look brief on `main` recommended Look 2.
- Three turns of the handwheel per pass of the wave (the look brief's recommendation; never
  answered).
- The base is 67 mm deep, where the concept had 60 and the brief allows about 70.
- A small fin behind each house shows from the back.
- Two of the eight houses are end-of-terrace parts, not interchangeable with the other six.
- Friction: if the test prints measure more than about 0.25 dry, the cam and the guide beads
  need a lubricant at assembly.
- The roofline slit: accept it, or close it in the full design.

**An earlier attempt was reviewed and set aside.** The branch `projects/fala/codex` built a
two-carriage bench rig with a fit ladder, in place of the motion proof. The review found that
its guides allow 2 to 5 mm of rocking at roof height, its pads bear on sharp edges, and each
house would need a non-standard shoulder screw. Do not build on it. Its outputs in
`projects/fala/dist/fala/0.1.0` and `0.2.0` are stale; this model writes to
`dist/fala/0.4.0/nikisz/` at the repository root.

## How to continue

1. Read `docs/brief.md` (source of truth), then `docs/motion-proof.md` (the state, as the
   client sees it), then `docs/design-notes.md`, last section "Motion proof: as built": the
   design and why, the numbers, the open points, what was tried and dropped. The sections
   before it are the earlier plan.
2. Look at the model: the films and stills in `docs/img/motion/`, or live in the OCP viewer.

```
uv sync --all-packages
uv run pytest projects/fala                  # about 2.5 minutes
uv run cadkit show fala -v nikisz            # the model in the OCP viewer (port 3939)
uv run cadkit build fala -v nikisz --render  # exports and stills, 40 seconds
uv run cadkit build fala -v nikisz --animate # adds the two looping films, 3 minutes
uv run python projects/fala/tools/motion_proof.py checks  # the report's figures, 8 minutes
uv run python projects/fala/tools/motion_proof.py assets  # the report's pictures
```

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The client brief, verbatim. Source of truth |
| `docs/look-brief.md` | Research, 25 references, palette, three looks, three drives, open questions |
| `docs/motion-proof.md` | Step 3: the report for the client, with films, evidence and open decisions |
| `docs/motion-proof-checks.json` | The figures the report quotes |
| `docs/design-notes.md` | Engineering reasoning; its last section is the state of the motion proof |
| `docs/img/` | Concept renders and diagrams; `motion/` has the films and stills of the model at 0.4.0 |
| `src/fala/model.py` | Parameters, the variant, `build()`, render settings and film poses |
| `src/fala/_layout.py` | Every level, depth and station derived from the parameters |
| `src/fala/_wave.py` | The motion: pose of the cam and of each house for a crank angle |
| `src/fala/_parts.py` | Sled, cam with gear, crank, base, rear panel |
| `src/fala/_massing.py` | Ground block and the plain house volumes |
| `src/fala/_statics.py` | Forces on a house and torque at the crank, with friction |
| `src/fala/_hidden.py` | What a viewer in front can see of the mechanism |
| `src/fala/_gaps.py` | What shows between two houses: pavement joint, laps, daylight |
| `tools/motion_proof.py` | The long checks and the pictures for the report |
| `tests/` | Snapshot of the variant and the motion tests |
| `concept/` | Throwaway scripts of the concept checkpoint; not product geometry |
| `research/` | Reference photos and `SOURCES.md` (third-party material: keep it out of anything shipped) |

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939. Commit only
when the client asks.
