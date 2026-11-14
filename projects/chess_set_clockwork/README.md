# Clockwork chess set

A 3D-printed chess set in the style of skeleton clocks, where each piece holds clockwork parts
that do something. Everything for this product lives in this folder.

## Status (2026-11-14, fifth session)

**Knight and king are built in CAD (`clockwork_knight` 0.1.0, `clockwork_king` 0.1.0). Nothing
is printed. The king now has a run model, and by it the king as built has too little margin:
it ticks with a friction of 0.25 or less and stalls on its second beat from 0.26. The other
four pieces are not started.**

Committed: the knight (commit `eb985d0`). Not committed: everything of the third, fourth and
fifth sessions, which is the king, `cadkit`'s escapement and how it runs, the shared parts
and these documents.

### The knight

- The head rears 28.65° through the first 3 mm of a lift and bows when the piece is set
  down. A weighted plunger in the base drives a rack, a pinion, the chest wheel and the mane,
  which is a slice of a gear and one part with the head.
- Six printed parts, four red jewel rings, six steel pins. Base Ø35 mm, 55.6 mm tall, 23.7 g.
- 13 tests pass: the snapshot, and 12 on the motion, clearances, stops, balance and assembly.
- What is not as it should be yet (`docs/knight/design-notes.md`, section 10): no test print,
  plain surfaces, and the chest wheel's spokes stand on a web that hides the rack and pinion.

### The king

- It is meant to tick after every move. Lifted, a plunger drops 4.0 mm and a pawl clicks
  under the next lobe of a small star. Set down, the king falls 0.9 mm onto the pawl and
  sinks the last 3.1 mm under its own weight, which drives a recoil anchor escapement with a
  pendulum: twenty beats per move, in about 2.1 s.
- Ten printed parts, six red jewel rings, eight steel pins. Base Ø44 mm, 86.7 mm tall, 40.7 g.
- 30 tests pass: the snapshot, 14 on the motion and 15 on the run. The motion tests cover one
  lobe and twenty beats per move, the pawl carrying and clicking, collisions through a move,
  the escapement rocked on the solids, the stops and the weights.
- **Whether it ticks depends on friction, and the margin is too small.** The run model
  follows a move with friction in the guide, the pawl, the arbors, the gears and on the
  pallets. With 0.2 everywhere the king ticks through a move; with 0.3, the value the
  earlier notes assumed, it stalls on its second beat. Two things take the margin: the king
  leans on its plunger's guide and loses 40 to 44 % of its weight there, and the lean hangs
  the pendulum 2° off the anchor's centre. `docs/king/design-notes.md`, section 9.
- The model also says what would help most: hanging the pendulum so that it is in beat while
  the king leans (ticks up to 0.38), and a thinner arbor for the anchor on top (0.47). Run
  once by hand, not designed (section 12).
- What else is not as it should be yet (section 11): no test print; the pawl falls in by its
  own weight only; the king leans 3° to the back while it sinks; the anchor's arch is 17 mm
  deep and looks heavy.

### This session

- `cadkit/features/escapement_run.py` is new: a recoil escapement run with forces. Wheel and
  pendulum are two bodies with contact at the pallets, the flanks included, and dry friction
  that can hold a part still, so a stall shows as a stall. Eight tests.
- `_king_run.py` is new: masses and inertias from the solids, the statics of the king
  leaning on its guide, the losses on the way to the escape wheel, and `tick`, which runs one
  move. `king.ticking(params, friction=..., pin_friction=..., fall=..., angle=...)` calls it.
- The king's films take their ticking frames from that run, in real time, with a friction of
  0.2 (`king.FILM_RUN`). The three films in `docs/img/king/` are rendered again; the stills
  are unchanged, because no solid changed.
- Small changes beside it: the layout names the rib that guides the stem (`Layout.rib`);
  `_shared.py` has the two densities and `grams`, which the knight's and the king's
  `balance` now use. Both snapshots are unchanged.
- The scratch model of the third session was superseded: it found the king running because
  its friction fades with speed and it has no guide and no lean. The client reviewed the king
  and it was deleted.
- After the review the project was laid out per piece: `src/chess_set_clockwork/<piece>/`,
  `tests/<piece>/` (each with its own `snapshots/`) and `docs/<piece>/` (notes and images).
  The entry points moved to `<piece>.model:model`; model names, variants and snapshots are
  unchanged.
- `cadkit`'s render now clears the frames of an earlier render first: the king's new film is
  four frames shorter than the old one, and the old last frames were ending up in it.
- The whole workspace passed: 230 tests, 8 minutes. Two tests were added after that run had
  begun; `cadkit` and this project passed again with them (172 tests, 50 seconds).

## How to continue

1. Read `docs/king/design-notes.md`: section 9 for what the run model is and found, section
   12 for the next steps in order. They are the client's view of the king, then giving the
   king margin against friction with the run model as the judge, then test prints.
2. For how a piece is put together in code, read the king or the knight. Each piece is its own
   folder, `src/chess_set_clockwork/<piece>/`: `model.py` holds the parameters, `build()` and
   the film; `_layout.py` every derived position and the motion, the pawl's included;
   `_parts.py` the solids; the king's `_run.py` whether it ticks.
3. Still open from before: the client's view of the knight, and test prints of the knight
   (`docs/knight/design-notes.md`, section 11). The brief's advice to prototype the pawn early
   (the tightest fit, sixteen of them) also still stands.

```
uv sync --all-packages
uv run pytest projects/chess_set_clockwork           # 35 seconds
uv run pytest projects/chess_set_clockwork/tests/king/test_run.py    # the run model, 5 seconds
uv run pytest packages/cadkit/tests/test_escapement.py packages/cadkit/tests/test_escapement_run.py
uv run cadkit show clockwork_king -v playing         # the model in the OCP viewer (port 3939)
uv run cadkit build clockwork_king -v playing --render    # exports and stills, 1 minute
uv run cadkit build clockwork_king -v playing --animate   # adds the three films, 8 minutes
```

A move run through by hand, from the repository root:

```
uv run python -c "
from chess_set_clockwork.king.model import Params, ticking
ran = ticking(Params(), friction=0.25, pin_friction=0.25)
print(ran.finished, len(ran.beats), ran.swing())"
```

The same build commands with `clockwork_knight` give the knight. Run `uv` from the repository
root, not from this folder. Outputs go to `dist/<model>/0.1.0/playing/` at the repository root.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The idea, the verdict, the recommended concept, the client's decisions and how the estimates were made |
| `docs/knight/design-notes.md` | The knight as built: how it works, parts, steel, figures, assembly, open points |
| `docs/king/design-notes.md` | The king as built: how it works, what changed from the paper design, parts, figures, what was checked and what the run model found, open points, next steps |
| `docs/<piece>/img/` | Stills and films of the piece at 0.1.0 |
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
sent to it in the fourth session, at the client's request, and at the start of the fifth.
Commit only when the client asks.
