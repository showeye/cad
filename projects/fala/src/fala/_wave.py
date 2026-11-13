"""The motion: where the cam and every moving unit are for a given turn of the crank.

A unit (sled plus house) is held along the street at its pivot, rests on the cam with two
crowned pads and is free to rise and to lean about Y. Its pose is exact rigid geometry from
`cadkit.features.cams`; nothing here is sampled or assumed.
"""

import math
from dataclasses import dataclass

import numpy as np

from fala._layout import layout

LOW_CROWN = 5.0  # nose radius of the lower, capturing pads


@dataclass(frozen=True)
class Pose:
    """One unit: its pivot, lean, the two touching points and the gaps under the cam."""

    x: float
    z: float
    rise: float
    lean: float
    contacts: tuple
    gap: float  # the smaller of the two gaps under the cam
    gaps: tuple = ()


def phase(p, turn: float | None = None) -> float:
    """Cam phase in degrees: the wave travels towards +X as the crank angle grows."""
    return (p.turn if turn is None else turn) / p.ratio


def cam_angle(p, turn: float | None = None) -> float:
    """Rotation of the cam about +X, degrees: the gear pair reverses the crank's sense."""
    return -phase(p, turn)


def pads(p) -> list[tuple[float, float]]:
    """Nose centres of the two upper pads in the unit's frame (origin at the pivot)."""
    L = layout(p)
    w = L.pad_z + p.pad_crown - L.pivot_z
    return [(-p.pad_span / 2, w), (p.pad_span / 2, w)]


def low_pads(p) -> list[tuple[float, float]]:
    """Nose centres of the two lower pads in the unit's frame: one under each upper pad."""
    L = layout(p)
    w = L.low_z - LOW_CROWN - L.pivot_z
    return [(-p.capture_span / 2, w), (p.capture_span / 2, w)]


def pose(p, index: int, turn: float | None = None) -> Pose:
    """Pose of unit `index` (0 at the -X end) at the model's turn, or at `turn`."""
    L = layout(p)
    x, angle = L.centres[index], phase(p, turn)
    seat = L.cam.seat(x, angle, pads(p), p.pad_crown)
    gaps = [
        L.cam.gap_below(x, angle, seat.height, seat.lean, pad, LOW_CROWN) for pad in low_pads(p)
    ]
    contacts = tuple((cx, cy + L.cam_y, cz + L.cam_z) for cx, cy, cz in seat.contacts)
    z = L.cam_z + seat.height
    return Pose(x, z, z - L.pivot_z, seat.lean, contacts, min(gaps), tuple(gaps))


def crest(p, index: int) -> float:
    """Crank angle, in degrees within one pass of the wave, at which unit `index` stands on
    the crest: at its highest and upright, its left-hand neighbour leaning away from it.

    This is where a house is put in. From one unit to the next it is the same step of the
    crank: `ratio` times the wave's phase step per house, a third of a turn for the Nikisz.
    """
    L = layout(p)
    return p.ratio * ((math.degrees(L.cam.k * L.centres[index]) + 270.0) % 360.0)


def unit_matrix(p, index: int, turn: float | None = None) -> np.ndarray:
    """4x4 transform that carries a unit built at rest about X = 0 to its pose."""
    L = layout(p)
    at = pose(p, index, turn)
    t = math.radians(at.lean)
    c, s = math.cos(t), math.sin(t)
    lean = np.array([[c, 0, -s, 0], [0, 1, 0, 0], [s, 0, c, 0], [0, 0, 0, 1]], float)
    down, up = np.eye(4), np.eye(4)
    down[2, 3] = -L.pivot_z
    up[0, 3], up[2, 3] = at.x, at.z
    return up @ lean @ down


def turn_matrix(angle: float, y: float, z: float) -> np.ndarray:
    """4x4 rotation by `angle` degrees about the axis parallel to X through (y, z)."""
    t = math.radians(angle)
    c, s = math.cos(t), math.sin(t)
    return np.array(
        [[1, 0, 0, 0], [0, c, -s, y - c * y + s * z], [0, s, c, z - s * y - c * z], [0, 0, 0, 1]],
        float,
    )
