# Fala (The Wave)

A hand-cranked kinetic souvenir: a terrace of Silesian familoks on ground that rolls like a
wave. Everything for this product lives in this folder.

## Status (2026-11-11)

**Step 2 of the brief, the concept checkpoint, is presented and waiting for the client's
approval. Do not model in detail until a look and a drive are approved.**

Recommended: Look 2 "Kolonia", drive A "Corkscrew shaft". Seven questions are open; they are
listed in section 10 of `docs/look-brief.md` (look, brick tone, crank ratio, lettering, rear
panel, ballast, filament brand). None has been answered yet.

After approval comes step 3, the motion proof: the bare mechanism as a parametric model,
simulated through full turns both ways with collision checks, plus a short animation.

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

- `cadkit` does not exist yet. `AGENTS.md` describes the target layout; the root `pyproject.toml`
  is not yet a uv workspace. Step 3 is the point to create `packages/cadkit` and to turn this
  folder into a workspace package (`pyproject.toml`, `src/fala/model.py`, `tests/`).
- The scripts in `concept/` are throwaway and are not the product model.
- `ruff` is not in the virtual environment; use `uvx ruff check --line-length 100`.
- Blender (through its MCP connection) and Snapmaker Orca are installed; neither has been used yet.
- Nothing has been committed. Commit only when the client asks.
- The reference photos in `research/refs/` are third-party material: keep them out of anything
  published or shipped (see `research/SOURCES.md`).
