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

## Motion proof: as built (2026-11-13, in progress)

Everything above is the plan from the concept checkpoint. This section is the state of the
model `fala` 0.3.0 (`src/fala/`), what it rests on, and what is open. Look 1 Nikisz, drive A.

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
- **Capture.** A third, crowned pad on a long arm passes under the cam. The gap is 0.45 nominal
  and breathes from 0.3 to 0.6 over the turn, because the arm sits between the two upper pads
  and sees the wave's curvature. A house cannot be lifted off by more than that.
- **Ground block in place of a thin tile with skirts.** The block is 11.5 thick. Its front face
  is the "earth" that rises behind the fixed front wall, so no separate skirt is needed and
  the house has a flat bottom to print on.
- **Joints that cannot be seen through.** The upper half of each block reaches over its
  right-hand neighbour and the lower half under its left-hand one, and the whole joint steps
  sideways behind the facades. A straight lap leaked light along the joint when seen from the
  front; the stepped one does not. Pavement joint 0.8.
- **Held along the street at pavement level.** A fixed blade rises through the block inside
  the house; a short land in the block bears on its edges 1.5 below the pavement. The house
  leans about that point, so the slab edges at a joint stay level within 0.1 and the pavement
  reads as one ribbon. A fin on the rear panel, in a notch at the back of the block, is the
  second point: the two together keep the house square to the street.
- **Kept upright by gravity.** The cam stands 13 behind the house's centre of gravity, so the
  weight tips the house forward onto a bead on the blade (front, high) and back onto the rear
  panel through the tip of the sled's arm (rear, low). The guide sits on those two points and
  does not cross its clearance. They lie on either side of the cam, so guide friction cannot
  wedge the house.
- **Drive.** Module 1 gears, 11 and 33 teeth with profile shifts +0.4 and -0.4, centres 22.
  The cam and its gear are one part on the 4 x 200 steel axle. The handwheel shaft carries the
  pinion on a hexagon. Turning the wheel clockwise, seen from its side, sends the wave away
  from it.
- **Assembly as intended:** sleds in from above, cam and axle in from the back into the open
  jaws, rear panel on, houses dropped on from above. Not yet checked in the model.

### Numbers

| | |
|---|---|
| Size | 224 x 67 x 93 mm; base 67 deep |
| Wave | 8 houses at 22, rise and fall 7.0, lean 6.0 degrees each way, 0.85 waves on the street |
| Cam | radius 8, centre 3.5 off the axle, axis 27.3 behind the low facades and 24 below the pavement |
| House | 16.4 g tall bay, 14.7 g low bay, sled included: assumed, 30 % of the solid volume |
| Printed parts | 22: base, rear panel, cam, pinion, handwheel, knob, 8 sleds, 8 houses |
| Bought | 1 steel axle so far; screws for the rear panel and the knob are not modelled |

Force model, one pass of the wave both ways. Seat is the smallest guide force as a share of a
house's weight (it must stay above zero); drag is the largest guide friction against a house's
travel as a share of its weight (it must stay below one); torque is at the handwheel.

| Friction | Seat | Drag | Torque, N mm |
|---|---|---|---|
| 0.1 | 0.22 | 0.13 | 0.5 to 1.1 |
| 0.2 | 0.13 | 0.28 | 0.9 to 1.6 |
| 0.3 | 0.02 | 0.49 | 1.4 to 2.3 |
| 0.35 | lets go | 0.63 | 1.5 to 2.8 |
| 0.45 | lets go | 1.12 | 1.9 to 4.0 |

At a friction of 0.3 the handwheel needs 0.10 to 0.16 N at its knob, forward or back. These
are model results, not measurements: the house mass and the friction are assumptions.

### Open points

1. **The guide at high friction (the one known defect).** Above about 0.3 the cam's drag on the
   pads, which acts front to back, outweighs the gravity seat in part of the turn. The house
   then rocks in its guide clearance, up to about 0.8 mm at the roof. At 0.45 the guide drag
   passes the house's weight, so a house would hang on the way down until the capturing arm
   pulls it. Ways forward, not yet chosen:
   - Move the sled's spine behind the cam, jaws open to the front, everything loaded from the
     back. Both guide points can then sit 9 above and below the pad height. In a simplified
     side-view model (not the full one) that variant keeps a seat of about 0.18 at a friction
     of 0.3, where the present layout keeps 0.02 to 0.10 depending on its settings. Its drag
     at 0.45 is no better, and the base would be about 67 to 68 deep. It is not modelled.
   - Grease on the pads: at 0.1 to 0.2 the present design has ample margin.
   - Narrow the block's slot in front of the blade, so that a house that lets go moves less.
   The limit is in the nature of a gravity seat: the seat needs the centre of gravity far from
   the cam, the drag needs it near. `bead` and `cam_gap` are the two parameters that trade them.
2. **Hidden mechanism: not yet proved.** `cadkit.visibility` has not been run. At both ends of
   the street a shelf hides the cam, but the joint to the bookends is 3.6 and 4.0 wide.
3. **Assembly paths: not yet checked.** The cam has to enter eight jaws at once; only the pads
   have lead-ins.
4. **Not designed yet:** how the house holds on its sled, how the pinion and the knob are kept
   on, the rear panel's screws, the look of the two bookends.
5. **Print plan to confirm:** the cam stands 190 tall; the rear panel prints on its outer face
   (the fins have 45 degree backs for that).

### Tried and dropped

- **The branch's rig:** short keel (2 to 5 mm of rock at the roof), flat pads, a shoulder screw
  for each house.
- **Posts behind the sled's plate,** both guide points in front of the cam: guide friction then
  feeds on itself and the house jams at a friction near 0.45.
- **Holding the house square by the posts alone:** the push along the street, where the cam's
  surface slopes, twists the house off one post. The rear fin replaced it.
- **A rear guide point at the cam's height:** it would close the jaws that the cam enters.
