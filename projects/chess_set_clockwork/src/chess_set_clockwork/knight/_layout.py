"""Every level, centre and angle of the knight derived from its parameters, and its motion.

Side view: X to the right, Z up, seen from -Y; the horse faces -X and the board is Z = 0.
Angles are counter-clockwise in that view. "Rest" is the piece standing on the board: plunger
pushed home, head bowed.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

from cadkit.features.gears import centre_distance, meshing_angle, pitch_radius

Point = tuple[float, float]


@dataclass(frozen=True)
class Layout:
    """Derived geometry of one knight; lengths in mm, angles in degrees."""

    # across the piece (Y)
    inner: float  # |Y| of the plates' inner faces
    outer: float  # |Y| of the plates' outer faces
    half: float  # |Y| of the faces of the moving parts
    wheel_y: tuple[float, float]
    pinion_y: tuple[float, float]
    rack_y: tuple[float, float]
    # the train
    wheel: Point  # arbor of the chest wheel and its pinion
    pivot: Point  # arbor of the head
    towards: float  # direction from the head's arbor to the wheel's
    pinion_radius: float
    wheel_tip: float
    mane_tip: float
    mane_root: float
    swing: float  # how far the head turns over the plunger's travel
    mane_from: float  # the two ends of the toothed arc, in the head's frame at rest
    mane_to: float
    wheel_angle: float  # of the wheel's gear at rest
    pinion_angle: float  # of the pinion's gear at rest
    # rack and plunger
    rack_x: float  # the line the pinion's pitch circle rolls on
    rack_low: float  # Z at rest of the tooth space below the lowest tooth
    rack_high: float  # Z at rest of the rack's upper end
    bar_half: float  # half the bar's length, without its ears
    ledge: float  # Z of the step in the base on which the ears hang
    # frame
    front_post: Point
    rear_post: Point
    banking: Point
    timing: Point  # hole through plates and mane that lines up when the piece stands
    bank_from: float  # ends of the slot's centre line, in the head's frame at rest
    bank_to: float
    feet: tuple[float, float]  # X of the front and rear foot


@dataclass(frozen=True)
class Pose:
    """Where the moving parts are for a given lift of the piece off the board."""

    drop: float  # of the plunger below the base
    wheel: float  # turn of the wheel and pinion from rest
    head: float  # turn of the head from rest; negative is rearing


@lru_cache(maxsize=32)
def layout(p) -> Layout:
    inner, half = p.gap / 2, p.moving / 2
    pinion_radius = pitch_radius(p.module, p.pinion_teeth)
    wheel_radius = pitch_radius(p.module, p.wheel_teeth)
    mane_radius = pitch_radius(p.module, p.mane_teeth)
    wheel_tip = wheel_radius + p.module
    wheel = (p.wheel_x, p.base_height + p.wheel_clear + wheel_tip)
    spacing = centre_distance(p.module, p.wheel_teeth, p.mane_teeth)
    pivot = (p.head_x, wheel[1] + math.sqrt(spacing**2 - (p.head_x - p.wheel_x) ** 2))
    towards = math.degrees(math.atan2(wheel[1] - pivot[1], wheel[0] - pivot[0]))
    step = 360 / p.mane_teeth
    swing = math.degrees(p.travel / pinion_radius) * p.wheel_teeth / p.mane_teeth

    # The rack's top tooth stands `rack_top` above the pinion's axis at rest, so that two
    # teeth are in the pinion at both ends of the travel.
    pitch = math.pi * p.module
    top_tooth = wheel[1] + p.rack_top
    space = top_tooth - pitch / 2 - wheel[1]  # centre of the space below it, from the axis
    pinion_angle = math.degrees(math.pi - space / pinion_radius) % (360 / p.pinion_teeth)

    # The rear post stands high enough for the wheel to come in under it from behind.
    front_post, rear_post = (-12.5, wheel[1] + 3.5), (13.0, wheel[1] + 13.5)
    bank = math.degrees(math.atan2(rear_post[1] - pivot[1], rear_post[0] - pivot[0]))
    along = (math.cos(math.radians(bank)), math.sin(math.radians(bank)))
    banking = (pivot[0] + p.bank_radius * along[0], pivot[1] + p.bank_radius * along[1])
    timing = (pivot[0] + p.timing_radius * along[0], pivot[1] + p.timing_radius * along[1])
    # The slot's round ends are wider than the pin, which lets the head turn this much
    # past the end of the slot's centre line before the pin stops it.
    reach = math.degrees(2 * math.asin(p.bank_play / (2 * p.bank_radius)))
    return Layout(
        inner=inner,
        outer=inner + p.plate,
        half=half,
        wheel_y=(-half, -half + p.wheel_face),
        pinion_y=(-half + p.wheel_face, half),
        rack_y=(-half + p.wheel_face + p.rack_relief, half),
        wheel=wheel,
        pivot=pivot,
        towards=towards,
        pinion_radius=pinion_radius,
        wheel_tip=wheel_tip,
        mane_tip=mane_radius + p.module,
        mane_root=mane_radius - 1.25 * p.module,
        swing=swing,
        mane_from=(p.mane_first - 0.5) * step,
        mane_to=(p.mane_last + 0.5) * step,
        wheel_angle=meshing_angle(p.mane_teeth, p.wheel_teeth, 0.0, towards),
        pinion_angle=pinion_angle,
        rack_x=wheel[0] - pinion_radius,
        rack_low=top_tooth - (p.rack_teeth - 0.5) * pitch,
        rack_high=top_tooth + pitch / 2,
        bar_half=p.bar_length / 2,
        ledge=p.bar_height - p.ear_height - p.travel,
        front_post=front_post,
        rear_post=rear_post,
        banking=banking,
        timing=timing,
        bank_from=bank - p.bank_margin + reach,
        bank_to=bank + swing + p.bank_margin - reach,
        feet=(-p.foot_x, p.foot_x),
    )


def pose(p, lift: float) -> Pose:
    """The plunger stays on the board through the first `travel` of a lift, then hangs."""
    L = layout(p)
    drop = min(max(lift, 0.0), p.travel)
    turn = math.degrees(drop / L.pinion_radius)
    return Pose(drop=drop, wheel=turn, head=-turn * p.wheel_teeth / p.mane_teeth)
