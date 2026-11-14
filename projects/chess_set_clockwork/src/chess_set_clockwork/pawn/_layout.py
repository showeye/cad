"""Every level, centre and angle of the pawn derived from its parameters, and its motion.

Side view: X to the right, Z up, seen from -Y; the board is Z = 0 and the arbors lie along Y.
Angles are counter-clockwise in that view, which is also the way the wheel turns. "Rest" is
the pawn standing on the board: plunger pushed home, the pawl under the tooth it has just
pushed, the click lying on the back of a tooth.

The ratchet itself is `cadkit.features.ratchet`. This module places it, sizes the click and
the pawl to it, and follows one move in small steps of the plunger: lifted, the wheel falls
back onto the click and the pawl rides down over the next tooth and falls under it; set down,
the pawl pushes that tooth up and the click rides over one tooth.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from cadkit.features.ratchet import Pawl, Ratchet

Point = tuple[float, float]
STEP = 0.02  # mm of the plunger's travel between two places at which a move is worked out


def polar(radius: float, angle: float, centre: Point = (0.0, 0.0)) -> Point:
    t = math.radians(angle)
    return centre[0] + radius * math.cos(t), centre[1] + radius * math.sin(t)


def direction(a: Point, b: Point) -> float:
    """Direction from `a` to `b` in degrees."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


@dataclass(frozen=True)
class Layout:
    """Derived geometry of one pawn; lengths in mm, angles in degrees."""

    # across the piece (Y)
    inner: float  # |Y| of the plates' inner faces
    outer: float  # |Y| of the plates' outer faces
    bar_wide: float  # |Y| of the faces of the plunger and the pawl
    wheel_y: tuple[float, float]
    click_y: tuple[float, float]
    # the ratchet
    wheel: Point  # the wheel's arbor
    ratchet: Ratchet
    home: float  # turn of the ratchet's outline at rest
    back: float  # how far the wheel falls back onto the click when the pawn is lifted
    reach: float  # radius at which a nose lies in a tooth's corner
    face: float  # direction of a tooth's face, root to tip, in the outline unturned
    # click
    click: Pawl
    click_pin: Point
    click_seated: float  # direction from the pin to the nose with the nose in a tooth's corner
    click_home: float  # the same at rest, the nose lying on a tooth's back
    click_face: float  # direction of the face the click holds, the click seated
    click_elbow: Point  # where arm and beak meet, the click seated
    # pawl
    pawl: Pawl
    knuckle: Point  # the pawl's pivot at rest
    pawl_home: float  # direction from the knuckle to the nose at rest
    pawl_face: float  # direction of the face the pawl pushes, at rest
    socket: float  # outer radius of the socket round the knuckle
    # plunger and base
    bar_half: float  # half the bar's length, without its ears
    ledge: float  # Z of the step in the base on which the ears hang
    # frame
    feet: tuple[float, float]
    column: tuple[float, float]  # inner and outer X of a column
    spring: float  # Z of the arch's centre
    seat: float  # Z of the flat on which the head sits
    top: float  # Z of the top of the tenon that the head sits over

    def to_wheel(self, point: Point) -> Point:
        """A point of the side view as the ratchet takes it: from the wheel's centre."""
        return point[0] - self.wheel[0], point[1] - self.wheel[1]


def _still(p):
    return p if p.lift == 0 else p.model_copy(update={"lift": 0.0})


def layout(p) -> Layout:
    return _layout(_still(p))


@lru_cache(maxsize=16)
def _layout(p) -> Layout:
    inner = p.gap / 2
    wheel = (0.0, p.base_height + p.wheel_clear + p.wheel_tip)
    ratchet = Ratchet(p.teeth, p.wheel_tip, p.tooth, p.rake, p.land)
    seat = ratchet.seat(p.nose)
    reach, at = math.hypot(*seat), math.degrees(math.atan2(seat[1], seat[0]))
    foot, top = ratchet.outline()[:2]
    face = direction(foot, top)

    # The pawl pushes its tooth from below the arbor's level to above it by the same amount,
    # and ends `fall_back` further than where the click holds the wheel.
    back = math.degrees(p.fall_back / reach)
    pushed = (ratchet.pitch + back) / 2  # where the pushed tooth's corner stands at rest
    home = pushed - at
    nose = polar(reach, pushed)
    across = p.pawl_x - nose[0]
    if abs(across) >= p.pawl_length:
        raise ValueError("pawl is too short to reach the wheel from its knuckle")
    low = nose[1] - math.sqrt(p.pawl_length**2 - across**2)
    pawl = Pawl(p.pawl_length, p.nose)

    # The click's nose lies `click_teeth` teeth further round, in the corner of its tooth
    # when the wheel has fallen back.
    hold = home - back
    turned = hold + p.click_teeth * ratchet.pitch
    click_nose = polar(reach, at + turned)
    pin = (0.0, p.click_rise)
    click = Pawl(math.dist(pin, click_nose), p.nose)
    click_seated = direction(pin, click_nose)
    click_home = ratchet.falls(click, pin, home, click_seated - 15, click_seated + p.click_in)
    click_face = face + turned
    # the beak leaves the nose just under the face and ends outside the tips, at the elbow
    axis = polar(1.0, click_face - p.beak_off - p.beak / 2)
    out = p.wheel_tip + p.arm_clear + p.click_arm / 2
    along = click_nose[0] * axis[0] + click_nose[1] * axis[1]
    length = -along + math.sqrt(along**2 + out**2 - reach**2)
    elbow = (click_nose[0] + length * axis[0], click_nose[1] + length * axis[1])

    crown = wheel[1] + p.click_rise
    return Layout(
        inner=inner,
        outer=inner + p.plate,
        bar_wide=p.bar_width / 2,
        wheel_y=(-p.wheel_face / 2, p.wheel_face / 2),
        click_y=(-p.click_face / 2, p.click_face / 2),
        wheel=wheel,
        ratchet=ratchet,
        home=home,
        back=back,
        reach=reach,
        face=face,
        click=click,
        click_pin=(0.0, crown),
        click_seated=click_seated,
        click_home=click_home,
        click_face=click_face,
        click_elbow=(elbow[0], elbow[1] + wheel[1]),
        pawl=pawl,
        knuckle=(p.pawl_x, wheel[1] + low),
        pawl_home=direction((p.pawl_x, low), nose),
        pawl_face=face + home,
        socket=p.knuckle + p.knuckle_play + p.socket_wall,
        bar_half=p.bar_length / 2,
        ledge=p.bar_height - p.ear_height - p.travel,
        feet=(-p.foot_x, p.foot_x),
        column=(p.column_x - p.column / 2, p.column_x + p.column / 2),
        spring=crown - p.column_x,
        seat=crown + p.crown,
        top=crown + p.crown + p.head_rise,
    )


# ---------------------------------------------------------------- one move
@dataclass(frozen=True, eq=False)
class Move:
    """One move followed in steps of the plunger; turns are counted from rest, in degrees.

    `up` holds the wheel's, the pawl's and the click's turn at each of `drops` while the pawn
    is lifted, `down` the same while it is set down again. The wheel's turn is counted from
    where it stood before the move, so it ends one tooth further.
    """

    drops: np.ndarray  # how far the plunger hangs below its place at rest
    up: np.ndarray
    down: np.ndarray
    fallen: float  # drop at which the wheel has fallen back onto the click
    under: float | None  # drop at which the pawl falls under the next tooth, if it gets there
    meets: float | None  # drop at which the pawl, coming up, meets that tooth's face
    turned: float  # the wheel's turn when the pawn stands again
    swing: float  # the furthest the pawl is pushed out from where it stands at rest
    lift: float  # the furthest the click is lifted from where it lies at rest


def move(p) -> Move:
    return _move(_still(p))


@lru_cache(maxsize=16)
def _move(p) -> Move:
    L = layout(p)
    W, pitch = L.ratchet, L.ratchet.pitch
    pin = L.to_wheel(L.click_pin)
    x, z = L.to_wheel(L.knuckle)
    drops = np.linspace(0.0, p.travel, round(p.travel / STEP) + 1)

    # The wheel's turn with the pawl in the corner of the tooth it pushed, followed from rest
    # as the plunger drops; None once the pawl no longer reaches that corner.
    seated, last = [], L.home
    for drop in drops:
        try:
            turn, way = W.seated(L.pawl, (x, z - drop))
        except ValueError:
            seated.append(None)
            continue
        last += (turn - last + pitch / 2) % pitch - pitch / 2
        seated.append((last, way))

    hold = L.home - L.back
    inwards = L.pawl_home + p.pawl_in
    low = L.click_seated + p.click_in
    pawl, click = L.pawl_home, L.click_home
    fallen = under = meets = None
    rode = False
    up = []
    for index, drop in enumerate(drops):
        at = seated[index]
        if fallen is None and at is not None and at[0] > hold:
            wheel, pawl = at  # the pawl goes down and the wheel follows it back
            click = W.falls(L.click, pin, wheel, click, low)
        else:
            if fallen is None:  # the click has caught its tooth: the wheel stands
                before = seated[index - 1][0]
                share = (before - hold) / (before - at[0]) if at else 1.0
                fallen = float(drops[index - 1] + share * (drop - drops[index - 1]))
                click = L.click_seated
            wheel = hold
            pawl = W.falls(L.pawl, (x, z - drop), hold, pawl, inwards)
            radius = math.hypot(*L.pawl.tip((x, z - drop), pawl))
            rode = rode or radius >= p.wheel_tip
            if rode and under is None and radius < p.wheel_tip - 0.3 * p.tooth:
                under = float(drop)
        up.append((wheel - L.home, pawl - L.pawl_home, click - L.click_home))

    down = []
    for index in range(len(drops) - 1, -1, -1):
        drop, at = drops[index], seated[index]
        if under is not None and at is not None and at[0] + pitch >= hold:
            if meets is None:
                meets = float(drop)
            wheel, pawl = at[0] + pitch, at[1]  # the next tooth is pushed as the last one was
            click = W.falls(L.click, pin, wheel, click, low)
        else:
            wheel = hold
            pawl = W.falls(L.pawl, (x, z - drop), hold, pawl, inwards)
        down.append((wheel - L.home, pawl - L.pawl_home, click - L.click_home))
    down.reverse()
    up, down = np.array(up), np.array(down)
    return Move(
        drops=drops,
        up=up,
        down=down,
        fallen=fallen if fallen is not None else float(p.travel),
        under=under,
        meets=meets,
        turned=float(down[0, 0]),
        swing=float(-min(up[:, 1].min(), down[:, 1].min())),
        lift=float(-min(up[:, 2].min(), down[:, 2].min())),
    )


@dataclass(frozen=True)
class Pose:
    """Where the moving parts are; turns are counted from rest, in degrees."""

    drop: float  # of the plunger below the base
    wheel: float
    pawl: float  # about its knuckle
    click: float  # about its pin


def _pose(p, lift: float, rows: np.ndarray) -> Pose:
    made = move(p)
    drop = min(max(lift, 0.0), p.travel)
    wheel, pawl, click = (float(np.interp(drop, made.drops, rows[:, i])) for i in range(3))
    return Pose(drop=drop, wheel=wheel, pawl=pawl, click=click)


def lifting(p, lift: float) -> Pose:
    """The pawn `lift` above the board on its way up: the plunger stays down on the board."""
    return _pose(p, lift, move(p).up)


def lowering(p, lift: float) -> Pose:
    """The pawn `lift` above the board on its way down: the board pushes the plunger home."""
    return _pose(p, lift, move(p).down)
