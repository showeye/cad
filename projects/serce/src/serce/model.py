"""Serce na węgiel: a heart of coal that opens to show a Silesian kitchen. Motion proof.

Origin at the heart's hidden tip, z up, front is -y, the viewer's left is -x. Units: mm, degrees.

This stage is the bare moving system of opening A (wings): the real faceted Bryła heart split
into two wings and a back half, the hinges, and the whole drive in the base. The room is a
stand-in. Every fit and clearance is a parameter. `turn` poses the model: 0 closed, 180 open.
"""

import math
from functools import lru_cache

import numpy as np
from build123d import Axis, Pos
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import U1
from pydantic import Field, model_validator

from serce import _base as base
from serce import _heart as heart
from serce import _kinematics as kin
from serce import _room as room
from serce import _shell as shell
from serce._solid import cut, named

COAL = "#17171A"
COAL_MATTE = "#222226"
HONEY = "#EDAE1C"
BONE = "#ECE5D2"
TILE = "#B4502A"
STEEL = "#8C97A1"
COLOURS = {"coal": COAL, "coal_matte": COAL_MATTE, "honey": HONEY, "bone": BONE, "tile": TILE}


class Params(BaseParams):
    """Pose, fits and mechanism dimensions. The heart's form is fixed by the look brief."""

    # pose
    turn: float = Field(default=0, ge=-3600, le=3600, description="cam angle; 0 closed, 180 open")

    # shell
    wall: float = Field(default=2.2, ge=1.6, le=3.0, description="coal wall")
    lining: float = Field(default=1.2, ge=0.8, le=2.0, description="honey lining")
    seam_gap: float = Field(default=0.3, ge=0.1, le=0.5, description="groove at both seams")
    seam_depth: float = Field(default=1.0, ge=0.4, le=1.6, description="depth of that groove")
    centre_clearance: float = Field(default=0.1, ge=0.0, le=0.3, description="wing to wing")
    tongue: float = Field(default=0.6, ge=0.0, le=1.2, description="lap across the centre seam")
    tongue_clear: float = Field(default=0.2, ge=0.1, le=0.4, description="lap under outer layer")
    bed_gap: float = Field(default=0.3, ge=0.2, le=0.6, description="wing foot above the coal bed")
    sill: float = Field(default=1.0, ge=0.0, le=3.0, description="coal below the lining's foot")
    stage_gap: float = Field(default=0.3, ge=0.2, le=1.0, description="room and cellar to linings")
    floor_thick: float = Field(default=1.5, ge=1.0, le=3.0, description="room floor")

    # hinge
    wing_max: float = Field(default=125, ge=90, le=135, description="swing of each wing")
    swing_margin: float = Field(default=5, ge=1, le=10, description="spare free arc at full open")
    flank_ridge: float = Field(default=18, ge=10, le=30, description="lean of each flank facet")
    hinge_radius: float = Field(default=2.0, ge=1.8, le=3.0, description="barrel radius")
    hinge_gap: float = Field(default=0.3, ge=0.15, le=0.5, description="barrel to cove, radial")
    seat_z: float = Field(default=15.0, ge=12, le=18, description="where the flanks meet the bed")
    barrel_stop: float = Field(default=6.0, ge=3, le=12, description="barrel ends below the lobe")
    knuckle: float = Field(default=15.0, ge=8, le=18, description="length of the fixed knuckle")
    heel: float = Field(default=1.4, ge=1.0, le=3.0, description="wing wall behind the seam plane")
    heel_reach: float = Field(default=2.2, ge=2.0, le=5.0, description="heel, into the heart")
    pin_d: float = Field(default=2.0, ge=1.5, le=3.0, description="steel hinge pin")
    pin_length: float = Field(default=55.0, ge=40, le=65)
    pin_clear: float = Field(default=0.15, ge=0.05, le=0.4, description="running bores, diametral")
    pin_grip: float = Field(default=3.0, ge=2.0, le=6.0, description="pin end below the pad")

    # root, lever and crank pin (one piece with the wing)
    root_radius: float = Field(default=3.0, ge=2.4, le=4.0, description="collar at the bed facet")
    journal_radius: float = Field(default=2.6, ge=2.0, le=3.6, description="root below the collar")
    collar_depth: float = Field(default=1.5, ge=1.0, le=3.0, description="collar's shoulder")
    journal_gap: float = Field(default=0.2, ge=0.1, le=0.5, description="root in its bore, radial")
    roof: float = Field(default=4.5, ge=3.0, le=8.0, description="coal bed over the levers")
    lever: float = Field(default=11.0, ge=8, le=14, description="hinge axis to crank pin")
    lever_width: float = Field(default=6.0, ge=4, le=8)
    lever_thick: float = Field(default=4.5, ge=2.4, le=5)
    lever_neck: float = Field(default=2.2, ge=1.5, le=3.0, description="arm at the root, one side")
    lever_clear: float = Field(default=0.4, ge=0.3, le=1.0, description="lever under the roof")
    crank_d: float = Field(default=5.0, ge=3, le=6, description="crank pin, printed")
    crank_len: float = Field(default=4.0, ge=3, le=8)
    keyhole: float = Field(default=197.5, ge=180, le=215, description="wing angle at insertion")
    keyhole_clear: float = Field(default=0.4, ge=0.2, le=0.8, description="lever in its keyhole")
    plug_gap: float = Field(default=0.1, ge=0.05, le=0.3, description="plug in its keyhole, a side")
    plug_drop: float = Field(
        default=0.1, ge=0.05, le=0.3, description="plug under facet and collar"
    )
    plug_lip: float = Field(default=0.6, ge=0.4, le=1.0, description="plug's head over its seat")
    plug_head: float = Field(default=1.2, ge=0.8, le=2.0, description="depth of that head")
    pad_thick: float = Field(default=1.6, ge=1.2, le=3.0, description="pin bearing under the root")
    root_boss: float = Field(default=0.3, ge=0.2, le=1.0, description="root below the lever")
    pad_gap: float = Field(default=0.3, ge=0.2, le=1.0, description="root above that bearing")

    # slider and pusher
    over_travel: float = Field(default=0.8, ge=0.4, le=2.0, description="slider past the seats")
    yoke_gap: float = Field(default=0.15, ge=0.05, le=0.4, description="play of a pin in its yoke")
    pusher_travel: float = Field(default=1.5, ge=1.0, le=4.0, description="pusher's free travel")
    yoke_clear: float = Field(default=0.5, ge=0.3, le=1.0, description="yoke plates under lever")
    plate: float = Field(default=2.4, ge=1.6, le=4.0, description="yoke plate thickness")
    slide_gap: float = Field(default=0.2, ge=0.1, le=0.5, description="slider in its guides")
    spring_preload: float = Field(default=2.5, ge=1, le=20, description="pusher spring, N")
    spring_rate: float = Field(default=3.0, ge=0.2, le=5, description="N per mm")

    # cam
    groove_radius: float = Field(default=20.9, ge=16, le=24)
    follower_d: float = Field(default=3.0, ge=2, le=4, description="steel follower pin")
    groove_clear: float = Field(default=0.3, ge=0.1, le=0.6, description="groove wider than pin")
    groove_depth: float = Field(default=2.4, ge=1.6, le=3.0)

    # base stack, top to bottom
    base_z: float = Field(default=-0.5, ge=-2, le=0, description="underside of the coal bed")
    ring_gap: float = Field(default=0.4, ge=0.2, le=0.8, description="between bed, ring and foot")
    slider_top: float = Field(default=-1.5, ge=-4, le=0)
    slider_thick: float = Field(default=3.0, ge=2, le=4)
    chassis_thick: float = Field(default=2.5, ge=2, le=4)
    cam_thick: float = Field(default=3.4, ge=2.8, le=5)
    web_thick: float = Field(default=2.6, ge=2, le=4, description="floor of the grip ring")
    ballast_thick: float = Field(default=5.0, ge=3, le=8, description="steel washer in the foot")
    foot_floor: float = Field(default=1.2, ge=0.8, le=2)
    ring_r: float = Field(default=38.0, ge=36, le=42, description="grip ring, axis to a flat")
    ring_wall: float = Field(default=3.2, ge=2.4, le=4)
    hub_r: float = Field(default=7.5, ge=6, le=8)

    # coal bed
    bed_ridge: float = Field(default=22.0, ge=10, le=24, description="half length of the ridge")
    bed_gable: float = Field(default=50.0, ge=40, le=70, description="slope of the bed's ends")
    bed_wall: float = Field(default=2.6, ge=2, le=5)
    slab_top: float = Field(default=1.0, ge=0, le=1.5, description="top of the bed's base slab")
    skirt: float = Field(default=1.1, ge=0.6, le=2.0, description="bed's rim over the ring's neck")

    # statics (assumptions of the effort model)
    friction: float = Field(default=0.3, ge=0.05, le=0.6, description="PLA on PLA")
    friction_steel: float = Field(default=0.2, ge=0.05, le=0.5, description="steel on PLA")
    hinge_friction: float = Field(default=1.0, ge=0, le=10, description="N mm per wing")
    ring_drag: float = Field(default=12.0, ge=0, le=60, description="N mm, constant")

    @model_validator(mode="after")
    def _check(self):
        groove_half = (self.follower_d + self.groove_clear) / 2
        if self.groove_radius - kin.stroke(self) / 2 - groove_half < self.hub_r + 1.3:
            raise ValueError("Cam groove cuts into the hub: raise groove_radius or shorten lever")
        if self.pusher_travel < self.over_travel + 0.2:
            raise ValueError("The pusher needs more free travel than the slider's over-travel")
        reach = self.groove_radius + kin.stroke(self) / 2 + self.follower_d / 2 + 1.5
        if reach > self.ring_r - self.ring_wall - 0.5:
            raise ValueError("Follower end of the slider does not fit inside the grip ring")
        if self.root_radius - self.journal_radius < self.journal_gap + 0.15:
            raise ValueError("The root's collar needs a shoulder wider than its running clearance")
        if self.collar_depth > self.roof - 2.0:
            raise ValueError("The collar's shoulder leaves too little of the roof under it")
        if self.plug_gap >= self.keyhole_clear:
            raise ValueError("The plug must be no wider than the lever that passes its keyhole")
        if self.heel + self.hinge_gap > self.hinge_radius - 0.2:
            raise ValueError("Heel must stay lower than the barrel, or the hinge is see-through")
        if self.tongue and self.seam_depth + self.tongue_clear > self.wall - 0.6:
            raise ValueError("No coal left in the lap behind the seam groove")
        if self.seam_depth >= self.wall:
            raise ValueError("Seam groove must be shallower than the coal wall")
        return self


MECHANISM = "#5A5A64"  # hidden printed parts; black in production, grey here to read them
MOVES_WITH_SLIDER = ("slider", "reference_follower_pin")
TURNS_WITH_RING = ("cam_disc", "grip_ring", "reference_cam_magnet", "reference_ring_magnet")
DENSITY = 1.24e-3  # g per mm³, PLA


def _key(params: Params) -> Params:
    """The parameters without the pose: the key of everything that is built once."""
    return params.model_copy(update={"turn": 0.0})


@lru_cache(maxsize=4)
def _neutral(params: Params) -> dict:
    """Every part in the closed position, named and coloured."""
    parts = {}

    def add(name, shape, colour):
        parts[name] = named(shape, name, colour)

    for name, side in heart.SIDES.items():
        wing = shell.wing(params, side)
        add(f"wing_{name}", wing["coal"], COAL)
        add(f"wing_{name}_lining", wing["lining"], HONEY)
    back = shell.back(params)
    add("back", cut(back["coal"], *base.back_insert_pockets(params), what="back"), COAL)
    add("back_lining", back["lining"], HONEY)
    add("coal_bed", base.coal_bed(params), COAL)
    for name, side in heart.SIDES.items():
        add(f"plug_{name}", base.keyhole_plug(params, side), COAL)
    add("grip_ring", base.grip_ring(params), COAL)
    add("foot", base.foot(params), COAL_MATTE)
    add("slider", base.slider(params), MECHANISM)
    add("pusher", base.pusher(params), MECHANISM)
    add("chassis", base.chassis(params), MECHANISM)
    add("cam_disc", base.cam_disc(params), MECHANISM)
    for name, (colour, solid) in room.room(params).items():
        add(name, solid, COLOURS[colour])
    for name, solid in base.hardware(params).items():
        add(f"reference_{name}", solid, STEEL)
    return parts


def _moved(shape, name, turn_from, params: Params):
    """`shape` (built closed) as it stands at params.turn."""
    hinge = heart.hinge(params)
    turn = params.turn
    if name.startswith("wing_"):
        side = heart.SIDES[name.split("_")[1]]
        angle = kin.wing_angle(params, turn)
        return shape.rotate(hinge.axis(side), side * angle) if angle else shape
    if name.startswith(MOVES_WITH_SLIDER):
        return Pos(0, kin.slider_y(params, turn) - kin.slider_y(params, turn_from), 0) * shape
    if name == "pusher":
        return Pos(0, kin.pin_y(params, turn) - kin.pin_y(params, turn_from), 0) * shape
    if name.startswith(TURNS_WITH_RING):
        return shape.rotate(Axis.Z, turn - turn_from) if (turn - turn_from) % 360 else shape
    return shape


def build(params: Params) -> dict:
    """The complete assembly at `params.turn`: every real part is one named solid."""
    key = _key(params)
    parts = {}
    for name, shape in _neutral(key).items():
        posed = _moved(shape, name, 0.0, params)
        posed.label, posed.color = name, shape.color
        parts[name] = posed
    parts["reference_spring"] = named(base.spring(params, params.turn), "reference_spring", STEEL)
    return parts


def moving_parts(params: Params) -> set[str]:
    """Names of the parts that change place when the ring turns."""
    names = set()
    for name in _neutral(_key(params)):
        if name.startswith(("wing_", "pusher", *MOVES_WITH_SLIDER, *TURNS_WITH_RING)):
            names.add(name)
    return names | {"reference_spring"}


@lru_cache(maxsize=4)
def _wing_mass(params: Params):
    """Mass in grams and centre of mass of the closed left wing."""
    neutral = _neutral(params)
    solids = [neutral["wing_left"], neutral["wing_left_lining"]]
    volume = sum(s.volume for s in solids)
    centre = sum((s.volume * np.array(tuple(s.center())) for s in solids), np.zeros(3)) / volume
    return volume * DENSITY, centre


def wing_gravity(params: Params, angle: float) -> float:
    """Torque of gravity on one wing about its hinge, N mm, positive when it helps opening."""
    mass, centre = _wing_mass(_key(params))
    hinge = heart.hinge(params)
    u = heart.V_DIR
    r = centre - np.array(hinge.origin)
    t = math.radians(-angle)  # the left wing opens by turning about +u by -angle
    r = r * math.cos(t) + np.cross(u, r) * math.sin(t) + u * (u @ r) * (1 - math.cos(t))
    weight = np.array([0.0, 0.0, -mass * kin.GRAVITY])
    return float(-(u @ np.cross(r, weight)))


def effort(params: Params, step: float = 2.0) -> dict:
    """Ring torque over a full turn in both directions: {direction: [(turn, parts dict)]}."""
    key = _key(params)
    gravity = lambda angle: wing_gravity(key, angle)
    turns = np.arange(0.0, 360.0 + step / 2, step)
    return {
        direction: [(float(t), kin.ring_torque(key, float(t), direction, gravity)) for t in turns]
        for direction in (1, -1)
    }


def _rigid(angle: float = 0.0, origin=(0, 0, 0), direction=(0, 0, 1), shift=(0, 0, 0)) -> list:
    """4x4 matrix: turn by `angle` degrees about the axis through `origin`, then move by `shift`."""
    k = np.asarray(direction, float) / np.linalg.norm(direction)
    t = math.radians(angle)
    cross = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    rotation = np.eye(3) + math.sin(t) * cross + (1 - math.cos(t)) * cross @ cross
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = np.asarray(origin) - rotation @ np.asarray(origin) + np.asarray(shift)
    return matrix.tolist()


def _render_poses(params: Params, steps: int = 72) -> list:
    """Rigid transforms of the moving parts for one full turn of the ring, from the built pose.

    The spring's change of length in the closed dwell is ignored: it rides with the pusher.
    """
    hinge = heart.hinge(params)
    names = moving_parts(params)
    start = params.turn
    frames = []
    for index in range(steps + 1):
        turn = start + 360.0 * index / steps
        at = params.model_copy(update={"turn": turn})
        swing = kin.wing_angle(at, turn) - kin.wing_angle(params, start)
        slide = kin.slider_y(at, turn) - kin.slider_y(params, start)
        push = kin.pin_y(at, turn) - kin.pin_y(params, start)
        frame = {}
        for name in sorted(names):
            if name.startswith("wing_"):
                side = heart.SIDES[name.split("_")[1]]
                axis = hinge.axis(side)
                frame[name] = _rigid(side * swing, tuple(axis.position), tuple(axis.direction))
            elif name.startswith(MOVES_WITH_SLIDER):
                frame[name] = _rigid(shift=(0, slide, 0))
            elif name in ("pusher", "reference_spring"):
                frame[name] = _rigid(shift=(0, push, 0))
            else:
                frame[name] = _rigid(turn - start)
        frames.append(frame)
    return frames


FRAMES = 72  # animation poses per turn of the ring: one every 5 degrees
STEPS = (0, 30, 80, 120, 180)  # the five steps of the opening in the look brief, ring degrees


def presentation(params: Params) -> dict:
    """Render settings for cadkit.render: the views of the motion proof and the looping film."""
    table = -base.total_height(params)
    frame = {"box": ((-68, -42, table), (68, 42, 88))}  # the open piece, so every view matches
    hero = {"azimuth": -17, "elevation": 13, "size": (1400, 1200), "margin": 1.04, **frame}
    step = {"azimuth": -14, "elevation": 12, "size": (900, 900), "margin": 1.04, **frame}
    cover = ("coal_bed", "plug_", "grip_ring", "foot", "reference_ballast", "reference_foot_pad")
    cover += ("reference_room", "back", "wing_left_lining", "wing_right_lining", "reference_tie")
    coal = {"roughness": 0.3, "coat": 0.3}
    honey = {"roughness": 0.5}
    views = {
        "hero": dict(hero),
        "open": {**hero, "frame": 180 * FRAMES // 360},
        "back": {**hero, "azimuth": 163},
        "top": {**hero, "azimuth": -20, "elevation": 42, "frame": 180 * FRAMES // 360},
        "side": {**hero, "azimuth": -90, "elevation": 8},
        # the drive with the coal bed, the ring and the foot taken away
        "mechanism": {
            "azimuth": -12,
            "elevation": 22,
            "size": (1400, 930),
            "frame": 120 * FRAMES // 360,
            "hide": (*cover, "reference_back_", "reference_leg_"),
            "margin": 1.05,
            "box": ((-42, -40, -14), (42, 40, 34)),
        },
        # the cam under the slider: chassis and wings taken away as well
        "cam": {
            "azimuth": -20,
            "elevation": 55,
            "size": (1400, 1050),
            "frame": 80 * FRAMES // 360,
            "hide": (
                *cover,
                "chassis",
                "wing_",
                "reference_hinge",
                "reference_leg",
                "reference_back_",
            ),
            "margin": 1.1,
        },
    }
    for index, turn in enumerate(STEPS):
        views[f"step_{index}"] = {**step, "frame": turn * FRAMES // 360}
    return {
        "sheet": {
            "title": "SERCE NA WĘGIEL",
            "subtitle": "{name}  /  Motion proof  /  {version}  /  bare mechanism, stand-in room",
            "caption": "Opening A, wings: half a turn of the ring opens, the next half closes",
            "footer": "84 x 77 x 108 mm closed, 133 mm wide open  |  Physical prototype required",
        },
        "views": views,
        "animation": {
            "view": "hero",
            "size": (700, 600),
            "samples": 16,
            "frame_ms": 90,
            "loop": True,
        },
        "light_target": (0, 0, 0.035),
        "materials": {
            "wing_left_lining": honey,
            "wing_right_lining": honey,
            "back_lining": honey,
            "wing_": coal,
            "back": coal,
            "coal_bed": coal,
            "plug_": coal,
            "grip_ring": coal,
            "foot": {"roughness": 0.7},
            "reference_room": honey,
            "reference_": {"roughness": 0.3},
            "": {"roughness": 0.6},
        },
    }


variants = {"honey": Params()}
process = U1
version = "0.2.0"
model = Model("serce", version, variants, process, build)
