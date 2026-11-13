"""Reusable machining-style primitives, centred on their axes, in mm."""

import math
from collections.abc import Callable

from build123d import (
    Box,
    Circle,
    Cylinder,
    Edge,
    Face,
    Plane,
    Pos,
    RegularPolygon,
    Rot,
    Spline,
    Wire,
    extrude,
    sweep,
)

from cadkit.features.motion import Belt, cam_rate


def cord_loop(belt: Belt, radius: float = 0.55, y: float = 0):
    """Closed circular cord in XZ, with exact contact arcs and straight tangents."""
    if radius <= 0 or radius >= min(belt.r1, belt.r2):
        raise ValueError("Cord radius must be positive and smaller than both pulleys")
    low, high = belt.normal_angles

    def point(centre, r, a):
        return centre[0] + r * math.cos(a), y, centre[1] + r * math.sin(a)

    a = point(belt.c1, belt.r1, high)
    b = point(belt.c1, belt.r1, low)
    c = point(belt.c2, belt.r2, low)
    d = point(belt.c2, belt.r2, high)
    edges = [
        Edge.make_three_point_arc(a, point(belt.c1, belt.r1, (high + low + 2 * math.pi) / 2), b),
        Edge.make_line(b, c),
        Edge.make_three_point_arc(c, point(belt.c2, belt.r2, (high + low) / 2), d),
        Edge.make_line(d, a),
    ]
    plane = Plane(origin=a, z_dir=(-math.sin(high), 0, math.cos(high)))
    return sweep(plane * Circle(radius), path=Wire(edges), is_frenet=True)


def cam_groove(
    profile: Callable[[float], float],
    width: float,
    depth: float,
    overshoot: float = 0.2,
    steps: int = 144,
):
    """Cutting tool for a closed cam groove about Z: sits at z=0, points -Z.

    `profile(angle)` is the radius of the groove's centre line under a follower that is held on
    the +Y radial line, after the cam has turned counter-clockwise by `angle` degrees. It must
    be periodic over 360 degrees and smooth. Both walls are true offsets of the centre line by
    width / 2, so a round follower pin of that width fits at every angle.
    """
    if min(width, depth) <= 0 or steps < 24:
        raise ValueError("Require positive width and depth and at least 24 steps")
    radii = [profile(360 * k / steps) for k in range(steps)]
    if min(radii) <= width / 2:
        raise ValueError("Groove would cross the axis")
    walls = []
    for side in (1, -1):
        points = []
        for k in range(steps):
            turn = 360 * k / steps
            psi = math.radians(90 - turn)  # the point that the turn brings under the follower
            radius = radii[k]
            slope = -cam_rate(profile, turn)  # d radius / d psi
            x, y = radius * math.cos(psi), radius * math.sin(psi)
            tx = slope * math.cos(psi) - radius * math.sin(psi)
            ty = slope * math.sin(psi) + radius * math.cos(psi)
            norm = math.hypot(tx, ty)
            # the outward normal of a counter-clockwise curve is (ty, -tx)
            points.append((x + side * width / 2 * ty / norm, y - side * width / 2 * tx / norm))
        walls.append(Wire([Spline(*points, periodic=True)]))
    ring = Face(walls[0], [walls[1]])
    return Pos(0, 0, overshoot) * extrude(ring, amount=depth + overshoot, dir=(0, 0, -1))


def hex_prism(radius: float, length: float):
    """Centred hexagonal coupling around Z; radius is to a corner, not a standard bolt."""
    if min(radius, length) <= 0:
        raise ValueError("Positive coupling radius and length required")
    return Pos(0, 0, -length / 2) * extrude(RegularPolygon(radius, 6), amount=length)


def bar_between(a, b, width: float, depth: float):
    """Rectangular beam with local Z joining two 3D end points."""
    length = math.dist(a, b)
    if length <= 0 or min(width, depth) <= 0:
        raise ValueError("Beam length, width and depth must be positive")
    mid = tuple((u + v) / 2 for u, v in zip(a, b))
    axis = tuple(v - u for u, v in zip(a, b))
    return Plane(origin=mid, z_dir=axis).location * Box(width, depth, length)


def link(length: float, width: float, thickness: float, bore: float):
    """Flat round-ended link along X; end bores at x=0 and x=length, axis Z."""
    if not 0 < bore < width < length or thickness <= 0:
        raise ValueError("Require 0 < bore < width < length, positive thickness")
    shape = Pos(length / 2, 0, 0) * Box(length, width, thickness)
    for x in (0, length):
        shape += Pos(x, 0, 0) * Cylinder(width / 2, thickness)
    for x in (0, length):
        shape -= Pos(x, 0, 0) * Cylinder(bore / 2, thickness + 2)
    return shape


def spoked_wheel(radius: float, width: float, bore: float, spokes: int = 8):
    """Single solid wheel around Z with a retained, flat-bottom rope groove."""
    if radius < 6 or width < 3 or not 0 < bore < radius / 2 or spokes < 3:
        raise ValueError("Invalid spoked-wheel proportions")
    hub = max(bore / 2 + 2, radius * 0.19)
    rim = max(2, radius * 0.105)
    shape = Cylinder(radius, width) - Cylinder(radius - rim, width + 2)
    shape += Cylinder(hub, width)
    for i in range(spokes):
        shape += (
            Rot(0, 0, i * 360 / spokes)
            * Pos(radius / 2, 0, 0)
            * Box(radius, max(2, radius * 0.075), width - 1)
        )
    groove = Cylinder(radius + 1, 1.8) - Cylinder(radius - 0.8, 3)
    shape -= groove
    return shape - Cylinder(bore / 2, width + 2)
