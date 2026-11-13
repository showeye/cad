# Serce na węgiel (Coal-Powered Heart)

A kinetic Silesian souvenir: a heart of coal that opens to show a warm Silesian kitchen inside.
Everything for this product lives in this folder.

## Status (2026-11-13, end of the third session)

**Step 3 of the brief, the motion proof, is finished and waits for the client's review:
`docs/motion-proof.md`. Nothing of it is committed. Stop here until the client has answered.**

What exists:

- `projects/serce` is a `cadkit` package (`serce`, version 0.2.0, variant `honey`): the real
  faceted Bryła heart split into two wings and a back half, the hinges, and the whole drive in the
  base. 73 named solids, 12 printed parts, every fit a parameter. The room is a stand-in.
- The proof is a test suite (24 tests, all pass): no overlap at 126 positions of a full turn, a
  free assembly path, measured seams, the closed heart shows nothing of the inside, the open room
  is fully in view, the ring torque stays in a band, the drive is hidden closed, half open and
  open.
- The one defect of the second session, a glimpse of the slider past a hinge root with the wings
  open, is fixed by a small plug in each assembly keyhole. It rides in on the lever and is held
  by the wing's collar and the back half, with no glue, press fit or screw.
- The build with renders and the looping film is in `dist/serce/0.2.0/honey/`; the pictures of
  the review document are in `docs/img/motion/`.

Approved earlier (step 2): Look 1 "Bryła", opening A "Skrzydła" (wings), honey lining, about 150 g
of steel ballast, a room with no figures and no religious objects, an edition tag under the foot.

Asked in the review document (section 6), not answered yet:

- The rounded ridge along each flank (open since the concept), the round hairline at its foot,
  the long ridge of the coal bed, 4 mm more height (108 mm), the idle first 23° of turn, the
  firmer last 23° of closing.
- The filament choice and what "cost" includes in the price rule.
- The go-ahead for the test prints (step 4).

**An earlier attempt at the later steps was rejected by the client:** "The heart was just one box,
with gaps. It simply was not reflecting the idea." It is on the branch `projects/heart/codex`. Do
not build on it. Its build outputs `dist/serce/0.1.0` and `dist/serce-coupons` are stale; this
model writes to `dist/serce/0.2.0`.

## How to continue

1. Read the client's answers to the nine questions of `docs/motion-proof.md`, section 6.
2. Read `docs/design-notes.md`, **section 9**: the design as built and why (9.2), the open points
   (9.3), what the tests prove (9.4), what comes next (9.5), the keyhole plug and its one limit
   (9.6). Sections 1 to 8 are the earlier plan; `docs/brief.md` is the source of truth.
3. If the client rejects the flank ridge, the hairline or the long bed, that is a redesign first.
   Otherwise go on to step 4 of the brief, the test prints (design notes, section 8 and 9.5).

```
uv sync --all-packages
uv run pytest projects/serce                      # about four and a half minutes
uv run cadkit show serce -v honey                 # the model in the OCP viewer, closed
uv run cadkit build serce -v honey --render --animate    # two minutes
uv run python projects/serce/tools/motion_report.py      # pictures and numbers of the review
uv run python projects/serce/tools/root_sight.py         # dense rays down both roots, 20 minutes
```

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The client brief, verbatim. Source of truth. Read this first. |
| `docs/look-brief.md` | The approved look brief: research, 25 references, form, interior, palette, the opening, three looks, three openings, corrections, what could not be verified, decisions, stages |
| `docs/design-notes.md` | Engineering reasoning. Sections 1 to 8: the plan (decisions, the acceptance test set by the failed build, the hinge, planned parts, constraints, filament and cost, test prints). **Section 9: the motion proof as built, its open points and what comes next** |
| `pyproject.toml`, `src/serce/` | The product package; the modules are listed in design notes 9.1 |
| `tests/` | The motion proof as tests, and the geometry snapshot |
| `docs/motion-proof.md`, `docs/img/motion/` | **The review document of step 3 for the client, and its pictures** |
| `tools/motion_report.py` | Builds those pictures and the numbers the document quotes |
| `tools/root_sight.py` | Dense ray check of the two hinge roots (design notes 9.6) |
| `docs/img/` | Concept renders, opening strips and mechanism diagrams used by the look brief |
| `concept/heart_concept.py` | Throwaway massing geometry: the three looks, the room, the base, the three openings. `wing_parts()` returns the wings design sorted by what moves, with the hinge axes |
| `concept/look_concepts.py` | Builds the concept scenes, sends them to the OCP viewer, exports STL files to `concept/_build/` |
| `concept/render_blender.py` | Blender side: renders the scenes to `concept/_build/render/` |
| `concept/compose_sheets.py` | Builds the comparison sheets and strips in `docs/img/` from the renders |
| `concept/mechanism_diagrams.py` | Schematic diagrams of the three openings; prints the drive numbers of A |
| `research/refs/` | Reference photos (coal, carving, heart forms, Silesian homes, reveals, prints, market) |
| `research/SOURCES.md` | Where each photo and text source came from, with licence and how it was checked |
| `research/sheet_*.jpg` | Contact sheets of the reference photos |

## Regenerate the concept material

Run from the repository root (about three minutes in all):

```
uv run python projects/serce/concept/look_concepts.py
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P projects/serce/concept/render_blender.py
uv run python projects/serce/concept/compose_sheets.py
uv run python projects/serce/concept/mechanism_diagrams.py
```

`concept/_build/` is ignored by git.

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939, and
`look_concepts.py` streams the scenes to it. Read the documents in the Markdown preview.

## Notes for whoever continues

- To pose the model: `build(Params(turn=120))`. `turn` is the ring angle: 0 closed, 180 open.
- The ray-cast tests take most of the test time. To trace a sight line that one of them reports,
  step along the ray from the seen point towards the viewer and ask every solid `is_inside`: the
  ray should have met a solid, and where it meets none is the opening.

- The scripts in `concept/` are throwaway and are not the product model. They have four
  outstanding `ruff` findings and some long lines, left as they were.
- The mechanism diagram of A still draws the first idea of the drive. The plan in
  `docs/design-notes.md` is newer where they differ.
- Commit only when the client asks.
- The reference photos in `research/refs/` are third-party material: keep them out of anything
  published or shipped (see `research/SOURCES.md`).
