"""Carnall product geometry. X runs along cylinders, Y along shafts, Z is up; front is -Y.

Full-size interpretation, not a survey model. Every output is a named single-solid component.
Cord is a reference purchased flexible part. Print layout and assembly are documented separately.
"""

import math
from functools import lru_cache

from build123d import (
    Axis,
    Box,
    Cylinder,
    Pos,
    Rot,
    Sphere,
)
from cadkit.features.mechanical import bar_between, cord_loop, hex_prism, link, spoked_wheel
from cadkit.features.motion import Belt, slider_crank
from cadkit.features.text import engraving
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import FDM
from pydantic import Field, model_validator


class Params(BaseParams):
    """Prototype geometry and pose; product identity and footprint remain fixed."""

    angle: float = Field(default=35, ge=-3600, le=3600)
    crank_radius: float = Field(default=8, ge=6, le=9)
    rod_length: float = Field(default=37, ge=35, le=39)
    fit: float = Field(default=0.4, ge=0.3, le=0.6)
    sheave_lift: float = Field(default=0, ge=0, le=1.5)

    @model_validator(mode="after")
    def _check_stroke(self):
        if self.rod_length + self.crank_radius > 46:
            raise ValueError("Stroke exceeds crosshead guide envelope")
        if self.rod_length - self.crank_radius < 29:
            raise ValueError("Stroke exceeds cylinder front clearance")
        return self


_IRON = "#252C2C"
_OCHRE = "#BB8A3B"
_BRICK = "#934E3C"
_CREAM = "#E5DBC3"
_SHAFT = (10, 0, 44)
_WHEEL_R = 32.0
_SHEAVE_R = 12.0


def _box(x, y, z, at):
    return Pos(*at) * Box(x, y, z)


def _cyl_y(radius, length, at):
    return Pos(*at) * Rot(90, 0, 0) * Cylinder(radius, length)


def _cyl_x(radius, length, at):
    return Pos(*at) * Rot(0, 90, 0) * Cylinder(radius, length)


def _arch(width, height, thickness):
    """Arched opening in XZ, flat bottom at z=0, through Y."""
    spring = height - width / 2
    return _box(width, thickness, spring, (0, 0, spring / 2)) + _cyl_y(
        width / 2, thickness, (0, 0, spring)
    )


def _label(shape, name, colour):
    from build123d import Color

    shape.label, shape.color = name, Color(colour)
    return shape


def _brick_courses(wall, start, end, top, plane="back"):
    """Product's simplified shallow mortar joints; rounded-looking brick from real relief."""
    for row, z in enumerate(range(15, top, 5)):
        if plane == "back":
            wall -= _box(end - start, 0.6, 0.55, ((start + end) / 2, 39.1, z))
        else:
            wall -= _box(0.6, end - start, 0.55, (43.1, (start + end) / 2, z))
        for u in range(start + (5 if row % 2 else 0), end, 10):
            if plane == "back":
                wall -= _box(0.55, 0.6, 4.5, (u, 39.1, z + 2.5))
            else:
                wall -= _box(0.6, 0.55, 4.5, (43.1, u, z + 2.5))
    return wall


@lru_cache(maxsize=12)
def _fixed(fit: float, lift: float):
    parts = {}

    def add(name, shape, colour):
        parts[name] = _label(shape, name, colour)

    # Stepped plinth with sockets, rather than a miniature landscape.
    base = _box(180, 90, 6, (0, 0, 3)) + _box(176, 85, 2, (0, 0, 7))
    base -= _box(82 + fit, 4, 12 + fit, (-35, -43.7, 8))
    for x in (-68, -2, 45, 69):
        for y in (-28, 28):
            base -= Pos(x, y, 6) * Cylinder(1.7, 6)
    for x in (-64, -6):
        base -= _cyl_y(1.7, 8, (x, -41.5, 5))
    add("plinth", base, _IRON)

    bed = _box(124, 63, 5, (-20, 0, 10.5))
    bed -= _box(70, 9, 5, (10, 0, 13.5))
    for x in (-68, -2):
        for y in (-28, 28):
            bed += Pos(x, y, 7.5) * Cylinder(1.5, 5)
    # Cylinders and guide pedestals have a common removable bed.
    for y in (-20, 20):
        for x in (-77, -58):
            bed += _box(5, 13, 25, (x, y, 25))
        for x in (-44, -10):
            bed += _box(3, 14, 34, (x, y, 29))
            bed -= _cyl_x(1.5 + fit / 2, 5, (x, y, 44))
        for rail_y in (y - 4.8, y + 4.8):
            bed -= _cyl_x(1.2 + fit / 2, 39, (-27, rail_y, 39.5))
        bed -= _cyl_x(8.5 + fit / 2, 31, (-67, y, 44))
    for y in (-9, 9):
        bed += _box(11, 5, 32, (10, y, 29))
        bed += _cyl_y(5.5, 5, (10, y, 44))
        bed -= _cyl_y(3.5 + fit / 2, 8, (10, y, 44))
    add("engine_bed", bed, _IRON)

    for side, y in (("front", -20), ("rear", 20)):
        shell = _cyl_x(8.5, 30, (-67, y, 44))
        shell -= _cyl_x(3.8, 26, (-68, y, 44))
        shell -= _cyl_x(1.5 + fit / 2, 34, (-67, y, 44))
        shell -= _box(23, 12, 15, (-67.5, y - 3, 48))
        # Underside sockets into pedestal tops.
        for x in (-77, -58):
            shell -= Pos(x, y, 35.5) * Cylinder(1.4, 6)
        add(f"{side}_cylinder", shell, _IRON)
        for i, x in enumerate((-80.5, -53.5)):
            collar = _cyl_x(9.3, 1.8, (x, y, 44)) - _cyl_x(8.5 + fit / 2, 3.8, (x, y, 44))
            add(f"{side}_cylinder_band_{i}", collar, _OCHRE)
        for i, rail_y in enumerate((y - 4.8, y + 4.8)):
            add(f"{side}_guide_{i}", _cyl_x(1.2, 38, (-27, rail_y, 39.5)), _CREAM)

    # Journal bushes spin on the hex shaft's cylindrical journal lands.
    for side, y in (("front", -9), ("rear", 9)):
        bush = _cyl_y(3.5, 5, (10, y, 44)) - _cyl_y(2.5 + fit / 2, 8, (10, y, 44))
        add(f"{side}_bearing", bush, _OCHRE)

    # Rear brick wall, tall openings, pilasters and a narrow surviving roof strip.
    wall = _box(129, 4, 77, (-19.5, 41, 46.5))
    for x in (-58, -12, 26):
        wall -= Pos(x, 41, 28) * _arch(24, 48, 8)
    for x in (-82, -35, 43):
        wall += _box(3, 1.5, 77, (x, 38.75, 46.5))
    wall = _brick_courses(wall, -84, 45, 84)
    add("brick_back", wall, _BRICK)
    for i, x in enumerate((-58, -12, 26)):
        trim = Pos(x, 38.6, 27) * _arch(27, 52, 1.2)
        trim -= Pos(x, 38.6, 28) * _arch(24, 48, 4)
        add(f"back_window_trim_{i}", trim, _CREAM)

    # Tall rope portal in the end wall, with deliberately removed front upper quarter.
    end = _box(4, 73, 102, (45, 4.5, 59))
    end -= _box(8, 13, 84, (45, -27.5, 71))
    opening = Pos(45, 0, 27) * Rot(0, 0, 90) * _arch(29, 81, 9)
    end -= opening
    end = _brick_courses(end, -32, 41, 110, plane="end")
    add("brick_rope_portal", end, _BRICK)
    trim = Pos(42.6, 0, 26) * Rot(0, 0, 90) * _arch(32, 85, 1.2)
    trim -= Pos(42.6, 0, 27) * Rot(0, 0, 90) * _arch(29, 81, 4)
    add("rope_portal_trim", trim, _CREAM)
    add("back_coping", _box(131, 6, 2.5, (-19.5, 41, 86.25)), _CREAM)
    roof = _box(129, 12, 2.4, (-19.5, 36, 89)).rotate(Axis((-19.5, 41, 89), (1, 0, 0)), -12)
    add("roof_fragment", roof, _IRON)

    # Two-plane braced trestle: front and rear frame openings remain clear.
    frame = _box(29, 37, 3, (69, 0, 9.5))
    for y in (-13, 13):
        for x in (58, 80):
            frame += bar_between((x, y, 10), (69, y, 101), 3, 3)
        for z in (38, 66, 94):
            w = 22 * (101 - z) / 91
            frame += _box(w + 5, 3, 2.4, (69, y, z))
        for z0, z1 in ((12, 38), (38, 66), (66, 94)):
            w0, w1 = 11 * (101 - z0) / 91, 11 * (101 - z1) / 91
            frame += bar_between((69 - w0, y, z0), (69 + w1, y, z1), 1.8, 2)
            frame += bar_between((69 + w0, y, z0), (69 - w1, y, z1), 1.8, 2)
        # Slots let the upper axle move 1.5 mm before clamping with screws.
        frame += _box(10, 5, 15, (69, y, 103.5))
        frame -= _cyl_y(1.7, 9, (69, y, 104))
        frame -= _cyl_y(1.7, 9, (69, y, 105.5))
        frame -= _box(3.4, 9, 1.5, (69, y, 104.75))
    for x in (58, 80):
        frame += _box(3, 29, 3, (x, 0, 12))
    # Tie the inclined trestle back to its top bearings in both planes.
    for y in (-13, 13):
        frame += bar_between((52, y, 12), (69, y, 101), 2.8, 2.8)
        frame += _box(20, 5, 3, (60, y, 11))
    add("headframe", frame, _IRON)
    add("headframe_header", _box(23, 35, 2, (69, 0, 119)), _IRON)
    # Header sits on two side posts, clear of the rotating sheave.
    for side, y in (("front", -13), ("rear", 13)):
        add(f"header_post_{side}", _box(3, 3, 10, (69, y, 115)), _IRON)
    add("sheave_axle", _cyl_y(1.5, 33, (69, 0, 104 + lift)), _OCHRE)
    for side, y in (("front", -6), ("rear", 6)):
        add(
            f"sheave_spacer_{side}",
            _cyl_y(3.3, 7, (69, y, 104 + lift)) - _cyl_y(1.5 + fit / 2, 9, (69, y, 104 + lift)),
            _CREAM,
        )

    plate = _box(82, 2.6, 12, (-35, -43.6, 8))
    for x in (-64, -6):
        plate += _cyl_y(1.5, 5, (x, -40.8, 5))
    for text, size, z in (
        ("CARNALL / ZABRZE", 5.5, 10.5),
        ("NA SZYCHCIE OD 1915", 3.2, 5),
    ):
        plate -= Pos(-35, -44.95, z) * Rot(90, 0, 0) * engraving(text, size)
    add("nameplate", plate, _OCHRE)

    return parts


def _belt(params):
    return Belt((10, 44), 31.8, (69, 104 + params.sheave_lift), 11.8)


@lru_cache(maxsize=4)
def _cord(lift):
    return cord_loop(Belt((10, 44), 31.8, (69, 104 + lift), 11.8))


def _motion(params):
    """Product pose data consumed by CAD, numerical checks and render animation alike."""
    out = {}
    for side, phase, sign in (("front", 0, -1), ("rear", 90, 1)):
        cx, cz, sx = slider_crank(params.crank_radius, params.rod_length, params.angle + phase)
        out[side] = {
            "slider": 10 + sx,
            "pin": (10 + cx, sign * 29, 44 + cz),
            "rod_angle": math.degrees(math.atan2(cz, cx - sx)),
        }
    out["sheave_angle"] = params.angle * 31.8 / 11.8
    out["rope_witness"] = _belt(params).point_at(math.radians(params.angle) * 31.8)
    return out


@lru_cache(maxsize=16)
def _moving_neutral(radius, rod, fit, lift):
    parts = {}

    def add(name, shape, colour):
        parts[name] = _label(shape, name, colour)

    wheel = spoked_wheel(32, 6.5, 4.5, 8) - hex_prism(2.5 + fit / 2, 12)
    add("rope_wheel", Pos(*_SHAFT) * Rot(90, 0, 0) * wheel, _OCHRE)
    shaft = hex_prism(2.5, 48)
    for y in (-9, 9):
        shaft += Pos(0, 0, y) * Cylinder(2.5, 5)
    for y in (-22, 22):
        shaft -= Pos(0, 0, y) * Cylinder(0.8, 7)
    add("main_shaft", Pos(*_SHAFT) * Rot(90, 0, 0) * shaft, _IRON)

    for side, phase, sign in (("front", 0, -1), ("rear", 90, 1)):
        y = sign * 20
        piston = _box(8, 14, 14, (0, y, 44))
        for rail_y in (y - 4.8, y + 4.8):
            piston -= _cyl_x(1.2 + fit / 2, 12, (0, rail_y, 39.5))
        piston += _cyl_x(1.5, 39, (-19.5, y, 44))
        piston += _cyl_x(3.4, 5, (-39, y, 44))
        piston -= _cyl_y(1.5 + fit / 2, 20, (0, y, 44))
        add(f"{side}_piston_crosshead", piston, _OCHRE)
        rod_shape = Pos(0, sign * 29, 44) * Rot(90, 0, 0) * link(rod, 5.5, 2.8, 3 + fit)
        add(f"{side}_connecting_rod", rod_shape, _CREAM)
        # Quartered crank plates are keyed to one common hex shaft.
        disc = _cyl_y(radius + 3.5, 3.5, (10, sign * 22, 44))
        disc -= Pos(*_SHAFT) * Rot(90, 0, 0) * hex_prism(2.5 + fit / 2, 50)
        cx = 10 + radius * math.cos(math.radians(phase))
        cz = 44 + radius * math.sin(math.radians(phase))
        if side == "front":
            disc += _cyl_y(1.5, 22, (cx, -32, cz))
            disc -= _cyl_y(0.6, 5, (cx, -42, cz))
        else:
            disc += _cyl_y(1.5, 10, (cx, sign * 26.5, cz))
        add(f"{side}_crank_disc", disc, _IRON)
        # Pivot pins and wide heads retain the rods without clamping the running faces.
        pin = _cyl_y(1.5, 21, (0, sign * 22, 44))
        pin += _cyl_y(2.5, 1.2, (0, sign * 32, 44))
        add(f"{side}_crosshead_pin", pin, _IRON)
        cap = _cyl_y(2.5, 1.2, (cx, sign * 32, cz))
        cap -= _cyl_y(1.5 + fit / 2, 3, (cx, sign * 32, cz))
        add(f"{side}_crank_pin_cap", cap, _OCHRE)

    # Turn the eccentric front crank pin itself. No shaft crosses the rod plane.
    grip = _cyl_y(4.2, 8, (10 + radius, -38, 44))
    grip -= _cyl_y(1.5 + fit / 2, 11, (10 + radius, -38, 44))
    add("crank_grip", grip, _OCHRE)
    grip_cap = _cyl_y(2.5, 1, (10 + radius, -43.5, 44))
    grip_cap -= _cyl_y(0.9, 3, (10 + radius, -43.5, 44))
    add("crank_grip_cap", grip_cap, _IRON)
    # Cap on the rear shaft; screw pilot dimensions require a physical coupon.
    cap = _cyl_y(3.8, 2, (10, 25, 44)) - _cyl_y(1.1, 5, (10, 25, 44))
    add("shaft_rear_cap", cap, _OCHRE)
    cap = _cyl_y(3.8, 2, (10, -25, 44)) - _cyl_y(1.1, 5, (10, -25, 44))
    add("shaft_front_cap", cap, _OCHRE)
    sheave = spoked_wheel(12, 4, 3 + fit, 6)
    add("headframe_sheave", Pos(69, 0, 104 + lift) * Rot(90, 0, 0) * sheave, _OCHRE)
    return parts


def build(params: Params):
    """Build the complete posed assembly, with independent solids for every real part."""
    parts = dict(_fixed(params.fit, params.sheave_lift))
    moving = _moving_neutral(params.crank_radius, params.rod_length, params.fit, params.sheave_lift)
    state = _motion(params)
    main_axis = Axis(_SHAFT, (0, -1, 0))
    for name, shape in moving.items():
        if name == "headframe_sheave":
            posed = shape.rotate(
                Axis((69, 0, 104 + params.sheave_lift), (0, -1, 0)), state["sheave_angle"]
            )
        elif "piston_crosshead" in name or "crosshead_pin" in name:
            side = name.split("_")[0]
            posed = Pos(state[side]["slider"], 0, 0) * shape
        elif "connecting_rod" in name:
            side = name.split("_")[0]
            posed = shape.rotate(Axis((0, 0, 44), (0, -1, 0)), state[side]["rod_angle"])
            posed = Pos(state[side]["slider"], 0, 0) * posed
        else:
            posed = shape.rotate(main_axis, params.angle)
        posed.label, posed.color = name, shape.color
        parts[name] = posed

    cord = _cord(params.sheave_lift)
    parts["reference_flexible_cord"] = _label(cord, "reference_flexible_cord", _CREAM)
    wx, wz = state["rope_witness"]
    parts["reference_rope_witness"] = _label(
        Pos(wx, 0, wz) * Sphere(0.9), "reference_rope_witness", _OCHRE
    )
    return parts


def _render_poses(params, steps=24):
    """Rigid transforms from the exported pose; one full turn and its reverse."""
    import numpy as np

    original = _motion(params)

    def transform(angle=0, centre=(0, 0, 0), shift=(0, 0, 0)):
        t = math.radians(angle)
        c, s = math.cos(t), math.sin(t)
        rotation = np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
        matrix = np.eye(4)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = np.array(centre) - rotation @ centre + shift
        return matrix.tolist()

    frames = []
    indices = list(range(steps + 1)) + list(range(steps - 1, -1, -1))
    names = _moving_neutral(params.crank_radius, params.rod_length, params.fit, params.sheave_lift)
    for i in indices:
        angle = params.angle + i * 360 / steps
        state = _motion(params.model_copy(update={"angle": angle}))
        data = {}
        for name in names:
            if name == "headframe_sheave":
                matrix = transform(
                    state["sheave_angle"] - original["sheave_angle"],
                    (69, 0, 104 + params.sheave_lift),
                )
            elif "piston_crosshead" in name or "crosshead_pin" in name:
                side = name.split("_")[0]
                matrix = transform(shift=(state[side]["slider"] - original[side]["slider"], 0, 0))
            elif "connecting_rod" in name:
                side = name.split("_")[0]
                matrix = transform(
                    state[side]["rod_angle"] - original[side]["rod_angle"],
                    (original[side]["slider"], 0, 44),
                    (state[side]["slider"] - original[side]["slider"], 0, 0),
                )
            else:
                matrix = transform(angle - params.angle, _SHAFT)
            data[name] = matrix
        wx, wz = state["rope_witness"]
        ox, oz = original["rope_witness"]
        data["reference_rope_witness"] = transform(shift=(wx - ox, 0, wz - oz))
        frames.append(data)
    return frames


# Text of the review sheet (cadkit.render); the views and the scene are cadkit's defaults.
presentation = {
    "sheet": {
        "title": "NA SZYCHCIE OD 1915",
        "subtitle": "{name}  /  Full form  /  {version}  /  Engineering concept",
        "caption": "Cutaway engine house / exposed twin slider-cranks / continuous cord",
        "footer": (
            "180 x 90 x 120 mm  |  Iron / ochre / brick / cream  |  Physical prototype required"
        ),
    }
}

variants = {"full": Params()}
process = FDM
version = "0.1.0"
model = Model("carnall", version, variants, process, build)
