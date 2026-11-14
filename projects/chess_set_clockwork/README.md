# Clockwork chess set

A 3D-printed chess set in the style of skeleton clocks, where each piece holds clockwork parts
that do something. Everything for this product lives in this folder.

## Status (2026-11-14, seventh session)

**Knight, king and pawn are built in CAD (`clockwork_knight` 0.1.0, `clockwork_king` 0.2.0,
`clockwork_pawn` 0.1.0). Nothing is printed. The pawn is new in this session: a ratchet wheel
that goes on by one tooth with every move and cannot turn back. It works in the model; its
weak point is that the pawl falls towards the wheel by its own weight only, a tenth of a
gram. The client has not seen the pawn yet. Rook, bishop and queen are not started.**

Committed and pushed: the knight (`eb985d0`), `cadkit`'s escapement (`aae0d45`), the king's
first build with its run model (`ffc89cc`) and its second build (`b30e687`), `cadkit`'s
ratchet (`e8d9128`), and the pawn in the commit after that one, which also holds this file
and the note of the client's answer on the king from the sixth session.

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
  sixteen beats per move, in 0.8 to 1.4 s depending on friction.
- Ten printed parts, six red jewel rings, eight pieces of steel. Base Ø44 mm, 86.7 mm tall,
  38.1 g.
- 65 tests pass: the snapshot, 14 on the motion and 50 on the run.
- By its run model it ticks from rest with a friction of up to 0.51. The client accepted the
  one-second tick on 2026-11-14 ("one second tick is fine for now - we will see how it works
  once printed"). The king rests until it is printed: `docs/king/design-notes.md`, sections
  12 and 13.

### The pawn

- Every move turns its wheel on by one tooth, 22.5°. Lifted, a plunger drops 4.5 mm; the
  pawl that stands on it rides down over the next tooth and falls under it. Set down, the
  pawl pushes that tooth up, and the click on top of the wheel is lifted over one tooth and
  falls behind it. The wheel cannot turn back.
- Eight printed parts (seven different: the two plates are one part), two red jewel rings,
  three pieces of steel. Base Ø32 mm, 46.9 mm tall, 15.3 g.
- 17 tests pass: the snapshot and 16 on the motion, clearances, stops and balance.
- **Weak point, measured:** the pawl weighs 0.10 g and its centre of mass stands 0.69 mm
  inside its knuckle when it has to fall under the tooth. Friction in its socket may hold
  that. If it does, that move does not turn the wheel; nothing jams. A remedy is worked out
  on paper (a steel roller behind the pawl), not built. `docs/pawn/design-notes.md`, section
  10, point 2, and section 11.
- **Decisions the client has not seen** (section 2 of the notes): base Ø32 where the brief
  estimated 30, a travel of 4.5 mm, a wheel of Ø15 with sixteen teeth, a round arch, a
  separate head, click and pawl in the plunger's dark colour.
- **Not met:** the brief asked for a pawn that prints nearly in one piece. This one has
  eleven items; the knight has twelve.

### This session

- The client named the piece: "Continue building the chess set with the pawn".
- New in `cadkit`: `features/ratchet.py`, a ratchet wheel with saw teeth and how a pawl's
  nose meets it (outline, the nose in a tooth's corner, where a pawl comes to rest, how
  surely a tooth holds it), with 12 tests. Nothing else in `cadkit` changed.
- New: `src/chess_set_clockwork/pawn/` (`model.py`, `_layout.py`, `_parts.py`),
  `tests/pawn/` with its snapshot, `docs/pawn/` with notes, stills and films. The entry
  point `clockwork_pawn` is in `pyproject.toml`. `_shared.py`, the knight and the king are
  unchanged.
- The pawn's motion is rigid geometry followed in steps of 0.02 mm of the plunger's travel
  (`pawn/_layout.py`, `move()`). There is no friction in it and no run model as the king
  has.
- The whole workspace passed at the end of the session: 296 tests, 8 minutes. Lint is clean
  in this project and in `cadkit`; `ruff check .` reports four findings in
  `projects/serce/concept/` that were there before.
- Nothing listened on the viewer's port 3939, so the pawn was not sent to VS Code.

## How to continue

1. **The client's view of the pawn**, and of the decisions listed above. Until then the pawn
   is a proposal.
2. **Then either the next piece or test prints**; the client decides. Rook, bishop and queen
   are left; `docs/brief.md`, section 4, gives each its clockwork element. For prints, the
   pawn is the smallest piece and the cheapest to try: `docs/pawn/design-notes.md`, section
   11; the king's are in `docs/king/design-notes.md`, section 13, the knight's in
   `docs/knight/design-notes.md`, section 11.
3. For how a piece is put together in code, read the pawn: it is the shortest. Each piece is
   its own folder, `src/chess_set_clockwork/<piece>/`: `model.py` holds the parameters,
   `build()` and the film; `_layout.py` every derived position and the motion; `_parts.py`
   the solids; the king's `_run.py` whether it ticks. Tests go in `tests/<piece>/` with their
   own `snapshots/`, notes and images in `docs/<piece>/`.
4. Still open from before: the client's view of the knight.

```
uv sync --all-packages
uv run pytest projects/chess_set_clockwork           # 50 seconds
uv run pytest projects/chess_set_clockwork/tests/pawn                # 7 seconds
uv run pytest packages/cadkit/tests/test_ratchet.py
uv run cadkit show clockwork_pawn -v playing         # the model in the OCP viewer (port 3939)
uv run cadkit build clockwork_pawn -v playing --render    # exports and stills, 30 seconds
uv run cadkit build clockwork_pawn -v playing --animate   # adds the two films, 4 minutes
```

One move of the pawn looked at by hand, from the repository root:

```
uv run python -c "
from chess_set_clockwork.pawn.model import Params, balance
from chess_set_clockwork.pawn._layout import move
made = move(Params())
print(made.fallen, made.under, made.meets, made.turned, made.swing)
print(balance(Params()))"
```

The same build commands with `clockwork_knight` or `clockwork_king` give the other pieces
(the king's films take 15 minutes). Run `uv` from the repository root, not from this folder.
Outputs go to `dist/<model>/<version>/playing/` at the repository root.

## Where things are

| Path | What it is |
|---|---|
| `docs/brief.md` | The idea, the verdict, the recommended concept, the client's decisions and how the estimates were made |
| `docs/knight/design-notes.md` | The knight as built: how it works, parts, steel, figures, assembly, open points |
| `docs/king/design-notes.md` | The king as built: how it works, what changed between the two builds, parts, figures, what the run model finds, open points, next steps |
| `docs/pawn/design-notes.md` | The pawn as built: how it works, the decisions taken, parts, steel, figures, assembly, what was tried and dropped, open points, next steps |
| `docs/<piece>/img/` | Stills and films of the piece: the knight at 0.1.0, the king at 0.2.0, the pawn at 0.1.0 |
| `A_skeleton_clocks.png` | The client's concept picture: style reference only, its mechanisms do not work as drawn |
| `src/chess_set_clockwork/<piece>/model.py` | Parameters, the variant, `build()`, `balance()`, render settings and film poses |
| `src/chess_set_clockwork/<piece>/_layout.py` | Every level, centre and angle derived from the parameters; the motion |
| `src/chess_set_clockwork/<piece>/_parts.py` | The solids |
| `src/chess_set_clockwork/king/_run.py` | Whether the king ticks: masses from the solids, friction on the way to the escape wheel, one move run through |
| `src/chess_set_clockwork/_shared.py` | What every piece shares: drawing helpers, the base's body, feet, jewel rings, steel pins |
| `tests/<piece>/` | The piece's snapshot (`snapshots/`), model and motion tests; the king's run in `tests/king/test_run.py` |
| `packages/cadkit/src/cadkit/features/ratchet.py` (repository root) | Ratchet wheel with saw teeth, and how a pawl's nose meets it |
| `packages/cadkit/src/cadkit/features/escapement.py` | Recoil anchor escapement: wheel outline, pallets, and a check of how they meet |
| `packages/cadkit/src/cadkit/features/escapement_run.py` | The same escapement run with forces: torque, inertia, contact and dry friction |

The stills and films in `docs/<piece>/img/` are small copies made by hand from `dist/`; a
build does not update them.

The client watches progress in VS Code: the OCP CAD Viewer listens on port 3939. In the sixth
and seventh sessions nothing listened on that port, so the king's second build and the pawn
were not sent. Commit only when the client asks.
