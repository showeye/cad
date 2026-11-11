# Engineering concept — full form, v0.1.0

## Geometry and motion

Axes: X along the horizontal cylinders; Y along the main shaft; Z up. Front is -Y.
The base is 180 × 90 mm; the headframe header reaches Z=120 mm. All moving envelopes
stay within that footprint at the tested poses. There is no roof or front wall over the engine.

| Item | Nominal design |
|---|---|
| Main shaft centre | X=10, Z=44 mm |
| Main wheel | Ø64 × 6.5 mm, eight spokes, central cord groove |
| Upper sheave | Ø24 × 4 mm, six spokes |
| Upper axle | X=69, Z=104 mm; tension adjustment 0…1.5 mm upwards |
| Cord | Ø1.1 mm reference; 310.047 mm neutral loop length at zero lift |
| Cord pitch radii | 31.8 / 11.8 mm |
| Upper sheave ratio | 2.694915 turns per main-shaft revolution, same sense |
| Crank throw | 8 mm radius, 16 mm piston stroke |
| Connecting rod | 37 mm between pivot centres |
| Cylinder lanes | Y=-20 and +20 mm |
| Crank phases | 0° and 90°; unverified historical arrangement |
| Shaft coupling | Hexagonal, 5 mm over corners; not a standard fastener size |
| Initial fit | 0.4 mm diametral clearance, configurable 0.3…0.6 mm |
| Model components | 49 single solids, including two visual reference components |

The left-hand slider is solved exactly:

`x_slider = x_shaft + r cos(theta) - sqrt(L² - r² sin²(theta))`.

The rear mechanism uses `theta + 90°`. CAD and animation use the same pose function; the
animation applies rigid transforms to the exported CAD mesh. It runs a full turn and then
reverses, returning both the cord marker and the non-integral sheave rotation to the start.
The marker is a visual witness only, not an attached bead required for the product.

The closed cord uses exact circular contact arcs and external tangent lines. This mirrors
the real engine's Koepe principle while avoiding a finite-capacity spool. It is a compressed
demonstration loop between two wheels, not a complete mining hoist reeving system.

The hand grip sits on the **front eccentric pin**, outside the connecting rod. Extending
the main shaft through that rod's plane would obstruct it near dead centre. This arrangement
leaves the mechanism visible and avoids that interference. The grip can rotate freely on
the pin; its round shape makes that spin visually irrelevant.

## What is checked

- Every sellable variant passes BRep validity, positive volume, one solid per component,
  closed oriented mesh and per-part build-volume checks.
- Every component has a snapshot of volume, area, bounds, face count and solid count.
- Exact BRep intersections are checked at **72 positions, 5° apart**, for each moving part
  against the rest of the assembly and for the cord against the architecture and frame.
  Only the visual rope witness is excluded; there is no contact whitelist hiding collisions.
- Numerical checks cover rod closure, stroke, speed ratio, cord tangency and loop length.
- Selected render transforms are compared with independently rebuilt CAD poses, including
  the forward/reverse endpoints.
- Export tests verify repeatable CAD hashes and re-import STEP, STL, GLB and 3MF.

STEP contains named geometry. The palette is preserved in GLB, 3MF and renders. OCCT's colour
style ordering varies across processes, so STEP omits those styles to keep its bytes stable.

This is **sampled collision checking**, not a mathematical swept-volume proof between samples.
It does not model deformation, surface roughness, friction, screw torque or accumulated wear.
Static decorative parts may intentionally seat into brick or other stationary parts for bonding.

## Prototype bill of materials and retention

The 47 non-reference CAD components are a design breakdown, not 47 mandatory separate print
jobs. Group stationary colour details in the slicer where practical. The coloured 3MF is an
assembly reference; determine actual print plates after the coupons pass.

| Group | Prototype approach |
|---|---|
| Plinth, bed, brick walls, roof strip, trestle | Printed; bond stationary interfaces after dry fitting |
| Window trims, coping, cylinder bands, plate | Separate colour parts; bond trims, leave plate pins removable |
| Wheel, crank discs, hex shaft | Separate keyed pieces; align the disc pin phases to the drawing |
| Piston/crosshead units | One rigid printed component per lane, including piston rod and head |
| Guide rods, pivot pins and upper axle | Printed geometry supplied; evaluate smooth metal replacements of matching nominal dimensions |
| Bearings and upper spacers | Printed prototype bushes; do not glue rotating surfaces |
| Front/rear shaft caps | Two bought-in M2 screws; 1.6 mm pilot holes are provisional, verify screw and material on a coupon |
| Crank-grip end cap | One bought-in M1.6 screw; 1.2 mm pilot is provisional, verify against the chosen screw |
| Rod pin caps | Prototype bonded to their pins; keep adhesive off rod bores |
| Crosshead pins | Retain the inner ends after insertion; develop a serviceable positive retainer before production |
| Upper axle/tension slots | Requires external clamping collars or a shoulder-bolt arrangement; final hardware is not modelled |
| Cord | Bought-in flexible round cord; start with Ø1.1 mm and tune grip, join and tension experimentally |

The screw sizes are choices for prototype development, not a claim of standard-compliant
thread geometry; no threads are modelled. Pilot sizes, screw lengths and retention hardware
must be confirmed physically. In particular, this design is not ready to ship with unretained
crosshead pins or upper axle. Printed 3 mm eccentric pins may require reinforcement or metal
substitution after strength and endurance tests.

## Assembly order

1. Print shaft/bush, rail/slider, pin/rod and screw-pilot coupons. Select fits before the model.
2. Dry fit bed and plinth. Check the nameplate pocket and removable two-pin plate.
3. Fit each piston head through its cylinder cutaway and feed the rod through the gland before
   seating the cylinder. Feed paired guide rods through supports and crosshead; check the stroke.
4. Put the bushes and wheel on the hex shaft; insert it through the bed bearings. Mount the
   quartered crank discs. Attach rods to crossheads and eccentric pins, then retain pivots.
5. Install grip, end caps and trial hardware. Check free motion in both directions by hand.
6. Fit brick walls and roof fragment after the engine passes the motion test. Route the cord
   through the tall end opening, around both wheels, and fit the headframe sheave and spacers.
7. Raise the upper axle only enough to prevent slip. Clamp it and check the cord join passes
   the grooves without catching. Install header and nameplate after the cord runs freely.

Print wheels and rods flat; orient small shafts and thin pins for strength and inspect their
surfaces. Brick walls should normally print flat with relief up. The connected engine bed and
trestle need orientation/support trials; no support-free or print-in-place claim is made.
Avoid turning until temporary supports and bonding have been removed from running faces.

## Release work

The next useful work is the bare physical mechanism: smooth motion at slow speed, secure
pins, a reliable cord join, comfortable effort and at least 500 turns each way. Then perform
handling, packaging and visitor tests from the research brief. Measure print time, material
and assembly cost before pricing. Exact museum paint, plate facts and replica fidelity still
need confirmation during the visit.

Changing intended geometry requires a version bump after release and explicit snapshot
regeneration. The initial 0.1.0 is an unreleased concept baseline. The manifest records source
hashes as well as git revision and dirty status, so uncommitted work remains traceable.
