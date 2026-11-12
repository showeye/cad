# Serce: plain CAD motion prototype, 0.1.0

The approved direction is **Bryła + two wings (A) + honey lining**, recorded from the user's
2026-11-12 choice. The new model is in `src/serce/model.py`, registered as `serce` in cadkit.
The earlier decorated concepts remain visual references; this model is the plain engineering
study required before the finished sculpture.

## What is built

The base ring contains the eccentric circular cam. A steel follower drives a slider on two
parallel guide rods. Two slotted forks on the slider capture the wing-tail balls; their necks
leave room for the lever arms to sweep. The wings rotate on opposed inclined pin axes. A fixed
rear carriage carries the hinge ears and a reference block reserves the room volume.

The CAD assembly has **7 proposed printed bodies and 7 reference bodies**. The reference room
block is honey coloured; the blue carrier and slider use an engineering review colour. These
colours distinguish the moving system in the preview. Final production drive parts are black.

| Proposed printed body | Quantity |
| --- | --- |
| Foot | 1 |
| Ring with integral cam groove | 1 |
| Carrier with rod supports | 1 |
| Slider with forks and bearing bores | 1 |
| Shell with integral hinge knuckles and tail | 2, handed |
| Rear plate, supporting columns and hinge ears | 1 |

Reference bodies reserve two Ø3 × 46 mm guide rods, two Ø3 × 48 mm hinge pins, a Ø4 × 10 mm
follower, a plain Ø4 × 20 mm tie-screw envelope, and a 36 × 20 × 30 mm room block. These are
nominal envelopes, not a purchased hardware BOM: fastener heads, retainers, spring preload and
the final mounting hardware still need design and physical qualification. The tie-screw envelope
extends 0.6 mm below the foot; its production head/recess and length are unresolved.

The closed nominal assembly envelope, including reference hardware, is approximately
**82 × 76 × 100.4 mm**. Fully open it is approximately **143.4 × 76 × 100.4 mm**. The rear plate,
base drive and hinge clearances are deliberately exposed for inspection. This study does not yet
establish the finished closed shell, hidden mechanism, support-free visible surfaces or shipping
retention; coal cladding and finished seam treatment follow the mechanical trials.

## Evidence and limits

The full workspace run passed **101 tests**. All three Serce poses and all three coupon variants
pass cadkit's valid-BRep, positive-volume, single-solid, watertight-mesh and build-volume gates,
with committed geometry snapshots. Existing Carnall snapshots continue to pass.

The motion test checks **361 poses**, ring angles 0° through 360° at 1° increments, using exact
OCCT solid intersections after a bounding-box check. No positive-volume collision above
`1e-5 mm³` was found. The moving parts are the cam ring, slider, follower and two shells; a
separate full-assembly check also covers fixed pairs. This is a sampled check, not a mathematical
proof of clearance between samples. Default geometry is swept; the 0.3 and 0.6 mm fit endpoints
are also checked at closed, mid and open poses.

Independent tests check that the follower lies on the actual circular groove, that the rotated
lever endpoint reaches the same slider displacement, and that the animation's rigid matrices
match the CAD poses. The loop contains 49 frames, including the repeated start frame. Blender
only displays CAD tessellations and rigid poses; it does not author the mechanism geometry.

The cam uses a 20 mm groove radius, approximately 9.76 mm eccentricity, approximately 19.51 mm
slider stroke, and 125° wing travel for a 180° ring turn. Continued ring rotation closes the
wings during the next half turn.

A numerical gravity-only estimate using the CAD wing volumes/centres and an assumed PLA density
of 1.24 g/cm³ gives approximately **0.0025 N·m maximum ring torque**. It excludes friction,
preload, print error and inertia. It neither predicts actual hand effort nor proves holding.
The calculation is saved as `ideal-load.json` beside the closed-pose export.

The default 0.4 mm diametral allowances are intentionally trial fits. Cam and fork play can
accumulate into several degrees of wing lost motion; a successful clearance check is not evidence
of the precise, backlash-free feel in the brief. A repeatable preload/drag system is the next
mechanical problem. Finger guarding, blocked-wing overload behaviour, 5,000-cycle wear and PLA
hot-window performance remain unproven. Do not release this as a finished working product.

## Open and reproduce the CAD

Run from the workspace root:

```sh
uv sync --all-packages
uv run cadkit list
uv run cadkit show serce -v motion_open
uv run cadkit build serce --all
uv run cadkit build serce-coupons --all
uv run pytest
```

The OCP viewer command requires the viewer to be connected. CAD construction, tests and exports
work without Blender. To regenerate the optional presentation from the CAD meshes:

```sh
uv run cadkit build serce -v motion_closed --animate
```

Outputs are in `dist/serce/0.1.0/{motion_closed,motion_mid,motion_open}/`. Each contains the named
STEP assembly, coloured GLB, assembled-reference 3MF, per-printed-body STL files and a manifest
with parameters, metrics, hashes, library versions and the git revision/dirty flag. The closed
pose additionally contains `motion.gif`, stills and `presentation.blend`.

The assembly 3MF keeps CAD coordinates and is **not a production print plate**. Use the dedicated
coupon layouts below for the first physical fit checks.

## First U1 fit prints

`src/serce/coupons.py` cuts small sections directly from the actual cam, fork and hinge/tail
geometry. It registers `serce-coupons`, with `fit_030`, `fit_040` and `fit_060` variants. The
suffix is the total diametral/slot allowance in hundredths of a millimetre, not clearance per side.

Start with `dist/serce-coupons/0.1.0/fit_040/assembly.3mf`. Its three separate bodies are laid out
on z=0; the hinge/tail cut face is oriented along the hinge axis so the bore prints vertically.
The individual `parts/*.stl` files preserve those same positions if 3MF import is inconvenient.

Use the intended black PLA, a 0.4 mm nozzle, 0.16 mm layers, four walls and 20% infill as initial
coupon settings. Keep XY scale at 100%, and record any hole compensation. Inspect the fork
overhangs and tail bridge in Orca; local support may be needed on their non-contact undersides.
Keep support off the bores, cam groove and ball/slot contact faces. These are geometry layouts,
not sliced Snapmaker Orca projects: temperature, support settings, print time and filament use
must be obtained from the user's actual profile.

| Coupon | Trial hardware / mating part | Record |
| --- | --- | --- |
| Cam track | Measured Ø4 mm smooth pin | Groove width, pin sliding effort, catching and lateral play |
| Fork | Ball on the hinge/tail coupon | Slot width, ball diameter, movement through the fork, rubbing and reversal play |
| Hinge/tail | Measured Ø3 mm smooth pin | Bore fit, easy rotation, splitting, bridging and visible layer defects |

The 0.4 mm set has nominal 4.4 mm cam-track width, 3.4 mm fork slot and 3.4 mm hinge bore.
Try `fit_030` if the reference set is loose, or `fit_060` if it binds. Compare prints made with
the same filament, orientation and compensation; do not ream or sand the mating surfaces.

For the next tuning pass, provide the chosen variant, measured pin/ball/bore/slot sizes, slicer
profile/compensation values and a short description of sticking or play. Photos of the bed-facing
and contact surfaces, plus a short motion video, will distinguish geometry from print defects.
The fit test does not establish holding torque or cycle life. Coal-surface and interior-detail
coupons still need to follow once the mechanical fits and preload approach are settled.
