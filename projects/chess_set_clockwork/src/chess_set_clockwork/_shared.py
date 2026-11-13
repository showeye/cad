"""Drawing helpers for pieces built from flat plates.

Every piece is drawn in its side view: X to the right, Z up, seen from -Y, with the arbors
along Y. A sketch in (x, z) becomes a plate between two Y levels; a turn is counter-clockwise
in that view. Kept here until a second piece needs them, then they move to `cadkit`.
"""

import math

from build123d import Cylinder, Pos, Rot, SlotOverall, extrude


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
