"""Drive kinematics and a simple statics model of opening A (wings). Units: mm, degrees, N.

Chain: the grip ring turns the cam disc; a groove in it moves a follower pin front to back; the
pin is fixed in the slider. Each wing carries a lever with a crank pin, which sits between a
front plate on the slider and a plate on the pusher bar. The pusher rides on the slider and a
spring presses it forward against a stop, so in travel the pin has only `yoke_gap` of play.
Closing, the pusher pushes both pins; when the wings reach their seats the slider goes on by
`over_travel` and the spring, now between pins and slider, holds the wings shut. Opening, the
pins follow the pusher back under gravity, or the front plates pull them.

`turn` is the angle of the cam disc: 0 is closed, 180 fully open, 360 closed again.
"""

import math

from cadkit.features.motion import cam_pressure_angle, cam_rate

GRAVITY = 9.81e-3  # N per gram


def half_swing(p) -> float:
    """The lever swings this far to either side of square to the slider's travel."""
    return p.wing_max / 2


def pin_travel(p) -> float:
    """Front-to-back travel of a crank pin over the full swing."""
    return 2 * p.lever * math.sin(math.radians(half_swing(p)))


def stroke(p) -> float:
    """Travel of the slider: the pins' travel plus the over-travel past the seats."""
    return pin_travel(p) + p.over_travel


def follower_y(p, turn: float) -> float:
    """World y of the follower pin (behind the axis): the cam profile.

    A pure cosine over the whole stroke, with a dead point at closed and at open. The wings
    are seated while the slider covers the last `over_travel`, so nothing moves for the first
    `dwell_angle` of ring turn. Where the wings seat the cam still has a healthy rate, so a
    blocked wing cannot be wedged with a large force by a small torque on the ring.
    """
    return p.groove_radius - stroke(p) / 2 * math.cos(math.radians(turn))


def follower_offset(p) -> float:
    """From the slider's reference (see slider_y) back to the follower pin's centre."""
    return p.groove_radius + stroke(p) / 2 - (pin_travel(p) / 2 - p.yoke_gap)


def slider_y(p, turn: float) -> float:
    """World y at which the slider's front plates would hold a crank pin's centre.

    The hinge axes lie in the plane y = 0, so a pin sits at +-pin_travel / 2 at the ends.
    """
    return follower_y(p, turn) - follower_offset(p)


def seated(p, turn: float) -> bool:
    """True in the closed dwell: the wings rest on their seats and the slider has moved on."""
    return slider_y(p, turn) + p.yoke_gap < -pin_travel(p) / 2


def pin_y(p, turn: float) -> float:
    """World y of the crank pins, resting on the pusher's plates."""
    return max(slider_y(p, turn) + p.yoke_gap, -pin_travel(p) / 2)


def wing_angle(p, turn: float) -> float:
    """Opening angle of each wing: 0 closed, wing_max fully open."""
    if seated(p, turn):
        return 0.0
    ratio = max(-1.0, min(1.0, pin_y(p, turn) / p.lever))
    return max(0.0, half_swing(p) + math.degrees(math.asin(ratio)))


def pusher_lag(p, turn: float) -> float:
    """How far the pusher bar stands behind its stop on the slider (only in the closed dwell)."""
    return pin_y(p, turn) - (slider_y(p, turn) + p.yoke_gap)


def dwell_angle(p) -> float:
    """Ring angle either side of closed over which the wings stay seated."""
    return math.degrees(math.acos(1 - 2 * p.over_travel / stroke(p)))


def lever_arm(p, turn: float) -> float:
    """Effective arm of the crank pin about the hinge for a force along the slider's travel."""
    return p.lever * math.cos(math.radians(wing_angle(p, turn) - half_swing(p)))


def follower_rate(p, turn: float) -> float:
    """Slider travel per radian of ring turn, signed."""
    return cam_rate(lambda t: follower_y(p, t), turn)


def pressure_angle(p, turn: float) -> float:
    """Cam pressure angle at the follower, degrees."""
    return cam_pressure_angle(lambda t: follower_y(p, t), turn)


# ---------------------------------------------------------------- statics
def spring_force(p, turn: float) -> float:
    """Force of the pusher spring, N."""
    return p.spring_preload + p.spring_rate * pusher_lag(p, turn)


def slider_force(p, turn: float, direction: int, wing_gravity=None) -> float:
    """Force the cam must put on the slider along +y (to the back) to keep moving, N.

    `wing_gravity(angle)` is the torque of gravity on one wing in N mm, positive when it helps
    the wing open.
    """
    if seated(p, turn):
        # The wings rest on their seats and the spring stands between the pins and the slider:
        # it pushes the slider back.
        return -spring_force(p, turn)
    moving = 1 if follower_rate(p, turn) * direction >= 0 else -1  # +1 back (opening)
    angle = wing_angle(p, turn)
    resist = p.hinge_friction - moving * (wing_gravity(angle) if wing_gravity else 0.0)
    force = moving * 2 * resist / lever_arm(p, turn)
    # the loaded pins slide along the plates as the levers swing
    slide = abs(math.tan(math.radians(angle - half_swing(p))))
    return force * (1 + p.friction * slide)


def ring_torque(p, turn: float, direction: int, wing_gravity=None) -> dict:
    """Quasi-static torque at the grip ring to keep turning in `direction` (+1 or -1), N mm.

    A simple model, good for the size and evenness of the effort, not for exact values:
    work done on the slider; Coulomb friction of the slider in its guides under the cam's side
    force; friction of the fixed steel follower sliding round the groove; a constant ring drag.
    Returns the parts and their sum under "total".
    """
    force = slider_force(p, turn, direction, wing_gravity)
    rate = follower_rate(p, turn)
    pressure = math.radians(pressure_angle(p, turn))
    parts = {
        "work": force * rate * direction,
        "guides": p.friction * abs(force * math.tan(pressure) * rate),
        "follower": p.friction_steel * abs(force) * follower_y(p, turn),
        "drag": p.ring_drag,
    }
    parts["total"] = sum(parts.values())
    return parts


def closing_torque(p, turn: float = 0.0) -> float:
    """Torque that holds each wing on its seat in the closed dwell, N mm."""
    return spring_force(p, turn) / 2 * lever_arm(p, turn)
