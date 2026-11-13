# Fala (The Wave)

A hand-cranked kinetic souvenir: a terrace of Silesian familoks on ground that rolls like a
wave. Everything for this product lives in this folder.

## Status (2026-11-13, end of the second session)

**Step 3 of the brief, the motion proof, is in progress and not finished. Nothing of it is
committed. There is no review document for the client yet.**

What exists:

- `projects/fala` is a `cadkit` package (`fala`, version 0.3.0, variant `nikisz`): the whole
  moving system as 23 named solids. Base, rear panel, corkscrew cam with its gear, pinion,
  handwheel, knob, eight sleds, eight houses and the steel axle. The mechanism is real geometry
  with every fit a parameter; the houses are plain Nikisz volumes on real ground blocks.
- It builds, passes the workspace quality gate, and no part runs into another at 12 positions
  of one pass of the wave (three turns of the handwheel). Size 224 x 67 x 93 mm.
- A force model (`_statics.py`) gives the load on every guide point and the torque at the crank.
- 14 tests pass. One more is marked as an expected failure: the open defect below.
- Two additions to `cadkit`, both tested: `features/cams.py` (corkscrew cam and crowned pads,
  solved exactly) and `features/gears.py` (involute gears). Two fixes carried over from the
  rejected branch: the interference check no longer disturbs later exports, and STEP files no
  longer depend on how many assemblies the process exported before.

**The open defect.** Each house is kept upright by its own weight, which seats it on two guide
points. In the force model that holds up to a friction of about 0.3. Above it, the seat lets go
in part of the turn and the house may rock in its guide clearance; at 0.45 the guide drag
passes the house's weight. Dry printed PLA can reach those values. The design notes
("Motion proof: as built", open points) give the numbers and three ways forward. Decide this
first: it may move the sled's spine to the rear, which changes most of `_parts.py`.

Still to do for the motion proof, in order:

1. Settle the guide (above).
2. Prove that the mechanism is hidden from the front, three-quarter and counter-height views
   (`cadkit.visibility`), and check the two ends of the street, where the joint to the bookends
   is still open.
3. Check the assembly paths: sleds from above, cam and axle from the back, rear panel last.
4. Render the looping film and the bare-mechanism film, measure the gaps between houses, and
   write `docs/motion-proof.md` with the questions for the client.

Decisions this work rests on, to confirm with the client:

- **Look 1 "Nikisz" and drive A "corkscrew".** The approval is recorded only on the branch
  `projects/fala/codex` (2026-11-13). The look brief on `main` recommended Look 2.
- Three turns of the handwheel per pass of the wave (the look brief's recommendation; never
  answered).
- The base is 67 mm deep, where the concept had 60 and the brief allows about 70.
- A small fin behind each house shows from the back.

**An earlier attempt was reviewed and set aside.** The branch `projects/fala/codex` built a
two-carriage bench rig with a fit ladder, in place of the motion proof. The review found that
its guides allow 2 to 5 mm of rocking at roof height, its pads bear on sharp edges, and each
house would need a non-standard shoulder screw. Do not build on it. Its outputs in
`projects/fala/dist/fala/0.1.0` and `0.2.0` are stale; this model writes to
`dist/fala/0.3.0/nikisz/` at the repository root.

## How to continue

1. Read `docs/brief.md` (source of truth), then `docs/design-notes.md`, last section
   "Motion proof: as built": the design and why, the numbers, the open points, what was tried
   and dropped. The sections before it are the earlier plan.
2. Look at the model: `docs/img/motion/wip_*.jpg`, or live in the OCP viewer.

```
uv sync --all-packages
uv run pytest projects/fala                  # about 75 seconds
uv run cadkit show fala -v nikisz            # the model in the OCP viewer (port 3939)
uv run cadkit build fala -v nikisz --render  # exports and stills, 40 seconds
uv run cadkit build fala -v nikisz --animate # adds the looping film (not run yet)
```

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The client brief, verbatim. Source of truth |
| `docs/look-brief.md` | Research, 25 references, palette, three looks, three drives, open questions |
| `docs/design-notes.md` | Engineering reasoning; its last section is the state of the motion proof |
| `docs/img/` | Concept renders and diagrams; `motion/wip_*.jpg` are the current model |
| `src/fala/model.py` | Parameters, the variant, `build()`, render settings and film poses |
| `src/fala/_layout.py` | Every level, depth and station derived from the parameters |
| `src/fala/_wave.py` | The motion: pose of the cam and of each house for a crank angle |
| `src/fala/_parts.py` | Sled, cam with gear, crank, base, rear panel |
| `src/fala/_massing.py` | Ground block and the plain house volumes |
| `src/fala/_statics.py` | Forces on a house and torque at the crank, with friction |
| `tests/` | Snapshot of the variant and the motion tests |
| `concept/` | Throwaway scripts of the concept checkpoint; not product geometry |
| `research/` | Reference photos and `SOURCES.md` (third-party material: keep it out of anything shipped) |

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939. Commit only
when the client asks.
