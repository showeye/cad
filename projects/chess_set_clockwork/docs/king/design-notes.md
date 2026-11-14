# King: design notes

*Second build, 2026-11-14 (sixth session). Model `clockwork_king` 0.2.0, variant `playing`.
The first build (0.1.0, fourth session) and its run model (fifth session) are in the
repository's history. Modelled and checked in CAD only: nothing has been printed, so every
fit is a starting value and every friction value is assumed.*

**By the run model the king now ticks from rest with a friction of up to 0.51, where the
first build stalled from 0.26. Printed plastic on printed plastic is usually taken as 0.2 to
0.4. The price is a shorter tick: sixteen beats in about one second, where the first build
made twenty in about two. Section 5 has what changed and why, section 10 the figures.**

## 1. What was built

The king ticks for about a second after every move, and then stands still until it is moved
again.

When the king is lifted, a weighted plunger drops 4.0 mm out of its base and a pawl on it
clicks under the next lobe of a small star. Set down, the king falls 0.9 mm onto that pawl
and then sinks the last 3.1 mm under its own weight. The sinking drives a real recoil anchor
escapement with a pendulum: sixteen beats per move. The piece that moved last is the one
still ticking, and a tipped king stops.

The client chose the king as the second piece because it has the most room and there are only
two per set ("awesome, let's go for the king!"). This goes one step past `brief.md`, which
gives the king an escapement that is stepped one tooth per move by the plunger. That version
remains the fallback: it uses the same wheel and anchor.

![The king standing, from the front, and with the front plate taken off](img/standing.jpg)

Films: [`img/motion.gif`](img/motion.gif) (one move: lifted, set down, ticking),
[`img/mechanism.gif`](img/mechanism.gif) (the same with the front plate taken off)
and [`img/pendulum.gif`](img/pendulum.gif) (from behind, the rear plate taken off).
The hand's part is drawn. From the moment the king rests on its pawl the films show the run
model in real time, with a friction of 0.3 (section 10): a move takes 1.0 s and the pendulum
swings for 0.7 s more. At 33 frames a second that is two frames to a beat. Other stills are
in `img/`.

## 2. Decisions

The client answered the three decisions of `brief.md`, section 6, on 2026-11-14:

| Decision | Answer |
|---|---|
| Hardware | Steel allowed: pins as arbors, a steel bob on the pendulum |
| Size | Playing size: king base Ø44 mm, matching the knight as built |
| Files or printed sets | Not decided yet: every fit is generous and a named parameter |

The client reviewed the first build on 2026-11-14 ("it looks great"). The second build keeps
its look: the frame, the plates, the train and the pawl are unchanged.

## 3. How it works

Side view as on the knight: X to the right, Z up, seen from the front (-Y), arbors along Y.
All three arbors stand on the centre line, one above the other, at 22.6, 39.6 and 54.5 mm
above the board.

1. **Plunger.** A bar in a slot through the base with a steel weight, as on the knight but
   as wide as the piece. A stem rises from its front edge and ends in a socket.
2. **Pawl and star.** The pawl is a strut 10 mm long. Its round knuckle sits in the socket;
   its head has a cup with a straight fence beside it. The star is a small boss with six
   round lobes on stalks, on the front of the great wheel. A lobe lies in the cup like a pin
   in a bearing, so the pawl and the star work as a connecting rod and a crank: the king's
   weight on the star turns it 60° while the king sinks 3.14 mm.
3. **The click.** When the king is lifted the plunger drops. The sloping underside of the
   pawl's head rides over the next lobe and pushes the pawl aside by 9°; below the lobe the
   pawl falls back by its own weight and leans its fence on the lobe's side, with the cup
   right below it. That is what makes the drive one-way.
4. **Great wheel.** 24 teeth, one part with the star. It turns a 10-tooth pinion.
5. **Escape wheel.** 20 pointed teeth, one part with the pinion. It turns 144° per move,
   which is eight teeth.
6. **Anchor and pendulum.** One part, on a thin arbor of its own. The anchor's two pallets
   let one tooth pass for every two beats. The pendulum hangs behind the wheels: a ring that
   goes round the escape wheel's arbor, and a small steel pin as the bob below it.
7. **Stops.** The plunger hangs on two ears. The pendulum's ring stops the anchor 7.5° either
   side. The lips of the socket stop the pawl 6° inwards and 14° outwards of where it stands
   at rest.

One move is exactly 1 lobe of the star, 4 teeth of the great wheel, 4 of the pinion and 8 of
the escape wheel. Every part therefore ends a move looking as it did before it, and the film
of one move loops without a jump.

## 4. What changed from the paper design in the first build, and why

The third session ended with a design on paper. Building it (0.1.0) changed these points:

| Paper design | First build | Why |
|---|---|---|
| Star with six saw teeth, pawl with a round nose seated at a tooth's foot | Six round lobes on stalks, pawl with a cup | Seated at the foot of a tooth, the pawl pushes almost towards the star's centre at the start of a move: its lever arm was 0.4 to 1.4 mm there against 3.0 mm at the end, too little to start the escapement. Its shank also met the tooth below. A lobe in a cup turns like a hinge: 2.35 to 3.22 mm |
| Stroke 3.2 mm by hand | 3.14 mm computed | The hand figure assumed a hinge, which the saw tooth was not |
| Travel 4.5 mm | 4.0 mm | The pawl is under the next lobe at 3.25 mm, so 4.0 leaves 0.75 mm. Less travel means a shorter free fall |
| Escape wheel 13.0 over the teeth | 12.7 | The star and the escape wheel share a layer and pass each other; 0.5 mm between them |
| Rear bosses, radius not set | Radius 2.0 | At rest the bob's block stands above the lower boss, and it comes closer as it swings |
| Nine printed parts, cross on the crown | Ten: the cross is its own flat part | Printed upright its arms would hang in the air |
| Height 83 to 88 mm | 86.7 mm | |

## 5. What changed in the second build, and why

The run model of the fifth session found the first build without margin: it ticked with a
friction of 0.25 or less and stalled on its second beat from 0.26. The second build is the
answer. The goal was set in the notes of the fifth session: tick with a friction of 0.4 from
a pendulum at rest. The run model was the judge throughout.

| | First build (0.1.0) | Second build (0.2.0) | Why |
|---|---|---|---|
| Escape wheel | 25 teeth, 10 per move | 20 teeth, 8 per move | Each beat gets a quarter more of the weight's work, and with 4.0 mm from tooth to tooth instead of 3.2 the pallets' ramps can lie flatter |
| A tooth leaves a pallet at | 4.0° | 3.0° | The pendulum has less far to be pushed |
| Pallets' ramps, from the wheel's tangent | 45.8° | 28.6° | With a friction of 0.4 on the ramp a tooth lifts the pallet with 0.83 of its own push; on the steep ramp it was 0.41 |
| Pallets stand in the wheel by | 0.56 mm | 0.41 mm | What the flatter ramp costs: less room for printing error (section 12) |
| Anchor's arbor | Ø2 pin | Ø1 wire | Friction at this arbor brakes the pendulum on every beat, and it grows with the arbor's radius. The thin arbor also leaves the hub over the escape wheel a wall of 1.0 mm instead of 0.7 |
| Bob | Ø6 × 14, 3.1 g | Ø4 × 10, 1.0 g | Gravity pulls a heavy pendulum back harder than a tooth can push it out |
| Pendulum | 7.0 g, 25 g·cm² | 4.5 g, 11 g·cm² | |
| Pendulum in a standing king | Anchor centred | Anchor 1.0° off centre, the entry pallet lowered | Sinking, the king leans 2° and the pendulum hung 2° off the anchor's centre. Now it hangs 1° off, and 1° to the other side when the king stands. Done by the arch alone: it is 2° shorter on the exit side |
| Anchor stopped by its ring at | 8.5° | 7.5° | On the solids the entry pallet meets the flank of a tooth at 8.3°; in the first build that was 9.2° |
| Pallets | Both faces 5.5 mm | Drawn 7.2 mm and cut off by the arch's ends and outer edge | The flat ramp has to be longer to reach the arch |
| One move at a friction of 0.2 | 20 beats in 2.1 s | 16 beats in 0.9 s | See below |
| Ticks from rest, lowered onto the pawl, up to | 0.25 | 0.51 | |
| The same, dropped 0.86 mm onto it | 0.27 | 0.60 | |

The frame, both plates' outlines, the great wheel, the star, the pawl, the plunger, the base
and the crown are as they were.

### What was learned on the way

Each figure is the highest friction at which a move ran through in the run model. They were
found with scratch scripts, on the model of the first build unless something else is said;
the scripts are not kept. Only what section 10 lists is held by tests.

- **What the notes of the fifth session expected to help most helped less than it seemed.**
  Hanging the pendulum 1.9° off, so that it is in beat while the king leans, gave 0.38
  there. Started from true rest, with the pendulum already hanging where the lean puts it,
  the same king ran to 0.24: the gain came from the two degrees the pendulum is off its new
  rest when the king suddenly leans, which kick it. A king that is lowered slowly does not
  get that kick.
- **The pendulum decides, and by two of its figures only.** The limit follows its mass
  (friction at the arbor) and its moment about the arbor, mass times depth of the centre of
  mass (how hard gravity pulls it back). Its inertia hardly moves the limit: it sets how
  long a move takes. Halving mass and moment alone took the first build from 0.24 to 0.34.
- **The escapement's own geometry is worth about as much.** 20 teeth instead of 25: 0.24 to
  0.28. Release at 3° instead of 4°: 0.24 to 0.28. Both: 0.32. A longer anchor (a span of
  five teeth instead of four) changes nothing at the same release.
- **The guide is where most of the weight is lost, and fixing it would gain little.** With a
  friction of 0.4 the first build's pawl carries 47 to 51 % of the weight. A guide with the
  load in the plane of the centre of mass would carry 66 to 68 % and bring 42 % more torque
  to the escape wheel, and the limit rose from 0.24 to 0.28. It would mean moving the star
  and the pawl into the middle of the piece, behind the great wheel. Not done.
- **More weight helps in proportion.** Six grams of steel in the base: 0.24 to 0.26. Not
  done.
- **Robust and long do not go together.** A move lasts as long as its beats take, and a beat
  takes about as long as the wheel needs to throw the pendulum from one side to the other.
  Everything that makes the start surer makes that throw quicker: stronger beats, fewer of
  them, a lighter pendulum. Combinations tried, as limit from rest and time for a move at a
  friction of 0.2 (the two builds to 0.01, the others on a grid of 0.02):

  | | Limit | A move |
  |---|---|---|
  | First build | 0.25 | 2.1 s, 20 beats |
  | 25 teeth, release 3°, bob Ø4 × 10, Ø1 arbor | 0.40 | 1.3 s, 20 beats |
  | 20 teeth, release 3.5°, bob Ø5 × 10, Ø1 arbor | 0.40 | 1.2 s, 16 beats |
  | 20 teeth, release 3°, bob Ø4 × 10, Ø1 arbor, anchor centred | 0.46 | 1.0 s, 16 beats |
  | The same with the pendulum 1° off centre: the second build | 0.51 | 0.9 s, 16 beats |
  | 15 teeth, release 4°, bob Ø5 × 10, Ø1 arbor | 0.44 | 0.8 s, 12 beats |

- **A pendulum that would do both needs weight above its arbor.** A pendulum whose centre
  of mass is near the arbor and whose mass is far from it is easy to push and slow to swing:
  3.5 g with the inertia of the first build's pendulum and a fifth of its moment, on a Ø1
  arbor, ran to 0.44 and took 2.5 s over a move. The king has no room for it: the crown and
  the upper pillar are 5 to 10 mm above the arbor. A bar across at the arbor's height would
  do the same and would stand out of the frame on both sides.

## 6. Parts

Every printed part but the base and the crown is a stack of flat pierced plates and prints
lying down without support.

| Part | Size (mm) | Prints | Notes |
|---|---|---|---|
| `base` | Ø44 × 9.0 | upright | Slot for the plunger, four mortises, sixteen studs |
| `plate_front`, `plate_rear` | 30 × 67 × 3 | outer face down | Gothic window: columns on plinths, a bar across at the escape wheel, a pointed arch and its mullion. Half posts 9 mm high on the inner face; sprung feet |
| `jewel_*` (6) | Ø5.2 × 0.8, one Ø4.0 | with the plate, first layers | Red rings flush in the outer faces; the arbors turn in them. The anchor's two have a bore of 1.3 |
| `great_wheel` | Ø25.2 × 8.5 | wheel down | 24 teeth, six open spokes; the star on its front |
| `escape_wheel` | Ø25.4 × 8.5 | wheel down | 20 teeth, five spokes on a 0.8 mm web; the pinion on its back |
| `anchor` | 26 × 32 × 17 | pendulum down | Pallets on an arch 17 mm deep; rod, ring and the block for the bob in the rear 8 mm |
| `plunger` | 23 × 17 × 18 | front face down | Bar, ears, tunnel for the weight, stem with the socket |
| `pawl` | 6 × 12 × 4 | flat | Knuckle, arm, cup and fence |
| `crown` | 11 × 24 × 15 | upright | Block with a notch for the tenon on each plate's top; orb on a collar |
| `cross` | 7.5 × 10 × 1.6 | flat | Stands in a slot in the orb |

What differs between the plates: the front one holds the star's arbor in a small boss on a bar
from the left column only, so that the star and the pawl stay in view, and carries a rib that
guides the plunger's stem. The rear one has a full bar there and two bosses 8.8 mm tall; the
wheels bear on them and the pendulum's ring swings round the upper one.

Steel (named `reference_*` in the model, left out of the printable files):

| Item | Size | Count | Fit |
|---|---|---|---|
| Arbor of the wheels | Ø2 × 24 | 2 | Pressed into the wheel (bore 2.1), turns in the plates (bore 2.3) |
| Arbor of the anchor | Ø1 × 24 | 1 | Pressed into the anchor (bore 1.1), turns in the plates (bore 1.3) |
| Pillar | Ø2 × 24 | 3 | Pressed through both plates, inside the posts: two in the plinths, one above the anchor |
| Bob | Ø4 × 10 | 1 | Pushed across the pendulum's block; it stands out 1 mm on both sides |
| Weight | Ø6 × 18 | 1 | Slides into the plunger from the right end; the slot's end wall keeps it in |

The pins are ISO 2338 nominal sizes; verify against the supplier's sheet. The anchor's arbor
is thinner than pins of this length are commonly sold: take straight spring steel wire of
Ø1.0, cut it to 24 mm and deburr its ends, and verify what the supplier offers.

## 7. Across the piece

24.0 mm in all, the length of the pins. Plates 3.0 each, 18.0 between them. From the front:

| Layer | Thickness | What is in it |
|---|---|---|
| Front | 4.0 | Escape wheel, pallets, star, pawl, the plunger's stem |
| Middle | 4.0 | Great wheel and pinion |
| Rear | 8.0 | Pendulum: rod, ring, bob |

There is 0.5 between the layers, and a 0.3 bearing ring plus 0.2 play at each plate. The
anchor's arch goes through all three layers so that the part prints flat; where the escape
wheel passes under the arbor its hub is 1.59 mm in radius round a bore of 1.1.

## 8. Figures

All from the model; `king.balance()` and the tests reproduce them.

- **Size.** Base Ø44, 86.7 mm tall. Held up, the plunger hangs 4.0 mm below the base.
- **Weight.** 38.1 g at PLA density: 30.0 g printed, 8.1 g steel. The plunger with its
  weight and the pawl is 7.5 g. The other 30.6 g rest on the pawl while the king sinks.
- **One move.** 0.86 mm of free fall, then 3.14 mm on the pawl: 0.94 mJ. The knight's plunger
  gives 0.15 mJ per lift.
- **Lever arm of the pawl on the star.** 2.35 mm at the start of a move, 3.22 mm at its
  greatest, 3.18 mm at the end.
- **Torque, friction left out.** 0.70 to 0.97 mN·m on the star, which is 0.29 to 0.40 mN·m at
  the escape wheel. With a friction of 0.3 everywhere, 0.11 to 0.17 mN·m arrive; with 0.4,
  0.07 to 0.13 (section 10).
- **Pawl.** It leans 23.8° at rest. It pushes the stem sideways against its rib.
- **Pendulum.** Anchor 3.4 g, bob 1.0 g, arbor 0.15 g. Its centre of mass is 9.6 mm below the
  arbor, the arbor counted, and it hangs with the anchor 1.0° off centre. Moment of inertia
  11 g·cm²; swinging freely its period would be 0.32 s. Gravity turns it back with
  7.4 mN·mm for every degree; friction of 0.3 on its Ø1 arbor holds 6.6 mN·mm, so it can rest
  up to 0.9° from where it hangs.
- **Wheels.** Escape wheel with its arbor 2.3 g and 0.95 g·cm², great wheel 2.0 g and
  0.99 g·cm². Seen at the escape wheel, the wheels and the sinking king together are 1.4 to
  1.7 g·cm².
- **Lean.** While it sinks the king leans on its plunger by the guide's play: 2.1° to the left
  at the start of a move and 1.7° at its end, and 3.1° to 2.5° to the back.
- **Escapement.** 20 teeth, 12.7 over the tips, teeth 3.2 deep. The anchor's arbor is 14.89
  above the wheel's, the pallets 7.78 from it. A tooth leaves a pallet 3.0° either side of
  centre; the drop is 0.5 mm; the working faces stand at 28.6° to the wheel's tangent; with
  the anchor centred the pallets stand 0.41 mm inside the circle of the tips.
- **Gear clearance.** 0.11 to 0.12 mm between flanks at every position checked.

## 9. How it goes together

Worked out on the model. Not tried with parts.

1. Push the weight into the plunger and the bob into the pendulum. Slide the pawl's knuckle
   into the socket from the front. Drop the plunger into the slot in the base.
2. Lay the rear plate down with its posts up and press the three pillars into it. Press an
   arbor into each of the three moving parts: the thin one into the anchor.
3. Put the anchor on first, its ring over the upper boss. Then the great wheel, then the
   escape wheel with its pinion down. The wheels may be meshed at any tooth.
4. Lower the front plate over the three arbors and the pillars. Press the crown onto the two
   tenons and the cross into the orb.
5. Push the frame into the base until the four feet click. The pawl is pushed aside by the
   star on the way; lift the king once and it clicks under its lobe.

The four holes for the thin arbor (1.1 in the anchor, 1.3 in the plates and their jewels) are
small for a printed hole and will want clearing with a drill or with the wire itself.

## 10. What was checked, and what was not

`tests/king/test_motion.py`, 14 tests, and the snapshot in `tests/king/test_model.py`:

- One move is one lobe and sixteen beats; the train does not turn above the stroke.
- The lobe lies in the cup through the whole stroke, the star's push goes through the pawl's
  knuckle, and the lever arm stays between 2.3 and 3.3 mm.
- The pawl is under the next lobe 0.75 mm before the plunger hangs. While it is pushed aside,
  the star's push is more than 55° away from the line to the knuckle, so the pawl cannot
  wedge between the star and the dropping plunger.
- No part overlaps another: standing, at nine heights of a lift, and in frames of the
  sinking with the anchor swinging.
- Gear clearance stays between 0.05 and 0.2 mm; 2.5° either way meets a tooth.
- **The escapement on the solids.** With the anchor rocked slowly to both stops and the wheel
  pushed on, pallets and teeth never overlap, a tooth tip always touches, the wheel advances
  one tooth for two beats and is pushed back when the anchor swings on. At 8.5° the entry
  pallet is in a tooth's flank; at 8.1° it is not. The stop is at 7.5°.
- The plunger's ears, the pendulum's ring and the socket's lips stop what they should, where
  they should.
- A standing king's anchor is 1.0° off centre, in the built model and in the film's first
  frame, and the wheel stands just short of the pallet there.
- Weights, the torque and the height are as in section 8, and nothing stands out past the
  base.
- Five impossible kings are refused.

`cadkit` has the escapement's geometry (`features/escapement.py`, ten tests) and how an
escapement runs (`features/escapement_run.py`, eight tests). Neither changed in the second
build.

`tests/king/test_run.py`, 50 tests, on the run model below.

### Whether it ticks: the run model

`king/_run.py` and `cadkit.features.escapement_run` follow one move from the moment the king
rests on its pawl until nothing moves.

- **The escapement.** Wheel and anchor are two bodies in a plane. Both corners of every
  tooth's flat are tried against both pallets, and each pallet's nose against the flanks of
  the tooth beside it. Where they overlap, a stiff spring with damping and sliding friction
  pushes them apart. The ring's stops are in.
- **Friction that holds.** Each arbor has dry friction that keeps a stopped part where it is
  until it is pushed harder than that.
- **Masses and inertias** are taken from the solids (section 8).
- **The drive** is the body's weight on the pawl, with the pawl's changing lever arm, less
  friction at every place on the way: the plunger's guide, the pawl's two joints, the great
  wheel's arbor, the gear teeth and the pinion's arbor. Friction takes the same share when a
  pallet pushes the wheel back.
- **The guide.** The pawl pushes on a lobe that is 2.4 to 3.0 mm right of the centre line and
  6.5 mm in front of the body's centre of mass, and it leans 21° to 24°. The body therefore
  does not come straight down. It turns until the rib of the front plate lies on the top of
  the plunger's stem and the left end of the slot on the bar, and it tips back until the front
  plate lies on the stem and the slot's rear wall on the bar. It rubs at all four places.
  This is worked out as statics; it also gives the lean.
- **The lean** moves the pendulum's rest by 2° for as long as the king sinks: from 1.0° on
  one side of the anchor's centre to 1.1° on the other.
- **The start.** The anchor starts at rest where the pendulum hangs in a standing king, or
  at any angle that is given. If a pallet then stands in a tooth, the wheel starts where
  that pallet has pushed it back to, as a pendulum swinging in the hand does with a train
  that nothing drives.

Where the torque goes with a friction of 0.4, in mN·mm on the star:

| | Start of a move | End of a move |
|---|---|---|
| The weight times the pawl's lever arm | 704 | 954 |
| Lost in the plunger's guide | 368 (52 %) | 460 (48 %) |
| Lost in the pawl's two joints | 66 | 64 |
| Lost at the great wheel's arbor | 57 | 60 |
| Lost between the gear teeth and at the pinion's arbor | 37 | 64 |
| Left, and what that is at the escape wheel | 176, so 73 | 306, so 127 |

What the run finds, with the same friction at every printed surface and every pin, the
pendulum at rest where it hangs:

| Friction | The pawl carries | At the escape wheel (mN·mm) | Lowered onto the pawl | Dropped 0.86 mm onto it |
|---|---|---|---|---|
| none | all of the weight | 293 to 403 | | |
| 0.10 | 82 to 84 % | 210 to 301 | ticks, 0.82 s | ticks, 0.81 s |
| 0.20 | 68 to 71 % | 150 to 227 | ticks, 0.94 s | ticks, 0.93 s |
| 0.30 | 57 to 61 % | 106 to 170 | ticks, 1.02 s | ticks, 1.00 s |
| 0.40 | 48 to 52 % | 73 to 127 | ticks, 1.10 s | ticks, 1.05 s |
| 0.45 | 44 to 48 % | 61 to 110 | ticks, 1.24 s | ticks, 1.19 s |
| 0.50 | 40 to 44 % | 50 to 94 | ticks, 1.36 s | ticks, 1.29 s |
| 0.51 | 39 to 44 % | 48 to 92 | ticks, 1.36 s | ticks, 1.28 s |
| 0.52 | 39 to 43 % | 46 to 89 | stalls on the second beat | ticks |
| 0.55 | 37 to 41 % | 40 to 81 | stalls on the first beat | ticks, 1.17 s |
| 0.60 | 34 to 38 % | 33 to 69 | stalls on the first beat | ticks, 1.34 s |
| 0.61 | 33 to 37 % | 31 to 67 | stalls on the first beat | stalls on the fourth beat |

- **Where it ticks** it runs evenly: 17 landings on the pallets in a move (the first comes
  at once), 0.04 to 0.10 s apart, and no nose of a pallet meets a flank. With a friction of
  0.3 the anchor swings 5.1° to one side and 3.9° to the other; with 0.1 it reaches its stop
  on one side.
- **From any start.** Let go from rest at 7°, 3.5° and 0° either side, lowered or dropped,
  the king ticks through with frictions of 0.2, 0.4 and 0.45: thirty runs, all tests. Run by
  hand as well: every whole degree from -7° to 7° with 0.1 to 0.45, 160 runs, none failed.
- **With fits that print differently.** A loose guide (play 0.5 instead of 0.25, so the king
  leans 3.1°), a tight one (1.1°) and pallets that stand 0.07 mm deeper in the wheel than
  drawn (release at 3.5°) each tick through with 0.4, lowered and dropped: tests. By hand,
  the loose guide and the deep pallets each ran from twenty starts with 0.2, 0.3, 0.4 and
  0.45 without a failure; both together ran from all twenty with 0.4 and failed six of
  them with 0.45.
- **Where it stalls** a tooth lies on a pallet and cannot push it out.

**What this model is not.** Nothing is measured: every friction value is assumed, and the
table moves with them. The guide's four places of contact are taken from the geometry, not
from a print, and the pawl's push is taken in the middle of its layer. Left out are the play
of the arbors in their holes, the pallets' push on the arbors, the click of the pawl and
anything the hand does. The films and the tests use the same model, so they cannot check it.
The same model chose the second build's dimensions, so its figures for the second build are
the best case it can show: they say that the design is no longer the limit, not that a
printed king will tick.

## 11. Found on the way

From the third session, on the escapement:

- **A pallet with a thick nose stalls the wheel.** The pallet comes down behind the tooth it
  has just let go and lands on it. The nose has to be a sharp wedge whose back is steeper than
  its working face.
- **The flat at a tooth's tip uses up the drop.** With a 0.3 flat and a 0.35 drop the wheel
  jammed. Now 0.2 and 0.5.
- **The two pallets do not behave alike**, because the anchor turns and a pallet does not move
  exactly straight into the wheel. On the solids this shows as the flank met on the entry
  side only.
- **Gears of 25 and 10 teeth with a 24-tooth escape wheel** leave the wheels a sixth of a
  tooth out of place after every move; 24 and 10 with an escape wheel of 20 or 25 do not.

From the fourth session, on the pawl:

- **A strut seated in a saw tooth pushes badly.** For the nose to stay seated, the push has to
  lie between the two faces of the notch. Over 60° of the star that leaves the push nearly
  radial at one end of the stroke. Hooking the tooth helps the lever arm and then the shank
  no longer fits past the tooth below.
- **A lobe in a cup needs no lip on the star's side.** The king's weight holds the lobe at the
  cup's lowest point from wherever it lands; the cup reaches only 25° past that point,
  because further on it would meet the star's boss.
- **The next lobe decides where the stroke may end.** The pawl's head has to pass it on the
  way down. If the lobe stands straight below the head, the head lands on it squarely and the
  pawl stands as a strut. The pushed lobe therefore ends a move at 38° above level, the next
  one sits to the left of the head's path, and the head's underside is a ramp that meets it
  on its upper right.
- **The fence finds the lobe.** Hanging, the pawl leans its fence on the side of the lobe it
  will push; the cup is then 0.1 mm off centre below it, whatever the socket's play.
- **The socket has to be cut to the arm.** A socket with a wedge-shaped opening either let
  the knuckle out or stopped the arm too early; its lips now follow the arm's two edges.
- **Two pieces, one variant name.** Knight and king both have a variant `playing`. Each piece
  has its own `tests/<piece>/snapshots/`, because creating the king's beside the knight's
  overwrote it.

From the fifth session, on the run:

- **A load that is off centre is paid for in the guide.** The body's weight acts in the
  middle; the pawl holds it up 3 mm to the right and 7 mm to the front, and pushes sideways
  as well. The guide is only 15 to 18 mm long, and the forces on it add up to 1.3 to 1.5
  times the weight at a friction of 0.3. A flat share for "the guide" hid this.
- **Friction that fades with speed cannot show a stall.** A tooth on a pallet then always
  creeps off in the end. The arbors need friction that holds a stopped part.
- **Out of beat is worse than weak.** With the pendulum hanging 2° off the anchor's centre
  the first beat is easy and the second is the one that fails.
- **A wheel that nothing pushes on is thrown about.** After the king has landed the pallets
  can meet the wheel anywhere, flanks included; only the driven part of a run says whether
  a nose meets a flank.

From the sixth session, on giving the king margin (section 5 has the figures):

- **A start that is tested with a kick hides a weak start.** The king's sudden lean throws
  the pendulum 2° off its rest, and that carried most of what "in beat" seemed to give. A
  design has to be judged from true rest and from every angle the hand may leave.
- **A flat ramp recoils more.** Past the release a flat ramp pushes the wheel back further
  for every degree of the anchor, which brings the tooth ahead back against the pallet's
  nose: the flank is met at 8.3° instead of 9.2°, although the teeth stand further apart.
- **Two pallets that are not mirror images hang the pendulum askew.** The entry pallet's ramp
  runs away from the arch's middle and the exit pallet's towards it. With the light bob that
  was 0.46° of hang for an arch of equal ends. One degree of arch at one end moves the hang
  by 0.3°, which is how the hang of 1.0° is set.
- **A pendulum that starts off its drawn rest shifts the film.** The run then starts with
  the wheel pushed back, and frames drawn from the drawn rest were 0.6° out. The layout
  now takes the anchor's rest from the same parameter as the solids.
- **A scratch script named `numbers.py` breaks numpy**, which imports the standard module of
  that name.

## 12. Open points

1. **Nothing is printed.** A lobe is Ø1.6 on a stalk 1.0 wide, the cup's finger is 0.5 mm at
   its tip, a tooth of the escape wheel has a 0.2 flat, the anchor's arbor turns in holes of
   1.3. All of these print rounder and tighter than drawn, and friction decides whether the
   escapement runs.
2. **The king ticks for one second, not two.** Sixteen beats 0.04 to 0.10 s apart are about
   sixteen a second. Whether that is heard as ticking or as a rattle the model cannot say.
   Section 5 has what a longer tick would cost.
3. **The pallets stand 0.41 mm in the wheel.** That is about one width of a printed line.
   Pallets 0.07 mm deeper were run (section 10). Pallets that print shallower let a tooth go
   earlier, which is easier to drive, and at some depth a tooth slips past both: not run,
   because the parameter does not go below 3°.
4. **The pendulum's offset of 1° counts on the lean.** Both the lean's side and its size come
   from the statics of the guide, not from a print. A king that leans less is covered down
   to 1.1° (section 10); one that leaned the other way would be 3° out of beat.
5. **The run starts from a wheel at rest in its drawn place.** After a move the wheels can
   run on by up to half a tooth; the next move then has a beat more or less. Not run through.
6. **The pawl falls in by its own weight only**: 0.1 g, with its centre of mass 14° inside
   the knuckle while it waits under its lobe. If the king is set down tilted more than that
   towards the pawl's side, the pawl hangs away from the star and that move does not tick.
   Friction in the socket takes about 6° of the 14°. A counterweight on the pawl would widen
   this; not designed.
7. **The king leans while it sinks**: 2° to the left and 3° to the back, by the play in the
   plunger's guide, and stands up again as its base lands. The lean to the back shows.
8. **A hand pressing the king down** drives the wheels harder, so it buzzes instead of
   ticking, and a king that is pushed all the way down has no stroke left to tick with.
9. **Fingers reach the pendulum** through the rear plate, and the escape wheel from the
   front.
10. **The anchor's arch is 17 mm deep** and reads as a roof under the arch. Two parts on one
    arbor, pallets in front and pendulum behind, would be lighter to look at and would need a
    way to set one against the other. The arch is now also half of the pendulum's weight on
    its arbor.
11. **Surfaces are plain**, as on the knight: no chamfers, no tracery in the arch, no pinnacles
    on the columns, the crown's block is a plain bar.
12. **The feet cannot be released** once clicked in, as on the knight.
13. **No sign that the king has moved** (for castling) and no way to reset one. The brief asks
    for it; it is not part of this build.
14. **The plunger's guide and the 0.86 mm fall** are not looked at for wear or noise.

## 13. Next steps, in order

1. **The client's view of the second build**: the films in `img/`, and the trade in section
   5 between a tick that is sure and one that is long.
2. **Test prints.** The model has gone as far as it can without a measurement. Smallest
   first, and each one measures a figure the model assumes:
   - the escape wheel with the anchor on two pins in a strip, a thread round the wheel's
     arbor and a weight on it: the torque at which it starts is the pallets' friction;
   - the plunger in its guide with the frame's weight on the pawl: what the guide takes, and
     how far and to which side the king leans;
   - the star with the pawl and its socket;
   - then one king complete in one colour.
3. **If a printed king has less margin than the model**, what is in reserve, as the model
   values it: a dry lubricant on the pallets and in the guide (the table in section 10 is
   read one or two rows higher); six grams of steel in the base (about 0.03); a guide with
   the load nearer the middle (about 0.04, and a new layout of the layers).
4. Open point 10, with the client's view of it: a lighter anchor in two parts.
