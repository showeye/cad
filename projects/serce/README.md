# Serce na węgiel (Coal-Powered Heart)

A kinetic Silesian souvenir: a heart of coal that opens to show a warm Silesian kitchen inside.
Everything for this product lives in this folder.

## Status (2026-11-13)

**Step 2 of the brief, the concept checkpoint, is approved. The next stage is step 3, the motion
proof. No product geometry exists yet.**

Approved: Look 1 "Bryła", opening A "Skrzydła" (wings), honey lining, about 150 g of steel
ballast, a room with no figures and no religious objects, an edition tag under the foot. All
decisions are in section 12 of `docs/look-brief.md`.

Done since the approval: the client saw that the wings overlapped the heart in the concept
pictures. The hinge in the concept model is corrected (a barrel on each flank instead of a pivot
deep in the wall), the model shows no overlap at any point of the opening, and every concept image
was rendered again. The corrected heart has a rounded ridge along each flank; **the client has not
yet said whether that ridge is acceptable.**

Still open:

- The filament choice (probably the colours in `../blend/filaments/README.md`).
- What "cost" includes in the price rule (retail about 2 × cost, 25% to the retailer).
- The points listed as "still open" and "not designed yet" in `docs/design-notes.md`.

**An earlier attempt at the later steps was rejected by the client:** "The heart was just one box,
with gaps. It simply was not reflecting the idea." It is on the branch `projects/heart/codex`. Do
not build on it. Its leftovers in this working copy are untracked and ignored:
`src/serce/__pycache__`, `tests/__pycache__`, and `dist/serce` and `dist/serce-coupons` in the
repository root.

## How to start the next stage

1. Read `docs/brief.md` (step 3 and the definition of done), then `docs/design-notes.md` whole. It
   holds the hinge geometry, the planned parts, the kinematics, the space constraints found so
   far, and what the motion proof has to show.
2. Turn this folder into a workspace package on the pattern of `projects/carnall`, and add it to
   the workspace members and test paths in the root `pyproject.toml`.
3. Build the real faceted heart, not a box, and prove the motion with tests before rendering.
4. Stop for the client's review when the motion proof is done.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The client brief, verbatim. Source of truth. Read this first. |
| `docs/look-brief.md` | The approved look brief: research, 25 references, form, interior, palette, the opening, three looks, three openings, corrections, what could not be verified, decisions, stages |
| `docs/design-notes.md` | Engineering reasoning for the motion proof: decisions, the acceptance test set by the failed build, the wing collision and the hinge, planned parts and kinematics, constraints, what to prove, filament and cost, test prints |
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

- The scripts in `concept/` are throwaway and are not the product model. They have four
  outstanding `ruff` findings and some long lines, left as they were.
- The mechanism diagram of A still draws the first idea of the drive. The plan in
  `docs/design-notes.md` is newer where they differ.
- Commit only when the client asks.
- The reference photos in `research/refs/` are third-party material: keep them out of anything
  published or shipped (see `research/SOURCES.md`).
