"""The knight's solids at rest: base, two plates, chest wheel, head, plunger, jewels and steel.

Every part is a flat plate with a pierced outline, as in a skeleton clock, and prints lying
down without support: the plates with their outer face on the bed, the wheel with its spoked
face down, the head on either face, the plunger with the rack's side down. The base prints
upright. Sizes come from the parameters, positions from the layout.
"""

from build123d import (
    CenterArc,
    Circle,
    Cylinder,
    Pos,
    Rectangle,
    Rot,
    SlotArc,
    Spline,
    fillet,
    trace,
)
from cadkit.features.gears import rack_outline

from chess_set_clockwork import _shared as shared
from chess_set_clockwork._shared import box as _box
from chess_set_clockwork._shared import gear_face as _gear
from chess_set_clockwork._shared import polygon as _polygon
from chess_set_clockwork._shared import rod_y, slab, strap
from chess_set_clockwork._shared import sector as _sector
from chess_set_clockwork.knight._layout import layout

# The head's outline in its own frame at rest: arbor at the origin, nose towards -X.
HEAD = [
    (2.0, 9.4),
    (-1.5, 9.2),
    (-3.2, 14.3),
    (-4.7, 9.8),
    (-6.5, 13.8),
    (-8.4, 8.0),
    (-9.6, 6.0),
    (-12.4, 1.8),
    (-14.9, -2.4),
    (-17.8, -6.2),
    (-17.6, -9.2),
    (-14.8, -10.9),
    (-12.5, -9.8),
    (-6.4, -7.7),
    (-1.3, -6.9),
    (1.0, -3.0),
]
CHEEK_RADIUS = 6.2  # the round of the jaw, about the arbor
EYE = [(-8.4, 5.2), (-5.0, 6.4), (-5.9, 3.6)]
CHEEK = [(-15.4, -5.2), (-9.1, 3.1), (-7.7, -4.6)]
NOSTRIL = ((-16.1, -7.1), 0.7)
ROUND = 0.5  # corner radius of the head's outline

# The front of the neck, from below the foot to the head's arbor (the last point is added).
NECK = [(-10.0, 5.0), (-10.2, 9.5), (-12.7, 17.0)]
NECK_UPPER = (3.2, 9.5)  # the neck's next point, measured from the front post


# ---------------------------------------------------------------- head and mane
def head_sketch(p):
    """Head and mane in the head's own frame: one flat outline, the mane a slice of a gear."""
    L = layout(p)
    mane = _gear(p.module, p.mane_teeth, 0.0, p.backlash)
    mane &= _sector(0.01, 2 * L.mane_tip, L.mane_from, L.mane_to)
    # between the rim and the hub the mane is open, but for the web that holds the banking slot
    rim, hub = L.mane_root - p.mane_rim, p.hub + p.mane_window
    step = 360 / p.mane_teeth
    mane -= fillet(
        _sector(hub, rim, L.mane_from + step, L.bank_from - p.bank_web).vertices(), ROUND
    )
    mane -= fillet(_sector(hub, rim, L.bank_to + p.bank_web, p.mane_open).vertices(), ROUND)
    face = fillet(_polygon(HEAD).vertices(), ROUND)
    sketch = mane + face + Circle(CHEEK_RADIUS)
    sketch -= Circle((p.pin + p.pin_grip) / 2)
    slot = CenterArc((0, 0), p.bank_radius, L.bank_from, L.bank_to - L.bank_from)
    sketch -= SlotArc(slot, p.pin + 2 * p.bank_play)
    for window in (EYE, CHEEK):
        sketch -= fillet(_polygon(window).vertices(), ROUND)
    sketch -= Pos(*NOSTRIL[0]) * Circle(NOSTRIL[1])
    timing = (L.timing[0] - L.pivot[0], L.timing[1] - L.pivot[1])
    return sketch - Pos(*timing) * Circle(p.timing / 2)


def head(p):
    L = layout(p)
    return slab(Pos(*L.pivot) * head_sketch(p), -L.half, L.half)


# ---------------------------------------------------------------- chest wheel and pinion
def wheel(p):
    """Spoked wheel and its pinion as one part; the spokes stand on a thin web."""
    L = layout(p)
    place = Pos(*L.wheel)
    root = L.wheel_tip - 2.25 * p.module
    rim = root - p.wheel_rim
    windows = shared.spoke_windows(rim, p.wheel_hub, p.spokes, p.spoke)
    turn = Rot(0, 0, L.wheel_angle)
    body = slab(place * turn * _gear(p.module, p.wheel_teeth, 0.0, p.backlash), *L.wheel_y)
    body -= slab(place * turn * windows, L.wheel_y[0] - 1, L.wheel_y[1] - p.wheel_web)
    pinion = _gear(p.module, p.pinion_teeth, p.shift, p.backlash)
    body += slab(place * Rot(0, 0, L.pinion_angle) * pinion, *L.pinion_y)
    return body - rod_y((p.pin + p.pin_grip) / 2, -L.half - 1, L.half + 1, L.wheel)


# ---------------------------------------------------------------- plunger
def plunger(p):
    """Foot bar with its retaining ears, the tunnel for the steel weight, and the rack."""
    L = layout(p)
    h, top = L.bar_half, p.bar_height
    step = top - p.ear_height
    bar = _polygon(
        [
            (-h, 0),
            (h, 0),
            (h, step),
            (h + p.ear, step),
            (h + p.ear, top),
            (-h - p.ear, top),
            (-h - p.ear, step),
            (-h, step),
        ]
    )
    body = slab(bar, -L.half, L.half)
    # the weight goes in from the rear end; the end of the slot in the base keeps it there
    bore = (p.weight + p.weight_fit) / 2
    x0 = -p.weight_length / 2 - 0.15
    body -= (
        Pos((x0 + h) / 2 + 0.5, 0, p.weight_floor + bore)
        * Rot(0, 90, 0)
        * Cylinder(bore, h - x0 + 1)
    )
    teeth = _polygon(rack_outline(p.module, p.rack_teeth, p.rack_back, p.shift, p.backlash))
    back = -p.shift * p.module - 1.25 * p.module - p.rack_back
    stem = Pos(back + p.rack_back / 2, (top - 1 + L.rack_low) / 2) * Rectangle(
        p.rack_back, L.rack_low - top + 1
    )
    stem = Pos(L.rack_x, 0) * stem
    return body + slab(Pos(L.rack_x, L.rack_low) * teeth + stem, *L.rack_y)


# ---------------------------------------------------------------- base
def base(p):
    """Flange and drum with the plunger's slot and the four mortises; prints upright."""
    L = layout(p)
    hb = p.base_height
    body = shared.base_body(p)
    y = L.half + p.slide
    lower = L.bar_half + p.slide
    upper = lower + p.ear
    body -= _box(-lower, lower, -y, y, -1, hb + 1)
    body -= _box(-upper, upper, -y, y, L.ledge, hb + 1)
    for side in (-1, 1):
        for x in L.feet:
            body -= shared.mortise(p, L.outer, x, side)
    return body


# ---------------------------------------------------------------- plates
def plate_sketch(p):
    """Outline of a side plate: neck, rear strap, bridge and the bosses, above the base."""
    L = layout(p)
    upper = (L.front_post[0] + NECK_UPPER[0], L.front_post[1] + NECK_UPPER[1])
    neck = trace(Spline(*NECK, L.front_post, upper, L.pivot), p.strap)
    rear_foot = (L.feet[1], 5.0)
    sketch = neck + strap(L.pivot, L.rear_post, p.strap) + strap(L.rear_post, rear_foot, p.strap)
    z = L.wheel[1]
    slope = (L.rear_post[0] - rear_foot[0]) / (L.rear_post[1] - rear_foot[1])
    sketch += strap((L.front_post[0], z), (rear_foot[0] + slope * (z - rear_foot[1]), z), p.strap)
    for centre in (L.pivot, L.wheel):
        sketch += Pos(*centre) * Circle(p.boss)
    for centre in (L.front_post, L.rear_post):
        sketch += Pos(*centre) * Circle(p.post + 1.0)
    sketch += Pos(*L.banking) * Circle(p.pin / 2 + 1.9)
    above = Pos(0, p.base_height + 50) * Rectangle(200, 100)
    return sketch & above


def plate(p, side: int):
    """One side plate; side -1 is the horse's left (Y < 0), +1 its right."""
    L = layout(p)
    turning = Circle((p.pin + p.pin_run) / 2)
    fixed = Circle((p.pin + p.pin_grip) / 2)
    arbors = (L.pivot, L.wheel)
    pins = (L.front_post, L.rear_post, L.banking)
    holes = [Pos(*c) * turning for c in arbors] + [Pos(*c) * fixed for c in pins]
    holes.append(Pos(*L.timing) * Circle(p.timing / 2))

    def span(a, b):  # Y levels for this side, from |Y| = a to |Y| = b
        return (a, b) if side > 0 else (-b, -a)

    sketch = plate_sketch(p)
    for hole in holes:
        sketch -= hole
    body = slab(sketch, *span(L.inner, L.outer))
    for centre in arbors:  # the moving parts bear on these rings, not on the plate's face
        ring = Pos(*centre) * (Circle(p.shoulder_ring) - turning)
        body += slab(ring, *span(L.inner - p.shoulder, L.inner))
        body -= slab(
            Pos(*centre) * Circle(p.jewel / 2), *span(L.outer - p.jewel_depth, L.outer + 1)
        )
    for centre in (L.front_post, L.rear_post):  # the two half posts meet in the middle
        body += slab(Pos(*centre) * (Circle(p.post) - fixed), *span(0, L.inner))
    for x in L.feet:
        body += slab(shared.sprung_tenon(p, x), *span(L.outer - p.tenon_thick, L.outer))
    return body


def jewel(p, centre, side: int):
    """Red ring in the plate's outer face; the arbor's steel pin turns in it."""
    return shared.jewel_ring(p, centre, layout(p).outer, side)


# ---------------------------------------------------------------- steel
def pin(p, centre, length=None):
    """A steel pin across the piece: arbor, pillar or banking pin."""
    return shared.steel_pin(p, centre, length)


def steel_weight(p):
    bore = (p.weight + p.weight_fit) / 2
    return (
        Pos(0, 0, p.weight_floor + bore) * Rot(0, 90, 0) * Cylinder(p.weight / 2, p.weight_length)
    )
