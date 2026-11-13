# Serce na węgiel: design notes for the motion proof

Engineering reasoning that is not in the look brief. Sections 1 to 8 were written on 2026-11-13,
after the concept was approved and before any product geometry existed: sections 4 to 7 are the
plan. **Section 9 is the state of the motion proof as built, written at the end of the second
session on the same day. Where it differs from sections 4 and 5, section 9 is right.**

Coordinates as in `concept/heart_concept.py`: origin at the heart's hidden tip, z up, front is -y,
the viewer's left is -x. Units mm and degrees.

## 1. Decisions (client, 2026-11-13)

| Question | Decision |
|---|---|
| Look | 1 Bryła (the lump) |
| Opening | A Skrzydła (wings) |
| Lining | Honey |
| Ballast | Yes, about 150 g of steel |
| Filament | Not final. Probably the five PLA colours of the report in the sibling repository, `../blend/filaments/README.md` (see section 7) |
| Room | No figures, no religious objects |
| Edition number | A small swappable tag under the foot, for example 07/50 |
| Price | Retail about 2 × cost, with a 25% discount to the retailer; ideally 3 × cost |
| The earlier build | "The heart was just one box, with gaps. It simply was not reflecting the idea." |

The client also noticed that the wings overlapped the heart in the concept pictures. Section 3 is
the answer.

## 2. What the earlier build sets as the acceptance test

The brief says to build the motion proof "as plain shapes". The earlier attempt took that to mean
a box, and it was rejected. For this project "plain" means undecorated, not simplified:

- The shell in the motion proof is the real faceted Bryła heart, split into the real wings and
  back half. No room detail, no false cracks, no texture.
- Closed, the seams are hairlines. No gap wider than 0.3 mm anywhere on the closed heart, and no
  gap under the wings where they meet the coal bed.
- A collision test, not a look at a picture, proves that nothing overlaps at any point of the
  turn.
- The renders of the motion proof must already read as a heart of coal that opens to a room.

## 3. The wing collision and the hinge

### What was wrong

In the concept model the hinge axis lay 3.2 mm inside the wall. Measured with exact booleans, each
wing cut into the fixed back half through the whole opening, up to 972 mm³ (8% of the wing) at 120°
of ring turn, and up to 71 mm³ into the room.

### Why

A wing folds back until its outer skin meets the outer skin of the back half. Seen from a pivot
that lies a depth `h` under both skins, skin at radius `r` from the pivot is free to swing through

    free arc = 2 × ridge + 2 × acos(h / r)

where `ridge` is how far each flank facet leans back from the plane that touches the heart along
the V edge (0° for a flat flank). At `r = h` the free arc is zero. So either the pivot lies on the
surface, or everything nearer to the pivot than some radius `R` must be a round barrel that turns
in a cove, and `h` must be small enough that the skin at `R` clears the swing:

    h ≤ R × cos((swing + margin) / 2 − ridge)

With 3.2 mm of depth and no barrel, a 125° swing was never possible.

### Options

1. **Pivot exactly on the flank edge, no barrel.** Geometrically the cleanest: the heart is convex,
   so a wing turning about a line on its surface cannot touch anything, and the flank seam is a
   plain butt joint. Rejected for now because the pivot has no good place to live. The axis is
   the corner of the wing's foot, so a coaxial journal overlaps the foot by only a quarter of its
   section, and half of the journal's top would show on the coal bed. The two axes also meet at
   the heart's tip, which leaves about 5 mm of length for a 12 mm journal. The wing would be held
   by a weak joint at its foot only.
2. **Pivot just under the skin, in a barrel on the flank (chosen).** A 2 mm steel pin runs the
   whole flank inside a barrel of 2 mm radius that belongs to the wing. The barrel shows as a
   rounded ridge along each flank. The pin is held at the bottom in the coal bed and at the top in
   a short fixed knuckle on the back half, so the wing is carried over 45 mm and cannot wobble.
3. **A groove instead of a barrel.** Same arithmetic, but a notch about 8 mm wide on each flank.
   Worse to look at.

### The chosen numbers (now in `concept/heart_concept.py`)

| Name | Value | Meaning |
|---|---|---|
| `WING_MAX` | 125° | Swing of each wing |
| `SWING_MARGIN` | 5° | Spare free arc at full open |
| `FLANK_RIDGE` | 18° | Lean of each flank facet; the two facets meet at 144° along the hinge line |
| `HINGE_R` | 2.0 mm | Barrel radius |
| `HINGE_DEPTH` | 1.36 mm | Pivot depth under both flank facets, from the formula |
| Barrel proud of the facets | 0.64 mm | `HINGE_R − HINGE_DEPTH` |
| `HINGE_GAP` | 0.3 mm | Between barrel and cove |
| `BARREL_TOP` | 35.5 mm | Barrel length up the flank from the coal bed |
| `KNUCKLE_TOP` | 50.5 mm | End of the fixed knuckle. The axis is inside the lobe until about 49 mm, so the knuckle must reach past that or the walls collide there too |
| `LINING` | 1.2 mm | Was 0.8; the barrel and the heel need the thickness, and thin honey would show the black |

The ridge trades against the barrel. A sharper ridge hides the barrel but narrows the room near the
flanks:

| `FLANK_RIDGE` | Barrel proud of the facets | Flank set back 10 mm from the seam plane |
|---|---|---|
| 12° | 0.80 mm | 2.1 mm |
| 18° | 0.64 mm | 3.2 mm |
| 24° | 0.49 mm | 4.5 mm |
| 30° | 0.36 mm | 5.8 mm |

Other details of the fix:

- The wing's wall runs back past the seam plane as a **heel** 2 mm deep along the barrel, so the
  barrel has a root. The back half is cut away to match.
- Nothing fixed inside the heart (room, cellar block) may come nearer than 4.4 mm to a hinge axis.
- Every facet recipe now keeps the straight ridge intact from the tip to past the tangent point.

### Result

Exact boolean overlap, both wings, 23 positions from closed to open, against the back half, the
room, the coal bed and each other:

| Look | Worst overlap |
|---|---|
| Bryła | none (below 0.001 mm³ everywhere) |
| Szlif | none |
| Pokład | 2.7 mm³ with the back half at 30° of turn. Its stepped bands break the straight hinge line. Not pursued, because the look was not chosen |

What it changed to the eye: a narrow rounded ridge along each flank, a short fixed knuckle where
the ridge runs into the lobe, and a slightly sharper lower flank. All concept images were rendered
again from the corrected model.

Still open on the hinge:

- Whether the ridge is acceptable to the client on the closed heart. If not, option 1 is the
  alternative and needs a different way to carry the wing.
- The barrel is a plain cylinder in the model. In the product it should be faceted like the rest.
- 1 mm of PLA round a 2 mm pin is the thinnest wall in the piece. The hinge coupon tests it.

## 4. Planned build of opening A

### Parts

| Part | What it is | Notes |
|---|---|---|
| Wing, left and right | Front quarter of the shell with barrel, heel, root and lever in one piece; coal outside, honey lining | Printed with the hinge axis vertical, so the pin bore is round |
| Back | Back half of the shell with the two fixed knuckles, the cellar block under the floor, lining | Screwed to the coal bed from below, after the wings are in |
| Room | Floor, back wall and furniture, four colours | Stand-in blocks in the motion proof |
| Coal bed | Faceted mound; its two main facets are square to the hinge axes | Holds the two root bores and the pillar for the tie screw |
| Chassis | Plate inside the ring with a hub down to the foot | Guides the slider |
| Slider | Moves front to back; two yokes, one per lever | Carries the follower through a sprung shuttle |
| Shuttle | Small block with the follower pin | One steel spring between shuttle and slider |
| Ring | Grip ring with 20 flats; a circular groove in its web, off-centre | Turns freely between foot and coal bed |
| Foot | Disc under the ring; ballast, feet, edition tag | |

Bought: 2 hinge pins 2 mm, 1 follower pin 3 mm, 1 compression spring, 1 M4 tie screw and insert,
2 M3 screws and inserts for the back, 1 spring washer for ring drag, about 150 g of steel washers,
3 silicone feet.

### Kinematics

- Ring angle `t`. The groove centre is `ECC` off the ring axis, so the follower moves
  `y = −ECC cos t` (exactly `−ECC cos t + sqrt(GR² − ECC² sin² t) − GR` for a groove of radius
  `GR`). Front is closed.
- Each wing has a lever of length `L = 11` on its root. The lever swings ±62.5° about the position
  square to the slider, so the slider moves `2 L sin 62.5° = 19.5 mm`, and with `y` measured from
  the middle of that travel the wing angle is `62.5° + asin(y / L)`. This is `wing_angle()` in the
  concept code.
- **Seat:** the wings reach their seats `e = 1 mm` of slider travel before the cam's dead point.
  From there the shuttle moves on alone and squeezes the spring. So `ECC = (19.5 + e) / 2 = 10.26`,
  and the first 26° of ring turn move nothing. That dwell is wanted: it holds the piece shut when
  it is picked up by the ring.
- The spring is preloaded against a stop inside the slider (about 2 N), so there is no lost motion
  in mid-travel. At the dead point it holds the wings shut with about 3 N at the slider.
- Leverage: the cleft is 40.4 mm from the hinge axis. At the ends of the swing the lever works at
  `cos 62.5° = 0.46` of its length, so play at the slider shows 8 times larger at the cleft (3.7
  times in mid-swing). That is why the closed position has to come from the seam faces and not
  from the drive.
- Gravity tries to open a closed wing with about 1.3 N·mm (18 g, centre of mass 12 mm in front of
  an axis that leans 37°).

### Constraints found while laying it out

- **The two hinge axes cross 2.4 mm above the heart's tip.** At a distance `d` from the crossing
  the axes are `0.96 d` apart. The root starts 17.0 mm from the crossing, so a root of 8 mm with a
  1 mm web between the bores can be 7.7 mm long, one of 6 mm can be 9.7 mm. Each millimetre of seat
  height (`Z_SEAT`, now 15) adds 1.26 mm, but raises the ridge of the coal bed, which is 23.7 high
  now and must stay under the floor at 31.
- **The lever cannot pass through the root bore.** Plan: a keyhole slot in the bore, placed under
  the back half's foot. The wing is put in turned about 197° from closed, where the lever lines up
  with the slot, and is then swung into its working range. The back half goes on afterwards and
  covers the slot. The wing then cannot lift out, with no screw.
- **The yoke must not cross the lever.** A ball between two plates collides with the arm. Instead
  the lever carries a crank pin parallel to the hinge axis, pointing down, and the yoke takes the
  pin below the arm. Two plates square to the slider's travel give line contact and leave the pin
  free to move in the other two directions, which it needs because its path lies in a plane
  tilted 37°.
- **Cam against hub.** With the ring's inner radius 34.8 and `ECC` 10.26, the groove radius can be
  20.9 at most, and the fixed hub in the middle 15 mm in diameter at most. A scotch yoke or a cam
  on the ring's inner wall does not fit or binds.
- **Tie screw.** One M4 from the foot through the hub and chassis into a pillar of the coal bed.
  The insert must end below z = 5.5, because the roots occupy the centre above that.
- **Slider.** 47 mm long at most (ring inside 69.6, travel 20.5). A central slot about 30 mm long
  lets the pillar through and guides it. The follower sits 20.9 mm behind the slider's middle, near its
  end.
- **Stacking, bottom to top:** foot −17.4 to −13.8; ring −13.4 to −0.9 with its web at −12.8 to
  −9.4; chassis plate −9 to −6.5; slider −6.5 to −3.5; yokes up to about +5 inside the coal bed;
  coal bed from −0.5.
- The coal bed stands on the chassis on two wall-like legs left and right of the slider, which
  also guide it.

### Not designed yet

- The slipping clutch between grip ring and cam. Estimate for sizing: with 80 N·mm of slip torque,
  a finger caught at the cleft when the gap is 10 mm feels about 1.1 N per wing. A magnetic
  coupling (two pairs of small magnets) would be silent and would not wear.
- The soft detent at closed. The 26° dwell may already be enough.
- Ring drag for "stays where it is left". Gravity drives the ring back with about 3 N·mm at most,
  so little drag is needed; the spring washer sets it.

## 5. What the motion proof has to show

1. `projects/serce` is a `cadkit` package: `Params`, `variants`, `process`, `version`, `build()`.
2. Every part is one valid solid; every fit and clearance is a named parameter.
3. A test turns the ring through 360° in both directions in small steps and finds no overlap
   between any two parts (`cadkit.validate.overlaps`).
4. Closed: the gap at the centre seam and at the seam plane is the nominal value, and the wings
   rest on their seats with the spring squeezed.
5. The ring torque from a simple statics model stays within a stated band over the whole turn.
6. Open: the share of the room seen from the front and from 45° to either side, by ray casting.
7. Nothing of the drive is visible from outside, closed or open, apart from the barrels.
8. A short animation of the bare version, stills at the five steps of the look brief, and the
   model live in the OCP viewer.

## 6. Other findings to carry forward

- **The heart hovers over the front of the coal bed.** The bed's front and back slopes fall away
  under the wings, which leaves a wedge-shaped gap up to 9 mm high below the front of the heart.
  Proposal: carry the two main facets of the bed to the full depth of the heart, so the wings sit
  on it everywhere. The bed becomes a ridge 24 mm high and 44 mm long. Show the client both.
- **A sliver of honey shows at the tip of the closed heart,** through the 0.4 mm gap between the
  wings and the bed. The lining must stop short of the wing's lower edge.
- **Print orientation.** A wing has two visible faces, so neither may carry support. Printed with
  the hinge axis vertical, the lobe's inner roof is the only steep overhang; hence the rule that
  the cavity roof is a vault no flatter than 40°. The underside of the wing's foot is hidden and
  may carry support. If that fails, the alternative is a skin and a liner printed separately.
- **Heat.** No PLA part bent or stretched at rest; the only spring is steel.
- **Massing details that break the print rules:** pendant lamp on a 1 mm cord, 1 mm stool legs,
  0.5 mm tile grooves, five facet slivers under 4 mm.
- **`cadkit` as it is on `main`:**
  - There is no `cadkit new`; copy the layout of `projects/carnall`.
  - `validate.overlaps` gives exact overlap volumes between named parts and is the tool for the
    collision test. `projects/carnall/tests/test_motion.py` is the pattern.
  - `render.py` and `_blender.py` are written for Carnall: fixed camera positions for a
    180 × 90 × 120 mm model standing on z = 0, and Carnall's title on the review sheet. They must
    be generalised (cameras fitted to the model, floor at its lowest point, text from the product)
    before Serce can use them, without changing Carnall's output.
  - `process.FDM` has a 220 × 220 × 250 build volume. The U1 is 270 × 270 × 270; define a process.
  - Parts whose names start with `reference_` are not exported as printable. Use that for bought
    hardware and for the stand-in room.
  - The root `pyproject.toml` lists only `projects/carnall` as a workspace member and in
    `testpaths`.

## 7. Filament and cost

The report `../blend/filaments/README.md` (dated 2026-11-13, no physical samples yet) recommends
five matte PLA filaments. Four of them cover this piece:

| Colour here | Hex in the renders | Filament | Published colour |
|---|---|---|---|
| Coal black | `#17171A` | Bambu Lab PLA Matte Charcoal | no usable code |
| Honey | `#EDAE1C` | Polymaker Panchroma Matte Savannah Yellow | `#F4C35C` (measured print): lighter and yellower |
| Bone white | `#ECE5D2` | Bambu Lab PLA Matte Desert Tan | `#E8DBB7` |
| Tile red | `#B4502A` | Bambu Lab PLA Matte Terracotta | `#B15533` |

- All four are matte. The look brief argues that coal needs some sheen, so the coal sample should
  still compare Charcoal with a standard and a glossy black.
- Charcoal is a dark grey-black, not jet black. Judge it on the sample.
- The renders should move to the published colours once the filaments are confirmed.

Cost, for the price rule (retail about 2 × cost, 25% to the retailer, ideally 3 ×):

- Filament: about 165 g at 76 to 90 zł per kg, so 12 to 15 zł a unit.
- Hardware: not priced yet.
- Print time: 12 to 16 h a unit (estimate). Assembly: about 10 minutes.
- What "cost" includes (machine time, labour, rejects) is the client's to say. Ask when the bill
  of materials exists.

## 8. Test prints to plan after the motion proof

- Hinge coupon: 40 mm of flank with barrel, cove, pin and knuckle; checks the 1 mm wall, the 0.3 mm
  gap and the swing.
- Root and lever coupon: bore, keyhole, crank pin in the yoke.
- Seam coupon: two rims meeting, to judge the hairline.
- Coal sample: one faceted patch in Charcoal, a standard black and a glossy black.
- Lining step coupon: honey over black at 0.8, 1.2, 1.6 and 2.0 mm.
- Vault coupon: lining faces at 35°, 40° and 45° without support.
- One interior detail (stove) at final scale in four colours.
- Heat soak: the coupons at 60 °C for two hours.

## 9. The motion proof as built (state at the end of session 2, 2026-11-13)

The stage is not finished. The geometry, the kinematics and the tests exist and pass, with one
known defect (9.3, item 1). The renders, the animation and the review document for the client do
not exist yet. Section 9.5 lists what is left.

### 9.1 What exists

| Path | What it is |
|---|---|
| `src/serce/model.py` | `Params` (every fit and clearance), `build()`, the pose, `effort()`, `_render_poses()`, `presentation()` |
| `src/serce/_heart.py` | The Bryła heart as half-space polyhedra; the hinge line and its local frame |
| `src/serce/_facets.py` | The facet planes, frozen from the concept recipe (seeds 7 and 23), so no random generator is involved |
| `src/serce/_shell.py` | Wings and back half, the hinge tools, the lever outline |
| `src/serce/_base.py` | Coal bed, slider, pusher, chassis, cam disc, grip ring, foot, bought hardware as stand-ins |
| `src/serce/_room.py` | The concept kitchen as a stand-in, clipped to the space the real room may fill |
| `src/serce/_kinematics.py` | Ring angle to slider, pins and wing angle; the statics model of the ring torque |
| `tests/test_motion.py` | The proof as tests (9.4) |
| `tests/test_model.py`, `tests/snapshots/honey.json` | The standard gate. The snapshot is of work in progress: regenerate it when the geometry changes |
| `tools/motion_report.py` | Figures and numbers for the review document. **Written, never run** |

The model is `serce`, version `0.2.0`, one variant `honey`. `Params.turn` poses it: 0 closed, 180
open. Hidden printed parts are grey in the model so that they can be read; they are black in
production.

New in `cadkit` (all with tests): `features/polyhedron.py` (solids from half-spaces, exact
offsets), `features/mechanical.cam_groove` and `features/motion.cam_rate`, `cam_pressure_angle`,
`smooth_step`, `visibility.py` (what a distant viewer sees, by exact parallel rays), `process.U1`,
and a generalised `render.py` / `_blender.py`: a product module may define `presentation` (views
fitted to the model, stills at animation poses, hidden parts per view, materials, sheet text).
Carnall's five renders were rendered again through it and differ from the old ones by one grey
level at most; its sheet text moved into `carnall/model.py`. **The fitted views and Serce's
`presentation()` have not been run through Blender yet.**

### 9.2 The design as built, and why it differs from section 4

**Parts.** Printed: wing left, wing right (each coal and lining in one print), back half (coal,
lining; includes the knuckles and the cellar block), coal bed, slider, pusher, chassis, cam disc,
grip ring, foot. Ten printed parts, plus the room (a stand-in here). Bought: 2 hinge pins 2 × 55,
1 follower pin 3 × 12, 1 compression spring, 1 M4 × 12 button-head screw and nut, 4 M3 × 8 screws
and 4 short M3 heat-set inserts (two hold the back half, two hold the chassis to the bed's legs),
6 disc magnets 5 × 2, 1 fender washer M24 (ISO 7093, 26 × 72 × 5, about 139 g) as ballast, 3
silicone feet. All sizes are placeholders to verify against datasheets.

**Size.** Closed 83.5 × 76.9 × 107.9 mm, open 133.4 mm wide. That is 4 mm taller than the concept:
the ballast washer needs 5 mm and the clutch needs a floor in the grip ring. Solid volume of the
printed parts is 125 cm³ (155 g if printed solid; less with infill).

**Seams.** The outer 1.0 mm of the coal wall stops 0.15 mm short of each seam plane, so the closed
heart shows a groove 0.3 mm wide and 1.0 mm deep with a closed, black bottom. Behind it:

- Front to back: wall and lining of wing and back half meet on the seam plane. That face is the
  seat that sets the closed position.
- Centre: a lap. The inner wall and the lining of the left wing run 0.6 mm across the centre plane
  under the outer layer of the right wing, which is cut back for it. The wings part square to the
  centre plane, so the lap slides straight out. Clearance 0.1 mm at its end, 0.2 mm over it. The
  wings never touch each other, so neither can hold the other off its seat.
- Under the wings: 0.3 mm over the bed. The lining starts 1.0 mm above the wing's foot. The back
  half's inner wall stands on the bed, so there is no line of sight under it.

**Hinge.** As section 3, with three changes found by ray casting:

- The heel is 1.4 mm deep, lower than the barrel (radius 2.0). With a 2.0 mm heel there was a
  straight slit 0.3 mm high along the whole hinge, through which the room showed from the side.
  Now the barrel blocks every straight line. `Params` rejects a heel that is too deep.
- The hole in the wing round the fixed knuckle is coal all through (the lining keeps 0.8 mm
  clear), so no honey shows round the knuckle.
- The knuckle is clipped to 0.64 mm proud of the lobe, so it fades into the lobe instead of ending
  as a stub.

The pin is 2 × 55 mm. It is meant to be pressed into the root (the press zone is not modelled yet)
and to run in the fixed knuckle at the top and in a pad under the root at the bottom. It goes in
from below, after wings and back half are on the bed, and stands 3 mm out below the pad so that
pliers can pull it for service. The two pins end 2.9 mm apart, short of where their axes cross.

**Root, lever and crank pin** (one piece with the wing). The root is a collar of radius 3.0, 1.5 mm
deep, on a shoulder in the bed, and below it a journal of radius 2.6. The shoulder carries the wing
and closes the running clearance to lines of sight. The collar's top is flush with the bed facet,
so **a round hairline of radius 3.2 shows at the foot of each flank ridge**, about 1.8 mm outside
the flank. A root as thin as the barrel would be invisible but would shear at about 200 N mm.
The lever is 11 mm long and 4.5 mm thick. It leaves the root as a neck on one side and widens to 6
mm at the printed crank pin (5 mm diameter, 4 mm long). Estimated strength of the neck: about 325
N mm at 40 MPa, the weakest link when a wing is forced by hand with the ring at a dead point
(about 7 N at the wing's tip). The root-and-lever coupon has to measure this.

**Assembly keyhole.** The wing goes in along its axis turned 197.5° from closed; the lever passes
a keyhole of its own outline in the bed's roof and is then swung into its range. The back half
slides on from behind along the ridge with the wings closed, and is held by two screws from inside
the bed. A test moves the parts along this path and finds no collision.

**Coal bed.** The full-depth ridge of section 6 (half length 22 mm), ends at 50°, on a low slab
that closes the grip ring from above, with a skirt round the ring's neck. It is hollow under a
roof 4.5 mm thick, stands on two legs on the chassis, and carries the pads for the pins. The short
ridge of the concept (12.5 mm) is `Params(bed_ridge=12.5)`; **it does not leave room for the
follower at the back** (the slider hits the bed's end wall when open), which is a second reason
for the long ridge besides the gap under the heart. The client has not seen either yet.

**Drive.** Grip ring, cam disc, follower, slider, as planned, with these differences:

- *Pusher instead of a sprung shuttle.* The follower is fixed in the slider. The slider's front
  plates pull the crank pins back (opening). A pusher bar rides on the slider behind the pins; a
  spring presses it forward against a stop on the slider, 0.15 mm (`yoke_gap`) behind the pins.
  Closing, the pusher pushes both pins. When the wings seat, the slider goes on by 0.8 mm
  (`over_travel`) and the spring holds the wings shut: 12 N mm on each wing against at most 1.7 N
  mm of gravity. The pusher can yaw, so each wing seats on its own. A rigid shuttle with two
  yokes would leave one wing short of its seat by the tolerance, magnified eight times.
- *The spring is preloaded against a stop, not pinching the pins.* Pinching gave no backlash but
  the pins slide along the plates fast near the ends of the swing, and the friction made the ring
  torque swing between 13 and 88 N mm. Gravity keeps the pins on the pusher in travel anyway.
- *The cam is a pure cosine* (the groove is a limaçon, `cadkit.features.mechanical.cam_groove`),
  stroke 20.31 mm, nothing moves for the first 22.9° either side of closed. A circular groove off
  centre is not a cosine for a follower on a radial line (the dwell came out at 35°). A profile
  with a separate seating ramp gave a smoother torque but zero cam rate where the wings seat, so
  that a blocked wing could be wedged with over 100 N by a light twist; rejected.
- *Clutch.* The cam disc lies on the floor of the grip ring and is coupled to it by three pairs
  of magnets. Estimated slip torque 60 to 90 N mm; not verified, needs a coupon. At the dwell's
  end the cam rate is 3.95 mm per radian, so a slipping clutch at 70 N mm limits the slider force
  to about 18 N.
- *Ballast and thrust.* The ring runs on the steel washer on a narrow land near the hub.

**Effort** (statics model in `_kinematics.py`, assumptions in `Params`: friction 0.3 PLA on PLA,
0.2 steel on PLA, hinge friction 1 N mm, ring drag 12 N mm): 11 to 21 N mm while the wings move,
up to 31.5 N mm on the last 20° of closing, never below 9 N mm, so the ring does not run by
itself. The one step, about 9 N mm, is the spring's preload coming onto the cam as the wings
seat. The ring drag is a guess until the clutch and the washer are tried.

**Sight lines closed in the base.** The ring's neck stands inside the bed's skirt, and the ring's
floor stands inside the foot's rim, so neither horizontal gap gives a straight view inside.

### 9.3 Known defects and open points

1. **A glimpse of the slider with the wings open** (`test_drive_is_hidden[180.0]`, marked as an
   expected failure). One viewing direction, about 20° off a hinge axis, looks down the 0.2 mm
   clearance round a root's collar, on through the part of the keyhole that cuts the shoulder,
   and reaches the slider 20 mm below. A ray can travel up to 41° of arc inside that clearance,
   so narrowing the lever's neck further cannot close it. Options: (a) a small printed plug that
   closes each keyhole from below after the wings are in (two more parts, robust, and the lever
   could be full width again and three times as strong); (b) accept it and state the criterion
   as "nothing but 0.2 mm clearances"; (c) a smaller clearance at the collar. Recommended: (a).
2. Not modelled: the press zone of the hinge pin, the edition tag under the foot, the real room.
3. Not verified, all for the test prints: magnet clutch torque and ring drag; the spring (2.5 N
   preload, 3 N/mm assumed); the strength of root, lever and crank pin; the 0.3 mm seam groove
   and the lap at print tolerance.
4. Printing: the wing has root and lever under its foot, so it prints on support under the foot
   (a hidden face). The bed's hollow has a ceiling at 37° that needs support inside. The root
   bores stand 37° from vertical in the bed.
5. Still as in the concept: five facet slivers under 4 mm, the barrel as a plain cylinder.
6. For the client: the flank ridge (still unanswered), the collar hairline at its foot, the long
   ridge of the bed, 4 mm more height, the firm last 20° of closing.

### 9.4 What the tests prove

`uv run pytest projects/serce` (about three and a half minutes):

- no two parts overlap closed; none overlap at 126 positions of a full turn (every 2.5° while the
  wings move, every 0.5° at first opening); the assembly path is free;
- closed: wing and back half touch on the seat, the wings stand 0.1 mm apart, the groove measures
  0.3 mm at both seams, the wings stand 0.3 mm over the bed, the spring is squeezed by 0.8 mm;
- closed, 47 viewers all round and along both seam planes see no point of the room or the linings;
- kinematics: 125° at half a turn, symmetric, dead points at both ends, pressure angle under 32°;
- effort within 5 to 40 N mm in both directions, without a step over 10 N mm;
- open: over 97% of the room in view from the front, from 45° to either side and from above;
  the share in view grows steadily from 23° on;
- the drive is hidden closed and at mid-swing; open, see 9.3 item 1;
- the animation poses match the CAD poses; bad parameters fail before any geometry is built.

### 9.5 What is left to close the stage

1. Decide and fix 9.3 item 1, then run the tests and regenerate the snapshot
   (`CADKIT_UPDATE_SNAPSHOTS=1 uv run pytest projects/serce/tests/test_model.py`).
2. `uv run cadkit build serce -v honey --render --animate`. Expect to debug the fitted views in
   `cadkit/_blender.py` and `serce.model.presentation` on the first run.
3. `uv run python projects/serce/tools/motion_report.py` (strip, charts, cut views, the two beds,
   numbers), then write `docs/motion-proof.md` for the client: animation, the five steps, each
   requirement of section 5 with its evidence, what changed against the plan and why, the
   questions in 9.3 item 6.
4. Update `README.md`, stream the model to the viewer (`uv run cadkit show serce -v honey`), and
   stop for the client's review. Commit only when the client asks.

