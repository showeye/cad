"""How a recoil anchor escapement runs: the wheel and the pendulum as two bodies in a plane.

`cadkit.features.escapement` has the geometry; this module puts forces on it. The escape
wheel is turned by a torque, the anchor swings with a pendulum, and teeth and pallets push
each other apart wherever they overlap: a stiff spring with damping and sliding friction.
Both corners of every tooth's land are tried against both pallets, and the nose of each
pallet against the flanks and the land of the tooth beside it, so a pallet that falls onto a
tooth or a nose that reaches a flank is felt.

Both arbors have dry friction that can hold a body still: a wheel or an anchor that has
stopped stays where it is until it is pushed harder than its friction. Friction between a
tooth and a pallet fades as the sliding stops, so a tooth that should stick on a pallet
creeps along it instead, far slower than it runs. `run` therefore ends when both arbors have
been all but still for a quarter of a second, and that is a stall.

Left out: the play of the arbors in their holes, any give in the parts beyond the contact
spring, air, and the wheel's root between two teeth (a nose that gets there is an error:
give the anchor a stop). Friction values are the caller's; nothing here is measured.

Units: mm, degrees, seconds and grams; forces in mN, torques in mN mm (which is uN m) and
inertia in g mm2. As in `escapement`, the wheel's progress is clockwise and the anchor's
angle counter-clockwise.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

from cadkit.features.escapement import RecoilEscapement

GRAVITY = 9810.0  # mm/s2
_STILL = 0.01  # rad/s: an arbor slower than this is held by its friction, if that is enough
_SLIDE = 0.5  # mm/s: surfaces that slide slower than this are taken as partly sticking
_GRID = 0.1  # degrees of the wheel between two samples of the drive
_QUIET = 0.25  # seconds with both arbors that slow, after which a run ends


def _none(turned: float) -> float:
    return 0.0


@dataclass(frozen=True)
class Drive:
    """What turns the escape wheel. Each function takes the wheel's turn from the start.

    `torque` is the moment at the wheel with friction left out, and `loss` the share of it
    that friction in the train takes, whichever way the wheel turns. `inertia` is that of the
    wheel and of everything that moves with it, seen at the wheel. `lean` is the anchor's
    angle at which the pendulum hangs at rest: zero in a frame that stands upright. `drag` is
    friction at the wheel's arbor that does not depend on the load. The functions are also
    asked beyond `turn`, where a drive that has run down returns no torque.
    """

    turn: float  # the wheel is driven this far; a run has finished when it gets there
    torque: Callable[[float], float]
    inertia: Callable[[float], float]
    loss: Callable[[float], float] = _none
    lean: Callable[[float], float] = _none
    drag: float = 0.0


@dataclass(frozen=True)
class Pendulum:
    """The anchor and all that swings with it."""

    inertia: float  # about the anchor's arbor
    mass: float
    arm: float  # its centre of mass below the arbor
    drag: float = 0.0  # friction at the arbor
    stop: float | None = None  # the anchor is stopped this far either side of centre


@dataclass(frozen=True)
class Run:
    """What `run` found; `times`, `turned` and `angles` are sampled at even intervals."""

    times: tuple[float, ...]
    turned: tuple[float, ...]  # the wheel's turn from the start
    angles: tuple[float, ...]  # the anchor's angle
    beats: tuple[tuple[float, int], ...]  # (time, pallet) of each landing; 0 is the entry
    finished: float | None  # when the wheel had turned as far as it is driven, if it did
    flank: float  # how far below a tooth's tip a nose met that tooth while the wheel was driven

    def swing(self, start: float = 0.0, end: float = math.inf) -> tuple[float, float]:
        """The anchor's least and greatest angle between two times."""
        seen = [a for t, a in zip(self.times, self.angles) if start <= t <= end]
        return min(seen), max(seen)

    def at(self, time: float) -> tuple[float, float]:
        """The wheel's turn and the anchor's angle at `time`; the last sample after the end."""
        gap = self.times[1] - self.times[0]
        index = min(max(time / gap, 0.0), len(self.times) - 1.0)
        low = min(int(index), len(self.times) - 2)
        part = index - low
        return (
            self.turned[low] + part * (self.turned[low + 1] - self.turned[low]),
            self.angles[low] + part * (self.angles[low + 1] - self.angles[low]),
        )


def _faces(points: list) -> tuple:
    """(normal x, normal y, offset) of each edge of a convex polygon; normals point out."""
    area = sum(a[0] * b[1] - a[1] * b[0] for a, b in zip(points, points[1:] + points[:1]))
    if area < 0:
        points = points[::-1]
    found = []
    for a, b in zip(points, points[1:] + points[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        size = math.hypot(dx, dy)
        found.append((dy / size, -dx / size, (dy * a[0] - dx * a[1]) / size))
    return tuple(found)


def run(
    e: RecoilEscapement,
    drive: Drive,
    pendulum: Pendulum,
    *,
    depth: float,
    length: float = 5.0,
    progress: float = 0.0,
    angle: float = 0.0,
    speed: float = 0.0,
    friction: float = 0.3,
    restitution: float = 0.5,
    stiffness: float = 2e4,
    step: float = 2.5e-5,
    sample: float = 0.01,
    limit: float = 10.0,
) -> Run:
    """Let the escapement go and follow it until nothing moves, or for `limit` seconds.

    The wheel starts at `progress` (in the escapement's own measure) turning at `speed`
    degrees a second, the anchor at `angle`. `depth` is that of the wheel's teeth, `length`
    that of the pallets' faces. `friction` is that between teeth and pallets. `restitution`
    is the share of its speed with which a tooth leaves a pallet it has struck; `stiffness`
    is the contact spring in mN per mm, stiff enough when a resting tooth sinks in by microns.
    A beat is a tooth landing on the pallet that the last beat did not land on. A nose
    passes the corner of every tooth it lets go, so `flank` is a few microns in a run in
    which no nose meets a flank. It is not kept once the drive has run down: a wheel that
    nothing pushes on is thrown about by the pallets and may meet them anywhere.
    """
    if not 0 < step <= sample or limit <= 0 or not 0 < restitution < 1:
        raise ValueError("Require 0 < step <= sample, a positive limit and 0 < restitution < 1")
    if depth <= 0 or depth >= e.tip_radius:
        raise ValueError("Tooth depth must be positive and less than the tip radius")
    radius, pivot, pitch = e.tip_radius, e.pivot_distance, math.radians(e.pitch)
    lead = e.land / 2 / radius
    root = radius - depth
    sin_half = math.sin(math.radians(e.tooth_angle / 2))
    cos_half = math.cos(math.radians(e.tooth_angle / 2))
    flank = radius * sin_half + e.land / 2 * cos_half  # offset of a tooth's flanks

    # the pallets about the anchor's arbor, with the anchor centred
    faces, noses = [], []
    for nose in e.pallets(length):
        faces.append(_faces([(x, y - pivot) for x, y in nose]))
        noses.append((nose[0][0], nose[0][1] - pivot))
    aims = (math.radians(90 + e.half_span), math.radians(90 - e.half_span))
    window = 0.75 * pitch  # no tip further than this from a pallet can be inside it
    tooth0 = aims[0] + lead  # centre line of a tooth at progress zero

    # the drive, sampled along the wheel's turn
    cells = math.ceil((drive.turn + 2 * e.pitch) / _GRID) + 1
    at = [(i + 0.5) * _GRID for i in range(cells)]
    torques = [drive.torque(a) for a in at]
    inertias = [drive.inertia(a) for a in at]
    holds = [abs(drive.loss(a) * t) + drive.drag for a, t in zip(at, torques)]
    leans = [math.radians(drive.lean(a)) for a in at]
    if min(inertias) <= 0 or pendulum.inertia <= 0:
        raise ValueError("Inertia must be positive")

    # damping for the asked restitution, from the mass that meets at a pallet
    ratio = -math.log(restitution) / math.hypot(math.pi, math.log(restitution))
    meeting = 1 / (radius**2 / inertias[0] + e.lever**2 / pendulum.inertia)
    damping = 2 * ratio * math.sqrt(stiffness * meeting * 1e-3)
    gravity = pendulum.mass * GRAVITY * pendulum.arm * 1e-3
    stop = None if pendulum.stop is None else math.radians(pendulum.stop)
    stop_spring = stiffness * pivot**2  # the stop is met at the wheel's distance
    stop_damping = 2 * ratio * math.sqrt(stop_spring * pendulum.inertia * 1e-3)

    start = math.radians(progress)
    ph, w = start, math.radians(speed)  # the wheel: progress and its rate
    th, om = math.radians(angle), 0.0  # the anchor
    time, count, quiet = 0.0, 0, 0
    every = max(1, round(sample / step))
    times, turned, angles, beats = [], [], [], []
    touching, last, finished = [False, False], -1, None
    deepest = 0.0
    cos, sin, tanh = math.cos, math.sin, math.tanh

    while time < limit:
        if count % every == 0:
            times.append(time)
            turned.append(math.degrees(ph - start))
            angles.append(math.degrees(th))
        c, s = cos(th), sin(th)
        base = tooth0 - ph
        on_wheel = on_anchor = 0.0  # moments from the contacts
        for side in (0, 1):
            # the corners of the lands near this pallet, tried against its faces
            aim = aims[side]
            nearest = round((aim - base) / pitch)
            met = False
            for tooth in (nearest - 1, nearest, nearest + 1):
                for psi in (base + tooth * pitch - lead, base + tooth * pitch + lead):
                    if abs(psi - aim) > window:
                        continue
                    tx, ty = radius * cos(psi), radius * sin(psi)
                    rx, ry = tx, ty - pivot
                    lx, ly = c * rx + s * ry, c * ry - s * rx  # in the anchor's frame
                    inside = math.inf
                    for nx, ny, offset in faces[side]:
                        reach = offset - nx * lx - ny * ly
                        if reach <= 0:
                            break
                        if reach < inside:
                            inside, bx, by = reach, nx, ny
                    else:
                        wx, wy = c * bx - s * by, s * bx + c * by  # the face's normal
                        vx, vy = w * ty + om * ry, -w * tx - om * rx  # tooth past pallet
                        push = stiffness * inside - damping * (vx * wx + vy * wy)
                        if push > 0:
                            met = True
                            rub = -friction * push * tanh((vy * wx - vx * wy) / _SLIDE)
                            fx, fy = push * wx - rub * wy, push * wy + rub * wx  # on the tooth
                            on_wheel -= tx * fy - ty * fx
                            on_anchor -= rx * fy - ry * fx
            if met and not touching[side] and last != side:
                beats.append((time, side))
                last = side
            touching[side] = met

            # the nose of this pallet, tried against the tooth beside it
            qx, qy = noses[side]
            rx, ry = c * qx - s * qy, s * qx + c * qy
            x, y = rx, ry + pivot
            far = math.hypot(x, y)
            if far < radius:
                if far < root:
                    raise ValueError("A pallet reaches the wheel's root: give the anchor a stop")
                around = math.atan2(y, x)
                off = (around - base) % pitch
                if off > pitch / 2:
                    off -= pitch
                u, v = far * cos(off), far * sin(off)  # along and across the tooth
                land = radius - u
                left = flank - u * sin_half - v * cos_half
                right = flank - u * sin_half + v * cos_half
                inside = min(land, left, right)
                if inside > 0:
                    if inside == land:
                        nu, nv = 1.0, 0.0
                    else:
                        nu, nv = sin_half, cos_half if inside == left else -cos_half
                    ux, uy = cos(around - off), sin(around - off)
                    wx, wy = nu * ux - nv * uy, nu * uy + nv * ux
                    vx, vy = -om * ry - w * y, om * rx + w * x  # nose past tooth
                    push = stiffness * inside - damping * (vx * wx + vy * wy)
                    if push > 0:
                        if finished is None:
                            deepest = max(deepest, land)
                        rub = -friction * push * tanh((vy * wx - vx * wy) / _SLIDE)
                        fx, fy = push * wx - rub * wy, push * wy + rub * wx  # on the nose
                        on_wheel += x * fy - y * fx
                        on_anchor += rx * fy - ry * fx

        if stop is not None and abs(th) > stop:
            way = 1.0 if th > 0 else -1.0
            push = stop_spring * (abs(th) - stop) + stop_damping * om * way
            if push > 0:
                on_anchor -= way * push

        cell = min(max(int(math.degrees(ph - start) / _GRID), 0), cells - 1)
        if finished is None and ph - start >= math.radians(drive.turn):
            finished = time
        # each arbor: held by its friction if it is still and the friction is enough
        moment, hold = torques[cell] + on_wheel, holds[cell]
        if abs(w) >= _STILL:
            moment -= math.copysign(hold, w)
        elif abs(moment) > hold:
            moment -= math.copysign(hold, moment)
        else:
            moment, w = 0.0, 0.0
        after = w + moment * 1e3 / inertias[cell] * step
        w = 0.0 if after * w < 0 else after

        moment = on_anchor - gravity * sin(th - leans[cell])
        if abs(om) >= _STILL:
            moment -= math.copysign(pendulum.drag, om)
        elif abs(moment) > pendulum.drag:
            moment -= math.copysign(pendulum.drag, moment)
        else:
            moment, om = 0.0, 0.0
        after = om + moment * 1e3 / pendulum.inertia * step
        om = 0.0 if after * om < 0 else after

        ph += w * step
        th += om * step
        time += step
        count += 1
        quiet = quiet + 1 if abs(w) < _STILL and abs(om) < _STILL else 0
        if quiet * step >= _QUIET:
            break

    if len(times) < 2:  # `at` needs two samples
        times.append(time)
        turned.append(math.degrees(ph - start))
        angles.append(math.degrees(th))
    return Run(tuple(times), tuple(turned), tuple(angles), tuple(beats), finished, deepest)
