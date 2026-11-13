"""Forces on a moving unit and the torque at the crank: a rigid, quasi-static friction model.

Each unit is held at six places. Its two pads rest on the cam. The blade's edge in front and
the rear panel's fin behind hold it along the street and square to it. The blade's rear bead
on the sled's tongue, high inside the house, and the rear panel against the sled's tip, low
behind the cam, hold it upright. That is exactly as many as a rigid body needs, so the forces
follow from equilibrium with no assumption about stiffness.

Because the cam stands behind the unit's centre of gravity, the weight tips the unit forward
onto the bead and back onto the panel: at ordinary friction the guide is seated by gravity on
those two points through the whole turn. The cam's skin also drags the pads front to back.
At high friction that drag can lift a guide point off its seat; the unit then meets a stop
after `stop_gap`: the blade's front bead against the wall of the house's slot, or the rail's
low bead against the sled's stem. `forces` finds which of the four states holds and reports
it. The two seats lie on either side of the cam and far apart in height, so guide friction
stays a small share of the weight and cannot wedge the unit.

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
    """Contact forces on one unit in newtons, and which contacts carry them."""

    pads: tuple[float, float]  # the two upper pads, resting on the cam
    locators: tuple[float, float]  # along the street, at the blade and at the fin; either sign
    blade: float  # upper seat: the blade's rear bead on the tongue; 0 once the unit has left it
    panel: float  # lower seat: the rear panel on the sled's tip
    stops: tuple[float, float]  # upper and lower stop; both 0 while the guide is seated
    weight: float
    guide_drag: float  # friction in the guide that opposes the unit's travel, as a share of weight
    torque: float  # at the cam, along its motion, N mm
    load: tuple[float, float]  # Y and Z force of the unit on the cam, N
    free: bool = True  # False when no set of contacts balances the unit: it is wedged
    low: tuple[float, float] = (0.0, 0.0)  # the two lower pads; 0 unless the cam pulls the unit

    @property
    def carried(self) -> bool:
        """Resting on both upper pads by its own weight: the cam does not have to pull."""
        return self.free and self.low == (0.0, 0.0) and min(self.pads) > 0

    @property
    def seated(self) -> bool:
        """Carried, and on both gravity seats of the guide."""
        return self.carried and self.stops == (0.0, 0.0) and min(self.blade, self.panel) > 0


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


@lru_cache(maxsize=8)
def _cam_weight(p) -> float:
    """Weight of the printed cam in newtons, at 60 % of its solid volume: an assumption."""
    return parts.cam(p).volume * PLA * GRAVITY * 0.6


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
    mass, (gx, gy, gz) = unit_mass(p, massing.kind(p, index), shell)
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

    phase = wave.phase(p, turn)

    def on_cam(cx, cy, cz, upper):  # (point, normal force direction, friction direction)
        point = np.array([cx, cy, cz])
        slope = math.atan(L.cam.slope(cx, phase))
        side = 1.0 if upper else -1.0
        normal = side * np.array([-math.sin(slope), 0.0, math.cos(slope)])
        surface = direction * np.array([0.0, cz - L.cam_z, -(cy - L.cam_y)])  # the cam's skin
        return point, normal, rub(point, normal, surface)

    above = [on_cam(cx, cy, cz, True) for cx, cy, cz in at.contacts]
    below = []  # where each lower pad would meet the underside of the cam
    for u, w in wave.low_pads(p):
        cx = world(u, 0.0, w + wave.LOW_CROWN)[0]  # the top of the nose
        centre_y, _ = L.cam.centre(cx, phase)
        below.append(
            on_cam(cx, L.cam_y + centre_y, L.cam_z + L.cam.crest(cx, phase, upper=False), False)
        )
    front = np.array([at.x, (L.blade_y0 + L.blade_y1) / 2, at.z])
    rear = np.array([at.x, (L.fin_y0 + L.block_y1) / 2, at.z])
    ahead, behind = np.array([0.0, 1.0, 0.0]), np.array([0.0, -1.0, 0.0])
    along = np.array([1.0, 0.0, 0.0])

    def on_axis(y, z):  # the point of the unit's centre line that is at height z
        return np.array([at.x - (z - at.z) * s / c, y, z])

    # the two seats, then the stop each guide point meets when it leaves its seat
    upper = [(on_axis(L.plate_y0, p.bead), ahead), (on_axis(L.slot_y0, p.bead), behind)]
    lower = [
        (world(0.0, L.rear_y, L.tip_z - L.pivot_z), behind),
        (on_axis(L.plate_y0, L.stop_z), ahead),
    ]
    centre = world(gx, gy, gz - L.pivot_z)
    rhs = np.concatenate([[0, 0, weight], np.cross(centre - pivot, [0, 0, weight])])

    def balance(pair, top, low):
        """Forces for one choice of contacts, or None when one of them would have to pull."""
        beads = [(q, n, rub(q, n)) for q, n in (top, low)]
        for signs in ((1, 1), (-1, -1), (1, -1), (-1, 1)):  # which side each locator bears on
            columns = [n + mu_pad * t for _, n, t in pair]
            columns += [
                along + sign * mu_guide * rub(q, along) for sign, q in zip(signs, (front, rear))
            ]
            columns += [n + mu_guide * t for _, n, t in beads]
            points = [pair[0][0], pair[1][0], front, rear, top[0], low[0]]
            matrix = np.zeros((6, 6))
            for k, (point, column) in enumerate(zip(points, columns)):
                matrix[:3, k] = column
                matrix[3:, k] = np.cross(point - pivot, column)
            try:
                found = np.linalg.solve(matrix, rhs)
            except np.linalg.LinAlgError:
                continue
            if found[2] * signs[0] >= 0 and found[3] * signs[1] >= 0:
                return (found, beads) if min(found[0], found[1], found[4], found[5]) >= 0 else None
        return None

    # Which two places on the cam carry the unit: both upper pads; then one upper pad with the
    # lower pad of the other side (the cam turns the unit into its lean); then both lower pads
    # (the cam pulls the unit down). For each, the guide seated first, then on one or both stops.
    pairs = [
        ((above[0], above[1]), (0, 0)),
        ((above[0], below[1]), (0, 2)),
        ((below[0], above[1]), (1, 0)),
        ((below[0], below[1]), (1, 2)),
    ]
    guides = [(0, 0), (1, 0), (0, 1), (1, 1)]
    solution = None
    for pair, pulled in pairs:
        for state in guides:
            if (result := balance(pair, upper[state[0]], lower[state[1]])) is not None:
                solution, beads = result
                break
        if solution is not None:
            break
    if solution is None:
        return UnitForces(
            (0.0, 0.0),
            (0.0, 0.0),
            0.0,
            0.0,
            (0.0, 0.0),
            weight,
            math.inf,
            math.inf,
            (0.0, 0.0),
            False,
        )
    n1, n2, hold_a, hold_b, top, low = (float(v) for v in solution)
    torque, load = 0.0, np.zeros(3)
    for size, (point, normal, friction) in zip((n1, n2), pair):
        push = size * (normal + mu_pad * friction)
        surface = direction * np.array([0.0, point[2] - L.cam_z, -(point[1] - L.cam_y)])
        torque += push @ surface
        load -= push
    drag = sum(abs(size) * mu_guide * abs(t[2]) for size, (_, _, t) in zip((top, low), beads))
    drag += sum(
        abs(size) * mu_guide * abs(rub(q, along)[2])
        for size, q in zip((hold_a, hold_b), (front, rear))
    )
    return UnitForces(
        (0.0 if pulled[0] else n1, 0.0 if pulled[1] else n2),
        (hold_a, hold_b),
        top if state[0] == 0 else 0.0,
        low if state[1] == 0 else 0.0,
        (top if state[0] else 0.0, low if state[1] else 0.0),
        weight,
        float(drag / weight),
        float(torque),
        (float(load[1]), float(load[2])),
        True,
        (n1 if pulled[0] else 0.0, n2 if pulled[1] else 0.0),
    )


def roof_play(p, height: float = massing.A_ROOF[3]) -> tuple[float, float]:
    """How far a roof at `height` moves front to back when a guide point goes to its stop.

    First value: the upper point leaves the blade's bead and the unit turns about the sled's
    tip. Second: the lower point leaves the rear panel and the unit turns about the bead.
    """
    L = layout(p)
    upper = p.stop_gap * (height - L.tip_z) / (p.bead - L.tip_z)
    lower = p.stop_gap * (height - p.bead) / (p.bead - L.stop_z)
    return upper, lower


def crank_torque(
    p, turn: float, direction: int = 1, mu: float = 0.3, shell: float = SHELL
) -> float:
    """Torque at the handwheel in N mm to keep turning slowly, friction and gear loss included."""
    units = [forces(p, i, turn, direction, mu, mu, shell) for i in range(p.houses)]
    cam = _cam_weight(p.model_copy(update={"turn": 0.0}))
    side = sum(u.load[0] for u in units)
    down = sum(u.load[1] for u in units) - cam
    bearing = AXLE_FRICTION * math.hypot(side, down) * p.axle / 2
    return (sum(u.torque for u in units) + bearing) / p.ratio / GEAR_EFFICIENCY


def survey(p, mu: float = 0.3, step: float = 15.0, shell: float = SHELL) -> dict:
    """One pass of the wave, forward and back: how the units sit and what the crank needs."""
    seat, pad, drag, torque = [], [], [], {1: [], -1: []}
    lost, pulled, wedged = 0, 0, 0
    turns = np.arange(0.0, 360.0 * p.ratio, step)
    for direction in (1, -1):
        for turn in turns:
            for i in range(p.houses):
                unit = forces(p, i, float(turn), direction, mu, mu, shell)
                seat.append(min(unit.blade, unit.panel) / unit.weight)
                pad.append(min(unit.pads) / unit.weight)
                wedged += not unit.free
                pulled += unit.free and not unit.carried
                lost += unit.carried and not unit.seated
                if unit.free:
                    drag.append(unit.guide_drag)
            torque[direction].append(crank_torque(p, float(turn), direction, mu, shell))
    every = torque[1] + torque[-1]
    return {
        "friction": mu,
        "seat_min": min(seat),  # smallest force on a guide seat, as a share of the unit's weight
        "pad_min": min(pad),  # smallest force on an upper pad, as a share of the unit's weight
        "drag_max": max(drag, default=math.inf),  # guide friction against the travel, of weight
        "unseated": lost / len(seat),  # share of poses with a guide point on its stop
        "pulled": pulled / len(seat),  # share of poses in which the cam pulls on a lower pad
        "wedged": wedged,  # poses with no balance at all: must be zero
        "torque_mean": float(np.mean(every)),
        "torque_min": min(every),
        "torque_max": max(every),
        "torque_forward": float(np.mean(torque[1])),
        "torque_back": float(np.mean(torque[-1])),
    }
