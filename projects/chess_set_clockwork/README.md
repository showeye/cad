# Clockwork chess set

A 3D-printed chess set in the style of skeleton clocks, where each piece holds clockwork parts
that do something. Everything for this product lives in this folder.

## Status (2026-11-13, second session)

**The knight is built in CAD as a first working model: `clockwork_knight` 0.1.0, variant
`playing`. Nothing is printed. The other five pieces are not started. The work of this
session is not committed.**

- The client picked the knight as the set's signature piece and asked for it to be built.
- The head rears 28.65° through the first 3 mm of a lift and bows when the piece is set
  down. A weighted plunger in the base drives a rack, a pinion, the chest wheel and the mane,
  which is a slice of a gear and one part with the head.
- Six printed parts, four red jewel rings, six steel pins. Base Ø35 mm, 55.6 mm tall, 23.7 g.
- 13 tests pass: the snapshot, and 12 on the motion, clearances, stops, balance and assembly.
- `cadkit` gained a rack (`features/gears.py`: `rack`, `rack_outline`, `rack_offset`).

**The three decisions in section 6 of the brief are still not answered.** The knight
assumes the brief's recommendations: steel pins allowed, playing size, generous fits. See
`docs/knight-design-notes.md`, section 2, for what changes if the client decides otherwise.

What is not as it should be yet (design notes, section 10):

- No test print: every fit is a starting value.
- Surfaces are plain. The outlines work and balance; the look needs its own pass.
- The chest wheel's spokes stand on a web, so the rack and pinion do not show through it.

## How to continue

1. Read `docs/brief.md` (the idea and the open decisions), then `docs/knight-design-notes.md`
   (the knight as built, the figures, assembly order, what was dropped, open points).
2. Look at the knight: the stills and films in `docs/img/knight/`, or live in the OCP viewer.
3. Get the client's view of the knight and their answers to the brief's section 6.
4. Then either test prints of the knight (design notes, section 11) or the next piece. The
   brief recommends the pawn next: the tightest fit, and sixteen of them. Base, plunger and
   the helpers in `_shared.py` should be generalised when the second piece is built.

```
uv sync --all-packages
uv run pytest projects/chess_set_clockwork           # 10 seconds
uv run cadkit show clockwork_knight -v playing       # the model in the OCP viewer (port 3939)
uv run cadkit build clockwork_knight -v playing --render    # exports and stills
uv run cadkit build clockwork_knight -v playing --animate   # adds the two looping films
```

Run `uv` from the repository root, not from this folder. Outputs go to
`dist/clockwork_knight/0.1.0/playing/` at the repository root.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The idea, the verdict, the recommended concept, open decisions and how the estimates were made |
| `docs/knight-design-notes.md` | The knight as built: how it works, parts, steel, figures, assembly, open points |
| `docs/img/knight/` | Stills and films of the knight at 0.1.0 |
| `A_skeleton_clocks.png` | The client's concept picture: style reference only, its mechanisms do not work as drawn |
| `src/chess_set_clockwork/knight.py` | Parameters, the variant, `build()`, `balance()`, render settings and film poses |
| `src/chess_set_clockwork/_knight_layout.py` | Every level, centre and angle derived from the parameters; the motion |
| `src/chess_set_clockwork/_knight_parts.py` | The solids: base, plates, wheel, head, plunger, jewels, steel |
| `src/chess_set_clockwork/_shared.py` | Drawing helpers for pieces built from flat plates |
| `tests/` | Snapshot of the variant and the motion tests |

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939. Commit only
when the client asks.
