"""Whether the king ticks: what its weight is worth at the escape wheel, and a move run through.

While the king sinks, its body rests on the pawl through one lobe of the star. That lobe is
in the front layer and to the right of the centre line, and the pawl leans, so the body does
not come straight down: it leans on the plunger until the guide stops it, and rubs there all
the way. `carried` works that out as statics, with dry friction at each place of contact:

- in the plane of the wheels the body turns until the rib of the front plate lies against
  the top of the plunger's stem and the left end of the slot against the bar;
- across the piece it tips back until the front plate lies against the stem's front face and
  the rear wall of the slot against the bar.

What is left of the weight turns the star. The pawl's two joints, both arbors and the gears
each take their share, and what arrives at the escape wheel goes into
`cadkit.features.escapement_run` together with the inertias and the pendulum, all taken from
the solids. The king's lean in the plane of the wheels moves the pendulum off the anchor's
centre for as long as it sinks; that is in the run as well.

Assumed, not measured: the friction values, that friction takes the same share of the torque
when the wheel is pushed back, that the pawl's push acts in the middle of its layer, and
that the king lands on the pawl without bouncing. Left out: the pallets' push on the arbors.

Lengths in mm, angles in degrees, masses in g, forces in mN, torques in mN mm, inertia in
g mm2. `turn` is the star's turn from rest, -60 at the start of a move; `turned` is the escape
wheel's turn from the start of a move.
"""

import math
from dataclasses import dataclass

import numpy as np
from build123d import CenterOf
from cadkit.features.escapement_run import GRAVITY, Drive, Pendulum, Run, run
from cadkit.features.gears import PRESSURE_ANGLE, pitch_radius

from chess_set_clockwork._shared import grams
from chess_set_clockwork.king._layout import _unit, layout

_STEPS = 48  # the drive is worked out at this many places along a move


@dataclass(frozen=True)
class Masses:
    """What a run needs of the solids."""

    body: float  # all that rests on the pawl while the king sinks
    centre: tuple[float, float]  # X and Y of the body's centre of mass
    great: tuple[float, float]  # mass and inertia of the great wheel with its arbor
    escape: tuple[float, float]  # of the escape wheel with its arbor
    pendulum: tuple[float, float]  # of the anchor with its bob and its arbor
    arm: float  # the pendulum's centre of mass below its arbor
    hang: float  # the anchor's angle at which the pendulum hangs at rest


def masses(p, solids: dict, kinds: dict) -> Masses:
    """Masses, centres and inertias about the arbors, from the solids of a standing king.

    `kinds` names what each moving part does ("great", "escape", "anchor", "plunger",
    "pawl"); every part that is not of the plunger or the pawl rests on the pawl.
    """
    L = layout(p)

    def about(kind, centre):
        """Mass, centre of mass and inertia about the arbor through `centre` (x, z)."""
        mass, at, inertia = 0.0, np.zeros(3), 0.0
        for name, shape in solids.items():
            if kind(kinds.get(name)):
                m, c = grams(name, shape), shape.center(CenterOf.MASS)
                own = shape.matrix_of_inertia[1][1] * m / shape.volume
                inertia += own + m * ((c.X - centre[0]) ** 2 + (c.Z - centre[1]) ** 2)
                at += m * np.array([c.X, c.Y, c.Z])
                mass += m
        return mass, at / mass, inertia

    body, centre, _ = about(lambda kind: kind not in ("plunger", "pawl"), (0.0, 0.0))
    great = about(lambda kind: kind == "great", L.great)
    escape = about(lambda kind: kind == "escape", L.escape)
    pendulum, at, swing = about(lambda kind: kind == "anchor", L.pivot)
    below = L.pivot[1] - at[2]
    return Masses(
        body=body,
        centre=(float(centre[0]), float(centre[1])),
        great=(great[0], great[2]),
        escape=(escape[0], escape[2]),
        pendulum=(pendulum, swing),
        arm=math.hypot(below, at[0] - L.pivot[0]),
        hang=math.degrees(math.atan2(L.pivot[0] - at[0], below)),
    )


# ---------------------------------------------------------------- the guide
def carried(p, m: Masses, turn: float, friction: float) -> tuple[float, float, float]:
    """What the pawl carries, and how the king leans, with the star turned by `turn`.

    Returns the push on the lobe measured straight up, the king's lean to the left and its
    lean to the back in degrees. The body is in balance under its weight, the pawl's push
    along the pawl, and four places of contact with the plunger, each with friction that
    holds the body up: the rib on the stem (R), the slot's left end on the bar (S), and the
    front plate on the stem with the slot's rear wall on the bar (a couple, C).
    """
    L = layout(p)
    drop, _ = L.ratchet.seated(turn)
    lobe = _unit(p.star_end + turn)
    lobe = (L.great[0] + p.star_circle * lobe[0], L.great[1] + p.star_circle * lobe[1])
    knuckle = (L.knuckle[0], L.knuckle[1] - drop)
    slope = (knuckle[0] - lobe[0]) / (lobe[1] - knuckle[1])  # sideways push per push upwards
    weight = m.body * GRAVITY * 1e-3
    cx, cy = m.centre
    layer = (L.front[0] + L.front[1]) / 2  # Y of the pawl's push and of the rib's
    top = min(L.knuckle[1] + L.socket - drop, L.rib[1])  # the stem's top corner on the rib
    wall = -(L.bar_half + p.slide)  # X of the slot's left end, met at the base's underside
    face = (p.plinth_x + L.stem[1]) / 2  # X at which the front plate meets the stem
    across = 2 * cy + L.inner - (L.bar_wide + p.slide)  # Y levers of the couple's friction
    mu = friction
    # sideways, upwards, turning in the plane of the wheels, tipping across the piece
    balance = [
        [-slope, 1.0, -1.0, 0.0],
        [1.0, mu, mu, 2 * mu],
        [lobe[0] + slope * lobe[1], mu * L.rib[0] - top, mu * wall, mu * (face + cx)],
        [cy - layer, mu * (cy - layer), 0.0, mu * across - top],
    ]
    push, rib, slot, couple = np.linalg.solve(balance, [0.0, weight, cx * weight, 0.0])
    if min(push, rib, slot, couple) < -1e-9:
        raise ValueError("The king does not lean on its guide the way the model takes it to")
    side = math.degrees((p.guide + p.slide) / top)
    back = math.degrees((p.shoulder + L.play + p.slide) / top)
    return float(push), side, back


# ---------------------------------------------------------------- the train
def at_escape(p, m: Masses, turn: float, friction: float, pin_friction: float):
    """Torque at the escape wheel with friction left out, and what friction leaves of it.

    `friction` is that of print on print: guide, pawl, gears. `pin_friction` is that of a
    steel pin in its printed hole.
    """
    L = layout(p)
    R = L.ratchet
    arm = R.arm(turn)
    ideal = m.body * GRAVITY * 1e-3 * arm / L.ratio
    push, _, _ = carried(p, m, turn, friction)
    drop, _ = R.seated(turn)
    lobe = _unit(p.star_end + turn)
    away = (p.star_circle * lobe[0] - p.pawl_x, p.star_circle * lobe[1] - R.knuckle[1] + drop)
    ux, uz = away[0] / math.hypot(*away), away[1] / math.hypot(*away)
    strut = push / uz  # along the pawl
    # the lobe turns in the cup and the knuckle in its socket
    step = 0.5
    rate = (R.seated(turn + step)[1] - R.seated(turn - step)[1]) / (2 * step)
    star = push * arm - friction * strut * (p.lobe * abs(1 - rate) + p.knuckle * abs(rate))
    # the great wheel's arbor carries the pawl's push and the pinion's
    pin = p.pin / 2
    spread = math.tan(math.radians(PRESSURE_ANGLE))
    reach = pitch_radius(p.module, p.wheel_teeth)
    left = star
    for _ in range(3):
        mesh = max(left, 0.0) / reach
        load = math.hypot(strut * ux + mesh, strut * uz - mesh * spread)
        left = star - pin_friction * pin * load
    # sliding between the teeth, by the usual estimate for spur gears, and the pinion's arbor
    sliding = friction * math.pi * (1 / p.wheel_teeth + 1 / p.pinion_teeth) / 2
    mesh = max(left, 0.0) / reach
    real = left / L.ratio * (1 - sliding) - pin_friction * pin * mesh * math.hypot(1.0, spread)
    return ideal, max(real, 0.0)


def drive(p, m: Masses, friction: float, pin_friction: float) -> Drive:
    """The king's weight as a drive of the escape wheel through one move."""
    L = layout(p)
    lobe = 360 / p.star_teeth
    turn = lobe * L.ratio  # of the escape wheel in one move
    grid = [turn * i / _STEPS for i in range(_STEPS + 1)]
    star = [-lobe + turned / L.ratio for turned in grid]
    found = [at_escape(p, m, t, friction, pin_friction) for t in star]
    ideal = [f[0] for f in found]
    loss = [1 - f[1] / f[0] for f in found]
    lean = [m.hang - carried(p, m, t, friction)[1] for t in star]
    wheels = m.escape[1] + m.great[1] / L.ratio**2
    sinking = [wheels + m.body * (L.ratchet.arm(t) / L.ratio) ** 2 for t in star]
    pin = p.pin / 2

    def along(values, after):
        # on the board the king no longer rests on the pawl
        return lambda turned: float(np.interp(turned, grid, values)) if turned < turn else after

    return Drive(
        turn=turn,
        torque=along(ideal, 0.0),
        inertia=along(sinking, wheels),
        loss=along(loss, 0.0),
        lean=along(lean, m.hang),
        drag=pin_friction * pin * (m.escape[0] + m.great[0] / L.ratio) * GRAVITY * 1e-3,
    )


def landing(p, m: Masses, fall: float) -> float:
    """Speed of the escape wheel in degrees a second after the king fell `fall` onto the pawl.

    The body lands on the pawl without bouncing and shares its momentum with the wheels.
    """
    L = layout(p)
    if not 0 <= fall <= p.travel - L.stroke + 1e-9:
        raise ValueError("The king cannot fall further than the plunger travels above the stroke")
    lever = L.ratchet.arm(-360 / p.star_teeth) / L.ratio  # mm the body sinks per radian
    wheels = m.escape[1] + m.great[1] / L.ratio**2
    speed = math.sqrt(2 * GRAVITY * fall)
    return math.degrees(m.body * speed * lever / (wheels + m.body * lever**2))


def tick(
    p,
    m: Masses,
    *,
    friction: float = 0.3,
    pin_friction: float = 0.3,
    fall: float = 0.0,
    angle: float | None = None,
    limit: float = 8.0,
    sample: float = 0.01,
) -> Run:
    """One move from the moment the king rests on its pawl until nothing moves any more.

    `fall` is how far the king dropped onto the pawl: nothing if a hand lowered it there, up
    to the plunger's travel above the stroke if it was let go as the plunger touched. `angle`
    is where the anchor stands at that moment, let go from rest: where the pendulum hangs in
    a standing king if it is not given, anywhere up to its stops if the hand left it swinging.
    If a pallet then stands in a tooth, the wheel starts where that pallet has pushed it back
    to, as a pendulum swinging in the hand does with a train that nothing drives.
    """
    L = layout(p)
    e = L.escapement
    pendulum = Pendulum(
        inertia=m.pendulum[1],
        mass=m.pendulum[0],
        arm=m.arm,
        drag=pin_friction * p.anchor_pin / 2 * m.pendulum[0] * GRAVITY * 1e-3,
        stop=p.swing_stop,
    )
    weight = drive(p, m, friction, pin_friction)
    angle = m.hang if angle is None else angle
    progress = L.progress - weight.turn
    if e.interference(progress, angle, p.pallet_length) > 0:
        progress = e.settle(progress, angle, p.pallet_length) - p.rest_gap
    return run(
        e,
        weight,
        pendulum,
        depth=p.escape_depth,
        length=p.pallet_length,
        progress=progress,
        angle=angle,
        speed=landing(p, m, fall),
        friction=friction,
        limit=limit,
        sample=sample,
    )
