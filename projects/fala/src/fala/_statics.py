"""Forces on a moving unit and the torque at the crank: a rigid, quasi-static friction model.

Each unit is held at six places. Its two pads rest on the cam. The blade's edge in front and
the rear panel's fin behind hold it along the street and square to it. The blade's bead on
the sled's tongue, high in front, and the rear panel against the sled's tip, low behind,
hold it upright. That is exactly as many as a rigid body needs, so the forces follow from
equilibrium with no assumption about stiffness.

Because the cam stands behind the unit's centre of gravity, the weight tips the unit forward
onto the bead and back onto the panel: the guide is seated by gravity on the same two points
through the whole turn, and its clearance is never crossed. The two points lie on either
side of the cam, so friction in the guide cannot wedge the unit. `forces` reports whether
the seat holds for a given friction: both pads and both guide points must push.

What this is not: a measurement. The house mass is an assumed share of its solid volume, the
friction coefficients are inputs, and inertia is left out (at one crank turn a second the
accelerations are under 0.2 % of gravity). The test prints have to confirm the numbers.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from build123d import CenterOf

from fala import _massing as massing
from fala import _parts as parts
from fala import _wave as wave
from fala._layout import layout

PLA = 1.24e-3  # g per mm3, solid
SHELL = 0.30  # a printed house weighs about this share of its solid volume: an assumption
GRAVITY = 9.81e-3  # N per gram
GEAR_EFFICIENCY = 0.9  # printed spur pair: an assumption
AXLE_FRICTION = 0.25  # printed cam on its steel axle: an assumption


@dataclass(frozen=True)
class UnitForces:
    """Contact forces on one unit in newtons; `seated` when the guide stays on its beads."""

    pads: tuple[float, float]
    locators: tuple[float, float]  # along the street, at the blade and at the fin; either sign
    blade: float
    panel: float
    weight: float
    guide_drag: float  # friction in the guide that opposes the unit's travel, as a share of weight
    torque: float  # at the cam, along its motion, N mm
    load: tuple[float, float]  # Y and Z force of the unit on the cam, N

    @property
    def seated(self) -> bool:
        return min(*self.pads, self.blade, self.panel) > 0


@lru_cache(maxsize=16)
def unit_mass(p, which: str, shell: float = SHELL) -> tuple[float, tuple[float, float, float]]:
    """Mass in grams and centre of gravity (rest coordinates, about X = 0) of sled plus house."""
    p = p.model_copy(update={"turn": 0.0})
    sled, house = parts.sled(p), massing.house(p, which)
    masses = (sled.volume * PLA, house.volume * PLA * shell)
    centres = [np.array(tuple(s.center(CenterOf.MASS))) for s in (sled, house)]
    total = sum(masses)
    centre = sum(m * c for m, c in zip(masses, centres)) / total
    return total, tuple(float(v) for v in centre)


def _rate(p, index, turn, direction, step=0.05):
    """Rise and lean of a unit per radian of cam phase, in the direction of travel."""
    a = wave.pose(p, index, turn - step)
    b = wave.pose(p, index, turn + step)
    span = math.radians(2 * step / p.ratio)
    return direction * (b.z - a.z) / span, direction * math.radians(b.lean - a.lean) / span


def forces(
    p,
    index: int,
    turn: float,
    direction: int = 1,
    mu_pad: float = 0.3,
    mu_guide: float = 0.3,
    shell: float = SHELL,
) -> UnitForces:
    """Equilibrium of unit `index` at crank angle `turn`, turning forward (1) or back (-1)."""
    L = layout(p)
    at = wave.pose(p, index, turn)
    theta = math.radians(at.lean)
    c, s = math.cos(theta), math.sin(theta)
    rise_rate, lean_rate = _rate(p, index, turn, direction)
    mass, (gx, gy, gz) = unit_mass(p, massing.kind(index), shell)
    weight = mass * GRAVITY
    pivot = np.array([at.x, 0.0, at.z])

    def world(u, y, w):  # a point of the unit, given in its own frame about the pivot
        return np.array([at.x + u * c - w * s, y, at.z + u * s + w * c])

    def local_at(x, z):  # the unit's own coordinates of the world point (x, z)
        dx, dz = x - at.x, z - at.z
        return dx * c + dz * s, -dx * s + dz * c

    def speed(point):  # velocity of the unit's material at a world point, per radian of phase
        u, w = local_at(point[0], point[2])
        return np.array(
            [lean_rate * (-u * s - w * c), 0.0, rise_rate + lean_rate * (u * c - w * s)]
        )

    def rub(point, normal, other=None):  # unit direction of friction on the unit at a contact
        slide = (np.zeros(3) if other is None else other) - speed(point)
        slide = slide - (slide @ normal) * normal
        size = np.linalg.norm(slide)
        return slide / size if size > 1e-12 else np.zeros(3)

    contacts = []  # (point, normal force direction, friction direction, coefficient)
    phase = wave.phase(p, turn)
    for cx, cy, cz in at.contacts:
        point = np.array([cx, cy, cz])
        slope = math.atan(L.cam.slope(cx, phase))
        normal = np.array([-math.sin(slope), 0.0, math.cos(slope)])
        surface = direction * np.array([0.0, cz - L.cam_z, -(cy - L.cam_y)])  # the cam's skin
        contacts.append((point, normal, rub(point, normal, surface), mu_pad))
    front = np.array([at.x, (L.blade_y0 + L.blade_y1) / 2, at.z])
    rear = np.array([at.x, (L.fin_y0 + L.block_y1) / 2, at.z])
    lift = p.bead - at.z
    top = np.array([at.x - lift * s / c, L.plate_y0, p.bead])  # on the tongue's centre line
    low = world(0.0, L.rear_y, L.tip_z - L.pivot_z)  # the sled's rear tip on the rear panel
    ahead, behind = np.array([0.0, 1.0, 0.0]), np.array([0.0, -1.0, 0.0])
    along = np.array([1.0, 0.0, 0.0])
    beads = [(top, ahead, rub(top, ahead)), (low, behind, rub(low, behind))]

    centre = world(gx, gy, gz - L.pivot_z)
    rhs = np.concatenate([[0, 0, weight], np.cross(centre - pivot, [0, 0, weight])])
    solution, signs = None, (1, 1)
    for signs in ((1, 1), (-1, -1), (1, -1), (-1, 1)):  # which side each locator bears on
        columns = [n + mu * t for _, n, t, mu in contacts]
        columns += [
            along + sign * mu_guide * rub(q, along) for sign, q in zip(signs, (front, rear))
        ]
        columns += [n + mu_guide * t for _, n, t in beads]
        points = [contacts[0][0], contacts[1][0], front, rear, top, low]
        matrix = np.zeros((6, 6))
        for k, (point, column) in enumerate(zip(points, columns)):
            matrix[:3, k] = column
            matrix[3:, k] = np.cross(point - pivot, column)
        solution = np.linalg.solve(matrix, rhs)
        if solution[2] * signs[0] >= 0 and solution[3] * signs[1] >= 0:
            break
    n1, n2, hold_a, hold_b, blade, panel = (float(v) for v in solution)
    torque, load = 0.0, np.zeros(3)
    for size, (point, normal, friction, mu) in zip((n1, n2), contacts):
        push = size * (normal + mu * friction)
        surface = direction * np.array([0.0, point[2] - L.cam_z, -(point[1] - L.cam_y)])
        torque += push @ surface
        load -= push
    drag = sum(abs(size) * mu_guide * abs(t[2]) for size, (_, _, t) in zip((blade, panel), beads))
    drag += sum(
        abs(size) * mu_guide * abs(rub(q, along)[2])
        for size, q in zip((hold_a, hold_b), (front, rear))
    )
    return UnitForces(
        (n1, n2),
        (hold_a, hold_b),
        blade,
        panel,
        weight,
        float(drag / weight),
        float(torque),
        (float(load[1]), float(load[2])),
    )


def crank_torque(
    p, turn: float, direction: int = 1, mu: float = 0.3, shell: float = SHELL
) -> float:
    """Torque at the handwheel in N mm to keep turning slowly, friction and gear loss included."""
    units = [forces(p, i, turn, direction, mu, mu, shell) for i in range(p.houses)]
    cam = parts.cam(p.model_copy(update={"turn": 0.0})).volume * PLA * GRAVITY * 0.6
    side = sum(u.load[0] for u in units)
    down = sum(u.load[1] for u in units) - cam
    bearing = AXLE_FRICTION * math.hypot(side, down) * p.axle / 2
    return (sum(u.torque for u in units) + bearing) / p.ratio / GEAR_EFFICIENCY


def survey(p, mu: float = 0.3, step: float = 15.0, shell: float = SHELL) -> dict:
    """One pass of the wave, forward and back: how firmly the guide sits and what the crank needs."""
    seat, drag, torque, lost = [], [], {1: [], -1: []}, 0
    turns = np.arange(0.0, 360.0 * p.ratio, step)
    for direction in (1, -1):
        for turn in turns:
            for i in range(p.houses):
                unit = forces(p, i, float(turn), direction, mu, mu, shell)
                seat.append(min(unit.blade, unit.panel) / unit.weight)
                drag.append(unit.guide_drag)
                lost += not unit.seated
            torque[direction].append(crank_torque(p, float(turn), direction, mu, shell))
    every = torque[1] + torque[-1]
    return {
        "friction": mu,
        "seat_min": min(seat),  # smallest guide force, as a share of the unit's weight
        "drag_max": max(drag),  # largest guide friction against the travel, share of weight
        "unseated": lost,
        "torque_mean": float(np.mean(every)),
        "torque_min": min(every),
        "torque_max": max(every),
        "torque_forward": float(np.mean(torque[1])),
        "torque_back": float(np.mean(torque[-1])),
    }
