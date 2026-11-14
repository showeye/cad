"""The king's solids at rest: base, plates, wheels, anchor, plunger, pawl, crown and steel.

Every part but the base and the crown is a stack of flat pierced plates, as in a skeleton
clock, and prints lying down without support: the plates with their outer face on the bed,
the two wheels with the wheel down and the star or the pinion on top, the anchor with the
pendulum down, the plunger with its front face down, the pawl and the cross flat. Base and
crown print upright. Sizes come from the parameters, positions from the layout.

In the side view the front plate is the nearest: Y runs from the front (-) to the back (+).
"""

from build123d import Circle, Cylinder, Pos, Rot, Sphere

from chess_set_clockwork import _shared as shared
from chess_set_clockwork._shared import box as _box
from chess_set_clockwork._shared import gear_face as _gear
from chess_set_clockwork._shared import polygon as _polygon
from chess_set_clockwork._shared import rectangle as _rect
from chess_set_clockwork._shared import rod_y, slab, strap
from chess_set_clockwork.king._layout import _unit, layout

ORB_SITS = 0.82  # the orb's centre above the crown's block, in orb radii


def _arbor(p, centre) -> float:
    """Diameter of the steel pin at `centre`: the anchor's arbor is thinner than the others."""
    return p.anchor_pin if centre == layout(p).pivot else p.pin


def _bore(p, centre, turns: bool):
    """Hole for a steel pin through everything at `centre`: a running or a press fit."""
    fit = p.pin_run if turns else p.pin_grip
    return rod_y((_arbor(p, centre) + fit) / 2, -50, 50, centre)


# ---------------------------------------------------------------- base
def base(p):
    """Flange and drum with the plunger's slot and the four mortises; prints upright."""
    L = layout(p)
    body = shared.base_body(p)
    y = L.bar_wide + p.slide
    lower = L.bar_half + p.slide
    upper = lower + p.ear
    body -= _box(-lower, lower, -y, y, -1, p.base_height + 1)
    body -= _box(-upper, upper, -y, y, L.ledge, p.base_height + 1)
    for side in (-1, 1):
        for x in L.feet:
            body -= shared.mortise(p, L.outer, x, side)
    return body


# ---------------------------------------------------------------- plunger and pawl
def stem_sketch(p):
    """The stem with the socket for the pawl's knuckle, as it stands at rest."""
    L = layout(p)
    x, z = L.knuckle
    sketch = _rect(L.stem[0], L.stem[1], p.bar_height - 1, z)
    sketch += Pos(x, z) * Circle(L.socket)
    sketch += _rect(x, L.stem[1], z, z + L.socket)  # a straight flank for the guide
    sketch -= Pos(x, z) * Circle(p.knuckle + p.knuckle_play)
    # The opening lets the pawl's arm swing from its outer stop to its inner stop; each lip
    # is cut along the edge of the arm that comes to lie against it.
    R = L.ratchet
    half, far = p.pawl_neck / 2, 3 * L.socket
    out, into = R.edges[0] - p.pawl_out, R.edges[1] + p.pawl_in
    right = shared.polar((0, 0), half, R.axis - p.pawl_out - 90)
    left = shared.polar((0, 0), half, R.axis + p.pawl_in + 90)
    steps = [out + (into - out) * i / 4 for i in range(5)]
    opening = [right, shared.polar(right, far, out)]
    opening += [shared.polar((0, 0), 2 * far, a) for a in steps]
    opening += [shared.polar(left, far, into), left]
    return sketch - Pos(x, z) * _polygon(opening)


def plunger(p):
    """Foot bar with its ears and the tunnel for the weight, and the stem at the front."""
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
    body = slab(bar, -L.bar_wide, L.bar_wide)
    # the weight goes in from the right end; the end of the slot in the base keeps it there
    bore = (p.weight + p.weight_fit) / 2
    x0 = -p.weight_length / 2 - 0.15
    body -= (
        Pos((x0 + h) / 2 + 0.5, 0, p.weight_floor + bore)
        * Rot(0, 90, 0)
        * Cylinder(bore, h - x0 + 1)
    )
    return body + slab(stem_sketch(p), *L.front)


def pawl(p):
    """Strut between the plunger and the star: knuckle below, cup and fence above."""
    L = layout(p)
    sketch = _polygon(list(L.ratchet.outline))
    sketch -= Pos(*L.ratchet.cup) * Circle(p.lobe + p.cup_play)  # the cup as a true arc
    return slab(Pos(*L.knuckle) * sketch, *L.front)


# ---------------------------------------------------------------- wheels
def star_sketch(p):
    """The star about its own centre at rest: a boss with round lobes on stalks."""
    sketch = Circle(p.star_boss)
    for i in range(p.star_teeth):
        arm = Pos(p.star_circle, 0) * Circle(p.lobe)
        arm += _rect(0, p.star_circle, -p.star_stalk / 2, p.star_stalk / 2)
        sketch += Rot(0, 0, p.star_end + i * 360 / p.star_teeth) * arm
    return sketch


def great_wheel(p):
    """Spoked great wheel with the star on its front; prints with the wheel down."""
    L = layout(p)
    place = Pos(*L.great)
    gear = Rot(0, 0, p.great_angle) * _gear(p.module, p.wheel_teeth, -p.shift, p.backlash)
    rim = L.great_root - p.great_rim
    gear -= shared.spoke_windows(rim, p.great_hub, p.great_spokes, p.spoke)
    body = slab(place * gear, *L.middle)
    body += slab(place * star_sketch(p), L.front[0], L.middle[0])
    return body - _bore(p, L.great, turns=False)


def escape_wheel(p):
    """Escape wheel with the pinion on its back; the spokes stand on a thin web."""
    L = layout(p)
    place = Pos(*L.escape)
    e = L.escapement
    body = slab(place * _polygon(e.wheel_outline(p.escape_depth, L.progress)), *L.front)
    rim = p.escape_tip - p.escape_depth - p.escape_rim
    windows = shared.spoke_windows(rim, p.escape_hub, p.escape_spokes, p.spoke)
    # a spoke points straight up at rest
    body -= slab(place * Rot(0, 0, 90) * windows, L.front[0] - 1, L.front[1] - p.escape_web)
    pinion = Rot(0, 0, L.pinion_angle) * _gear(p.module, p.pinion_teeth, p.shift, p.backlash)
    body += slab(place * pinion, L.front[1], L.middle[1])
    return body - _bore(p, L.escape, turns=False)


# ---------------------------------------------------------------- anchor and pendulum
def yoke_sketch(p):
    """Pallets and the arch that carries them, about the escape wheel's centre."""
    L = layout(p)
    e = L.escapement
    sketch = Circle(L.yoke[1]) - Circle(L.yoke[0])
    for nose in e.pallets(p.pallet_length):
        sketch += _polygon(nose)
    # the arch's ends and its outer edge cut the pallets off where no tooth reaches them
    return sketch & shared.wedge(2 * L.yoke[1], *L.yoke_span) & Circle(L.yoke[1])


def pendulum_sketch(p):
    """Rod, the ring round the escape wheel's boss, and the block for the bob."""
    L = layout(p)
    x, z = L.bob
    half = p.bob_block / 2
    tall = (p.bob + p.bob_fit) / 2 + p.bob_wall
    cut = 1.0  # the lower corners are cut off: they pass close to the boss below
    block = _polygon(
        [
            (x - half, z + tall),
            (x - half, z - tall + cut),
            (x - half + cut, z - tall),
            (x + half - cut, z - tall),
            (x + half, z - tall + cut),
            (x + half, z + tall),
        ]
    )
    ring = Pos(*L.escape) * Circle(L.ring)
    rod = strap(L.pivot, L.bob, p.rod)
    return rod + ring + block - Pos(*L.escape) * Circle(L.ring_hole)


def anchor(p):
    """Pallets, arch, hub and pendulum as one part; prints with the pendulum down."""
    L = layout(p)
    body = slab(Pos(*L.escape) * yoke_sketch(p), L.front[0], L.rear[1])
    # where the escape wheel passes under the arbor the hub is no wider than it may be
    body += slab(Pos(*L.pivot) * Circle(L.hub_front), L.front[0], L.rear[1])
    body += slab(Pos(*L.pivot) * Circle(p.hub), L.front[1] + p.layer_gap / 2, L.rear[1])
    body += slab(pendulum_sketch(p), *L.rear)
    bore = (p.bob + p.bob_fit) / 2
    middle = (L.rear[0] + L.rear[1]) / 2
    body -= Pos(L.bob[0], middle, L.bob[1]) * Rot(0, 90, 0) * Cylinder(bore, p.bob_block + 2)
    return body - _bore(p, L.pivot, turns=False)


# ---------------------------------------------------------------- plates
def window_sketch(p):
    """What both plates share: columns, plinths, the bar across, the arch and its mullion."""
    L = layout(p)
    inner, outer = L.column
    top = p.base_height + p.plinth
    sketch = _rect(-outer, -inner, 0, L.spring) + _rect(inner, outer, 0, L.spring)
    for side in (-1, 1):  # a plinth below each column, cut off at 45 degrees inside
        foot = [
            (outer, 0),
            (outer, top),
            (inner - 0.01, top),
            (p.plinth_x, top - (inner - p.plinth_x)),
            (p.plinth_x, 0),
        ]
        sketch += _polygon([(side * u, v) for u, v in foot])
    sketch += strap((-p.column_x, L.spring), (p.column_x, L.spring), p.strap)
    # a pointed arch: each side is struck from the foot of the other
    radius = 2 * outer
    lens = (Pos(-outer, L.spring) * Circle(radius)) & (Pos(outer, L.spring) * Circle(radius))
    hole = (Pos(-outer, L.spring) * Circle(radius - p.column)) & (
        Pos(outer, L.spring) * Circle(radius - p.column)
    )
    above = _rect(-outer - 1, outer + 1, L.spring, L.apex + 1)
    sketch += (lens - hole) & above
    sketch -= _rect(-outer, outer, L.apex - p.crown_seat, L.apex + 1)  # the point gives way
    tenon = p.crown_tenon / 2
    sketch += _rect(-tenon, tenon, L.apex - p.crown_seat - 1, L.apex + p.crown_rise)
    sketch += strap(L.pivot, (0, L.apex - p.crown_seat - 1), p.strap)
    for centre in (L.escape, L.pivot):
        sketch += Pos(*centre) * Circle(p.boss)
    sketch += Pos(*L.posts[2]) * Circle(p.post + 1.0)  # the lower pillars stand in the plinths
    return sketch & _rect(-outer - 1, outer + 1, p.base_height, L.apex + p.crown_rise + 1)


def plate(p, side: int):
    """One plate; side -1 is the front (Y < 0), +1 the rear."""
    L = layout(p)
    fixed = Circle((p.pin + p.pin_grip) / 2)
    arbors = (L.great, L.escape, L.pivot)

    def turning(centre):  # the hole in which the arbor at `centre` turns
        return Circle((_arbor(p, centre) + p.pin_run) / 2)

    def span(a, b):  # Y levels for this side, from |Y| = a to |Y| = b
        return (a, b) if side > 0 else (-b, -a)

    sketch = window_sketch(p)
    level = L.great[1]
    if side < 0:  # a small boss held from the left column: the star and the pawl stay in view
        sketch += strap((-p.column_x, level), L.great, p.strap - 0.6)
        sketch += Pos(*L.great) * Circle(p.boss_small)
    else:
        sketch += strap((-p.column_x, level), (p.column_x, level), p.strap)
        sketch += Pos(*L.great) * Circle(p.boss)
    for centre in arbors:
        sketch -= Pos(*centre) * turning(centre)
    for centre in L.posts:
        sketch -= Pos(*centre) * fixed
    body = slab(sketch, *span(L.inner, L.outer))

    for centre in arbors:
        small = side < 0 and centre == L.great
        pocket = (p.jewel_small if small else p.jewel) / 2
        body -= slab(Pos(*centre) * Circle(pocket), *span(L.outer - p.jewel_depth, L.outer + 1))
        tall = side > 0 and centre != L.pivot
        if tall:  # the wheels bear on these; the pendulum's ring swings round the upper one
            boss = Pos(*centre) * (Circle(p.boss_tall) - turning(centre))
            body += slab(boss, *span(L.wheels[1] + L.play, L.inner))
        else:  # the moving parts bear on these rings, not on the plate's face
            ring = Pos(*centre) * (Circle(p.shoulder_ring) - turning(centre))
            body += slab(ring, *span(L.inner - p.shoulder, L.inner))
    for centre in L.posts:  # the two half posts meet in the middle
        body += slab(Pos(*centre) * (Circle(p.post) - fixed), *span(0, L.inner))
    if side < 0:  # the rib that the plunger's stem is pushed against while the king sinks
        rib = _rect(L.rib[0], L.rib[0] + p.guide_rib, p.base_height, L.rib[1])
        body += slab(rib, -L.inner, L.front[1])
    for x in L.feet:
        body += slab(shared.sprung_tenon(p, x), *span(L.outer - p.tenon_thick, L.outer))
    return body


def jewel(p, centre, side: int):
    """Red ring in a plate's outer face; the arbor's steel pin turns in it."""
    L = layout(p)
    small = side < 0 and centre == L.great
    diameter = p.jewel_small if small else None
    return shared.jewel_ring(p, centre, L.outer, side, diameter, _arbor(p, centre))


# ---------------------------------------------------------------- crown
def crown(p):
    """Block that sits over the tops of both plates, with the orb; prints upright."""
    L = layout(p)
    z0, z1 = L.apex - p.crown_seat + p.crown_lift, L.apex + p.crown_rise + p.crown_cap
    half, slot = p.crown_width / 2, p.crown_tenon / 2 + p.tenon_fit
    body = _box(-half, half, -L.outer, L.outer, z0, z1)
    for side in (-1, 1):  # a notch for the tenon on top of each plate
        y0, y1 = L.inner - p.tenon_fit, L.outer + 1
        y0, y1 = (y0, y1) if side > 0 else (-y1, -y0)
        body -= _box(-slot, slot, y0, y1, z0 - 1, L.apex + p.crown_rise + p.tenon_fit)
    radius = p.orb / 2
    centre = z1 + radius * ORB_SITS
    collar = radius * 0.7071  # below 45 degrees the orb would overhang; a collar carries it
    body += Pos(0, 0, (z1 + centre - collar) / 2) * Cylinder(collar, centre - collar - z1 + 0.2)
    body += Pos(0, 0, centre) * Sphere(radius)
    top = centre + radius
    w, t = p.cross_tenon / 2 + p.tenon_fit, p.cross_thick / 2 + p.tenon_fit
    return body - _box(-w, w, -t, t, top - p.cross_socket, top + 1)


def cross_sketch(p):
    """A cross with flared arms about its own centre, and the tenon below it."""
    a, b, r = p.cross_waist / 2, p.cross_flare / 2, p.cross / 2
    arm = [(a, -a), (r, -b), (r, b)]  # the next arm starts where this one ends
    points = []
    for quarter in range(4):
        c, s = _unit(90 * quarter)
        points += [(c * x - s * z, s * x + c * z) for x, z in arm]
    tenon = _rect(-p.cross_tenon / 2, p.cross_tenon / 2, -r - p.cross_socket + 0.3, -r + 0.3)
    return _polygon(points) + tenon


def cross(p):
    """The cross on the orb: a flat plate that stands in a slot in the orb's top."""
    L = layout(p)
    top = L.apex + p.crown_rise + p.crown_cap + p.orb / 2 * (ORB_SITS + 1)
    place = Pos(0, top + p.cross / 2)
    return slab(place * cross_sketch(p), -p.cross_thick / 2, p.cross_thick / 2)


# ---------------------------------------------------------------- steel
def pin(p, centre, length=None):
    """A steel pin across the piece: arbor or pillar."""
    return shared.steel_pin(p, centre, length, _arbor(p, centre))


def steel_weight(p):
    bore = (p.weight + p.weight_fit) / 2
    return (
        Pos(0, 0, p.weight_floor + bore) * Rot(0, 90, 0) * Cylinder(p.weight / 2, p.weight_length)
    )


def steel_bob(p):
    L = layout(p)
    middle = (L.rear[0] + L.rear[1]) / 2
    return Pos(L.bob[0], middle, L.bob[1]) * Rot(0, 90, 0) * Cylinder(p.bob / 2, p.bob_length)
