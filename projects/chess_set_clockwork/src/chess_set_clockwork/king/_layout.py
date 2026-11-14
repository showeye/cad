"""Every level, centre and angle of the king derived from its parameters, and its motion.

Side view: X to the right, Z up, seen from the front (-Y); the board is Z = 0 and the three
arbors stand on the centre line. Angles are counter-clockwise in that view. "Rest" is the
king standing on the board: plunger pushed home, pawl under the lobe it has just pushed.

The train turns one way only. Seen from the front the star and the great wheel turn
counter-clockwise, the pinion and the escape wheel clockwise.

The pawl and the star are worked out here in the plane, in millimetres from the star's
centre: the star is a boss with round lobes on stalks, the pawl an outline that turns about
its knuckle, and `Ratchet` finds where the pawl rests against the star.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from cadkit.features.escapement import RecoilEscapement
from cadkit.features.gears import centre_distance, meshing_angle, pitch_radius

Point = tuple[float, float]
TOUCH = 1e-3  # outlines closer than this are taken to touch, not to overlap
STAND_OFF = 0.1  # a pawl that leans on the star is drawn this many degrees short of it


def _unit(angle: float) -> Point:
    return math.cos(math.radians(angle)), math.sin(math.radians(angle))


def _arc(centre: Point, radius: float, start: float, end: float, step: float = 6.0):
    """Points on an arc from `start` to `end` degrees, both ends included."""
    count = max(1, math.ceil(abs(end - start) / step))
    angles = [start + (end - start) * i / count for i in range(count + 1)]
    return [(centre[0] + radius * _unit(a)[0], centre[1] + radius * _unit(a)[1]) for a in angles]


def _meets(point: Point, centre: Point, axis: float, offset: float, radius: float) -> float:
    """Direction from `centre` to where an edge of the pawl's arm meets the knuckle's circle.

    The edge runs from `point` to the place `offset` to the left of `centre`, seen along
    `axis`; the direction is that of the point at which it enters the circle.
    """
    side = _unit(axis + 90)
    aim = (centre[0] + offset * side[0], centre[1] + offset * side[1])
    dx, dz = aim[0] - point[0], aim[1] - point[1]
    length = math.hypot(dx, dz)
    dx, dz = dx / length, dz / length
    fx, fz = point[0] - centre[0], point[1] - centre[1]
    along = fx * dx + fz * dz
    reach = -along - math.sqrt(along**2 - (fx**2 + fz**2 - radius**2))
    return math.degrees(math.atan2(fz + reach * dz, fx + reach * dx))


# ---------------------------------------------------------------- pawl and star
@dataclass(frozen=True, eq=False)
class Ratchet:
    """The star and the pawl in the plane; lengths from the star's centre, angles in degrees.

    The pawl's knuckle slides on the line x = `p.pawl_x`. `drop` is how far the plunger, and
    the knuckle with it, hangs below its place at rest. `lean` is the pawl's turn from the
    way it stands at rest, `turn` the star's turn from rest (negative: earlier in a move).
    """

    p: object
    lobe0: Point  # the pushed lobe at rest
    knuckle: Point  # the pawl's pivot at rest
    axis: float  # direction from the knuckle to the pushed lobe at rest
    outline: tuple  # the pawl's outline about its knuckle, as it stands at rest
    cup: Point  # centre of the cup, about the knuckle
    edges: tuple[float, float]  # directions of the arm's right and left edge, up from the neck
    dense: object  # the outline as closely spaced points

    # ------------------------------------------------------------ the pawl pushing
    def knuckle_height(self, turn: float) -> float:
        """Z of the knuckle with the pawl seated under the lobe that is pushed."""
        p = self.p
        x, z = _unit(p.star_end + turn)
        x, z = p.star_circle * x, p.star_circle * z
        return z - math.sqrt(p.pawl_length**2 - (p.pawl_x - x) ** 2)

    def seated(self, turn: float) -> tuple[float, float]:
        """Drop and lean of the pawl seated under its lobe, for a star turned by `turn`."""
        p = self.p
        x, z = _unit(p.star_end + turn)
        x, z = p.star_circle * x, p.star_circle * z
        height = self.knuckle_height(turn)
        lean = math.degrees(math.atan2(z - height, x - p.pawl_x)) - self.axis
        return self.knuckle[1] - height, lean

    def arm(self, turn: float) -> float:
        """Torque on the star per unit of force on the plunger, in mm; friction left out."""
        step = 0.01
        rise = self.knuckle_height(turn + step) - self.knuckle_height(turn - step)
        return rise / math.radians(2 * step)

    def turn_for(self, drop: float) -> float:
        """The star's turn at which a seated pawl has its plunger `drop` below rest."""
        low, high = -360 / self.p.star_teeth, 0.0
        for _ in range(50):
            middle = (low + high) / 2
            low, high = (middle, high) if self.seated(middle)[0] > drop else (low, middle)
        return (low + high) / 2

    # ------------------------------------------------------------ the pawl leaning
    def _placed(self, drop: float, lean: float):
        c, s = _unit(lean)
        x = self.knuckle[0] + c * self.dense[:, 0] - s * self.dense[:, 1]
        z = self.knuckle[1] - drop + s * self.dense[:, 0] + c * self.dense[:, 1]
        return x, z

    def _star(self, x, z, turn: float):
        """Distance from points to the star turned by `turn`; negative inside it."""
        p = self.p
        nearest = np.hypot(x, z) - p.star_boss
        for i in range(p.star_teeth):
            ux, uz = _unit(p.star_end + turn + i * 360 / p.star_teeth)
            along = np.clip(x * ux + z * uz, 0.0, p.star_circle)
            stalk = np.hypot(x - along * ux, z - along * uz) - p.star_stalk / 2
            lobe = np.hypot(x - p.star_circle * ux, z - p.star_circle * uz) - p.lobe
            nearest = np.minimum(nearest, np.minimum(stalk, lobe))
        return nearest

    def gap(self, drop: float, lean: float, turn: float) -> float:
        """Least distance between the pawl and the star; negative if they overlap."""
        return float(self._star(*self._placed(drop, lean), turn).min())

    def escape(self, drop: float, lean: float, turn: float) -> float:
        """How surely the star pushes a touching pawl aside instead of holding it, in degrees.

        The angle between the star's push on the pawl and the line from the point of contact
        to the knuckle. If it is smaller than the angle of friction the pawl is a strut
        between star and plunger and the plunger hangs on it. Negative if the push turns the
        pawl inwards.
        """
        x, z = self._placed(drop, lean)
        at = int(np.argmin(self._star(x, z, turn)))
        x, z, h = x[at], z[at], 1e-4
        nx = float(self._star(np.array([x + h]), np.array([z]), turn)[0])
        nx -= float(self._star(np.array([x - h]), np.array([z]), turn)[0])
        nz = float(self._star(np.array([x]), np.array([z + h]), turn)[0])
        nz -= float(self._star(np.array([x]), np.array([z - h]), turn)[0])
        size = math.hypot(nx, nz)
        nx, nz = nx / size, nz / size
        rx, rz = x - self.knuckle[0], z - (self.knuckle[1] - drop)
        return -math.degrees(math.asin((rx * nz - rz * nx) / math.hypot(rx, rz)))

    def settle(self, drop: float, lean: float, turn: float) -> float:
        """Where a pawl that stood at `lean` comes to rest: its own weight turns it inwards.

        If it stands in the star it is pushed out, clockwise, until it is clear; otherwise it
        falls in, counter-clockwise, until it touches or reaches the stop in its socket.
        """
        p = self.p
        step = 0.25

        def clear(angle):
            return self.gap(drop, angle, turn) >= -TOUCH

        if not clear(lean):
            low = lean
            while not clear(low):
                low -= step
                if low < -p.pawl_out:
                    raise ValueError("Pawl is caught on the star")
            low, high = low + step, low  # high is clear, low is not
            for _ in range(30):
                middle = (low + high) / 2
                low, high = (low, middle) if clear(middle) else (middle, high)
            return high
        low = lean
        while low + step <= p.pawl_in and clear(low + step):
            low += step
        if low + step > p.pawl_in:
            return p.pawl_in
        high = low + step
        for _ in range(30):
            middle = (low + high) / 2
            low, high = (middle, high) if clear(middle) else (low, middle)
        return low

    def lifted(self, drop: float, step: float = 0.05) -> float:
        """Lean of the pawl after the plunger has dropped by `drop` from rest."""
        if drop <= 0:
            return 0.0
        path = self.falling(step)
        index = min(len(path) - 1, max(0, math.ceil(drop / step - 1e-9)))
        return self.settle(drop, path[index][1], 0.0) - STAND_OFF

    @lru_cache(maxsize=4)  # noqa: B019 - one layout per set of parameters, itself cached
    def falling(self, step: float = 0.05) -> tuple:
        """(drop, lean) of the pawl as the plunger drops from rest, the star standing still."""
        lean, path = 0.0, [(0.0, 0.0)]
        for i in range(1, math.ceil(self.p.travel / step - 1e-9) + 1):
            drop = min(i * step, self.p.travel)
            lean = self.settle(drop, lean, 0.0)
            path.append((drop, lean))
        return tuple(path)

    def waiting(self, drop: float) -> float:
        """Lean of a pawl that has clicked under the next lobe and waits `drop` below rest."""
        turn = -360 / self.p.star_teeth
        return self.settle(drop, self.seated(turn)[1], turn) - STAND_OFF


def pawl_outline(p) -> tuple:
    """The pushed lobe at rest, the knuckle at rest, the pawl's axis, outline, cup and edges.

    The outline is drawn about the knuckle with the pawl as it stands at rest: a fence that
    leans on the lobe's side, a cup under the lobe, a finger whose sloping underside rides
    over the next lobe when the plunger drops, and an arm down to the round knuckle.
    """
    lobe0 = (p.star_circle * _unit(p.star_end)[0], p.star_circle * _unit(p.star_end)[1])
    reach = p.pawl_x - lobe0[0]
    if abs(reach) >= p.pawl_length:
        raise ValueError("Pawl is too short to reach the star from its knuckle")
    knuckle = (p.pawl_x, lobe0[1] - math.sqrt(p.pawl_length**2 - reach**2))
    axis = math.degrees(math.atan2(lobe0[1] - knuckle[1], lobe0[0] - knuckle[0]))
    ax = _unit(axis)
    cup = p.lobe + p.cup_play  # radius of the cup; a seated lobe touches its lowest point
    centre = (lobe0[0] + p.cup_play * ax[0], lobe0[1] + p.cup_play * ax[1])
    tip = axis + 180 - p.cup_hold  # where the cup ends, past the point that carries the load

    # the finger's underside: a straight ramp that faces the next lobe and stands clear of it
    below = _unit(p.star_end - 360 / p.star_teeth)
    below = (p.star_circle * below[0], p.star_circle * below[1])
    normal, along = _unit(p.cam), _unit(p.cam - 90)
    foot = (
        below[0] + (p.lobe + p.cam_clear) * normal[0],
        below[1] + (p.lobe + p.cam_clear) * normal[1],
    )
    end = (centre[0] + cup * _unit(tip)[0], centre[1] + cup * _unit(tip)[1])
    out = _unit(tip)
    # from the end of the cup straight out to the ramp
    depth = ((foot[0] - end[0]) * normal[0] + (foot[1] - end[1]) * normal[1]) / (
        out[0] * normal[0] + out[1] * normal[1]
    )
    if depth < 0.25:
        raise ValueError("Finger is too thin at its tip: lower star_end or the cam's clearance")
    corner = (end[0] + depth * out[0], end[1] + depth * out[1])
    heel = (foot[0] + p.cam_run * along[0], foot[1] + p.cam_run * along[1])
    fence = (centre[0] + cup + p.fence_wall, centre[1] + p.fence)

    # The arm narrows to a neck at the knuckle, so that the socket can hold the knuckle.
    left = _meets(heel, knuckle, axis, p.pawl_neck / 2, p.knuckle)
    right = _meets(fence, knuckle, axis, -p.pawl_neck / 2, p.knuckle) + 360
    points = [(centre[0] + cup, centre[1] + p.fence)]
    points += _arc(centre, cup, 0.0, tip - 360 if tip > 0 else tip, step=2.0)
    points += [corner, heel]
    points += _arc(knuckle, p.knuckle, left, right)
    points += [fence]
    about = [(x - knuckle[0], z - knuckle[1]) for x, z in points]
    # the way the arm's two edges run up from the neck: the socket's lips are cut to them
    side = _unit(axis + 90)
    half = p.pawl_neck / 2
    edges = (
        math.degrees(
            math.atan2(
                fence[1] - knuckle[1] + half * side[1], fence[0] - knuckle[0] + half * side[0]
            )
        ),
        math.degrees(
            math.atan2(heel[1] - knuckle[1] - half * side[1], heel[0] - knuckle[0] - half * side[0])
        ),
    )
    return lobe0, knuckle, axis, about, (centre[0] - knuckle[0], centre[1] - knuckle[1]), edges


def _dense(points: list[Point], spacing: float = 0.03) -> np.ndarray:
    found = []
    for a, b in zip(points, points[1:] + points[:1]):
        count = max(1, math.ceil(math.dist(a, b) / spacing))
        found += [
            (a[0] + (b[0] - a[0]) * i / count, a[1] + (b[1] - a[1]) * i / count)
            for i in range(count)
        ]
    return np.array(found)


# ---------------------------------------------------------------- layout
@dataclass(frozen=True)
class Layout:
    """Derived geometry of one king; lengths in mm, angles in degrees."""

    # across the piece (Y); the front plate is at -Y
    inner: float  # |Y| of the plates' inner faces
    outer: float  # |Y| of the plates' outer faces
    play: float  # between a moving part and the bearing ring beside it
    front: tuple[float, float]  # escape wheel, pallets, star, pawl, the plunger's stem
    middle: tuple[float, float]  # great wheel and pinion
    rear: tuple[float, float]  # pendulum
    wheels: tuple[float, float]  # both wheel parts, front face to rear face
    # arbors
    great: Point  # great wheel and star
    escape: Point  # escape wheel and pinion
    pivot: Point  # anchor and pendulum
    # the train
    ratio: float  # turns of the escape wheel for one of the great wheel
    great_tip: float
    great_root: float
    pinion_tip: float
    pinion_angle: float  # of the pinion's gear at rest
    # the escapement
    escapement: RecoilEscapement
    progress: float  # of the escape wheel at rest, in the escapement's own measure
    free: float  # how far the escape wheel can turn on at rest before a pallet stops it
    hub_front: float  # radius of the anchor's hub where the escape wheel passes under it
    yoke: tuple[float, float]  # the anchor's arch about the escape wheel's centre: radii
    yoke_span: tuple[float, float]  # and the directions of its two ends
    # the pendulum
    bob: Point
    ring_hole: float  # radius of the hole that goes round the escape wheel's boss
    ring: float  # outer radius of that ring
    # ratchet and plunger
    ratchet: Ratchet
    knuckle: Point  # the pawl's pivot at rest
    stroke: float  # the king sinks this far with the pawl pushing
    click: float  # drop of the plunger at which the pawl has gone under the next lobe
    socket: float  # outer radius of the socket round the knuckle
    stem: tuple[float, float]  # X of the stem's two flanks
    rib: tuple[float, float]  # X of the face that guides the stem, and Z of the rib's top
    bar_half: float  # half the bar's length, without its ears
    bar_wide: float  # half the bar's width across the piece
    ledge: float  # Z of the step in the base on which the ears hang
    # frame
    column: tuple[float, float]  # X of a column's inner and outer edge
    spring: float  # Z from which the arch rises: the escape wheel's arbor
    apex: float  # Z of the arch's point, outside
    posts: tuple[Point, Point, Point]  # the three pillars
    feet: tuple[float, float]


@dataclass(frozen=True)
class Pose:
    """Where the moving parts are; turns are from rest."""

    drop: float  # of the plunger below the base
    turn: float  # of the great wheel and the star; negative is earlier in the move
    escape: float  # of the escape wheel and the pinion
    pawl: float  # lean of the pawl from the way it stands at rest
    anchor: float  # of the anchor from its centre; a pendulum that hangs plumb holds `beat`


def escapement(p) -> RecoilEscapement:
    return RecoilEscapement(
        teeth=p.escape_teeth,
        tip_radius=p.escape_tip,
        span=p.span,
        release=p.release,
        drop=p.escape_drop,
        tooth_angle=p.tooth_angle,
        land=p.escape_land,
        back=p.pallet_back,
    )


@lru_cache(maxsize=32)
def layout(p) -> Layout:
    inner = p.gap / 2
    layers = p.front_layer + p.middle_layer + p.rear_layer + 2 * p.layer_gap
    play = (p.gap - 2 * p.shoulder - layers) / 2
    y0 = -inner + p.shoulder + play
    front = (y0, y0 + p.front_layer)
    middle = (front[1] + p.layer_gap, front[1] + p.layer_gap + p.middle_layer)
    rear = (middle[1] + p.layer_gap, middle[1] + p.layer_gap + p.rear_layer)

    great_radius = pitch_radius(p.module, p.wheel_teeth)
    pinion_radius = pitch_radius(p.module, p.pinion_teeth)
    great_tip = great_radius + p.module * (1 - p.shift)
    great = (0.0, p.base_height + p.wheel_clear + great_tip)
    escape = (0.0, great[1] + centre_distance(p.module, p.wheel_teeth, p.pinion_teeth))
    e = escapement(p)
    pivot = (0.0, escape[1] + e.pivot_distance)

    # At rest the pendulum hangs plumb, which holds the anchor at `beat`, and the wheel has
    # been pushed on until a pallet stops it; it is drawn a little short of that, so that the
    # solids do not touch.
    stopped = e.settle(-math.degrees(e.impulse / e.tip_radius), p.beat, p.pallet_length)
    progress = stopped - p.rest_gap

    lobe0, knuckle, axis, outline, cup, edges = pawl_outline(p)
    ratchet = Ratchet(p, lobe0, knuckle, axis, tuple(outline), cup, edges, _dense(outline))
    stroke = ratchet.seated(-360 / p.star_teeth)[0]
    below = _unit(p.star_end - 360 / p.star_teeth)
    click = p.travel + 1.0  # stays beyond the travel if the pawl never gets under the lobe
    for drop, lean in ratchet.falling():
        cup = _unit(axis + lean)
        cup = (knuckle[0] + p.pawl_length * cup[0], knuckle[1] - drop + p.pawl_length * cup[1])
        if (
            abs(cup[0] - p.star_circle * below[0]) < 0.3
            and cup[1] <= p.star_circle * below[1] + 0.02
        ):
            click = drop
            break

    socket = p.knuckle + p.knuckle_play + p.socket_wall
    half = p.column / 2
    rib = p.pawl_x + socket + p.guide
    yoke_in = p.escape_tip + p.yoke_clear
    return Layout(
        inner=inner,
        outer=inner + p.plate,
        play=play,
        front=front,
        middle=middle,
        rear=rear,
        wheels=(front[0], middle[1]),
        great=great,
        escape=escape,
        pivot=pivot,
        ratio=p.wheel_teeth / p.pinion_teeth,
        great_tip=great_tip,
        great_root=great_radius - p.module * (1.25 + p.shift),
        pinion_tip=pinion_radius + p.module * (1 + p.shift),
        pinion_angle=meshing_angle(p.wheel_teeth, p.pinion_teeth, p.great_angle, 90.0),
        escapement=e,
        progress=progress,
        free=p.rest_gap,
        hub_front=e.pivot_distance - p.escape_tip - p.hub_clear,
        yoke=(yoke_in, yoke_in + p.yoke),
        yoke_span=(90 - e.half_span - p.yoke_past[0], 90 + e.half_span + p.yoke_past[1]),
        bob=(0.0, pivot[1] - p.bob_arm),
        ring_hole=p.boss_tall + 2 * e.pivot_distance * math.sin(math.radians(p.swing_stop / 2)),
        ring=p.boss_tall
        + 2 * e.pivot_distance * math.sin(math.radians(p.swing_stop / 2))
        + p.ring_wall,
        ratchet=ratchet,
        knuckle=(knuckle[0] + great[0], knuckle[1] + great[1]),
        stroke=stroke,
        click=click,
        socket=socket,
        stem=(p.pawl_x - socket, p.pawl_x + socket),
        # the rib ends under the cut corner of the plinth
        rib=(rib, p.base_height + p.plinth - (p.column_x - half - rib)),
        bar_half=p.bar_length / 2,
        bar_wide=p.bar_width / 2,
        ledge=p.bar_height - p.ear_height - p.travel,
        column=(p.column_x - half, p.column_x + half),
        spring=escape[1],
        apex=escape[1] + math.sqrt((2 * (p.column_x + half)) ** 2 - (p.column_x + half) ** 2),
        posts=((-p.column_x, p.post_z), (p.column_x, p.post_z), (0.0, pivot[1] + p.post_above)),
        feet=(-p.column_x, p.column_x),
    )


# ---------------------------------------------------------------- motion
def level(p, progress: float) -> float:
    """An angle at which the anchor stands clear of an escape wheel at `progress`.

    The pendulum hangs plumb if the wheel lets it, which is the anchor at `beat`; otherwise
    the anchor is turned the shorter way until its pallets are clear, as a tooth would push
    it.
    """
    L = layout(p)
    e = L.escapement
    if e.interference(progress, p.beat, p.pallet_length) <= 0:
        return p.beat
    for i in range(1, 200):
        for way in (-1, 1):
            angle = p.beat + 0.1 * i * way
            if e.interference(progress, angle, p.pallet_length) <= 0:
                return angle + 0.05 * way
    raise ValueError("No angle of the anchor clears the escape wheel")


def sinking(p, lift: float, anchor: float | None = None) -> Pose:
    """The king `lift` above the board on its way down, the pawl under the next lobe.

    Above the stroke the pawl waits below its lobe and nothing has turned yet; within the
    stroke the pawl carries the king and the train has turned as far as the king has sunk.
    """
    L = layout(p)
    drop = min(max(lift, 0.0), p.travel)
    if drop > L.stroke + 1e-9:
        turn, pawl = -360 / p.star_teeth, L.ratchet.waiting(drop)
    else:
        turn = L.ratchet.turn_for(drop)
        pawl = L.ratchet.seated(turn)[1]
    return running(p, turn, drop, pawl, anchor)


def lifting(p, lift: float, anchor: float | None = None) -> Pose:
    """The king `lift` above the board on its way up: the train stands, the pawl clicks."""
    L = layout(p)
    drop = min(max(lift, 0.0), p.travel)
    anchor = p.beat if anchor is None else anchor
    return Pose(drop=drop, turn=0.0, escape=0.0, pawl=L.ratchet.lifted(drop), anchor=anchor)


def running(p, turn: float, drop: float, pawl: float, anchor: float | None = None) -> Pose:
    """A pose of the train `turn` from rest; the anchor stands clear unless it is given."""
    L = layout(p)
    escape = -turn * L.ratio
    if anchor is None:
        anchor = level(p, L.progress - escape)
    return Pose(drop=drop, turn=turn, escape=escape, pawl=pawl, anchor=anchor)
