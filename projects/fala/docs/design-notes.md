# Fala: design notes for the motion proof

**Historical starting points.** Stage 3A now supersedes the follower/contact and
assembly assumptions below: see [the finite-contact rig](contact-rig.md). In
particular, the rear keel prevents simply dropping the cam into the rear-open
jaws; the rig uses axial carriage insertion before lowering the group into its
frame. The full product's assembly method is still to be developed.

Engineering reasoning behind the look brief that is not written there. Everything here is a
starting point for step 3 and is open to change. All dimensions in mm and degrees.

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
