"""Bare two-carriage contact rig for approved drive A; not the decorated product.

X follows the street, front is -Y, Z is up. Shaft phase is degrees. The cam is
a smooth loft of circles normal to X. A fixed-X pin in a vertical slot locates
each rigid carriage; a rear keel controls depth, roll and yaw. Broad C-jaws
allow contact to slide in both X and Y. Purchased axes are reference solids.
"""

import math
from functools import lru_cache

import numpy as np
from build123d import Box, Color, Cylinder, Plane, Pos, Rot, Solid, Wire
from cadkit.features.cams import HelicalCam
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import Process
from pydantic import Field, model_validator


class Params(BaseParams):
    """Adjustable contact geometry; mm and degrees. No production SKU is defined."""

    angle: float = Field(default=0, ge=-3600, le=3600)
    cam_radius: float = Field(default=9, ge=8.5, le=9.5)
    amplitude: float = Field(default=3.5, ge=3, le=4)
    wavelength: float = Field(default=176 / 0.85, ge=195, le=220)
    support_span: float = Field(default=16, ge=15, le=16)
    pad_width: float = Field(default=2.4, ge=2, le=2.8)
    pad_depth: float = Field(default=32, ge=31, le=33)
    capture_clearance: float = Field(default=0.4, ge=0.3, le=0.6)
    fit: float = Field(default=0.4, ge=0.3, le=0.6)
    pad_drop: float = Field(default=5, ge=5, le=6)
    jaw_wall: float = Field(default=2.4, ge=2.4, le=3)
    shaft_height: float = Field(default=21, ge=21, le=23)
    cam_sections: int = Field(default=55, ge=28, le=109)

    @model_validator(mode="after")
    def _check_envelope(self):
        if self.cam_radius - self.amplitude < (4 + self.fit) / 2 + 2:
            raise ValueError("Insufficient wall between eccentric surface and axle bore")
        if self.cam_radius + self.amplitude + self.fit > self.pad_depth / 2:
            raise ValueError("Cam envelope approaches the front spine")
        alpha = math.atan(self.amplitude * math.tau / self.wavelength)
        floor_bound = (
            self.shaft_height
            - self.cam_radius
            - self.amplitude
            - self.jaw_wall
            - self.capture_clearance
            + self.pad_drop * (math.cos(alpha) - 1)
            - (self.support_span + self.pad_width) * math.sin(alpha)
        )
        if floor_bound < 3.2:
            raise ValueError("Lower jaw approaches the rig floor")
        return self


_CENTRES = (11.0, 33.0)
_CAM_START, _CAM_LENGTH = -5.0, 54.0
_DECK_WIDTH, _DECK_DEPTH, _DECK_WALL = 20.0, 44.0, 2.4
_PIN_Y, _PIN_LENGTH, _PIN_RADIUS = 27.0, 14.0, 1.5
_KEEL_Y, _KEEL_THICKNESS = 20.0, 2.4


def _box(x, y, z, at):
    return Pos(*at) * Box(x, y, z)


def _cyl_x(radius, length, at):
    return Pos(*at) * Rot(0, 90, 0) * Cylinder(radius, length)


def _cyl_y(radius, length, at):
    return Pos(*at) * Rot(90, 0, 0) * Cylinder(radius, length)


def _cam(params):
    return HelicalCam(params.cam_radius, params.amplitude, params.wavelength)


def _pose(params, x):
    return _cam(params).flat_pads(
        x,
        params.angle,
        params.support_span,
        params.pad_width,
        params.pad_drop,
        2 * params.cam_radius + params.capture_clearance,
        params.pad_depth,
    )


@lru_cache(maxsize=16)
def _neutral(params):
    """Cache pose-independent rig solids, with the cam axis at world Z=0."""
    cam = _cam(params)
    wires = []
    for x in np.linspace(_CAM_START, _CAM_START + _CAM_LENGTH, params.cam_sections):
        y, z = cam.centre(x, 0)
        wires.append(Wire.make_circle(params.cam_radius, Plane(origin=(x, y, z), z_dir=(1, 0, 0))))
    shaft = Solid.make_loft(wires)
    shaft += _cyl_x(16, 4, (47, 0, 0))
    shaft -= _cyl_x((4 + params.fit) / 2, 60, (22, 0, 0))

    frame = _box(76, 62, 3, (22, 2, 1.5))
    for x in (-8, 52):
        block = _box(4, 18, params.shaft_height + 6, (x, 0, (params.shaft_height + 6) / 2))
        block -= _cyl_x((4 + params.fit / 2) / 2, 6, (x, 0, params.shaft_height))
        frame += block
    for x in _CENTRES:
        # Rear pin passes through a vertical capsule slot. Keep the slot tall
        # enough for the full amplitude and the finite-pad deck-height offset.
        nominal = params.shaft_height + params.cam_radius + params.pad_drop
        bracket = _box(10, 3, nominal + 8, (x, 31, (nominal + 8) / 2))
        radius = _PIN_RADIUS + params.fit / 2
        slot = _box(2 * radius, 5, 10, (x, 31, nominal))
        for z in (nominal - 5, nominal + 5):
            slot += _cyl_y(radius, 5, (x, 31, z))
        frame += bracket - slot
        # Paired cheeks surround the keel with a total Y clearance of fit.
        for sign in (-1, 1):
            y = _KEEL_Y + sign * (_KEEL_THICKNESS / 2 + params.fit / 2 + 1.2)
            frame += _box(26, 2.4, 24, (x, y, 15))

    carriage = _box(_DECK_WIDTH, _DECK_DEPTH, _DECK_WALL, (0, 0, 0))
    opening = 2 * params.cam_radius + params.capture_clearance
    top_thickness = params.pad_drop - _DECK_WALL / 2
    for u in (-params.support_span / 2, params.support_span / 2):
        carriage += _box(
            params.pad_width,
            params.pad_depth,
            top_thickness,
            (u, 0, -params.pad_drop + top_thickness / 2),
        )
        carriage += _box(
            params.pad_width,
            params.pad_depth,
            params.jaw_wall,
            (u, 0, -params.pad_drop - opening - params.jaw_wall / 2),
        )
        carriage += _box(
            params.pad_width,
            params.jaw_wall,
            opening + params.jaw_wall + top_thickness,
            (
                u,
                -params.pad_depth / 2 - params.jaw_wall / 2,
                -params.pad_drop + (top_thickness - opening - params.jaw_wall) / 2,
            ),
        )
    carriage += _box(10, _KEEL_THICKNESS, 20, (0, _KEEL_Y, -10))
    carriage += _cyl_y(3, 8, (0, 19, 0))
    carriage -= _cyl_y(_PIN_RADIUS + params.fit / 4, 12, (0, 19, 0))
    return shaft, frame, carriage


def build(params: Params):
    """Build the complete posed rig; each real part is an independent solid."""
    neutral = params.model_copy(update={"angle": 0})
    shaft, frame, carriage = _neutral(neutral)
    parts = {
        "frame": frame,
        "cam_and_thumbwheel": Pos(0, 0, params.shaft_height) * Rot(-params.angle, 0, 0) * shaft,
        "reference_steel_axle_4x68": _cyl_x(2, 68, (22, 0, params.shaft_height)),
    }
    for i, x in enumerate(_CENTRES, 1):
        p = _pose(params, x)
        parts[f"carriage_{i}"] = (
            Pos(x, 0, params.shaft_height + p.height) * Rot(0, -p.lean, 0) * carriage
        )
        parts[f"reference_guide_pin_{i}_3x14"] = _cyl_y(
            _PIN_RADIUS, _PIN_LENGTH, (x, _PIN_Y, params.shaft_height + p.height)
        )
    for name, shape in parts.items():
        shape.label = name
        colour = "#958C7C" if name == "frame" else "#252C2C"
        if name.startswith("carriage"):
            colour = "#8B4435" if name.endswith("1") else "#C4161C"
        if name.startswith("reference_"):
            colour = "#9DA5A8"
        shape.color = Color(colour)
    return parts


def _render_poses(params, steps=36):
    """Rigid matrices of the actual CAD contacts, forward then backward."""
    base = {x: _pose(params, x) for x in _CENTRES}
    frames = []
    for step in [*range(steps), *range(steps, 0, -1)]:
        angle = 360 * step / steps
        p = params.model_copy(update={"angle": params.angle + angle})
        t = math.radians(-angle)
        c, s = math.cos(t), math.sin(t)
        z = params.shaft_height
        transforms = {
            "cam_and_thumbwheel": [
                [1, 0, 0, 0],
                [0, c, -s, s * z],
                [0, s, c, z * (1 - c)],
                [0, 0, 0, 1],
            ]
        }
        for i, x in enumerate(_CENTRES, 1):
            a, b = base[x], _pose(p, x)
            t = math.radians(b.lean - a.lean)
            c, s = math.cos(t), math.sin(t)
            z0, z1 = z + a.height, z + b.height
            transforms[f"carriage_{i}"] = [
                [c, 0, -s, x - c * x + s * z0],
                [0, 1, 0, 0],
                [s, 0, c, z1 - s * x - c * z0],
                [0, 0, 0, 1],
            ]
            transforms[f"reference_guide_pin_{i}_3x14"] = [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, z1 - z0],
                [0, 0, 0, 1],
            ]
        frames.append(transforms)
    return frames


model = Model(
    name="fala",
    version="0.1.0",
    variants={"contact_rig": Params()},
    process=Process(name="U1 PLA contact development, 0.4 mm nozzle", build_volume=(270, 270, 270)),
    build=build,
)
