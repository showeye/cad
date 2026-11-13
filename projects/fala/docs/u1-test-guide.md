# Stage 3B — U1 fit ladder and loaded contact test

Fala **0.2.0** continues approved Nikisz/corkscrew A. Print the fit ladder first;
use its result to tune the rig. The decorated terrace and provisional 3:1 input
remain later work. These are development parts, not a production release.

## Files and reproduction

From the repository root:

```sh
uv sync --all-packages
uv run python projects/fala/engineering/prepare_u1.py
uv run python projects/fala/engineering/prove_contact.py --export --render
uv run python projects/fala/engineering/prove_contact.py --variant loaded_rig --export --render
uv run cadkit show fala -v loaded_rig
```

Use `prepare_u1.py --render` to regenerate review images. Outputs stay in
`projects/fala/dist/fala/0.2.0/`. Each variant has assembly STEP/GLB/3MF, STL
parts, source/parameter/hash manifest, and a `print/` directory with explicitly
oriented **individual STEP/STL and a geometry-only plate.3mf**. Each variant
also has a ZIP including this guide. Reference hardware is excluded from print
files. The print manifest links to the assembly manifest by SHA256.

The 3MFs do not yet include a Snapmaker machine profile or painted supports.
Import them as separate objects, preserve orientation and XY placement, and
inspect the layer preview before printing. They are test plate geometry, not
released Orca projects or printer instructions. Do not print the assembly 3MF.

## What to print

| Variant | Parts | Purpose |
|---|---|---|
| `u1_fit_030` | Labelled full carriage, axle coupon, guide coupon | 0.30 mm nominal allowances |
| `u1_fit_040` | Same, label 40 | 0.40 mm nominal allowances |
| `u1_fit_050` | Same, label 50 | 0.50 mm nominal allowances |
| `contact_rig` | Frame, cam/thumbwheel, two identical carriages | Unloaded control rig |
| `loaded_rig` | Same plus two removable slotted ballast masts | Measured loaded comparison |

Labels 30/40/50 mean **total** clearance: bore minus shaft diameter, cheek gap
minus 2.4 mm keel thickness, and jaw opening minus 18 mm cam diameter. These
are separate measurements even though each ladder variant uses one nominal
value for all three. Finite-pad lean changes the actual seated return gap; a
label of 40 does not promise 0.40 mm measured rocking or return clearance.

Print one common cam from `contact_rig/print/cam_and_thumbwheel.stl` alongside
the three fit rows, on a separate plate or with its XY placement rearranged.
Keep its supplied vertical-axis orientation. It is needed to assess the jaws;
the fit-row packages contain the carriages and coupons, not a duplicate cam.
Defer the full frame until the fit results are known.

The cam and guide both use 4 mm smooth steel surfaces. The axle coupon contains
two aligned **horizontal** 4+c bores with the frame's wall thickness and one
**vertical** 4+c bore matching the cam's print direction. Test these separately.
The guide coupon reproduces the real slot and keel cheeks; slide its labelled
carriage through the usable rise while rocking it by about ±6°. The jaw coupon
is the actual carriage and can be tested on the real cam. Do not use a printed
rod as the steel diameter reference.

Start with one PLA colour, 0.4 mm nozzle, 0.20 mm layers, four walls, five top
and bottom layers and 20% infill. These are starting settings, not measured
production settings. Use identical settings and filament for ladder and rig.
Disable hole/XY compensation and adaptive layers for the first comparison;
record any elephant-foot compensation. Keep seams off working faces. Do not
change several settings between rows. Print time and filament use must come
from the saved slicer project after support inspection; no estimate is released
from CAD volume alone.

## Orientation and supports

| Part | Bed orientation | Support rule |
|---|---|---|
| Frame and guide/axle coupons | Floor down | Initial candidate: no supports; inspect 4.3–4.5 mm bore crowns and slot bridges |
| Cam/thumbwheel | Thumbwheel down; axle vertical | No supports; the cam's shallow lateral drift grows continuously from the wheel |
| Carriage/jaw coupon | Local −X deck end down; neutralise assembly lean | Use brim and painted supports on leading **X end faces** of lower jaws, keel and boss |
| Load mast | Shared flat +Y face of foot and mast down | No supports; keep the ballast slot clear |

The side-oriented carriage has a narrow first-layer footprint. Support must
reach its second lower pad and the keel before those features start. Keep
support off the broad ±Z cam contact planes and the keel's two ±Y sliding
faces. Its hidden X end faces carry no intended sliding contact. The nut pocket
must stay accessible after support removal. Inspect these regions in layer
preview; automatic support defaults have not established an acceptable result.
If the slicer cannot support only the allowed end faces, stop that plate and
send the preview for a revised split-part design. Do not sand a working face
or accept a support scar because a tighter row will compensate for it.

## Purchased hardware and retention

| Item | Quantity | Geometry/selection |
|---|---:|---|
| Smooth steel axle | 1 | Ø4 × 80 mm, straight, supplied with clean ends |
| Shaft collar | 2 | DIN 705, Ø4 bore × Ø8 OD × 5 wide, supplied with set screw |
| Shoulder screw | 2 | Elesa+Ganter `ISO 7379-4-M3-12`: Ø4 shoulder, **12 mm shoulder**, 7 mm M3 thread, Ø7 × 3 head |
| M3 prevailing-torque nut | 2 | 5.5 mm AF, total height at most 4 mm; verify purchased geometry and thread engagement |
| Optional mast mounting screw | 2 | ISO 4762 M3 × 8 |
| Optional mast mounting nut | 2 | ISO 4032 M3, nominal 5.5 AF × 2.4 high |
| Ballast pack | 2 | Individually weighed M3 bolt/nut/washers; chosen after weighing each moving assembly |

Dimensions come from the [Elesa+Ganter shoulder screw sheet](https://live-katalog.ganternorm.com/pdf/ganter/en/7379.pdf),
[Gardette DIN 705 table](https://gardette.com/en/catalog/shaft-collars-din-705)
and [Bossard ISO 4762 table](https://media.distrelec.com/Web/Downloads/_t/ds/1003763_eng_tds.pdf).
The 4-M3 shoulder size is a **vendor extension**, not a size in the official
ISO 7379 sheet. Verify against datasheets and actual purchased parts; similar
looking shoulder screws can have different threaded lengths. CAD depicts
nominal envelopes, without threads, sockets or detailed set screws. Locknut
height is a conservative 4 mm envelope, not a claim about a particular brand.

The collars sit 0.5 mm outside each frame end support, preventing loss of the
axle without preloading the frame. Two adjustable stops remain serviceable;
they are appropriate to a bench rig, not a released anti-tamper product.
The cam is axially trapped between the frame supports. The guide screw's
shoulder seats at local Y=22; its head starts at Y=34, leaving 1.5 mm behind
the Y=32.5 bracket. Tightening against the nut seats the shoulder in the boss,
not against the slot. Its thread points into the carriage and stays out of the
sliding slot. Frame cheeks are 2 mm lower than 0.1.0 to clear the larger boss.

Check that the selected nut's locking insert is fully engaged, at least one
full thread projects, and the shoulder is seated while the slot remains free.
Stop if the bolt bottoms early or the nut spins in the pocket. Use light hand
tightening, mark bolt/nut positions, then check them again after 100 turns.
Do not use glue or assume PLA clamp load survives heat or endurance.

## Assembly order

1. Remove hidden supports. Record each fit separately, without sanding. Pick
   the smallest row that slides freely without forcing; record loose motion.
2. Before installing the cam, place the guide locknuts in the front-loaded
   pockets. If using masts, fit their M3×8 screws and plain nuts now. The screw
   head sits above the foot; the nut sits directly below the deck.
3. Thread the right carriage over the cam's left end, then the left carriage.
   Keep the masts loose of the frame while doing this. Lower the group into
   the keel cheeks. The guide screws are not fitted during this lowering.
4. Pass the Ø4 axle through the frame and cam. Fit collars outside both frame
   supports with 0.5 mm clearance; tighten their supplied set screws.
5. Insert the two shoulder screws from the rear through the slots and into
   their carriage nuts. Confirm the shoulder seats and the slot stays loose.
6. Turn by hand slowly through two full turns each way, unloaded first.
   Stop at any binding, jaw lift, loose fastener or visible contact marking.

The tested assembly paths sample axial threading and vertical lowering of the
cam/carriage group; they do not certify hand/tool access or a 15 minute build.
The optional mount/ballast hardware is installed before the moving group enters
the frame. Removal reverses these steps; no moving joint uses glue.

## Set a representative load

The earlier calculation assumed **15 g per moving bay, CG 30 mm above its
deck**. Weigh the complete moving group for each bay: carriage, shoulder screw,
locknut, mast, mast screw and nut. Include everything that moves. Determine its
vertical centre of gravity by balancing the removed group in a side orientation.
Then weigh the complete adjustable ballast pack (including its bolt and nut).

For measured unballasted mass m0 and CG z0 above deck, choose ballast mass
mb = 15 − m0 grams and locate the **pack's CG**, not merely its screw centre, at:

```
zb = (15 × 30 − m0 × z0) / mb    [mm above deck]
```

The mast slot's centre-height range is 14–138 mm above deck by default. Its
1.6 mm rails and offset foot print flat together without supports. A nominal
screen using solid CAD envelopes and **assumed** densities of 1.24 g/cm³ for
PLA and 7.85 g/cm³ for steel gives about 11.57 g unballasted, CG 7.03 mm above
deck: about 3.43 g ballast at 107.37 mm would reproduce the assumed target.
Thread/socket envelopes and actual infill change those numbers; they establish
adjustment headroom, not the real load. Weigh,
position and recheck the combined assembly; target 15±0.5 g and 30±2 mm.
Keep ballast symmetric front/back about the mast to limit roll bias. Confirm
neighbour clearance with the actual washer/bolt envelopes through a full turn;
the CAD sweep includes masts and mounting hardware but **no ballast pack**.
If m0 ≥15 g, zb is outside the slot, or the pack contacts anything, do not
claim the assumed load was tested. Report actual mass/CG and revise the fixture
or agree a heavier representative load. The test mast is not a roof or facade.

## Record and return

Use `u1-results.csv` for phase/force observations and `u1-fit-results.csv` for
fits. Include photos of both carriage orientations, working faces, support
removal, nut seating and the finished rig. Save the Orca project and its layer
preview, settings, time/filament estimate, measured masses and CGs.

1. **Fits:** measure actual shaft/shoulder diameters, bore diameters where
   accessible and keel thickness/gap. Record free, dragging, seized or loose
   for every row and interface. A nominal allowance is not a measurement.
2. **Unloaded baseline:** measure starting and steady tangential force at the
   16 mm thumbwheel radius every 30° in both directions. Use a low-range force
   gauge and a consistent tangent pull. Report force in N; shaft torque is
   force ×16 in N·mm (mN·m). Record the phase datum with a photo and use it for
   both directions. Repeat three times after 20 gentle bedding-in turns.
3. **Loaded comparison:** fit balanced test packs and repeat the same readings.
   Include peaks between logged points; stop on a catch. Video one slow full
   turn forward and reverse with sound. Geometry alone cannot predict friction.
4. **Lift/rock:** at 0°, 90°, 180° and 270°, record deck lift and lateral
   movement of a marked point **60 mm above deck**. Apply the same measured
   light probe force each time (start at 0.1 N); state its direction and value.
   Do not interpret lower-jaw clearance as roof-height backlash.
5. **100-turn screening:** inspect fastener marks, powder, polished tracks,
   scraping, squeaks and force change. Stop if anything loosens or binds.

Advance only when every turn is continuous both ways, parts remain captured,
no contact face is damaged, and the force/rock measurements have been reviewed.
The 16 mm direct thumbwheel does not establish the future product's two-finger
effort at an unconfirmed 3:1 ratio. No absolute premium-feel force/backlash
threshold has been approved yet. These results choose the contact geometry;
10,000-turn, warm-window, overload and shipping trials remain later gates.
