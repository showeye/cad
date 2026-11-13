"""Bare two-carriage contact rig for approved drive A; not the decorated product.

X follows the street, front is -Y, Z is up. Shaft phase is degrees. The cam is
a smooth loft of circles normal to X. A fixed-X pin in a vertical slot locates
each rigid carriage; a rear keel controls depth, roll and yaw. Broad C-jaws
allow contact to slide in both X and Y. Hardware uses nominal reference solids.
"""

import math
from functools import lru_cache
from typing import Literal

import numpy as np
from build123d import Box, Color, Cylinder, Plane, Pos, Rot, Solid, Wire
from cadkit.features.cams import HelicalCam
from cadkit.features.hardware import nut_m3, shaft_collar_4, shoulder_screw_4_m3, socket_screw_m3
from cadkit.features.mechanical import hex_prism
from cadkit.features.text import engraving
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
    study: Literal["contact", "fit", "loaded"] = "contact"
    nut_fit: float = Field(default=0.3, ge=0.2, le=0.5)
    mast_height: float = Field(default=140, ge=120, le=160)

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
_PIN_RADIUS = 2.0
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
        block -= _cyl_x((4 + params.fit) / 2, 6, (x, 0, params.shaft_height))
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
            frame += _box(26, 2.4, 22, (x, y, 14))

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
    # The 12 mm shoulder bottoms at Y=22; its head bears at Y=34,
    # 1.5 mm behind the slot bracket. Tightening cannot clamp the slot.
    carriage += _cyl_y(5, 8, (0, 19, 0))
    carriage -= _cyl_y((3 + params.fit) / 2, 10, (0, 19, 0))
    carriage -= _cyl_y((4 + params.fit) / 2, 3, (0, 23.5, 0))
    # Front-loading hex pocket; an approximately 4 mm tall M3 locknut seats
    # at Y=20. The thread tip is Y=15, leaving 1 mm nominal protrusion.
    carriage -= Pos(0, 17, 0) * Rot(90, 0, 0) * hex_prism((5.5 + params.nut_fit) / math.sqrt(3), 6)
    # Optional removable test mast: M3x8 through the deck, plain M3 nut below.
    carriage -= Pos(0, -6, 0) * Cylinder((3 + params.fit) / 2, 5)
    return shaft, frame, carriage


def _mast(params):
    """Removable test ballast carrier; sliding mass height is measured, not assumed."""
    # Mast and foot share their +Y face, allowing the whole fixture to lie
    # flat on that face without supports. Thin rails keep ballast headroom.
    shape = _box(18, 12, 3.2, (0, -5.2, 2.8))
    shape -= Pos(0, -6, 2.8) * Cylinder((3 + params.fit) / 2, 6)
    shape += _box(8, 1.6, params.mast_height, (0, 0, 4.4 + params.mast_height / 2))
    # A through slot for a separately weighed M3 bolt/washer/nut ballast pack.
    lo, hi = 14, params.mast_height - 2
    slot = _box(3.4, 5, hi - lo, (0, 0, (lo + hi) / 2))
    for z in (lo, hi):
        slot += _cyl_y(1.7, 5, (0, 0, z))
    return shape - slot


def _fit_parts(params):
    """Full-size jaw/keel plus matching orientation-specific fit coupons."""
    _, _, carriage = _neutral(params.model_copy(update={"study": "contact", "angle": 0}))
    code = str(round(params.fit * 100))
    carriage -= Pos(0, -11, 1.2) * engraving(code, 3.5, 0.6)
    # Horizontal bores reproduce the frame; the standing bore reproduces the
    # cam's axial print orientation. Both use a real 4 mm steel gauge shaft.
    coupon = _box(48, 24, 3, (0, 0, 1.5))
    for x in (-15, 0):
        block = _box(4, 18, 24, (x, 0, 12))
        block -= _cyl_x((4 + params.fit) / 2, 6, (x, 0, 18))
        coupon += block
    ring = Pos(15, 0, 6) * Cylinder(5, 6)
    ring -= Pos(15, 0, 6) * Cylinder((4 + params.fit) / 2, 8)
    coupon += ring
    coupon -= Pos(12, -8, 3) * engraving(code, 3.5, 0.6)
    # A separate shortened frame uses the exact keel cheeks and guide slot.
    guide = _box(30, 24, 3, (0, 22, 1.5))
    for sign in (-1, 1):
        y = _KEEL_Y + sign * (_KEEL_THICKNESS / 2 + params.fit / 2 + 1.2)
        guide += _box(26, 2.4, 22, (0, y, 14))
    bracket = _box(10, 3, 43, (0, 31, 21.5))
    radius = (4 + params.fit) / 2
    slot = _box(2 * radius, 5, 10, (0, 31, 35))
    for z in (30, 40):
        slot += _cyl_y(radius, 5, (0, 31, z))
    guide += bracket - slot
    guide -= Pos(0, 12, 3) * engraving(code, 3.5, 0.6)
    return {
        f"jaw_keel_{code}": carriage,
        f"axle_coupon_{code}": Pos(45, -15, 0) * coupon,
        f"guide_coupon_{code}": Pos(90, 0, 0) * guide,
    }


def build(params: Params):
    """Build the complete posed rig; each real part is an independent solid."""
    if params.study == "fit":
        return _fit_parts(params)
    neutral = params.model_copy(update={"angle": 0})
    shaft, frame, carriage = _neutral(neutral)
    parts = {
        "frame": frame,
        "cam_and_thumbwheel": Pos(0, 0, params.shaft_height) * Rot(-params.angle, 0, 0) * shaft,
        "reference_steel_axle_4x80": _cyl_x(2, 80, (22, 0, params.shaft_height)),
    }
    for i, x in enumerate((-13, 57), 1):
        parts[f"reference_shaft_collar_{i}_DIN705"] = (
            Pos(x, 0, params.shaft_height) * Rot(0, 90, 0) * shaft_collar_4()
        )
    for i, x in enumerate(_CENTRES, 1):
        p = _pose(params, x)
        location = Pos(x, 0, params.shaft_height + p.height) * Rot(0, -p.lean, 0)
        parts[f"carriage_{i}"] = location * carriage
        parts[f"reference_guide_shoulder_{i}_4_M3_12"] = (
            location * Pos(0, 34, 0) * Rot(-90, 0, 0) * shoulder_screw_4_m3()
        )
        parts[f"reference_guide_locknut_{i}_M3"] = (
            location * Pos(0, 18, 0) * Rot(90, 0, 0) * nut_m3(height=4)
        )
        if params.study == "loaded":
            parts[f"load_mast_{i}"] = location * _mast(params)
            parts[f"reference_mast_screw_{i}_M3x8"] = (
                location * Pos(0, -6, 4.4) * socket_screw_m3(8)
            )
            parts[f"reference_mast_nut_{i}_M3"] = location * Pos(0, -6, -2.4) * nut_m3()
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
            carriage_transform = [
                [c, 0, -s, x - c * x + s * z0],
                [0, 1, 0, 0],
                [s, 0, c, z1 - s * x - c * z0],
                [0, 0, 0, 1],
            ]
            for name in (
                f"carriage_{i}",
                f"reference_guide_shoulder_{i}_4_M3_12",
                f"reference_guide_locknut_{i}_M3",
                *(
                    (
                        f"load_mast_{i}",
                        f"reference_mast_screw_{i}_M3x8",
                        f"reference_mast_nut_{i}_M3",
                    )
                    if params.study == "loaded"
                    else ()
                ),
            ):
                transforms[name] = carriage_transform
        frames.append(transforms)
    return frames


model = Model(
    name="fala",
    version="0.2.0",
    variants={
        "contact_rig": Params(),
        "loaded_rig": Params(study="loaded"),
        **{
            f"u1_fit_{code:03}": Params(study="fit", fit=code / 100, capture_clearance=code / 100)
            for code in (30, 40, 50)
        },
    },
    process=Process(name="U1 PLA contact development, 0.4 mm nozzle", build_volume=(270, 270, 270)),
    build=build,
)
