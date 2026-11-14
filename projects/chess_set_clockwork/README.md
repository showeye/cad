# Clockwork chess set

A 3D-printed chess set in the style of skeleton clocks, where each piece holds clockwork parts
that do something. Everything for this product lives in this folder.

## Status (2026-11-14, sixth session)

**Knight and king are built in CAD (`clockwork_knight` 0.1.0, `clockwork_king` 0.2.0). Nothing
is printed. The king's second build has the margin against friction that the first one lacked:
by its run model it ticks from rest with a friction of up to 0.51, where the first build
stalled from 0.26. It pays with a shorter tick: sixteen beats in about one second instead of
twenty in about two. The other four pieces are not started.**

Everything is committed: the knight (`eb985d0`), `cadkit`'s escapement (`aae0d45`), the
king's first build with its run model (`ffc89cc`), and the king's second build, which is
everything of the sixth session, in the commit after that.

### The knight

- The head rears 28.65° through the first 3 mm of a lift and bows when the piece is set
  down. A weighted plunger in the base drives a rack, a pinion, the chest wheel and the mane,
  which is a slice of a gear and one part with the head.
- Six printed parts, four red jewel rings, six steel pins. Base Ø35 mm, 55.6 mm tall, 23.7 g.
- 13 tests pass: the snapshot, and 12 on the motion, clearances, stops, balance and assembly.
- What is not as it should be yet (`docs/knight/design-notes.md`, section 10): no test print,
  plain surfaces, and the chest wheel's spokes stand on a web that hides the rack and pinion.

### The king

- It ticks after every move. Lifted, a plunger drops 4.0 mm and a pawl clicks under the next
  lobe of a small star. Set down, the king falls 0.9 mm onto the pawl and sinks the last
  3.1 mm under its own weight, which drives a recoil anchor escapement with a pendulum:
  sixteen beats per move, in 0.8 to 1.4 s depending on friction, and the pendulum swings on
  for about half a second.
- Ten printed parts, six red jewel rings, eight pieces of steel. Base Ø44 mm, 86.7 mm tall,
  38.1 g.
- 65 tests pass: the snapshot, 14 on the motion and 50 on the run.
- **By the run model it has margin now.** From a pendulum at rest it ticks with a friction of
  up to 0.51 lowered onto its pawl and 0.60 dropped onto it. With 0.2, 0.4 and 0.45 it ticks
  from wherever the pendulum is let go, and with 0.4 also with a loose guide, a tight one,
  and pallets that stand deeper than drawn. `docs/king/design-notes.md`, section 10.
- What changed from the first build (section 5): an escape wheel of 20 teeth instead of 25,
  pallets with flatter ramps that let a tooth go at 3° instead of 4°, a Ø1 wire as the
  anchor's arbor, a bob of Ø4 × 10 instead of Ø6 × 14, and a pendulum that hangs 1° off the
  anchor's centre to meet the king's lean. Frame, plates, train, pawl and plunger are as the
  client saw them.
- **The model is still all there is.** Every friction value is assumed, and the same model
  chose the dimensions. What is not as it should be yet (section 12): no test print; the tick
  is short and may sound like a rattle; the pallets stand only 0.41 mm in the wheel; the
  pawl falls in by its own weight only; the king leans 3° to the back while it sinks; the
  anchor's arch is 17 mm deep and looks heavy.

### This session

- The king was given margin against friction, with the run model as the judge. The goal was
  the one the fifth session set: tick with a friction of 0.4 from a pendulum at rest.
- What the fifth session expected to help most did less than it seemed. Hanging the pendulum
  in beat owed most of its gain to the kick the king's sudden lean gives the pendulum; from
  true rest it gave nothing. What decides is the pendulum's mass and its moment about the
  arbor, and how much of a tooth's push the pallets pass on.
- Margin and a long tick pull against each other, and the notes say why and by how much
  (section 5). A pendulum that would give both needs weight above its arbor, where the crown
  is.
- `king/model.py`: new parameters `anchor_pin` (the thin arbor) and `beat` (where the anchor
  stands when the pendulum hangs plumb); the escapement's, the bob's and the arch's values;
  version 0.2.0. The film runs at 33 frames a second with a friction of 0.3.
- `king/_layout.py` takes the anchor's rest from `beat`. `king/_parts.py` gives the anchor
  its own bores and cuts the pallets off at the arch. `king/_run.py` starts a run with the
  wheel pushed back if a pallet stands in a tooth, so a run can start from any angle.
- `_shared.py`: `jewel_ring` and `steel_pin` take a diameter. The knight is unchanged.
- `tests/king/test_run.py` is rewritten: 50 tests, among them thirty starts and three kings
  with fits that print differently. The king's snapshot is regenerated. `cadkit` is
  unchanged.
- Stills and films in `docs/king/img/` are of 0.2.0.
- The whole workspace passed after the last change to geometry: 267 tests, 8 minutes. Lint
  is clean in this project; `ruff check .` reports four findings in `projects/serce/concept/`
  that were there before.

## How to continue

1. Read `docs/king/design-notes.md`: section 5 for what the second build changed and what
   was learned, section 10 for what the run model finds, section 13 for the next steps in
   order. They are the client's view of the second build and of its shorter tick, then test
   prints, which are now the only way to learn more.
2. For how a piece is put together in code, read the king or the knight. Each piece is its own
   folder, `src/chess_set_clockwork/<piece>/`: `model.py` holds the parameters, `build()` and
   the film; `_layout.py` every derived position and the motion, the pawl's included;
   `_parts.py` the solids; the king's `_run.py` whether it ticks.
3. Still open from before: the client's view of the knight, and test prints of the knight
   (`docs/knight/design-notes.md`, section 11). The brief's advice to prototype the pawn early
   (the tightest fit, sixteen of them) also still stands.

```
uv sync --all-packages
uv run pytest projects/chess_set_clockwork           # 40 seconds
uv run pytest projects/chess_set_clockwork/tests/king/test_run.py    # the run model, 15 seconds
uv run pytest packages/cadkit/tests/test_escapement.py packages/cadkit/tests/test_escapement_run.py
uv run cadkit show clockwork_king -v playing         # the model in the OCP viewer (port 3939)
uv run cadkit build clockwork_king -v playing --render    # exports and stills, 1 minute
uv run cadkit build clockwork_king -v playing --animate   # adds the three films, 15 minutes
```

A move run through by hand, from the repository root:

```
uv run python -c "
from chess_set_clockwork.king.model import Params, ticking
ran = ticking(Params(), friction=0.4, pin_friction=0.4, angle=-5.0)
print(ran.finished, len(ran.beats), ran.swing())"
```

The same build commands with `clockwork_knight` give the knight. Run `uv` from the repository
root, not from this folder. Outputs go to `dist/<model>/<version>/playing/` at the repository
root.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The idea, the verdict, the recommended concept, the client's decisions and how the estimates were made |
| `docs/knight/design-notes.md` | The knight as built: how it works, parts, steel, figures, assembly, open points |
| `docs/king/design-notes.md` | The king as built: how it works, what changed from the paper design and between the two builds, parts, figures, what was checked and what the run model finds, open points, next steps |
| `docs/<piece>/img/` | Stills and films of the piece: the knight at 0.1.0, the king at 0.2.0 |
| `A_skeleton_clocks.png` | The client's concept picture: style reference only, its mechanisms do not work as drawn |
| `src/chess_set_clockwork/<piece>/model.py` | Parameters, the variant, `build()`, `balance()`, render settings and film poses |
| `src/chess_set_clockwork/<piece>/_layout.py` | Every level, centre and angle derived from the parameters; the motion |
| `src/chess_set_clockwork/<piece>/_parts.py` | The solids |
| `src/chess_set_clockwork/king/_run.py` | Whether the king ticks: masses from the solids, friction on the way to the escape wheel, one move run through |
| `src/chess_set_clockwork/_shared.py` | What every piece shares: drawing helpers, the base's body, feet, jewel rings, steel pins |
| `tests/<piece>/` | The piece's snapshot (`snapshots/`), model and motion tests; the king's run in `tests/king/test_run.py` |
| `packages/cadkit/src/cadkit/features/escapement.py` (repository root) | Recoil anchor escapement: wheel outline, pallets, and a check of how they meet |
| `packages/cadkit/src/cadkit/features/escapement_run.py` | The same escapement run with forces: torque, inertia, contact and dry friction |

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939. The king was
sent to it in the fourth session, at the client's request, and at the start of the fifth. In
the sixth session nothing listened on that port, so the second build was not sent.
Commit only when the client asks.
