"""The pawn's solids at rest: base, two plates, ratchet wheel, plunger, pawl, click and head.

Every part but the base and the head is a flat plate with a pierced outline, as in a skeleton
clock, and prints lying down without support: the plates with their outer face on the bed,
the wheel, the click, the pawl and the plunger on either face. Base and head print upright.
The two plates are the same part: the outline is the same left and right, so one plate turned
round is the other. Sizes come from the parameters, positions from the layout.
"""

import math

from build123d import Circle, Cylinder, Pos, Rot, Sphere

from chess_set_clockwork import _shared as shared
from chess_set_clockwork._shared import box as _box
from chess_set_clockwork._shared import polygon as _polygon
from chess_set_clockwork._shared import rectangle as _rect
from chess_set_clockwork._shared import slab, strap
from chess_set_clockwork.pawn._layout import direction, layout, polar

BALL_SITS = 0.82  # the ball's centre above the head's block, in ball radii


def _unit(angle: float) -> tuple[float, float]:
    return polar(1.0, angle)


def _along(point, way, length: float, side: float = 0.0):
    """`length` from `point` in direction `way`, and `side` to the left of that direction."""
    u = _unit(way)
    return point[0] + length * u[0] - side * u[1], point[1] + length * u[1] + side * u[0]


def _meet(a, way_a: float, b, way_b: float):
    """Where the line through `a` in direction `way_a` crosses the one through `b`."""
    u, v = _unit(way_a), _unit(way_b)
    t = ((b[0] - a[0]) * v[1] - (b[1] - a[1]) * v[0]) / (u[0] * v[1] - u[1] * v[0])
    return a[0] + t * u[0], a[1] + t * u[1]


# ---------------------------------------------------------------- wheel
def wheel(p):
    """Ratchet wheel with its spokes; a flat disc that prints on either face."""
    L = layout(p)
    sketch = _polygon(L.ratchet.outline(L.home))
    rim = p.wheel_tip - p.tooth - p.wheel_rim
    sketch -= Rot(0, 0, 90) * shared.spoke_windows(rim, p.wheel_hub, p.spokes, p.spoke)
    sketch -= Circle((p.pin + p.pin_grip) / 2)
    return slab(Pos(*L.wheel) * sketch, *L.wheel_y)


# ---------------------------------------------------------------- click
def click_sketch(p):
    """The click with its nose in a tooth's corner: eye, arm, elbow and beak."""
    L = layout(p)
    nose = L.click.tip(L.click_pin, L.click_seated)
    # the beak is a wedge from the elbow to the round nose; its upper side lies under the face
    way = direction(nose, L.click_elbow)
    length = math.dist(nose, L.click_elbow)
    wide = p.nose + length * math.tan(math.radians(p.beak / 2))
    beak = _polygon(
        [
            _along(nose, way + p.beak / 2, 0.0, p.nose),
            _along(nose, way, length, wide),
            _along(nose, way, length, -wide),
            _along(nose, way - p.beak / 2, 0.0, -p.nose),
        ]
    )
    sketch = beak + Pos(*nose) * Circle(p.nose)
    sketch += Pos(*L.click_elbow) * Circle(wide)
    sketch += strap(L.click_elbow, L.click_pin, p.click_arm)
    sketch += Pos(*L.click_pin) * Circle(p.click_eye)
    return sketch - Pos(*L.click_pin) * Circle((p.pin + p.pin_run) / 2)


def click(p):
    """The click as it lies at rest, on the back of a tooth; it turns on its steel pin."""
    L = layout(p)
    body = slab(click_sketch(p), *L.click_y)
    return shared.turned(body, L.click_pin, L.click_home - L.click_seated)


# ---------------------------------------------------------------- pawl
def pawl_sketch(p):
    """The pawl at rest: knuckle below, a bar that lies along the tooth below, nose on top.

    The bar's inner edge is the line from the knuckle to the nose, so that only the nose
    stands in the wheel. The pawl only rises while its tooth turns with the wheel, so the
    bar's top is cut to lie under the face as it stands when the pawl first meets it: one
    tooth and the fall-back earlier. Towards the knuckle the bar narrows to a neck that
    swings in the socket's opening.
    """
    L = layout(p)
    nose = L.pawl.tip(L.knuckle, L.pawl_home)
    down = L.pawl_home + 180  # from the nose towards the knuckle; the wheel is to its right
    top = L.pawl_face - L.ratchet.pitch - L.back - p.beak_off  # along the top, outwards
    start = _along(nose, top + 90, p.nose)  # where the top leaves the nose
    corner = _meet(start, top, _along(nose, down, 0.0, p.pawl_body), down)
    neck, half = p.pawl_length - L.socket - 0.3, p.pawl_neck / 2
    body = [
        start,
        corner,
        _along(nose, down, neck - 1.2, p.pawl_body),
        _along(nose, down, neck, half),
        _along(nose, down, p.pawl_length - 0.3, half),
        _along(nose, down, p.pawl_length - 0.3, -half),
        _along(nose, down, neck, -half),
        _along(nose, down, neck - 0.9, 0.0),
        _along(nose, down, p.nose, 0.0),
    ]
    sketch = _polygon(body) + Pos(*nose) * Circle(p.nose)
    return sketch + Pos(*L.knuckle) * Circle(p.knuckle)


def pawl(p):
    L = layout(p)
    return slab(pawl_sketch(p), -L.bar_wide, L.bar_wide)


# ---------------------------------------------------------------- plunger
def stem_sketch(p):
    """The stem with the socket for the pawl's knuckle, as it stands at rest."""
    L = layout(p)
    x, z = L.knuckle
    sketch = _rect(x - L.socket, x + L.socket, p.bar_height - 1, z)
    sketch += Pos(x, z) * Circle(L.socket)
    sketch -= Pos(x, z) * Circle(p.knuckle + p.knuckle_play)
    # The opening lets the pawl swing from its outer stop to its inner stop; each lip is cut
    # along the edge of the pawl's neck that comes to lie against it.
    half, far = p.pawl_neck / 2, 3 * L.socket
    out, into = L.pawl_home - p.pawl_out, L.pawl_home + p.pawl_in
    right, left = polar(half, out - 90), polar(half, into + 90)
    steps = [out + (into - out) * i / 4 for i in range(5)]
    opening = [right, polar(far, out, right)]
    opening += [polar(2 * far, a) for a in steps]
    opening += [polar(far, into, left), left]
    return sketch - Pos(x, z) * _polygon(opening)


def plunger(p):
    """Foot bar with its ears and the tunnel for the weight, and the stem at its right end."""
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
    body = slab(bar + stem_sketch(p), -L.bar_wide, L.bar_wide)
    # the weight goes in from the right end; the end of the slot in the base keeps it there
    bore = (p.weight + p.weight_fit) / 2
    x0 = -p.weight_length / 2 - 0.15
    return body - (
        Pos((x0 + h) / 2 + 0.5, 0, p.weight_floor + bore)
        * Rot(0, 90, 0)
        * Cylinder(bore, h - x0 + 1)
    )


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


# ---------------------------------------------------------------- plates
def plate_sketch(p):
    """A round-headed window: sill, two columns, the arch, and a mullion with the two bosses."""
    L = layout(p)
    inner, outer = L.column
    hb = p.base_height
    sketch = _rect(-outer, outer, hb, hb + p.sill)
    for side in (-1, 1):
        sketch += _rect(side * inner, side * outer, hb, L.spring)
        # a low plinth over each foot, cut off at 45 degrees inside
        low = p.foot_x - p.tenon / 2
        foot = [(inner, hb), (inner, hb + p.sill + inner - low), (low, hb + p.sill), (low, hb)]
        sketch += _polygon([(side * u, v) for u, v in foot])
    arch = Pos(0, L.spring) * (Circle(outer) - Circle(inner))
    sketch += arch & _rect(-outer - 1, outer + 1, L.spring, L.spring + outer + 1)
    sketch += strap((0, hb + p.sill / 2), L.click_pin, p.strap)
    sketch += Pos(*L.wheel) * Circle(p.boss)
    sketch += Pos(*L.click_pin) * Circle(p.crown)
    # a flat for the head to sit on, and the tenon that it sits over
    sketch += _rect(-p.head_seat / 2, p.head_seat / 2, L.click_pin[1], L.seat)
    sketch += _rect(-p.head_tenon / 2, p.head_tenon / 2, L.seat - 1, L.top)
    sketch &= _rect(-outer - 1, outer + 1, hb, L.top + 1)  # nothing reaches into the base
    sketch -= Pos(*L.wheel) * Circle((p.pin + p.pin_run) / 2)
    return sketch - Pos(*L.click_pin) * Circle((p.pin + p.pin_grip) / 2)


def plate(p, side: int):
    """One plate; side -1 stands at Y < 0, +1 at Y > 0. Both are the same part."""
    L = layout(p)

    def span(a, b):  # Y levels for this side, from |Y| = a to |Y| = b
        return (a, b) if side > 0 else (-b, -a)

    body = slab(plate_sketch(p), *span(L.inner, L.outer))
    # the wheel bears on a boss round its arbor, the click lies between two half posts
    turning = Circle((p.pin + p.pin_run) / 2)
    boss = Pos(*L.wheel) * (Circle(p.boss_tall) - turning)
    body += slab(boss, *span(L.wheel_y[1] + p.play, L.inner))
    post = Pos(*L.click_pin) * (Circle(p.post) - Circle((p.pin + p.pin_grip) / 2))
    body += slab(post, *span(L.click_y[1] + p.play, L.inner))
    body -= slab(Pos(*L.wheel) * Circle(p.jewel / 2), *span(L.outer - p.jewel_depth, L.outer + 1))
    for x in L.feet:
        body += slab(shared.sprung_tenon(p, x), *span(L.outer - p.tenon_thick, L.outer))
    return body


def jewel(p, side: int):
    """Red ring in a plate's outer face; the wheel's arbor turns in it."""
    L = layout(p)
    return shared.jewel_ring(p, L.wheel, L.outer, side)


# ---------------------------------------------------------------- head
def head(p):
    """Round collar that sits over the tops of both plates, with the ball; prints upright."""
    L = layout(p)
    z1 = L.top + p.head_cap
    slot = p.head_tenon / 2 + p.tenon_fit
    body = Pos(0, 0, (L.seat + z1) / 2) * Cylinder(p.head_collar / 2, z1 - L.seat)
    for side in (-1, 1):  # a notch for the tenon on top of each plate
        y0, y1 = L.inner - p.tenon_fit, L.outer + 1
        y0, y1 = (y0, y1) if side > 0 else (-y1, -y0)
        body -= _box(-slot, slot, y0, y1, L.seat - 1, L.top + p.tenon_fit)
    radius = p.ball / 2
    centre = z1 + radius * BALL_SITS
    neck = radius * 0.7071  # below 45 degrees the ball would overhang; a neck carries it
    body += Pos(0, 0, (z1 + centre - neck) / 2) * Cylinder(neck, centre - neck - z1 + 0.2)
    return body + Pos(0, 0, centre) * Sphere(radius)


# ---------------------------------------------------------------- steel
def pin(p, centre):
    """A steel pin across the piece: the wheel's arbor, or the pin the click turns on."""
    return shared.steel_pin(p, centre)


def steel_weight(p):
    bore = (p.weight + p.weight_fit) / 2
    return (
        Pos(0, 0, p.weight_floor + bore) * Rot(0, 90, 0) * Cylinder(p.weight / 2, p.weight_length)
    )
