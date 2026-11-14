# Brief: clockwork chess set

*Written on 2026-11-13 from the first concept discussion. Nothing here is modelled or tested.
Every figure is an estimate; section 7 shows how each was made.*

## 1. The idea

The client's words:

> The picture is just a concept - but the idea is to have 3d printed cad chess set that
> incorporates some clock like parts that do something.

The picture is `../A_skeleton_clocks.png`: six pieces in gold and six in black, each an open
cage in the style of a skeleton clock, with spoked wheels, small pinions, pendulums, balls and
red jewels at the wheel centres.

The question asked was whether the pieces can hold movement that does anything meaningful. The
client's reply to the assessment below was "Fantastic, let's store it as a brief in the project
for future work". The three decisions in section 6 were answered later, on 2026-11-14.

## 2. Verdict

**Yes, but not as clocks.** The pieces can hold real clockwork parts that work when a player
handles them. They cannot hold a movement that runs by itself for any useful time.

Why a self-running movement is out:

- **Space.** At a normal playing size (55 mm squares, king base 44 mm) the king has about
  Ø27 × 40 mm free inside its cage and the pawn about Ø16 × 20 mm.
- **Tooth size.** On the U1's 0.4 mm nozzle the smallest dependable tooth is module 1, which is
  what Fala uses. A 10-tooth pinion is then Ø12 mm over the tips. The king holds two or three
  wheels, the pawn one. The fine pinions in the picture are about module 0.5 and would not
  print.
- **Energy.** A printed spring that fits in the king stores 10 to 90 mJ. At the low end, which
  is what the plastic holds without creeping, that is a minute or two of ticking at best,
  before friction in the wheels. Plastic springs also weaken when left wound.

## 3. What can drive the parts

Three sources of motion have ample energy at this size:

1. **Lifting and placing.** A weighted plunger in the base drops about 3 mm when the piece is
   lifted, and the board pushes it back when the piece is set down. That gives exactly one tick
   per move.
2. **The jolt of the move.** A 25 mm pendulum swings about three times a second and keeps
   going for some seconds after the piece is set down.
3. **The hand.** The crown becomes a real winding crown that turns the wheels.

## 4. Recommended concept: one tick per move

The set is a clock that counts moves instead of seconds. Each piece is one real clockwork
element, chosen to match how the piece moves.

| Piece | Element | Link to chess |
|---|---|---|
| Pawn | Ratchet and click | Turns one way only, as a pawn only goes forward |
| Knight | Sector gear that rears the head (the toothed mane in the picture) | The only piece that jumps |
| King | Anchor escapement | One tooth per beat, one square per move |
| Rook | Rack and pinion | Straight-line motion |
| Bishop | Pendulum | Loose link |
| Queen | Full wheel train | Loose link |

Three effects are useful in a game, not only decoration:

- The piece that moved last is the one still swinging.
- King and rooks show whether they have moved. That decides castling, and the board cannot
  show it.
- A tipped king stops, because a pendulum only works upright.

## 5. What changes from the picture

The style survives; the layout does not. The wheels drawn there do not mesh and have nothing
to turn on.

- Each piece is built like a real skeleton clock: two plates joined by pillars, with the wheels
  on arbors between them.
- Teeth are coarser and fewer than drawn.
- A red jewel sits only where there is a real bearing.
- A set has 32 mechanisms. The pawn has to print nearly in one piece, or assembly becomes the
  weak point.

A movement that really keeps time belongs in a matching chess clock, which is large enough for
a printed escapement. That would be a separate product.

## 6. Decisions before modelling

Answered by the client on 2026-11-14, before the king was designed. Each answer is the
recommendation that was given with the question.

1. **Hardware: steel is allowed.** Steel pins as arbors, steel pins or balls as weights and
   pendulum bobs. A printed Ø10 ball weighs 0.6 g against 4 g in steel, and the plunger and
   pendulum need that mass.
2. **Size: normal playing size.** King base 44 mm, matching the knight as built. A 1.5×
   display set would make everything easier but no longer fits a normal board.
3. **Files or printed sets: not decided yet.** Every fit stays generous and a named parameter;
   the choice is made after the first test prints. If the set is sold as files, the mechanisms
   must tolerate other people's printers, which pushes towards the simpler options.

## 7. How the estimates were made

- **Sizes.** Measured on the picture and scaled so that the king's base is 44 mm, which is 80%
  of a 55 mm square. That gives a king 81 mm tall and a pawn 51 mm tall on a 30 mm base. The
  free space is the opening between the columns of each cage.
- **Module.** `projects/fala/src/fala/model.py` bounds the module at 0.8 to 1.25 with 1.0 as
  default, on the same printer. The small pinion under the king's wheel measures about 9 mm
  with some 16 teeth in the picture, which is module 0.5.
- **Wheels in the king.** A 20-tooth wheel (Ø22 over the tips) and an 8-tooth pinion sit 14 mm
  apart and take 30 mm of the 40 mm height. A third wheel needs a second plane.
- **Spring.** A PETG strip of 0.8 × 5 × 300 mm fills about half of a Ø24 barrel. Bending
  energy is stress² × volume / (6 × modulus). With a modulus of 2 GPa that is 10 mJ at 10 MPa,
  a stress the plastic holds without creeping, and 90 mJ at 30 MPa for a short time.
- **Running time.** A 4 g bob on a 25 mm arm swinging 15° each way holds 33 µJ. Assuming the
  pivot loses a fifth of that per swing and the escapement passes on a third of what the spring
  gives, each swing costs about 20 µJ. At 10 mJ that is some 500 swings, about two and a half
  minutes, before any loss in the wheels. Both assumptions are guesses.
- **Pendulum.** Period = 2π√(length / g) = 0.32 s at 25 mm.
- **Plunger.** 5 g falling 3 mm gives 0.15 mJ per lift. A light ratchet wheel needs a few µJ
  to move one tooth, so the margin is thirtyfold or more.
- **Balls.** Ø10 mm is 0.52 cm³: 0.65 g in PLA (1.24 g/cm³), 4.1 g in steel (7.8 g/cm³).

## 8. Open points for the design

- The pawn is the tightest fit and there are sixteen of them. Prototype it first: a ratchet
  wheel and plunger at pawn size, printed as nearly one piece as possible.
- How long a printed pendulum keeps swinging decides whether "the last piece moved is still
  swinging" works. Measure it on a test print.
- The counting wheels need a way back to zero at the start of a game. The crown is the
  natural place.
- The "has moved" sign on king and rooks must be armed after the pieces are set up.
- The plunger must leave the piece standing flat and steady, with or without felt under the
  base.
- The U1 has four toolheads, so the red jewels can be printed with the body.

## 9. Set aside

- **A self-running movement in every piece.** See section 2.
- **A board that drives the pieces.** One gear under each square, coupled to a rotor in each
  base by magnets, all turned by one crank. A square grid of meshing gears does run: light
  squares turn one way and dark squares the other. It needs 64 gears and about a hundred
  magnets. It was not discussed with the client and could follow as a later product.
