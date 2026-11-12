# Serce na węgiel: concept checkpoint

Prepared 2026-11-12. **User approved Bryła + two wings (A) + honey lining on 2026-11-12.**
The base design has no electronics. The concept checkpoint required by the original
[brief](brief.md) is complete; work proceeds to the plain CAD motion prototype. These studies
establish a visual direction and candidate drive, not a working product.

The [reference register](../research/references.md) contains 22 annotated references with sources,
local photographs and verification gaps. The conclusions below are design judgements informed by
those references.

## The closed sculpture

Use a symbolic heart with a deep cleft, slightly unequal lobes and an irregular coal fracture
surface. Large faces establish the mass; smaller chips break their edges. Keep the main silhouette
simple enough to recognise at shelf distance. Avoid medical vessels, decorative borders, labels
and a regular triangular mesh.

Standard black PLA with a satin surface is the starting material. Facet orientation should create
the highlight changes; do not rely on painted weathering, transparent effects or glitter. Place
the real shell seams along fracture lines and add a small number of shallow false cleats so the
centre joint does not become the only vertical line. Those decoy cleats are still to be modelled.

The current study is roughly 100 mm high on a 76 mm diameter base. Proportions remain provisional
until the drive fits. A faceted coal bed ties the sculpture into a low turn ring; the user holds
the stationary foot and turns the ring.

![Three looks, closed and open](img/looks_comparison.png)

| Look | Character | Production concern | Decision |
| --- | --- | --- | --- |
| 1 — Bryła / lump | Unequal cleaved faces; strongest coal reading | Preserve the heart outline while hiding joints | Recommended |
| 2 — Szlif / cut | Orderly gemstone facets; a precise jewellery object | May read as black crystal rather than coal | Alternative |
| 3 — Pokład / seam | Layered ledges; a geological specimen | More edges, overhangs and dust traps; heavier walls | Alternative |

The existing illustrations compare form and colour. Layer texture is not simulated, and the tiny
interior details have not been qualified for FDM.

## The room inside

Show a compressed Silesian kitchen, with no people: a pot, table setting and a small coal scuttle
suggest someone has just stepped away. The strongest forms are a tiled cooking stove on the left,
a pale byfyj on the right, a table in front, and a window above the stove. Add a simple wall hanging
and coarse geranium/pot shapes only if they survive the first detail coupon.

The museum's exhibit supports a mid-century domestic setting, not a specific miniature floor
plan. Bonclok documents the stove, white dresser, plants and kitchen textiles. The orange floor in
the study is a deliberate colour simplification: wooden flooring with a tiled area by the stove
would be more faithful. Develop broad floor relief after the motion proof.

| Toolhead | PLA colour target | Roles |
| --- | --- | --- |
| T0 | Satin black, nominal `#17171A` | Coal shell, base, ironwork, window panes, hidden drive |
| T1 | Warm honey, nominal `#EDAE1C` | Room wall, shell lining, small fire accent |
| T2 | Warm ivory, nominal `#ECE5D2` | Dresser, window frame, tablecloth, wall hanging |
| T3 | Terracotta, nominal `#B4502A` | Stove tiles, floor accent, pots |

These are colour targets, not verified spool matches. The concepts distinguish `coal` and
`coal_matte` for rendering; production should map both to T0, giving four filaments overall.
Shells use black + honey; hidden mechanism parts use black; the room uses all four. Honey lining
is the recommendation because the open wings read as a warm frame. Terracotta lining is the
alternative already shown in the comparison below.

![Honey and terracotta lining](img/lining_comparison.png)

Use relief rather than printed miniature lettering or lace strands. Start coupon design with
0.8–1.2 mm raised details, at least 1.2 mm freestanding stems/posts and broad colour islands;
these are proposed trial sizes for a 0.4 mm nozzle, not established machine limits. The current
0.5 mm stove lines and 1 mm lamp stem need simplification or qualification.

## The opening as an experience

At first, a narrow crack admits a sliver of honey colour. The table and stove appear as the two
front shells part. Finally the wings move clear of the sightline and frame the complete room;
the rear shell and interior remain stationary. The slow start preserves the surprise, and the
slow finish helps the user find the open position. Reverse the turn to close.

![A: wing opening sequence](img/opening_a_wings_strip.png)

The current concept aims at a 180° ring turn and 125° travel per wing. A continuous circular cam
could also close during the next 180° if the user keeps turning. The design still needs a clear
tactile open/closed cue and enough adjustable drag to hold every intermediate position.

## Three opening approaches

All counts and times below are planning estimates. There are no sliced production plates, torque
measurements or assembly trials yet. Counts assume integrated two-colour shell linings and a
four-colour room insert; small retainers may increase them.

| Approach | Action and drive | Printed parts, estimate | Bought hardware, provisional | Print time per unit, estimate |
| --- | --- | --- | --- | --- |
| A — Skrzydła / wings | Half turn; eccentric circular groove drives a guided slider and the two wing tails | About 9: foot, ring/cam, pedestal, back shell, 2 wings, slider, room, keeper | 2 hinge pins, follower pin, M4 tie screw + nut, 2 thrust washers, wave washer, optional captive ballast | 9–16 h |
| B — Pokład / seam lift | About 1¼ turns; a coarse screw lifts the top shell 30 mm on two guides | About 10–12 including lifter/slab and guide/drive retainers | 2 guide rods, tie/retaining screws + nuts, thrust/drag washers, optional ballast | 8–14 h |
| C — Rozkwit / bloom | About 2 turns; screw raises the room 12 mm and four links tip four shell shards | About 16–18 including 4 links and 4 shards | 4 hinge pins, 8 link pins, screw/thrust hardware, guide/retaining hardware, optional ballast | 12–20 h |

The ranges budget roughly 6–10 h for shells and drive plus 3–6 h for A's detailed multicolour room.
They assume 0.16 mm layers, a 0.4 mm nozzle, modest infill and slow visible walls. Travel, toolhead
changes, supports and batching can change the result substantially. Replace these estimates with
Snapmaker Orca results once actual parts and orientations exist.

### A — Skrzydła: recommended

![A: wing mechanism sketch and pacing](img/mechanism_a_wings.png)

The fixed back protects the room and gives the open object a composed front. Two moving shells
create fewer fit chains than the bloom. The circular groove permits continuous ring rotation,
which avoids driving into a rigid stop, but does not by itself provide overload protection if a
user blocks a wing.

Primary risks: unequal wing motion from fork clearance, a spatial linkage that may not fit the
coal bed, exposed hinge seams, and back-driving under wing weight. Adjustable axial drag is a
candidate holding method; the wave washer would maintain preload while printed keeper parts
remain replaceable. No friction performance is claimed yet.

### B — Pokład: simplest seam, weaker room view

![B: seam-lift sequence](img/opening_b_seam_lift_strip.png)

![B: screw and guides](img/mechanism_b_seam_lift.png)

One horizontal opening line could hide in a bedding layer. The room must fit inside a straight
clearance prism, making it smaller; the lifted top hides it from above on a shop counter. A fast
multi-start thread brings print-quality and back-driving risks. It requires captive travel
limits and overload protection; a hard stop alone does not meet the forcing requirement.

### C — Rozkwit: largest spectacle and largest fit burden

![C: bloom sequence](img/opening_c_bloom_strip.png)

![C: linked shards and room lift](img/mechanism_c_bloom.png)

Four shards spread around a rising room, giving broad access. The study opens to approximately
190 mm across. Four hinges and four links crowd the narrow lower heart, increase seam count and
leave long levers vulnerable to handling. Synchronisation, pinch shielding and protection against
blocked shards are harder to package at this scale.

![View from above a counter](img/counter_view_comparison.png)

## Engineering review

The sketches establish an opening direction only. Their previous “self-locked” and finger-safe
claims were unsupported and have been removed. The approved A direction now has a
[plain CAD prototype](motion-prototype.md) passing sampled interference checks. Physical feel,
holding and handling remain unproven.

| Question | Finding | Evidence required before full design |
| --- | --- | --- |
| Cam pacing | A's exact circular-groove follower differs from the old sinusoidal approximation; CAD poses and diagram now use the same law | Verify the actual 3D fork and lever construction, including contact and clearance |
| Holding | Zero cam velocity at an endpoint is not a lock; a coarse screw is not automatically self-locking | Measure ring torque and back-driving at open, closed and intermediate positions, upright and inverted |
| Even effort | Smooth geometry does not establish constant hand torque | Force/torque calculation, then a physical drive test over the full cycle |
| Pinch points | A nominal constant gap above the coal bed does not eliminate closing seams | Guard the accessible hinge/tail regions; assess centre-seam closure and blocked-wing forces |
| Stability | The sketch's former 150 g ballast claim was inconsistent with its shallow foot | Package a real captive weight and calculate the centre of mass throughout opening; test one-handed operation |
| Warm window | The specified PLA-only, unprocessed object has no demonstrated hot-window rating | Agree an exposure temperature/duration, measure the object temperature, then test loaded fits and creep |
| Wear | 5,000 cycles is a requirement, not an achieved result | U1 coupons, wear measurement and a repeatable cycle test |
| Print finish | Existing renders show no layer lines; several small details and support orientations remain unresolved | Coal and interior coupons, then oriented parts in Orca with visible faces free of support contact |
| Assembly | Counts and sub-20-minute assembly are unverified | Captive hardware/retainers, replaceable moving parts and a timed assembly trial |

For A, the nominal tail radius is 11 mm, groove radius 20 mm and eccentricity approximately
9.76 mm, giving approximately 19.51 mm slider travel. These are concept dimensions, not fits.
The exact follower ordinate is
`y = -e*cos(turn) + sqrt(R² - e²*sin(turn)²)`; slider travel relative to the groove radius is
`s = y - R`, and the proposed tail law is `wing = 62.5° + asin(s / 11 mm)`.

The [PLA datasheet](https://prusament.com/wp-content/uploads/2022/10/PLA_Prusament_TDS_2021_10_EN.pdf)
reports 55 °C heat deflection under its stated test conditions. That does not establish that a
black, loaded assembly will remain dimensionally stable in direct sun. Keep the original PLA-only
requirement open for testing; no material substitution or finishing step is assumed.

## Decision and next deliverable

The user approved **Bryła / A / honey** on 2026-11-12. The next stage is the
[plain build123d motion prototype and U1 fit coupons](motion-prototype.md). Geometric evidence
and the physical checks still required for feel, wear, heat and handling are recorded there.
Decoration and production STEP/3MF releases follow the mechanical proof and U1 fit tests.
