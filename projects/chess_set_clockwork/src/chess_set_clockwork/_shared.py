"""What every piece of the set shares: drawing helpers, the base, feet, jewels and steel.

Every piece is drawn in its side view: X to the right, Z up, seen from -Y, with the arbors
along Y. A sketch in (x, z) becomes a plate between two Y levels; a turn is counter-clockwise
in that view. The parts take a piece's parameters `p` and read the fields that every piece
names alike (base, drum, tenon, barb, jewel_depth and so on).
"""

import math

from build123d import (
    Axis,
    Box,
    Circle,
    Cylinder,
    Plane,
    Polyline,
    Pos,
    Rectangle,
    Rot,
    SlotOverall,
    Sphere,
    extrude,
    make_face,
    revolve,
)
from cadkit.features.gears import gear_outline

PLASTIC, STEEL = 1.24e-3, 7.85e-3  # g per mm3: PLA, and steel for the pins


def grams(name: str, shape) -> float:
    """Mass of a part; those named `reference_` are steel, the rest is printed."""
    return shape.volume * (STEEL if name.startswith("reference_") else PLASTIC)


def slab(sketch, y0: float, y1: float):
    """A sketch drawn in (x, z) as a solid from Y = y0 to Y = y1."""
    return Rot(90, 0, 0) * (Pos(0, 0, -y1) * extrude(sketch, amount=y1 - y0))


def turned(shape, centre: tuple[float, float], angle: float):
    """Turn about the arbor through `centre` (x, z); counter-clockwise seen from -Y."""
    x, z = centre
    return Pos(x, 0, z) * Rot(0, -angle, 0) * Pos(-x, 0, -z) * shape


def rod_y(radius: float, y0: float, y1: float, centre: tuple[float, float]):
    """Round bar along Y through `centre` (x, z)."""
    x, z = centre
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(radius, y1 - y0)


def strap(a: tuple[float, float], b: tuple[float, float], width: float):
    """Round-ended bar between two points of a sketch."""
    angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return Pos(*middle) * Rot(0, 0, angle) * SlotOverall(math.dist(a, b) + width, width)


def polar(centre: tuple[float, float], radius: float, angle: float) -> tuple[float, float]:
    """Point at `radius` from `centre` in the direction `angle` (degrees)."""
    t = math.radians(angle)
    return centre[0] + radius * math.cos(t), centre[1] + radius * math.sin(t)


def polygon(points):
    """Face bounded by straight lines through `points`."""
    return make_face(Polyline(*points, close=True))


def gear_face(module, teeth, shift, backlash):
    return polygon(gear_outline(module, teeth, shift, backlash))


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def rectangle(x0, x1, z0, z1):
    """Rectangle of a sketch between two corners."""
    return Pos((x0 + x1) / 2, (z0 + z1) / 2) * Rectangle(x1 - x0, z1 - z0)


def wedge(radius, start, end):
    """Slice of a disc about the origin between two directions, with straight outer edges."""
    steps = max(2, math.ceil(abs(end - start) / 10))
    angles = [start + (end - start) * i / steps for i in range(steps + 1)]
    return polygon([(0, 0)] + [polar((0, 0), radius, a) for a in angles])


def spoke_windows(rim, hub, spokes, spoke):
    """The openings between the spokes of a wheel: inside `rim`, outside `hub`."""
    windows = Circle(rim) - Circle(hub)
    for i in range(spokes):
        windows -= Rot(0, 0, i * 360 / spokes) * Pos(rim / 2, 0) * Rectangle(rim, spoke)
    return windows


def sector(inner, outer, start, end):
    """Part of a ring about the origin between two directions."""
    steps = max(2, round(abs(end - start) / 10))
    angles = [start + (end - start) * i / steps for i in range(steps + 1)]
    return polygon(
        [polar((0, 0), outer, a) for a in angles]
        + [polar((0, 0), inner, a) for a in reversed(angles)]
    )


# ---------------------------------------------------------------- base and feet
def base_body(p):
    """Flange and drum with their studs, before the slot and the mortises are cut."""
    rf, rd, hf, hb, c = p.base / 2, p.drum / 2, p.flange_height, p.base_height, p.base_chamfer
    profile = [
        (0, 0),
        (rf - c, 0),
        (rf, c),
        (rf, hf - (rf - rd) * 0.6),
        (rd + (rf - rd) * 0.4, hf),
        (rd, hf),
        (rd, hb - c),
        (rd - c, hb),
        (0, hb),
    ]
    body = revolve(Plane.XZ * polygon(profile), Axis.Z)
    for i in range(p.studs):
        at = polar((0, 0), rd, (i + 0.5) * 360 / p.studs)
        body += Pos(at[0], at[1], (hf + hb) / 2) * Sphere(p.stud)
    return body


def mortise(p, outer, x, side):
    """Hole through the base for one foot of a plate whose outer face is at |Y| = outer."""
    w, fit = p.tenon / 2 + p.tenon_fit, p.tenon_fit
    y0, y1 = outer - p.tenon_thick - fit, outer + fit
    y0, y1 = (y0, y1) if side > 0 else (-y1, -y0)
    hole = box(x - w, x + w, y0, y1, -1, p.base_height + 1)
    pocket = p.barb + 2 * fit
    return hole + box(x - w - pocket, x + w + pocket, y0, y1, -1, p.catch)


def sprung_tenon(p, x):
    """Two sprung prongs below a foot; each has a barb that catches under the base."""
    w, top, tip = p.tenon / 2, p.base_height + 1.0, p.tenon_tip
    catch = p.catch - 0.1
    prong = [
        (-w, top),
        (-w, catch),
        (-w - p.barb, catch),
        (-w - p.barb, catch - 0.25),
        (-w + 0.15, tip),
        (-w + p.prong, tip),
        (-w + p.prong, top),
    ]
    mirrored = [(-u, v) for u, v in prong]
    return Pos(x, 0) * (polygon(prong) + polygon(mirrored))


# ---------------------------------------------------------------- jewels and steel
def jewel_ring(p, centre, outer, side, diameter=None, pin=None):
    """Red ring flush in a plate's outer face at |Y| = outer; the arbor turns in it.

    `pin` is the arbor's diameter where it is not the piece's usual pin.
    """
    diameter = p.jewel if diameter is None else diameter
    pin = p.pin if pin is None else pin
    ring = Pos(*centre) * (Circle(diameter / 2) - Circle((pin + p.pin_run) / 2))
    y = (outer - p.jewel_depth, outer)
    return slab(ring, *(y if side > 0 else (-y[1], -y[0])))


def steel_pin(p, centre, length=None, diameter=None):
    """A steel pin across the piece: arbor, pillar or banking pin."""
    length = p.pin_length if length is None else length
    diameter = p.pin if diameter is None else diameter
    return rod_y(diameter / 2, -length / 2, length / 2, centre)
