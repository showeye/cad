# Fala (The Wave)

A hand-cranked kinetic souvenir: a terrace of Silesian familoks on ground that rolls like a
wave. Everything for this product lives in this folder.

## Status (2026-11-13)

The client approved **Look 1, Nikisz** and **Drive A, corkscrew shaft**, on 2026-11-13.
The drive comparison is complete; the next stage is a small contact rig and motion proof:

- [Drive comparison and recommendation](docs/drive-comparison.md)
- [Animated motion study](docs/img/drive_screening.gif)
- [Reproducible numerical results](docs/drive-screening.json)

A is the approved development direction; B remains a fallback if contact tests fail. Captured follower contact
and rigid-carriage compatibility need resolution before a full motion proof. This stage
makes no production-readiness, collision-free or durability claim.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The client brief, verbatim. Source of truth. Read this first. |
| `docs/look-brief.md` | The look brief: research, 25 references, stylisation, palette, motion, three looks, three drives, open questions, what could not be verified |
| `docs/design-notes.md` | Engineering reasoning for drive A that is not in the look brief: geometry, constraints, assembly, print plan, test-print ideas, rejected ideas |
| `docs/img/` | Concept renders, wave filmstrips and mechanism diagrams used by the look brief |
| `concept/look_concepts.py` | Throwaway massing models of the three looks, posed on the wave; sends them to the OCP viewer and renders PNGs |
| `concept/compose_sheets.py` | Builds the comparison sheet and filmstrips from those PNGs |
| `concept/mechanism_diagrams.py` | Schematic diagrams of the three drives; prints the wave numbers |
| `research/refs/` | Reference photos (familoks, mining damage, real prints) |
| `research/SOURCES.md` | Where each photo came from, with author and licence; extra text sources |
| `research/sheet_*.jpg` | Contact sheets of the reference photos |

## Regenerate the concept material

Run from the repository root:

```
uv run python projects/fala/concept/look_concepts.py --strip
uv run python projects/fala/concept/compose_sheets.py
uv run python projects/fala/concept/mechanism_diagrams.py
```

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939, and
`look_concepts.py` streams the three looks to it. Read `docs/look-brief.md` in the Markdown
preview.

## Repository notes for whoever continues

- `cadkit` and the uv workspace now exist. Fala is still a concept folder; register its
  product package when the drive is selected and prototype geometry is introduced.
- The scripts in `concept/` are throwaway and are not the product model.
- `ruff` and `pytest` are available through `uv run`.
- Blender (through its MCP connection) and Snapmaker Orca are installed; neither has been used yet.
- Nothing has been committed. Commit only when the client asks.
- The reference photos in `research/refs/` are third-party material: keep them out of anything
  published or shipped (see `research/SOURCES.md`).

## Handoff / next session

Read `AGENTS.md`, `docs/brief.md` and `docs/drive-comparison.md` first.
Proceed with Nikisz and drive A; do not ask for drive selection again.
Approval is for development, not a claim that the mechanism is proven.

Next work: solve real helix/follower contact, compare broad and narrow contact pads, and
provide the required sliding freedom for a rigid two-support carriage. Build a small
parametric two-carriage contact rig before decorating the full terrace. Sweep a full
rotation both ways, check contact and interference, and prepare a bare mechanism animation.
Then provide U1 test parts and a fit ladder.

Current evidence: `engineering/compare_drives.py` generates a prescribed-path GIF and
1,440-sample numerical screening report; four tests in `tests/test_drive_screening.py` pass.
These do not establish contact, collision clearance, friction, durability or production fit.
Narrow-pad capture can have 1.42 mm play; fixed-X support sampling implies about 0.12 mm
of varying support distance. Resolve both in the real geometry.

Keep a provisional 3:1 crank ratio, explicitly unconfirmed. Lettering, rear panel, ballast
and filament brand remain open; they need not block the contact rig. All Fala materials
stay under this directory. No commits unless requested.
