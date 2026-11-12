"""Plain CAD motion prototype for the approved Bryła / A / honey direction.

MM and degrees. Front is -Y, Z is up; origin is the nominal heart tip. Geometry
is deliberately undecorated. Hardware and the room envelope are reference parts.
This prototype establishes packaging and interference, not friction or endurance.
"""

import math
from copy import copy
from functools import lru_cache

from build123d import Axis, Box, Color, Cylinder, Plane, Polygon, Pos, Rot, Sphere, extrude, offset
from cadkit.features.mechanical import bar_between
from cadkit.features.motion import rigid_transform
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import Process
from pydantic import Field, model_validator


class Params(BaseParams):
    """Named prototype fits and drive dimensions; all limits precede kernel work."""

    turn: float = Field(default=0, ge=0, le=360)
    fit: float = Field(default=0.4, ge=0.3, le=0.6)
    wall: float = Field(default=2.4, ge=2, le=3)
    tail_radius: float = Field(default=11, ge=10.5, le=11.5)
    groove_radius: float = Field(default=20, ge=19, le=21)
    follower_diameter: float = Field(default=4, ge=3.8, le=4.2)
    hinge_diameter: float = Field(default=3, ge=2.8, le=3.2)
    guide_diameter: float = Field(default=3, ge=2.8, le=3.2)
    ball_diameter: float = Field(default=3, ge=2.8, le=3.2)
    hinge_relief_radius: float = Field(default=5.6, ge=5.4, le=6)
    wing_travel: float = Field(default=125, ge=120, le=125)

    @model_validator(mode="after")
    def _drive_envelope(self):
        eccentricity = self.tail_radius * math.sin(math.radians(self.wing_travel / 2))
        if self.groove_radius + eccentricity + (self.follower_diameter + self.fit) / 2 > 34:
            raise ValueError("Cam groove exceeds the web's reserved radius")
        return self


process = Process(name="Snapmaker U1 / PLA / motion prototype", build_volume=(270, 270, 270))
version = "0.1.0"
variants = {
    "motion_closed": Params(),
    "motion_mid": Params(turn=90),
    "motion_open": Params(turn=180),
}

_V = (-0.606600529, 0.0, 0.795006791)
_U = (_V[2], 0.0, -_V[0])
_P = (-8.90117357, 0.0, 16.9411217)
_AXIS = Axis(_P, _V)
_BLACK, _HONEY, _BLUE, _METAL = "#25252A", "#EDAE1C", "#3976B8", "#9AA3AB"
_EARS = ((0, 3), (13, 16), (30, 33), (43, 46))


def _point(axial=0, radial=0, y=0):
    return tuple(
        a + axial * v + radial * u + (y if i == 1 else 0)
        for i, (a, v, u) in enumerate(zip(_P, _V, _U))
    )


def _box(size, at):
    return Pos(*at) * Box(*size)


def _axial_cylinder(radius, start, end, radial=0, y=0):
    return Plane(origin=_point((start + end) / 2, radial, y), z_dir=_V).location * Cylinder(
        radius, end - start
    )


def _cyl_y(radius, length, at):
    return Pos(*at) * Rot(90, 0, 0) * Cylinder(radius, length)


def _profile():
    # A deliberately plain polygonal lobe, tangent to the V edge. This is the
    # motion envelope, not the approved final irregular fracture treatment.
    centre, radius = (-19.5, 61), 21.5
    tangent = (-35.5, 46.8)
    a0 = math.atan2(tangent[1] - centre[1], tangent[0] - centre[0]) % (2 * math.pi)
    a1 = math.acos(-centre[0] / radius)
    angles = [a0 + (a1 - a0) * i / 14 for i in range(15)]
    return [
        (0, 0),
        *[(centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a)) for a in angles],
    ]


def _drive(p):
    e = p.tail_radius * math.sin(math.radians(p.wing_travel / 2))
    theta = math.radians(p.turn)
    s = (
        -e * math.cos(theta)
        + math.sqrt(p.groove_radius**2 - (e * math.sin(theta)) ** 2)
        - p.groove_radius
    )
    angle = p.wing_travel / 2 + math.degrees(math.asin(max(-1, min(1, s / p.tail_radius))))
    return e, s, angle


@lru_cache(maxsize=8)
def _geometry(p):
    parts = {}
    foot = Pos(0, 0, -15.9) * Cylinder(36.4, 3)
    foot += Pos(0, 0, -9.6) * Cylinder(3.8, 9.6)
    foot -= Pos(0, 0, -10) * Cylinder(2.2, 20)
    parts["foot"] = foot

    e, _, _ = _drive(p)
    cam = Pos(0, 0, -9.6) * Cylinder(38, 8.4)
    cam -= Pos(0, 0, -9.6) * Cylinder(4.2, 10)
    groove_r = (p.follower_diameter + p.fit) / 2
    groove = Cylinder(p.groove_radius + groove_r, 5.4) - Cylinder(p.groove_radius - groove_r, 7)
    cam -= Pos(0, -e, -7.9) * groove
    parts["cam_ring"] = cam

    carrier = Pos(0, 0, -3.8) * Cylinder(36, 2)
    carrier -= Pos(0, 0, -3.8) * Cylinder(2.2, 4)
    carrier -= _box((p.follower_diameter + p.fit + 1, 26, 4), (0, 20, -3.8))
    for x in (-22, 22):
        for y in (-22, 22):
            holder = _box((7, 4, 8), (x, y, -0.8))
            holder -= _cyl_y((p.guide_diameter + p.fit) / 2, 6, (x, y, 0.4))
            carrier += holder
        parts[f"reference_guide_{'left' if x < 0 else 'right'}"] = _cyl_y(
            p.guide_diameter / 2, 46, (x, 0, 0.4)
        )
    parts["carrier"] = carrier

    # Rear bridge clears the stationary central tie screw over the entire stroke.
    slider = _box((32, 4, 3.6), (0, 17, 0.4))
    slider += _box((5, 5, 3.6), (0, 19, 0.4))
    for side in (-1, 1):
        slider += _box((4, 19, 3.6), (side * 14, 8.5, 0.4))
        slider += _box((16, 4, 3.6), (side * 18, 0, 0.4))
        bearing = _cyl_y(3, 6, (side * 22, 0, 0.4))
        bearing -= _cyl_y((p.guide_diameter + p.fit) / 2, 8, (side * 22, 0, 0.4))
        slider += bearing
        # Two cheeks span the radial ball sweep. Axial separation from the
        # lever arm leaves its neck free; their Y spacing sets follower play.
        cheeks = None
        for y in (-1, 1):
            plane = Plane(
                origin=_point(-3, -8.75, y * ((p.ball_diameter + p.fit) / 2 + 1)),
                x_dir=_U,
                z_dir=(0, 1, 0),
            )
            cheek = plane.location * Box(8.5, 5, 2)
            cheeks = cheek if cheeks is None else cheeks + cheek
        bridge = _box((4, 8, 6), (14, 0, 2.8))
        if side < 0:
            bridge = bridge.mirror(Plane.YZ)
        else:
            cheeks = cheeks.mirror(Plane.YZ)
        slider += bridge + cheeks
    slider -= Pos(0, p.groove_radius, 0.4) * Cylinder((p.follower_diameter + p.fit) / 2, 6)
    for x in (-22, 22):
        slider -= _cyl_y((p.guide_diameter + p.fit) / 2, 12, (x, 0, 0.4))
    parts["slider"] = slider
    parts["reference_follower"] = Pos(0, p.groove_radius, -5) * Cylinder(
        p.follower_diameter / 2, 10
    )

    outline = Polygon(*_profile(), align=None)
    skin = extrude(Plane.XZ * outline, amount=20, dir=(0, -1, 0))
    hollow = extrude(Plane.XZ * offset(outline, amount=-p.wall), amount=20, dir=(0, -1, 0))
    wing = skin - Pos(0, p.wall, 0) * hollow
    wing -= _box((12, 20, 44), (-4, -7.5, 46))
    seat = (
        Plane(origin=(-11.44519529, 0, 15), z_dir=_V).location * Pos(0, 0, 100) * Box(200, 200, 200)
    )
    wing &= seat
    for start, end in _EARS:
        wing -= _axial_cylinder(p.hinge_relief_radius + p.fit / 2, start - p.fit, end + p.fit)
    for start, end in ((4, 12), (34, 42)):
        wing += _axial_cylinder(3.2, start, end)
    half = math.radians(p.wing_travel / 2)
    radial, y = -p.tail_radius * math.cos(half), -p.tail_radius * math.sin(half)
    ball = _point(-2, radial, y)
    wing += bar_between(_point(6), _point(6, radial, y), 3, 3)
    wing += bar_between(ball, _point(6, radial, y), 2.2, 2.2)
    wing += Pos(*ball) * Sphere(p.ball_diameter / 2)
    wing -= _axial_cylinder((p.hinge_diameter + p.fit) / 2, -2, 49)
    parts["wing_left"] = wing
    parts["wing_right"] = wing.mirror(Plane.YZ)

    # The sketch lives in XY (its Y is height); mirror about its local Y axis.
    full = outline + outline.mirror(Plane.YZ)
    rear = Pos(0, 20, 0) * extrude(Plane.XZ * full, amount=2.4, dir=(0, -1, 0))
    rear &= _box((100, 60, 100), (0, 0, 74))
    for side in (-1, 1):
        rear += _box((6, 3, 47.8), (side * 29, 18.8, 21.1))
        low = _point(1.5, y=18.8)
        rear += bar_between((side * 29, 18.8, low[2]), (side * abs(low[0]), 18.8, low[2]), 3, 3)
        ears = None
        for start, end in _EARS:
            ear = _axial_cylinder(4.2, start, end)
            mount = Plane(origin=_point((start + end) / 2, y=11.2), x_dir=_U, z_dir=(0, 1, 0))
            ear += mount.location * Box(3, end - start, 16)
            ear -= _axial_cylinder((p.hinge_diameter + p.fit) / 2, start - 1, end + 1)
            ears = ear if ears is None else ears + ear
        rear += ears if side < 0 else ears.mirror(Plane.YZ)
        name = "left" if side < 0 else "right"
        pin = _axial_cylinder(p.hinge_diameter / 2, -1, 47)
        parts[f"reference_hinge_{name}"] = pin if side < 0 else pin.mirror(Plane.YZ)
    parts["back_carriage"] = rear
    parts["reference_room_envelope"] = _box((36, 20, 30), (0, 4, 48))
    parts["reference_tie_screw"] = Pos(0, 0, -8) * Cylinder(2, 20)
    return parts


def build(params: Params):
    """Individually named BReps at a ring pose; reference parts are not print files."""
    _, displacement, swing = _drive(params)
    parts = {}
    for name, original in _geometry(params.model_copy(update={"turn": 0})).items():
        shape = copy(original)
        if name == "cam_ring":
            shape = shape.rotate(Axis.Z, params.turn)
        elif name in ("slider", "reference_follower"):
            shape = Pos(0, displacement, 0) * shape
        elif name == "wing_left":
            shape = shape.rotate(_AXIS, -swing)
        elif name == "wing_right":
            shape = shape.rotate(Axis((-_P[0], 0, _P[2]), (-_V[0], 0, _V[2])), swing)
        colour = _HONEY if name == "reference_room_envelope" else _BLACK
        if name in ("slider", "carrier"):
            colour = _BLUE  # engineering review colour; production maps to black
        elif name.startswith("reference_") and name != "reference_room_envelope":
            colour = _METAL
        shape.label, shape.color = name, Color(colour)
        parts[name] = shape
    return parts


def _render_poses(params, steps=48):
    """Rigid transforms of the CAD parts, one complete open-and-close ring cycle."""
    _, initial_s, initial_angle = _drive(params)

    frames = []
    for i in range(steps):
        turn = (params.turn + 360 * i / steps) % 360
        _, s, angle = _drive(params.model_copy(update={"turn": turn}))
        frames.append(
            {
                "cam_ring": rigid_transform(angle=turn - params.turn),
                "slider": rigid_transform(shift=(0, s - initial_s, 0)),
                "reference_follower": rigid_transform(shift=(0, s - initial_s, 0)),
                "wing_left": rigid_transform(_V, _P, -(angle - initial_angle)),
                "wing_right": rigid_transform(
                    (-_V[0], 0, _V[2]), (-_P[0], 0, _P[2]), angle - initial_angle
                ),
            }
        )
    return [*frames, frames[0]]


model = Model("serce", version, variants, process, build)
