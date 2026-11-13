# Fala: design notes for the motion proof

Engineering reasoning behind the look brief that is not written there. The sections up to
"Rejected along the way" are the plan from the concept checkpoint; the last section,
"Motion proof: as built", is the state of the model and supersedes them where they differ.
All dimensions in mm and degrees.

## Concept model geometry (as drawn in `concept/look_concepts.py`)

- Axes: x along the street, y depth (front is -y), z up. Pavement at rest is z = 0, facade at y = 0.
- Street: 8 houses at 22 pitch = 176 long.
- Ground tile: y from -16 to 36 (52 deep), 3 thick, kerb step 5 wide at the front, skirts 1.6
  thick reaching z = -20.
- Base: y from -19 to 39, z from -46 to -6 (top of the fascia). Left bookend 12 wide, to z = 10.
  Right bookend (engine house) 29.5 wide, to z = 23.
- Handwheel 38 diameter, knob 10 long. **Overall length in the concept is about 235**, over the
  230 limit. Target is 225 or less: shorten the pitch to 21.5 or trim the engine house.
- Kolonia house: body 19 wide, 32 deep, eaves 26, ridge 38.5, chimney top 45.

## The wave

- `z(x, t) = A sin(k x - t)`, with A = 3.5 and k = 2π · 0.85 / 176 (0.85 wavelengths on the street).
- Each unit rests at its left and right edges, so it is a chord of the sine: centre height is
  the mean of the two edge heights, lean is `atan2(dz, pitch)`.
- Results from `concept/mechanism_diagrams.py`: lean up to 6.0°; gap between neighbours swings
  ±1.77 at the eaves and ±2.63 at the ridge.
- **The concept roofs collide in the troughs.** Roofs and chimneys must be narrower than the
  body, or the gap at rest must be at least 3.1 at ridge height.
- Scaling rules: lean ∝ A·k. Gap swing at height h ∝ h · pitch · A · k². So a longer wavelength
  buys smaller gaps and more rise for the same lean; taller houses cost gap.
- Neighbours' feet sit about 1.8 either side of the shared edge. The height step at a slab
  joint is second order, under 0.1.
- 8 houses over 0.85 of a wave is 9.4 houses per wavelength, inside the 8 to 12 that wave
  builders use.

## Drive A: how each house is held

A house has six freedoms; two must stay free (rise and lean).

- **Keel between two ribs** of the base: a flat plate in the x-z plane. Removes depth shift,
  roll and yaw. The round bar cannot stop roll, so the keel must (two contact lines apart in z).
- **Pin in a vertical slot:** fixes the position along the street. Its height sets where gaps
  appear: at height p above the pin, neighbours shift by p times their lean difference. Pin at
  pavement level keeps the slab joints closed and puts all the opening at the roofline. A pin
  at mid-wall height would halve both, but it cannot be hidden.
- **Two C-feet on the corkscrew:** set height and lean. Each foot has a flat face above and
  below the bar, 2R apart, so the house is driven both ways and cannot lift. Pads should be
  crowned (cylinder axis along y) and narrow in x because the bar's surface slopes under them.
- Jaws open to the **rear**, so the shaft drops in from behind.

## Drive A: the corkscrew

- Round bar, radius about 9, centre offset from the axle by e = A = 3.5, axle at about z = -27.
- **Fixed 4 mm steel axle; the PLA bar turns on it.** PLA on polished steel is the bearing.
- Print it upright: smooth all round, and the helix overhang is under 10°. It is 180 long, so
  it fits in one piece; two halves with a dog clutch are an option. The halves are identical
  only if the street carries exactly one wavelength, not 0.85.
- Gravity alone would hold the feet down up to about 8 shaft turns per second; the C-feet are
  for shipping and rattle, not for speed.
- House weights nearly cancel around the wave: residual torque under 1 mN·m at the shaft.
- Gears 3:1, for example module 1 with 11 and 33 teeth, centres 22 apart, crank axis above the
  cam axis. Check undercut on 11 teeth (profile shift, or 12/36 at module 0.9). Herringbone
  for quiet.
- A plastic-safe damping grease on the axle would give the crank a weighted feel and discourage
  frantic cranking. Compatibility with PLA not yet checked.
- Knob: about 8 diameter, spinning freely on an M3 × 20 screw, which also reinforces it.

## Assembly sequence for A (target 8 minutes)

1. Base on its face.
2. Drop in the eight houses, keels into the slot.
3. Drop the corkscrew with its axle into the jaws and the end saddles.
4. Fit pinion and handwheel.
5. Screw on the rear panel (4 × M3 into captive nuts); it carries the saddle caps.
6. Stick on the rubber feet.

## Print plan

- **Houses upright.** Layer lines read as brick courses and tile courses. No supports: feet and
  keel start on the bed, the underside of the tile bridges at most 22. Two perimeters, sparse
  infill to carry the 37° roof, seams at the back.
- **Base upright,** fascia vertical, inlays 0.6 deep.
- The same four filaments on every plate.
- Matte PLA is filled and may be weaker in layer adhesion; hidden mechanism parts could use
  plain black PLA. To check on test prints.
- Time basis: houses 12 to 18 g each, base about 150 g, about 330 g in total; 500 to 700 tool
  changes on the house plate at an assumed 5 to 10 s each. Not sliced.
- The edition number is parametric text, so each base can carry its own number.

## Heat

- A black base in a sunny window can pass 55 °C. Guards: the steel axle, no preloaded snap fits
  or springs, running clearances of 0.3 to 0.4, nuts instead of threads cut in PLA, ribbed box.

## Ideas for the test prints (step 4)

- Colour swatch: brick against signal red, with and without a bone separator.
- Sample house with three window variants: T-mullion, plain pane, single mullion.
- Foot-on-bar fit ladder at clearances 0.15, 0.25 and 0.35.
- Keel-in-slot fit.
- Two-house rig on a short corkscrew, driven by a small gear motor for 10,000 turns.
- The same rig after an hour at 50 °C.

## Rejected along the way

- **Camshaft of stacked discs on a keyed shaft:** nine parts and a phase to get wrong at
  assembly, where the corkscrew is one part.
- **Gravity-only followers:** quiet, but loose in shipping.
- **Flexible pavement strip:** truly continuous ground, but PLA takes a set in heat.
- **Houses leaning on each other for location:** rubbing contact, stick-slip risk.
- **Face-down printed facades:** best colour inlay, but no relief, against the fixed style.

## Motion proof: as built (2026-11-13)

Everything above is the plan from the concept checkpoint. This section is the state of the
model `fala` 0.4.0 (`src/fala/`), what it rests on, and what is open. Look 1 Nikisz, drive A.
`docs/motion-proof.md` is the report to the client; the reasoning is here.

### The design and why

- **A house is two printed parts: a sled and the house on its ground block.** The sled carries
  every fit. It prints with its flat plate on the bed, so the noses of its pads and its guiding
  edges are drawn by the nozzle in the plane, with no support. The house prints upright on the
  flat underside of its block, also without support. The plan above had one part per house;
  its pads would have been downward-facing overhangs.
- **Crowned pads, solved exactly.** Two pads 16 apart rest on the cam. Each nose is a cylinder
  of radius 12 with its axis front to back. The cam's sideways swing slides under it; in side
  view the nose rides the cam's upper edge, a travelling sine. `cadkit.features.cams` solves the
  pose from that with no sampling. Flat pads (the branch) touch on their sharp edges almost
  all the time.
- **Capture, and a drive that works both ways.** Two more crowned pads pass under the cam, one
  below each upper pad, on short arms from a foot at the bottom of the sled. Because they stand
  under the upper pads, the gap stays between 0.33 and 0.44 through the turn (0.35 nominal).
  A house cannot be lifted off by more than that. They also make the drive positive: if
  friction keeps a house from following by its weight, the cam pulls it down, or turns it
  into its lean, within that gap. Version 0.3.0 had one pad in the middle, whose gap breathed
  from 0.3 to 0.6 and which could not turn a house.
- **Ground block in place of a thin tile with skirts.** The block is 12.5 thick. Its front face
  is the "earth" that rises behind the fixed front wall, so no separate skirt is needed and
  the house has a flat bottom to print on.
- **Joints that cannot be seen through.** A thin lower lap (2.0) of each block reaches under
  its right-hand neighbour, and the whole joint steps sideways behind the facades. Three
  things had to be right, and `cadkit.visibility` found each one: the lap is thin, so the
  open joint below it stays behind the fixed rim even when a house is at the top of its
  travel (a lap at half height showed the sleds straight-on at 10 to 30 degrees above the
  horizon); the step goes towards the handwheel, so the block that owns the lap is also the
  wall behind the pavement joint (stepped the other way, the open joint under the rear lap
  lies straight behind the pavement joint and a line runs through both); and a tab closes
  the small shaft that the step leaves open. The sled's top is rebated at both edges to stay
  clear of the neighbour's lap. Pavement joint 0.8.
- **The street has no open ends.** The first and the last house are end-of-terrace parts:
  on the outer side their block has no lap but 4.4 more of plain pavement, which runs up to
  the bookend. Below the rim a pocket takes that edge. The joint to the bookend is a slot
  between two faces 12 deep, so a sight line down it ends on the pocket's floor, which a
  corbel carries on towards the cam. Version 0.3.0 had a 3.6 and a 4.0 wide gap there, down
  which the first sled and the cam's end could be seen from above.
- **Held along the street at pavement level.** A fixed blade rises through the block inside
  the house; a short land in the block bears on its edges 1.5 below the pavement. The house
  leans about that point, so the slab edges at a joint stay level within 0.15 and the pavement
  reads as one ribbon. A fin on the rear panel, in a notch at the back of the block, is the
  second point: the two together keep the house square to the street.
- **Kept upright by gravity, with stops.** The cam stands 13 behind the house's centre of
  gravity, so the weight tips the house forward onto a bead on the blade (front, 8 above the
  pavement, inside the house) and back onto the rear panel through the tip of the sled's
  centre arm (rear, low). The two seats lie on either side of the cam, so guide friction
  cannot wedge the house. Each seat has a stop 0.5 away: a second bead on the front of the
  blade, facing the wall of the house's slot, and a low bead along the rail, facing the
  sled's stem. A house that leaves a seat moves at most 0.9 at its roof, front to back.
  The blade narrows above the pavement so the slot in the house stays 11 wide.
- **What friction does, and where the limit is.** Two things grow with friction. The cam's
  skin drags the pads front to back, which works against the gravity seat. And every guide
  point slides sideways when the house leans, because the house turns about the pavement
  while the guide points sit well above and below it; that friction resists the lean, and
  only the two pads, 16 apart, can overcome it. The second effect is the one that sets the
  limit: just above a friction of 0.3 one pad unloads. From there on the lower pads take
  over. The guide's part of that moment is about friction x weight x (13 + friction x 14.5), where
  13 is the cam's distance behind the centre of gravity and 14.5 the depth of the pads below
  the pavement; it does not depend on where the guide points are. Only moving the cam up into
  the houses and under their centre of gravity would lower it much. That is a different
  architecture and was not pursued.
- **Drive.** Module 1 gears, 11 and 33 teeth with profile shifts +0.4 and -0.4, centres 22.
  The cam and its gear are one part on the 4 x 200 steel axle. The handwheel shaft carries the
  pinion on a hexagon. Turning the wheel clockwise, seen from its side, sends the wave away
  from it.
- **Assembly:** sleds in from above, cam and axle in from the back into the open jaws, rear
  panel on, houses dropped on from above, starting at the end away from the handwheel. All
  four steps are clear in the model.
- **A house goes in while its sled stands on the crest of the wave.** There it is upright, so
  it comes straight down over its blade and its fin, and the house on its left, already in
  place, leans 3.6 degrees away from it: its wing and its facade plate stand clear of the
  path. A third of a turn of the handwheel (114.75 degrees), turned so that the wave runs
  towards the handwheel, brings the next sled up. The position is not critical: a house
  goes in clear from 40 degrees of the handwheel before the crest to 140 past it
  (`wave.crest`, `tests/test_motion.py`). A house comes out the same way, after the houses
  on its right, because each block lies over the lap of the one on its left.

### Numbers

| | |
|---|---|
| Size | 224 x 67 x 93 mm; base 67 deep |
| Wave | 8 houses at 22, rise and fall 6.8, lean 6.0 degrees each way, 0.85 waves on the street |
| Cam | radius 8, centre 3.5 off the axle, axis 27.3 behind the low facades and 24 below the pavement |
| House | 16.8 g tall bay, 15.1 g low bay, 18.4 and 15.7 g the two end houses, sled included: assumed, 30 % of the solid volume |
| Printed parts | 22: base, rear panel, cam, pinion, handwheel, knob, 8 sleds, 8 houses (3 tall, 3 low, 2 end-of-terrace) |
| Bought | 1 steel axle so far; screws for the rear panel and the knob are not modelled |

Between two houses through one pass (`_gaps.py`; the figures are in
`docs/motion-proof-checks.json`, written by `tools/motion_proof.py checks`):

| | |
|---|---|
| Pavement joint | 0.71 to 0.94 wide (0.8 at rest); its two edges level within 0.15 |
| Wing over the low facade, seen straight on | 1.9 at rest; 0.006 to 3.9 through the pass: never open |
| Wing over the low roof's verge | 0.5 at rest; from 3.1 to an open slit of 1.9 (open point 2) |
| Daylight between walls | none: 12 poses, 105 directions |
| Daylight at pavement level | a slot 0.5 high, seen level with the pavement only (open point 3) |
| House going in from above | clear from 40 degrees of the handwheel before the crest to 140 past it |

Force model, one pass of the wave both ways at 72 crank angles, the same friction at every
contact. Seat is the smallest force on a guide seat and pad the smallest force on an upper
pad, both as a share of a house's weight. Off seat is the share of all poses in which a guide point rests on its
stop; pulled, the share in which the cam pulls on a lower pad. Torque is at the handwheel.

| Friction | Seat | Pad | Off seat | Pulled | Torque, N mm |
|---|---|---|---|---|---|
| 0.1 | 0.16 | 0.31 | none | none | 0.5 to 1.0 |
| 0.2 | 0.10 | 0.16 | none | none | 1.0 to 1.6 |
| 0.25 | 0.07 | 0.08 | none | none | 1.2 to 1.9 |
| 0.3 | 0.03 | 0 | none | 0.4 % | 1.4 to 2.2 |
| 0.35 | 0 | 0 | 9 % | 6 % | 1.7 to 2.5 |
| 0.45 | 0 | 0 | 38 % | 18 % | 2.3 to 3.4 |
| 0.55 | 0 | 0 | 41 % | 28 % | 2.9 to 6.0 |
| 0.6 | 2 poses of 1152 have no balance: they wedge | | | | |

Up to 0.25 every house rides on its two pads and its two seats, and the handwheel needs 0.08
to 0.13 N at its knob, the same forward and back. The two end houses, heavier on one side,
reach the limit first, just under 0.3. At 0.45 the handwheel needs 0.16 to 0.23 N and nothing
sticks. At 0.55 it still turns but unevenly, up to 0.42 N. These are model results, not
measurements: the house mass and the friction are assumptions, and the poses in which the
cam pulls are computed without the small lag in lean (at most 1.6 degrees) that goes with them.

### Open points

1. **Friction is not measured.** The design runs in the model up to a friction of 0.55,
   but the comfortable range ends near 0.25. Figures quoted for dry printed PLA on PLA run
   from about 0.2 to 0.5; no source was checked for this project. The test prints
   have to measure it on the U1's own surfaces. If it comes out above 0.25, a dry PTFE
   lubricant or a plastic-safe grease on the cam and the beads brings it to 0.1 to 0.2;
   whether that is acceptable for the product is a question for the client.
2. **A slit of sky opens at the stepped roofline.** Between walls nothing opens: seen
   straight on, a tall bay's wing covers the edge of the low facade beside it by 1.9 at
   rest and never by less than zero (0.006 at the top of the low facade, in the one pose
   where the two lean furthest apart). Above the low eaves the edge behind the wing is the
   verge of the low roof, 0.5 behind it at rest, and the two part by up to 1.9 over a height
   of about 8 (`_gaps.laps`). The low roof cannot be widened enough to close it: its verge
   would have to stand 2.4 behind the wing's edge, which leaves 1.9 to the tall body where
   the lean needs 2.6. A gable wall on the tall bay, behind the wing and above the low roof,
   would close it. A question of the look: put to the client.
3. **A slot at pavement level lets light through.** The outer parts of each facade plate
   start 0.5 above the pavement (`WING_LIFT`), so that they pass over the neighbour's slab.
   Behind the plates the space between two bodies is open to the back, so a level line of
   sight under the plates runs out over the rear panel. `_gaps.daylight` finds it at an
   elevation of 0 degrees within 5 degrees of straight on, at every pose, and not at 2
   degrees of elevation or at 10 degrees to the side. A sill about 1.5 high along the back
   edge of each block would close it from every angle; on the plates' own side of the joint
   the plate could also come down to the pavement. Not done: it changes the ground block,
   and the foot of each facade is drawn in the full design anyway.
4. **Not designed yet:** how the house holds on its sled, how the pinion and the knob are kept
   on, the rear panel's screws, the look of the two bookends.
5. **Print plan to confirm:** the cam stands 190 tall; the rear panel prints on its outer face
   (the fins have 45 degree backs for that).

Settled since 0.4.0 was drawn, with no change to the geometry: the houses go in from above
(on the crest, see "The design and why"); the full visibility sweep was run on the final
geometry and nothing of the cam, sleds, pinion, axle or blades is in view at 12 poses from
152 directions (the fins on the rear panel are not in the check: they show from the back).

### Tried and dropped

- **The branch's rig:** short keel (2 to 5 mm of rock at the roof), flat pads, a shoulder screw
  for each house.
- **Posts behind the sled's plate,** both guide points in front of the cam: guide friction then
  feeds on itself and the house jams at a friction near 0.45.
- **Holding the house square by the posts alone:** the push along the street, where the cam's
  surface slopes, twists the house off one post. The rear fin replaced it.
- **A rear guide point at the cam's height:** it would close the jaws that the cam enters.
- **Moving the sled's spine behind the cam** (the first way forward listed for 0.3.0): in a
  side-view force model both guide points then sit behind the cam, and guide friction feeds
  on itself. It wedges at a friction of 0.45.
- **A guide channel for the sled's stem at pad height:** it takes the cam's drag where it
  acts, but 20 in front of the cam, and its friction then tips the house. Worse than the
  rear panel from a friction of 0.3 up.
- **The upper bead at 16 instead of 8:** halves the guide's drag, but the seat is lost
  earlier (10 % of poses at 0.3) and the crank torque at 0.6 is higher. With the lower pads
  in place, 4 to 10 is the best range.
- **One capturing pad in the middle (0.3.0):** it cannot turn a house into its lean, so a
  house whose pad had unloaded would have lagged by up to 3 degrees.
- **A roof on the bookend over the pavement's end:** it hides the end joint completely, but
  the end house would have to be hooked under it, and the guide slot leaves no room to do so.
  The open pocket hides the mechanism as well, by the depth of the joint.
- **A shelf under the end gap, standard blocks at the ends (0.3.0):** sight lines pass
  between the shelf and a raised block and reach the first sled.
- **Lowering every house at one crank angle, along its sled's tongue:** neighbours lean up
  to 3.9 degrees differently, and the wing or facade plate of the house in place leans into
  the path of the next block: up to 41 mm3 of overlap, at five of the seven joints.
- **Lowering a house where it and its left neighbour lean alike:** that is on the steepest
  part of the wave, at 5.7 degrees. The house would have to come down that slope to pass
  the neighbour's wing, but the lands in its block must follow the upright blade over the
  last 4: the two paths differ by 0.45 there and the lands have 0.15 of play. Worked out by
  hand, not modelled. The crest needs neither.
- **Upper lap over the right-hand neighbour (0.3.0):** each house's facade stands over its
  left neighbour's pavement edge while that neighbour's block lay over its own, so no order
  of putting the houses in from above could work.
