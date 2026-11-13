"""Fala (The Wave): the moving system of the Nikisz terrace, for the motion proof.

Eight houses stand on a corkscrew cam (drive A of the look brief). Each house is carried by a
printed sled: two crowned pads rest on the cam, and two more pass under it, so the cam can
neither drop a house nor leave it behind. A fixed blade in front of the cam and the rear
panel behind it keep the house upright: the house's weight tips it forward onto a bead high
on the blade, inside the house, and back onto the panel, so at ordinary friction the guide is
seated by gravity and does not rattle in its clearance; stops limit how far a house can leave
those seats. The blade passes up through the house's ground block and, with a fin on the rear
panel, holds the house along the street at pavement level: the pavement stays one ribbon
while the house rises and leans. A handwheel turns the cam through a 3:1 gear pair.

Axes: X along the street (handwheel at +X), Y depth (the viewer is at -Y), Z up, pavement at
rest on Z = 0. Lengths in mm, angles in degrees. The houses are plain volumes (`_massing`);
everything that moves them is real geometry with every fit a named parameter.
"""

import math
from functools import lru_cache

import numpy as np
from build123d import Color, Location
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import U1
from pydantic import Field, model_validator

from fala import _massing as massing
from fala import _parts as parts
from fala import _wave as wave
from fala._layout import layout


class Params(BaseParams):
    """Every dimension that may need tuning after test prints; mm and degrees."""

    turn: float = Field(default=0.0, ge=-36000, le=36000)  # crank angle

    # the street and its wave
    houses: int = Field(default=8, ge=4, le=10)
    pitch: float = Field(default=22.0, ge=18, le=26)
    amplitude: float = Field(default=3.5, ge=2, le=4.5)
    waves: float = Field(default=0.85, ge=0.6, le=1.2)  # wavelengths along the street
    ratio: int = Field(default=3, ge=1, le=4)  # crank turns per turn of the cam

    # cam and axle
    cam_radius: float = Field(default=8.0, ge=7, le=10)
    axle: float = Field(default=4.0, ge=3, le=5)  # bought steel rod
    axle_length: float = Field(default=200.0, ge=180, le=220)
    axle_fit: float = Field(default=0.3, ge=0.15, le=0.6)  # cam bore minus axle
    hub: float = Field(default=10.0, ge=8, le=12)
    cam_gap: float = Field(default=8.0, ge=0.8, le=10)  # the sled's plate to the cam's sweep

    # sled
    sled_width: float = Field(default=19.0, ge=16, le=20)
    plate: float = Field(default=2.5, ge=2, le=3.2)
    tongue: float = Field(default=7.2, ge=5, le=8)
    bar: float = Field(default=3.5, ge=3.5, le=6)  # from the top of the sled to the pad nose
    pad_span: float = Field(default=16.0, ge=12, le=17)
    pad_width: float = Field(default=3.0, ge=2, le=4)
    pad_crown: float = Field(default=12.0, ge=6, le=30)
    pad_relief: float = Field(default=0.5, ge=0.3, le=1)
    capture: float = Field(default=0.35, ge=0.25, le=0.8)  # gap at the two lower pads
    capture_span: float = Field(default=15.0, ge=12, le=16)  # between the two lower pads
    capture_width: float = Field(default=3.0, ge=2.4, le=4)  # of each lower pad's arm
    arm: float = Field(default=3.5, ge=3, le=5)
    arm_width: float = Field(default=4.0, ge=3, le=5)  # the centre arm, to the rear panel

    # the guide: a blade in front of the sled, the rear panel behind it
    blade_front: float = Field(default=2.2, ge=2, le=6)
    blade: float = Field(default=2.6, ge=2, le=3.5)
    blade_width: float = Field(default=8.0, ge=6, le=9)
    blade_tip: float = Field(default=4.0, ge=4, le=9)  # width of a blade above the block's lands
    bead: float = Field(default=8.0, ge=-2, le=18)  # height of the blade's beads, in the house
    guide_gap: float = Field(default=0.4, ge=0.2, le=0.8)  # free play of a sled, front to back
    stop_gap: float = Field(default=0.5, ge=0.3, le=1.0)  # how far a guide point can leave its seat
    pivot_gap: float = Field(default=0.3, ge=0.15, le=0.6)  # block land minus blade, along X
    fin: float = Field(default=2.5, ge=2, le=3.5)  # rear locating fin, front to back
    fin_width: float = Field(default=6.0, ge=5, le=8)
    pivot_drop: float = Field(default=1.5, ge=0.5, le=3)  # pivot below the pavement

    # ground block and the fixed rim around the street
    block: float = Field(default=12.5, ge=10, le=14)
    block_front: float = Field(default=-16.0, ge=-20, le=-12)
    block_back: float = Field(default=34.5, ge=33.5, le=37)
    joint: float = Field(default=0.8, ge=0.6, le=1.5)  # pavement joint between two houses
    joint_flare: float = Field(default=0.6, ge=0.3, le=1.2)  # extra joint below the lap
    lap: float = Field(default=2.0, ge=1.4, le=3)
    lap_gap: float = Field(default=0.6, ge=0.4, le=1)
    lap_floor: float = Field(default=2.0, ge=1.8, le=4)  # thickness of the lower lap
    jog: float = Field(default=1.6, ge=1.2, le=2)  # sideways step of the joint behind the facades
    rim: float = Field(default=6.0, ge=4.5, le=7.5)  # fixed front wall below the pavement
    end_gap: float = Field(default=2.4, ge=2, le=4)  # street end to the wall beside it
    end_reach: float = Field(default=4.4, ge=3.5, le=6)  # end pavement past the last joint line

    # gears and crank
    module: float = Field(default=1.0, ge=0.8, le=1.25)
    pinion_teeth: int = Field(default=11, ge=10, le=14)
    shift: float = Field(default=0.4, ge=0.2, le=0.5)
    backlash: float = Field(default=0.1, ge=0.05, le=0.2)
    gear_face: float = Field(default=6.0, ge=4, le=8)
    crank_fit: float = Field(default=0.3, ge=0.15, le=0.6)
    boss: float = Field(default=3.0, ge=2, le=5)
    wheel: float = Field(default=38.0, ge=30, le=44)
    wheel_width: float = Field(default=5.0, ge=4, le=7)
    knob: float = Field(default=11.0, ge=8, le=14)
    knob_pin: float = Field(default=3.4, ge=3, le=4)
    knob_radius: float = Field(default=14.5, ge=10, le=18)

    # base
    base_height: float = Field(default=46.0, ge=44, le=52)
    wall: float = Field(default=2.6, ge=2.4, le=4)
    end_wall: float = Field(default=4.0, ge=3.5, le=6)
    shell: float = Field(default=2.4, ge=1.6, le=3)
    wall_height: float = Field(default=8.0, ge=4, le=12)  # low wall at the -X end
    engine_height: float = Field(default=21.0, ge=12, le=30)  # engine house at the +X end

    @model_validator(mode="after")
    def _check(self):
        L = layout(self)
        slope = L.cam.eccentricity * L.cam.k
        swing = lambda depth: depth * 2 * slope * math.sin(L.cam.k * self.pitch / 2)
        checks = {
            "wall between the cam's surface and its bore is under 1.6 mm": self.cam_radius
            - self.amplitude
            - (self.axle + self.axle_fit) / 2
            >= 1.6,
            "pads stand outside the sled": self.pad_span + self.pad_width <= self.sled_width,
            "floor is under 3 mm": L.floor_z + self.base_height >= 3,
            "sleds touch at full lean": self.pitch - self.sled_width - swing(L.pivot_z - L.pad_z)
            >= 0.6,
            "capturing arms touch at full lean": self.pitch
            - self.capture_span
            - self.capture_width
            - swing(L.pivot_z - L.arm_z)
            >= 1,
            "lower pads stand outside the sled": self.capture_span + self.capture_width
            <= self.sled_width,
            "centre arm runs into the lower pads' arms": self.capture_span
            - self.capture_width
            - self.arm_width
            >= 3,
            "pavement joint closes": self.joint - swing(L.pivot_z - L.block_z / 2) - self.pivot_gap
            >= 0.1,
            "lap is shorter than the joint": self.lap - self.joint >= 0.8,
            "rim does not cover the ground block": self.block >= self.rim + self.amplitude + 1.5,
            "crank bore breaks out of the end wall": L.crank_z + parts.SHAFT / 2 + 3 <= L.rim_z + 6
            and L.crank_y - parts.SHAFT / 2 - 3 >= L.wall_y,
            "axle does not reach both end walls": L.axle_x0 <= L.wall_x0 - 2.5,
            "guide slot breaks into the low house's roof": massing.slot_top(self)
            <= massing.B_EAVES - 1.0,
            "open joint between two ground blocks shows over the rim": L.block_z
            + self.lap_floor
            + self.amplitude * math.hypot(1.0, L.cam.k * self.pitch / 2)
            + 0.75
            <= L.rim_z,
        }
        failed = [text for text, ok in checks.items() if not ok]
        if failed:
            raise ValueError("; ".join(failed))
        return self


COLOURS = {
    "base": "#26262A",
    "rear_panel": "#33333A",
    "cam": "#E9E2D0",
    "pinion": "#E9E2D0",
    "handwheel": "#26262A",
    "knob": "#C4161C",
    "sled": "#C4161C",
    "house": "#70392B",
    "reference": "#9DA5A8",
}


@lru_cache(maxsize=8)
def _rest(params: Params) -> dict:
    """Every solid for the street at rest and the crank at turn 0; units about X = 0."""
    return {
        "base": parts.base(params),
        "rear_panel": parts.rear_panel(params),
        "cam": parts.cam(params),
        "pinion": parts.pinion(params),
        "handwheel": parts.handwheel(params),
        "knob": parts.knob(params),
        "sled": parts.sled(params),
        **{
            f"house_{kind}": massing.house(params, kind)
            for kind in sorted({massing.kind(params, i) for i in range(params.houses)})
        },
        "reference_axle": parts.axle(params),
    }


def _placed(shape, matrix, name: str):
    moved = Location(_gp(matrix)) * shape
    moved.label = name
    colour = COLOURS[name.split("_")[0] if not name.startswith("rear") else "rear_panel"]
    moved.color = Color(colour)
    return moved


def _gp(matrix):
    from OCP.gp import gp_Trsf

    trsf = gp_Trsf()
    m = np.asarray(matrix, float)
    trsf.SetValues(*m[0], *m[1], *m[2])
    return trsf


def _matrices(params: Params, turn: float | None = None) -> dict:
    """World transform of every part from its rest solid, at the model's turn or at `turn`."""
    L = layout(params)
    angle = params.turn if turn is None else turn
    cam = wave.turn_matrix(wave.cam_angle(params, angle), L.cam_y, L.cam_z)
    crank = wave.turn_matrix(angle, L.crank_y, L.crank_z)
    place = np.eye(4)
    place[1, 3], place[2, 3] = L.cam_y, L.cam_z
    to_crank = np.eye(4)
    to_crank[1, 3], to_crank[2, 3] = L.crank_y, L.crank_z
    result = {
        "base": np.eye(4),
        "rear_panel": np.eye(4),
        "cam": cam @ place,
        "pinion": crank @ to_crank,
        "handwheel": crank @ to_crank,
        "knob": crank @ to_crank,
        "reference_axle": np.eye(4),
    }
    for i in range(params.houses):
        unit = wave.unit_matrix(params, i, angle)
        result[f"sled_{i + 1}"] = unit
        result[f"house_{i + 1}"] = unit
    return result


def build(params: Params) -> dict:
    """The whole moving system at `params.turn`; every printed part is one named solid."""
    rest = _rest(params.model_copy(update={"turn": 0.0}))
    built = {}
    for name, matrix in _matrices(params).items():
        if name.startswith("sled_"):
            source = rest["sled"]
        elif name.startswith("house_"):
            source = rest[f"house_{massing.kind(params, int(name.split('_')[1]) - 1)}"]
        else:
            source = rest[name]
        built[name] = _placed(source, matrix, name)
    return built


def moving_parts(params: Params) -> set[str]:
    """Names of everything that moves when the crank turns."""
    return {
        name for name in _matrices(params) if name not in ("base", "rear_panel", "reference_axle")
    }


FRAMES = 72  # animation poses for one pass of the wave: one turn of the cam, three of the crank


def _render_poses(params: Params, steps: int = FRAMES) -> list:
    """Rigid transforms of the moving parts from the built pose, through one turn of the cam."""
    start = _matrices(params)
    inverse = {name: np.linalg.inv(matrix) for name, matrix in start.items()}
    moving = moving_parts(params)
    frames = []
    for index in range(steps + 1):
        turn = params.turn + 360.0 * params.ratio * index / steps
        now = _matrices(params, turn)
        frames.append({name: (now[name] @ inverse[name]).tolist() for name in sorted(moving)})
    return frames


variants = {"nikisz": Params()}
process = U1
version = "0.4.0"
model = Model("fala", version, variants, process, build)


def presentation(params: Params) -> dict:
    """Render settings for cadkit.render: the stills of the motion proof and the looping film."""
    L = layout(params)
    frame = {"box": ((L.out_x0, L.front_y, -params.base_height), (L.wheel_x + 16, L.back_y, 48))}
    hero = {"azimuth": 28, "elevation": 17, "size": (1600, 1000), "margin": 1.04, **frame}
    bare = ("house_", "rear_panel")
    coal = {"roughness": 0.55}
    views = {
        "hero": dict(hero),
        "front": {**hero, "azimuth": 0, "elevation": 6},
        "back": {**hero, "azimuth": 152, "elevation": 22, "hide": ("rear_panel",)},
        "top": {**hero, "azimuth": 10, "elevation": 55},
        "mechanism": {**hero, "azimuth": 150, "elevation": 30, "hide": bare},
        "mechanism_front": {**hero, "azimuth": 20, "elevation": 35, "hide": ("house_",)},
    }
    for index in range(4):  # the wave at four phases of one pass, for the filmstrip
        views[f"phase_{index}"] = {
            **hero,
            "azimuth": 0,
            "elevation": 8,
            "size": (1500, 520),
            "frame": index * FRAMES // 4,
            "box": ((L.out_x0, L.front_y, -14), (L.wheel_x + 16, L.back_y, 48)),
        }
    return {
        "sheet": {
            "title": "FALA",
            "subtitle": "{name}  /  Motion proof  /  {version}  /  real mechanism, plain house volumes",
            "caption": "Drive A, corkscrew: three turns of the handwheel pass one wave along the street",
            "footer": "Motion proof  |  Physical prototype required",
        },
        "views": views,
        "animation": {
            "view": "hero",
            "size": (800, 500),
            "samples": 16,
            "frame_ms": 80,
            "loop": True,
        },
        # the bare mechanism from the back: no houses, the rear panel taken off
        "films": {
            "mechanism": {
                "view": "mechanism",
                "hide": bare,
                "size": (800, 500),
                "samples": 16,
                "frame_ms": 80,
                "loop": True,
            },
        },
        "light_target": (0, 0.01, 0.0),
        "materials": {
            "house_": {"roughness": 0.75},
            "sled_": {"roughness": 0.6},
            "base": coal,
            "rear_panel": coal,
            "handwheel": coal,
            "reference_": {"roughness": 0.3},
            "": {"roughness": 0.6},
        },
    }
