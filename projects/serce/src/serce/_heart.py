"""The Bryła heart as half-space polyhedra, and the hinge line along each flank.

Origin at the heart's hidden tip, z up, front is -y, the viewer's left is -x. Units: mm, degrees.

Each half of the heart (left, right) is a convex polyhedron: every facet is one plane. A wall or
a lining of constant thickness is the same set of planes moved inwards, so the offsets are exact.
The outside of the two halves is cleaved differently; the hollow is the same on both sides and
lies inside both, so the lump is lopsided outside but never opens a gap at the mid-plane.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from build123d import Axis, Plane, Solid
from cadkit.features.polyhedron import halfspace_solid

from serce import _facets

# ---------------------------------------------------------------- form (approved look brief)
LOBE_C = (-19.5, 61.0)  # centre of the left lobe circle in the front view (x, z)
LOBE_R = 21.5  # the heart is 82 wide and 82.5 tall before cleaving; the cleft is at z = 70
FLOOR_Z = 31.0  # top of the room floor

# The V edges are tangent to the lobes, so a straight hinge can run along each flank.
_D = math.hypot(*LOBE_C)
V_TILT = math.atan2(-LOBE_C[0], LOBE_C[1]) + math.asin(LOBE_R / _D)  # V edge from vertical, rad
V_DIR = np.array([-math.sin(V_TILT), 0.0, math.cos(V_TILT)])  # up the left V edge
V_IN = np.array([math.cos(V_TILT), 0.0, math.sin(V_TILT)])  # square to it, into the heart
V_TANGENT = math.sqrt(_D**2 - LOBE_R**2)  # from the tip to where the V edge meets the lobe
BACK = np.array([0.0, 1.0, 0.0])

LEFT, RIGHT = -1, 1
SIDES = {"left": LEFT, "right": RIGHT}


def mirrored(vector, side: int) -> np.ndarray:
    """A vector given for the left side, as it is on `side`."""
    return np.asarray(vector, float) * [-side, 1.0, 1.0]


# ---------------------------------------------------------------- hinge
@dataclass(frozen=True)
class Hinge:
    """The hinge line of the left wing; the right one is its mirror image in x.

    Local frame: origin where the axis meets the coal-bed facet, x into the heart, y to the back,
    z up the axis. A wing opens by turning about the axis by -angle (left) or +angle (right).
    """

    depth: float  # of the axis under both flank facets
    proud: float  # how far the barrel stands out of the flank facets
    origin: tuple[float, float, float]
    seat: float  # axis . origin: the bed facet is the plane axis . x = seat
    barrel_top: float  # local z
    knuckle_top: float  # local z

    @property
    def frame(self) -> Plane:
        return Plane(origin=self.origin, x_dir=tuple(V_IN), z_dir=tuple(V_DIR))

    def axis(self, side: int) -> Axis:
        return Axis(tuple(mirrored(self.origin, side)), tuple(mirrored(V_DIR, side)))

    def point(self, x: float, y: float, z: float, side: int = LEFT) -> np.ndarray:
        """World coordinates of a local point of the hinge frame on `side`."""
        return mirrored(np.asarray(self.origin) + x * V_IN + y * BACK + z * V_DIR, side)

    def local(self, point, side: int = LEFT) -> np.ndarray:
        """Local hinge-frame coordinates of a world point."""
        rel = mirrored(point, side) - np.asarray(self.origin)
        return np.array([rel @ V_IN, rel @ BACK, rel @ V_DIR])


def hinge(p) -> Hinge:
    """Hinge geometry from the parameters.

    Seen from a pivot `depth` under both skins, skin at radius r is free to swing through
    2 * flank_ridge + 2 * acos(depth / r). Everything nearer than the barrel radius turns in a
    cove, so the depth only has to clear the swing at the barrel radius.
    """
    free = math.radians((p.wing_max + p.swing_margin) / 2 - p.flank_ridge)
    depth = p.hinge_radius * math.cos(free)
    edge = V_DIR * (p.seat_z / V_DIR[2])  # on the left V edge at the height of the bed facet
    origin = edge + depth / math.cos(math.radians(p.flank_ridge)) * V_IN
    seat = float(V_DIR @ origin)
    barrel_top = V_TANGENT - seat - p.barrel_stop
    return Hinge(
        depth=depth,
        proud=p.hinge_radius - depth,
        origin=tuple(float(v) for v in origin),
        seat=seat,
        barrel_top=barrel_top,
        knuckle_top=barrel_top + p.knuckle,
    )


# ---------------------------------------------------------------- planes
def _flanks(flank_ridge: float) -> np.ndarray:
    g = math.radians(flank_ridge)
    return np.array([-math.cos(g) * V_IN + math.sin(g) * sy * BACK for sy in (-1, 1)])


@lru_cache(maxsize=8)
def _planes(flank_ridge: float):
    """Plane sets in the left frame: the two skins and the shared hollow. Mid-plane last."""
    flanks = _flanks(flank_ridge)
    mid = np.array([[1.0, 0.0, 0.0]])
    out = {}
    tables = {LEFT: np.array(_facets.LEFT), RIGHT: np.array(_facets.RIGHT)}
    for side, table in tables.items():
        out[side] = (
            np.vstack([table[:, :3], flanks, mid]),
            np.concatenate([table[:, 3], [0, 0, 0]]),
        )
    both = np.vstack([tables[LEFT], tables[RIGHT]])
    out["hollow"] = (np.vstack([both[:, :3], flanks, mid]), np.concatenate([both[:, 3], [0, 0, 0]]))
    return out


def _solid(planes, side: int, depth: float, extra) -> Solid | None:
    a, d = planes
    d = np.append(d[:-1] - depth, d[-1])  # the mid-plane stays
    a = a * [-side, 1.0, 1.0]  # the tables describe the left side
    if extra:
        a = np.vstack([a, [n for n, _ in extra]])
        d = np.concatenate([d, [off for _, off in extra]])
    return halfspace_solid(a, d)


def skin(p, side: int, depth: float = 0.0, extra=()) -> Solid | None:
    """One half of the heart's outside, every facet moved in by `depth`, cut by `extra` planes.

    `extra` is a sequence of (normal, offset) half-spaces n . x <= offset in world coordinates.
    """
    return _solid(_planes(p.flank_ridge)[side], side, depth, extra)


def hollow(p, side: int, depth: float, extra=()) -> Solid | None:
    """One half of the shared hollow at `depth` under the skin (wall, wall + lining, ...)."""
    return _solid(_planes(p.flank_ridge)["hollow"], side, depth, extra)


# ---------------------------------------------------------------- cutting planes (n . x <= d)
def in_front(y: float):
    return (0.0, 1.0, 0.0), y


def behind(y: float):
    return (0.0, -1.0, 0.0), -y


def below(z: float):
    return (0.0, 0.0, 1.0), z


def above(z: float):
    return (0.0, 0.0, -1.0), -z


def beside(side: int, x: float):
    """On `side` of the mid-plane, at least `x` away from it."""
    return (-side, 0.0, 0.0), -x


def along_axis(h: Hinge, side: int, z0: float | None = None, z1: float | None = None):
    """Between local heights z0 and z1 of the hinge on `side` (either may be open)."""
    u = mirrored(V_DIR, side)
    planes = []
    if z0 is not None:
        planes.append((tuple(-u), -(h.seat + z0)))
    if z1 is not None:
        planes.append((tuple(u), h.seat + z1))
    return planes


def hinge_box(h: Hinge, side: int, x=(None, None), y=(None, None)):
    """Limits in the local x (into the heart) and y (to the back) of the hinge on `side`."""
    origin = mirrored(h.origin, side)
    planes = []
    for direction, (lo, hi) in ((mirrored(V_IN, side), x), (BACK, y)):
        base = float(direction @ origin)
        if lo is not None:
            planes.append((tuple(-direction), -(base + lo)))
        if hi is not None:
            planes.append((tuple(direction), base + hi))
    return planes
