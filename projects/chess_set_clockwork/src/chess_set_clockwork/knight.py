"""Clockwork knight: the head rears when the piece is lifted and bows when it is set down.

Built like a skeleton clock: two side plates joined by pillars, with the moving parts on steel
arbors between them. A weighted plunger in the base stays on the board through the first
3 mm of a lift. Its rack turns a pinion; the chest wheel on the same arbor turns the mane,
which is a slice of a larger gear and one part with the head. Setting the piece down pushes
the plunger home and the head bows again. Steel pins turn in the plates; the red jewels are
those bearings.

Axes: X towards the tail (the horse faces -X), Y across the piece (the horse's left side is
-Y, the side the concept picture shows), Z up, the board at Z = 0. Lengths in mm, angles in
degrees, counter-clockwise in the side view seen from -Y. Every fit is a named parameter.
"""

import math
from functools import lru_cache

import numpy as np
from build123d import Color, Pos
from cadkit.features.motion import smooth_step
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import U1
from pydantic import Field, model_validator

from chess_set_clockwork import _knight_parts as parts
from chess_set_clockwork._knight_layout import layout, pose
from chess_set_clockwork._shared import turned


class Params(BaseParams):
    """Every dimension that may need tuning after test prints; mm and degrees."""

    lift: float = Field(default=0.0, ge=0, le=40)  # height of the piece above the board

    # base
    base: float = Field(default=35.0, ge=32, le=40)  # diameter of the flange
    drum: float = Field(default=31.0, ge=29, le=36)
    flange_height: float = Field(default=4.5, ge=3, le=6)
    base_height: float = Field(default=8.5, ge=8.5, le=12)
    base_chamfer: float = Field(default=0.6, ge=0.3, le=1)
    studs: int = Field(default=12, ge=0, le=16)
    stud: float = Field(default=1.0, ge=0.6, le=1.4)  # radius

    # across the piece
    gap: float = Field(default=10.0, ge=9.6, le=12)  # between the plates
    plate: float = Field(default=3.0, ge=2.4, le=4)
    moving: float = Field(default=9.0, ge=8, le=10)  # thickness of every moving part
    shoulder: float = Field(default=0.3, ge=0.2, le=0.5)  # bearing rings inside the plates
    shoulder_ring: float = Field(default=2.6, ge=2, le=3.2)  # their radius

    # the train
    module: float = Field(default=1.0, ge=0.8, le=1.25)
    pinion_teeth: int = Field(default=10, ge=9, le=12)
    wheel_teeth: int = Field(default=20, ge=18, le=24)
    mane_teeth: int = Field(default=24, ge=22, le=28)  # of the whole gear the mane is cut from
    mane_first: int = Field(default=-7, ge=-9, le=-6)  # lowest tooth kept, counted from +X
    mane_last: int = Field(default=5, ge=3, le=6)  # highest tooth kept
    shift: float = Field(default=0.4, ge=0.2, le=0.5)  # profile shift of the pinion
    backlash: float = Field(default=0.12, ge=0.05, le=0.2)
    wheel_face: float = Field(default=4.0, ge=3, le=5)
    travel: float = Field(default=3.0, ge=2, le=4)  # of the plunger

    # where the arbors stand
    wheel_x: float = Field(default=2.0, ge=0, le=4)
    wheel_clear: float = Field(default=1.0, ge=0.6, le=3)  # wheel's teeth above the base
    head_x: float = Field(default=-0.5, ge=-4, le=2)

    # steel: cylindrical pins, ISO 2338 nominal sizes (verify against the supplier's sheet)
    pin: float = Field(default=2.0, ge=1.5, le=3)  # arbors, pillars and the banking pin
    pin_length: float = Field(default=16.0, ge=14, le=20)
    pin_run: float = Field(default=0.3, ge=0.15, le=0.5)  # bore minus pin where it turns
    pin_grip: float = Field(default=0.1, ge=0, le=0.2)  # bore minus pin where it is pressed in
    weight: float = Field(default=6.0, ge=5, le=6)  # steel pin lying in the plunger
    weight_length: float = Field(default=18.0, ge=12, le=20)
    weight_fit: float = Field(default=0.2, ge=0.1, le=0.4)
    weight_floor: float = Field(default=0.9, ge=0.8, le=1.5)  # plastic under the weight

    # plunger
    bar_length: float = Field(default=21.0, ge=18, le=23)
    bar_height: float = Field(default=8.0, ge=7, le=9)
    ear: float = Field(default=0.8, ge=0.6, le=1.2)  # how far each retaining ear stands out
    ear_height: float = Field(default=2.0, ge=1.5, le=3)
    slide: float = Field(default=0.3, ge=0.15, le=0.5)  # clearance to the slot, each side
    rack_teeth: int = Field(default=3, ge=2, le=4)
    rack_back: float = Field(default=2.6, ge=2, le=3.5)  # solid behind the teeth
    rack_top: float = Field(default=4.0, ge=3.2, le=4.8)  # top tooth above the pinion's axis
    rack_relief: float = Field(default=0.4, ge=0.2, le=0.8)  # rack clear of the wheel's face

    # frame
    strap: float = Field(default=3.6, ge=3, le=4.5)
    boss: float = Field(default=4.2, ge=3.6, le=5)  # radius around an arbor
    post: float = Field(default=2.25, ge=2, le=2.8)  # radius of a pillar's post
    bank_radius: float = Field(default=6.0, ge=5.5, le=7)  # banking pin from the head's arbor
    bank_margin: float = Field(default=3.0, ge=2.5, le=5)  # free turn past each end of the swing
    bank_play: float = Field(default=0.25, ge=0.15, le=0.5)  # slot to pin, each side
    jewel: float = Field(default=5.2, ge=4, le=6)  # outer diameter
    jewel_depth: float = Field(default=0.8, ge=0.4, le=1.2)
    foot_x: float = Field(default=10.0, ge=9, le=11)
    tenon: float = Field(default=4.0, ge=3.6, le=5)  # across both prongs
    tenon_thick: float = Field(default=2.2, ge=1.8, le=2.6)
    tenon_fit: float = Field(default=0.15, ge=0.1, le=0.3)  # clearance in the mortise, each side
    tenon_tip: float = Field(default=0.5, ge=0.3, le=1)  # end of a prong above the board
    prong: float = Field(default=1.4, ge=1.2, le=1.7)
    barb: float = Field(default=0.5, ge=0.3, le=0.7)
    catch: float = Field(default=1.6, ge=1.2, le=2.4)  # height of the step the barbs hold on
    timing: float = Field(default=1.4, ge=1, le=1.8)  # diameter of the timing hole
    timing_radius: float = Field(default=9.0, ge=8.5, le=9.5)  # timing hole from the head's arbor

    # head and wheel
    hub: float = Field(default=3.4, ge=3, le=4)  # radius around the head's arbor
    mane_rim: float = Field(default=3.4, ge=1.8, le=4)  # solid below the mane's teeth
    mane_window: float = Field(default=1.4, ge=1, le=3)  # solid around the hub, inside the windows
    mane_open: float = Field(default=62.0, ge=30, le=70)  # upper end of the upper window
    bank_web: float = Field(default=14.0, ge=6, le=14)  # solid past each end of the banking slot
    wheel_hub: float = Field(default=3.2, ge=2.8, le=4)
    wheel_rim: float = Field(default=1.5, ge=1.2, le=2.5)  # solid below the wheel's teeth
    wheel_web: float = Field(default=0.8, ge=0.6, le=1.2)  # behind the spokes
    spokes: int = Field(default=6, ge=4, le=8)
    spoke: float = Field(default=1.6, ge=1.2, le=2.4)

    @model_validator(mode="after")
    def _check(self):
        L = layout(self)
        rack_tip = L.rack_x + self.module * (1 - self.shift)
        checks = {
            "moving parts do not fit between the bearing rings": self.gap
            - 2 * self.shoulder
            - self.moving
            >= 0.2,
            "pins do not span the plates": self.pin_length <= 2 * L.outer + 0.01
            and self.pin_length >= 2 * L.outer - 1.0,
            "wheel reaches past the drum": abs(L.wheel[0]) + L.wheel_tip <= self.drum / 2,
            "rack would reach the mane": L.rack_high + 0.8 <= L.pivot[1] - L.mane_tip,
            "wheel cannot come in under the rear post": L.wheel[1] + L.wheel_tip + 0.2
            <= L.rear_post[1] - self.post,
            "timing hole leaves no wall": self.timing_radius - self.timing / 2
            >= self.bank_radius + self.pin / 2 + self.bank_play + 0.8
            and self.timing_radius + self.timing / 2 <= L.mane_root - 0.8,
            "plunger stands above the base": self.bar_height <= self.base_height - 0.3,
            "ledge for the ears is too low to print": L.ledge >= 1.2,
            "weight breaks through the bar": self.weight_floor * 2 + self.weight + self.weight_fit
            <= self.bar_height
            and self.weight + self.weight_fit + 2.4 <= self.moving,
            "weight is longer than the bar": self.weight_length + 1.5 <= self.bar_length,
            "slot breaks into the mortises": L.outer - self.tenon_thick - self.tenon_fit
            >= L.half + self.slide + 0.8,
            "mortise breaks out of the drum": math.hypot(
                self.foot_x + self.tenon / 2 + self.tenon_fit, L.outer + self.tenon_fit
            )
            <= self.drum / 2 - 0.8,
            "prongs cannot spring past their barbs": self.tenon - 2 * self.prong
            >= 2 * self.barb + 0.1,
            "banking slot leaves no wall": self.bank_radius - self.pin / 2 - self.bank_play
            >= self.hub + 0.6
            and self.bank_radius + self.pin / 2 + self.bank_play <= L.mane_root - 1.0,
            "rack does not clear the pinion's wheel": rack_tip <= L.wheel[0],
            "posts stand in the way of the wheel or the mane": min(
                math.dist(L.front_post, L.wheel) - L.wheel_tip,
                math.dist(L.rear_post, L.wheel) - L.wheel_tip,
                math.dist(L.rear_post, L.pivot) - L.mane_tip,
            )
            >= self.post + 0.5,
        }
        failed = [text for text, ok in checks.items() if not ok]
        if failed:
            raise ValueError("; ".join(failed))
        return self


COLOURS = {
    "base": "#C9A227",
    "plate": "#C9A227",
    "head": "#D8B13A",
    "wheel": "#B98F2B",
    "plunger": "#3B3B42",
    "jewel": "#B01030",
    "reference": "#9DA5A8",
}


@lru_cache(maxsize=8)
def _rest(params: "Params") -> dict:
    """Every solid with the piece standing on the board: plunger home, head bowed."""
    L = layout(params)
    built = {
        "base": parts.base(params),
        "plate_left": parts.plate(params, -1),
        "plate_right": parts.plate(params, 1),
        "wheel": parts.wheel(params),
        "head": parts.head(params),
        "plunger": parts.plunger(params),
    }
    for arbor, centre in (("head", L.pivot), ("wheel", L.wheel)):
        for name, side in (("left", -1), ("right", 1)):
            built[f"jewel_{arbor}_{name}"] = parts.jewel(params, centre, side)
        built[f"reference_arbor_{arbor}"] = parts.pin(params, centre)
    built["reference_pillar_front"] = parts.pin(params, L.front_post)
    built["reference_pillar_rear"] = parts.pin(params, L.rear_post)
    built["reference_banking_pin"] = parts.pin(params, L.banking)
    built["reference_weight"] = parts.steel_weight(params)
    return built


def moving_parts(params: "Params") -> dict:
    """What each moving part does: 'head' and 'wheel' turn on their arbors, 'plunger' slides."""
    return {
        "head": "head",
        "reference_arbor_head": "head",
        "wheel": "wheel",
        "reference_arbor_wheel": "wheel",
        "plunger": "plunger",
        "reference_weight": "plunger",
    }


def _posed(params: "Params", lift: float) -> dict:
    """Every part for the piece held `lift` above the board."""
    L = layout(params)
    at = pose(params, lift)
    motion = moving_parts(params)
    built = {}
    for name, shape in _rest(params.model_copy(update={"lift": 0.0})).items():
        kind = motion.get(name)
        if kind == "head":
            shape = turned(shape, L.pivot, at.head)
        elif kind == "wheel":
            shape = turned(shape, L.wheel, at.wheel)
        rise = lift - at.drop if kind == "plunger" else lift
        moved = Pos(0, 0, rise) * shape if rise else shape
        moved.label = name
        moved.color = Color(COLOURS[name.split("_")[0]])
        built[name] = moved
    return built


def build(params: "Params") -> dict:
    """The knight held `params.lift` above the board; every printed part is one named solid."""
    return _posed(params, params.lift)


def _matrix(params: "Params", name: str, lift: float) -> np.ndarray:
    """World transform of a part from its rest solid, for the piece held `lift` up."""
    L = layout(params)
    at = pose(params, lift)
    kind = moving_parts(params).get(name)
    matrix = np.eye(4)
    if kind in ("head", "wheel"):
        (x, z), angle = (L.pivot, at.head) if kind == "head" else (L.wheel, at.wheel)
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        matrix[0, 0], matrix[0, 2], matrix[2, 0], matrix[2, 2] = c, -s, s, c
        matrix[0, 3] = x - c * x + s * z
        matrix[2, 3] = z - s * x - c * z
    matrix[2, 3] += lift - at.drop if kind == "plunger" else lift
    return matrix


LIFT = 9.0  # how high the film lifts the piece
FRAMES = 48
_FILM = (6, 16, 8, 16)  # frames standing, going up, held up, coming down; the rest standing


def _film_lift(index: int) -> float:
    """Height of the piece in one frame: it stands, is lifted, is held, and is set down."""
    stand, up, hold, down = _FILM
    if index < stand:
        return 0.0
    if index < stand + up:
        return LIFT * smooth_step((index - stand) / up)
    if index < stand + up + hold:
        return LIFT
    return LIFT * (1 - smooth_step((index - stand - up - hold) / down))


def _render_poses(params: "Params", steps: int = FRAMES) -> list:
    """Rigid transforms of every part from the built pose: one lift and one setting down."""
    names = list(_rest(params.model_copy(update={"lift": 0.0})))
    start = {name: np.linalg.inv(_matrix(params, name, params.lift)) for name in names}
    return [
        {name: (_matrix(params, name, _film_lift(index)) @ start[name]).tolist() for name in names}
        for index in range(steps + 1)
    ]


PLASTIC, STEEL = 1.24e-3, 7.85e-3  # g per mm3: PLA, and steel for the pins


def balance(params: "Params") -> dict:
    """Weights in grams, and how hard the head's own weight works against the plunger.

    The head is not balanced on its arbor. Its moment, carried through the train, is a force
    at the rack; `head_at_plunger` is that force in grams, positive when it holds the plunger
    up. The plunger has to be several times heavier for the head to rear on every lift.
    """
    from build123d import CenterOf

    L = layout(params)
    rest = _rest(params.model_copy(update={"lift": 0.0}))
    grams = {
        name: shape.volume * (STEEL if name.startswith("reference_") else PLASTIC)
        for name, shape in rest.items()
    }
    lever = L.pivot[0] - rest["head"].center(CenterOf.MASS).X  # positive: nose-heavy
    train = (params.wheel_teeth / params.mane_teeth) / L.pinion_radius
    plunger = grams["plunger"] + grams["reference_weight"]
    return {
        "head": grams["head"],
        "head_lever": lever,
        "head_at_plunger": grams["head"] * lever * train,
        "plunger": plunger,
        "piece": sum(grams.values()),
    }


variants = {"playing": Params()}
process = U1
version = "0.1.0"
model = Model("clockwork_knight", version, variants, process, build)


def presentation(params: "Params") -> dict:
    """Render settings for cadkit.render: stills standing and lifted, and the looping films."""
    frame = {"box": ((-23, -18, 0), (19, 18, 67))}
    hero = {"azimuth": -32, "elevation": 12, "size": (1100, 1400), "margin": 1.05, **frame}
    side = {**hero, "azimuth": 0, "elevation": 3}
    lifted = sum(_FILM[:2]) + _FILM[2] // 2  # a frame in which the piece is held up
    open_side = ("plate_left", "jewel_head_left", "jewel_wheel_left")
    film = {"size": (660, 840), "samples": 16, "frame_ms": 70, "loop": True}
    return {
        "sheet": {
            "title": "CLOCKWORK KNIGHT",
            "subtitle": "{name}  /  {version}  /  first build: real mechanism, plain surfaces",
            "caption": "The head rears through the first 3 mm of a lift and bows when set down",
            "footer": "First build  |  Not printed yet",
        },
        "views": {
            "hero": dict(hero),
            "side": dict(side),
            "side_lifted": {**side, "frame": lifted},
            "hero_lifted": {**hero, "frame": lifted},
            "front": {**hero, "azimuth": -90, "elevation": 6},
            "back": {**hero, "azimuth": 148, "elevation": 14},
            "top": {**hero, "azimuth": -20, "elevation": 55},
            "mechanism": {**side, "hide": open_side},
            "mechanism_lifted": {**side, "hide": open_side, "frame": lifted},
        },
        "animation": {"view": "hero", **film},
        # the left plate taken off: rack, pinion, wheel and mane at work
        "films": {"mechanism": {"view": "mechanism", "hide": open_side, **film}},
        "light_target": (0, 0, 0.03),
        "materials": {
            "jewel_": {"roughness": 0.15, "coat": 0.6},
            "reference_": {"roughness": 0.25},
            "plunger": {"roughness": 0.6},
            "": {"roughness": 0.38, "coat": 0.25},
        },
    }
