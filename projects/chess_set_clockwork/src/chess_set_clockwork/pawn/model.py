"""Clockwork pawn: a ratchet wheel that goes on by one tooth with every move, and never back.

Built like a skeleton clock: two plates with a round-headed window, the wheel on a steel arbor
between them. A weighted plunger in the base stays on the board when the pawn is lifted; the
pawl that stands on it rides down over the next tooth and falls under it. Set down, the board
pushes the plunger home, the pawl pushes its tooth up, and the click on top of the wheel is
lifted over one tooth and falls behind it. The click holds the wheel when the pawl goes down
again, so the wheel turns one way only, as a pawn only goes forward.

Axes: X to the right in the side view (the pawl stands on that side), Y across the piece, Z
up, the board at Z = 0. Lengths in mm, angles in degrees, counter-clockwise in the side view
seen from -Y. Every fit is a named parameter.
"""

import math
from functools import lru_cache

import numpy as np
from build123d import CenterOf, Color, Pos
from cadkit.features.motion import smooth_step
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import U1
from pydantic import Field, model_validator

from chess_set_clockwork._shared import grams, turned
from chess_set_clockwork.pawn import _parts as parts
from chess_set_clockwork.pawn._layout import Pose, layout, lifting, lowering, move


class Params(BaseParams):
    """Every dimension that may need tuning after test prints; mm and degrees."""

    lift: float = Field(default=0.0, ge=0, le=40)  # height of the piece above the board

    # base
    base: float = Field(default=32.0, ge=30, le=34)  # diameter of the flange
    drum: float = Field(default=29.0, ge=27, le=31)
    flange_height: float = Field(default=4.5, ge=3, le=6)
    base_height: float = Field(default=9.0, ge=8.5, le=11)
    base_chamfer: float = Field(default=0.6, ge=0.3, le=1)
    studs: int = Field(default=12, ge=0, le=16)
    stud: float = Field(default=1.0, ge=0.6, le=1.4)  # radius

    # across the piece
    gap: float = Field(default=9.0, ge=8.6, le=10)  # between the plates
    plate: float = Field(default=2.5, ge=2.2, le=3)
    wheel_face: float = Field(default=4.0, ge=3, le=5)  # thickness of the wheel
    click_face: float = Field(default=3.0, ge=2.4, le=4)  # thickness of the click
    play: float = Field(default=0.2, ge=0.15, le=0.4)  # beside the wheel and the click, each side

    # the ratchet
    teeth: int = Field(default=16, ge=12, le=20)
    wheel_tip: float = Field(default=7.5, ge=7, le=8.4)  # radius over the teeth
    tooth: float = Field(default=1.4, ge=1.1, le=1.8)  # height of a tooth
    rake: float = Field(default=10.0, ge=0, le=15)  # undercut of a tooth's face
    land: float = Field(default=0.3, ge=0.2, le=0.5)  # flat on a tooth's tip
    nose: float = Field(default=0.3, ge=0.2, le=0.4)  # radius of the pawl's and the click's nose
    wheel_clear: float = Field(default=2.5, ge=0.6, le=3)  # wheel's teeth above the base
    travel: float = Field(default=4.5, ge=3.5, le=5)  # of the plunger
    fall_back: float = Field(default=0.5, ge=0.3, le=0.8)  # of the wheel onto the click, at a nose

    # click
    click_rise: float = Field(default=10.9, ge=10.2, le=12.5)  # its pin above the wheel's arbor
    click_teeth: int = Field(default=6, ge=5, le=7)  # teeth from the pawl's nose to the click's
    click_eye: float = Field(default=2.2, ge=2, le=2.6)  # radius round its pin
    click_arm: float = Field(default=1.6, ge=1.4, le=2.2)
    click_in: float = Field(default=12.0, ge=8, le=20)  # how far it could fall without a wheel
    arm_clear: float = Field(default=0.6, ge=0.4, le=1)  # the click's arm outside the tips
    beak: float = Field(default=34.0, ge=28, le=40)  # angle of the click's beak
    beak_off: float = Field(default=3.0, ge=2, le=6)  # a nose's upper side below the tooth's face

    # pawl
    pawl_x: float = Field(default=10.3, ge=9, le=10.4)  # where its knuckle slides up and down
    pawl_length: float = Field(default=7.0, ge=6, le=10)  # knuckle to nose
    pawl_body: float = Field(default=1.4, ge=1.2, le=2.4)  # width of its bar
    pawl_neck: float = Field(default=1.4, ge=1.2, le=1.6)
    pawl_in: float = Field(default=6.0, ge=3, le=10)  # free turn inwards from rest
    pawl_out: float = Field(default=15.0, ge=10, le=20)  # and outwards, to the socket's lips
    knuckle: float = Field(default=1.2, ge=1, le=1.5)  # radius
    knuckle_play: float = Field(default=0.2, ge=0.1, le=0.3)
    socket_wall: float = Field(default=1.0, ge=0.8, le=1.4)

    # plunger
    bar_length: float = Field(default=23.8, ge=20, le=25)
    bar_width: float = Field(default=7.0, ge=6.6, le=7.6)
    bar_height: float = Field(default=8.5, ge=7.5, le=9.5)
    ear: float = Field(default=0.8, ge=0.6, le=1.2)  # how far each retaining ear stands out
    ear_height: float = Field(default=2.0, ge=1.5, le=3)
    slide: float = Field(default=0.3, ge=0.15, le=0.5)  # clearance to the slot, each side

    # steel: cylindrical pins, ISO 2338 nominal sizes (verify against the supplier's sheet)
    pin: float = Field(default=2.0, ge=1.5, le=3)  # the wheel's arbor and the click's pin
    pin_length: float = Field(default=14.0, ge=12, le=16)
    pin_run: float = Field(default=0.3, ge=0.15, le=0.5)  # bore minus pin where it turns
    pin_grip: float = Field(default=0.1, ge=0, le=0.2)  # bore minus pin where it is pressed in
    weight: float = Field(default=5.0, ge=4, le=5)  # steel pin lying in the plunger
    weight_length: float = Field(default=22.0, ge=12, le=22)
    weight_fit: float = Field(default=0.2, ge=0.1, le=0.4)
    weight_floor: float = Field(default=0.9, ge=0.8, le=1.5)  # plastic under the weight

    # frame
    column: float = Field(default=2.6, ge=2.2, le=3.2)  # width of a column and of the arch
    column_x: float = Field(default=10.2, ge=9.6, le=10.4)  # its centre line
    strap: float = Field(default=2.4, ge=2, le=3)  # the mullion
    sill: float = Field(default=2.0, ge=1.5, le=3)  # height of the bar along the base
    boss: float = Field(default=3.2, ge=3, le=4)  # radius round the wheel's arbor
    boss_tall: float = Field(default=2.4, ge=2, le=2.6)  # inside the plate: the wheel bears on it
    crown: float = Field(default=3.0, ge=2.6, le=3.6)  # radius round the click's pin
    post: float = Field(default=2.25, ge=2, le=2.6)  # radius of the half posts beside the click
    jewel: float = Field(default=4.6, ge=4, le=5.2)  # outer diameter
    jewel_depth: float = Field(default=0.8, ge=0.4, le=1.2)
    foot_x: float = Field(default=9.5, ge=8.5, le=9.6)
    tenon: float = Field(default=4.0, ge=3.6, le=5)  # across both prongs
    tenon_thick: float = Field(default=2.2, ge=1.8, le=2.6)
    tenon_fit: float = Field(default=0.15, ge=0.1, le=0.3)  # clearance in the mortise, each side
    tenon_tip: float = Field(default=0.5, ge=0.3, le=1)  # end of a prong above the board
    prong: float = Field(default=1.4, ge=1.2, le=1.7)
    barb: float = Field(default=0.5, ge=0.3, le=0.7)
    catch: float = Field(default=1.6, ge=1.2, le=2.4)  # height of the step the barbs hold on

    # wheel
    wheel_hub: float = Field(default=2.5, ge=2.4, le=3.2)
    wheel_rim: float = Field(default=1.3, ge=1.1, le=2)  # solid below the teeth
    spokes: int = Field(default=8, ge=4, le=8)
    spoke: float = Field(default=1.0, ge=0.9, le=1.6)

    # head
    head_seat: float = Field(default=8.0, ge=6, le=9)  # width of the flat on top of a plate
    head_tenon: float = Field(default=4.0, ge=3.6, le=5)
    head_rise: float = Field(default=2.5, ge=2, le=4)  # tenon above the flat
    head_cap: float = Field(default=1.5, ge=1.2, le=2.5)  # block above the tenons
    head_collar: float = Field(default=15.0, ge=14.6, le=16)  # diameter of the round collar
    ball: float = Field(default=11.0, ge=9, le=12)  # diameter

    @model_validator(mode="after")
    def _check(self):
        L = layout(self)
        made = move(self)
        W = L.ratchet
        knuckle = L.to_wheel(L.knuckle)
        slot_end = L.bar_half + self.ear + self.slide
        out = L.pawl_home - made.swing  # the pawl's direction when it is pushed out furthest
        checks = {
            "wheel and click do not fit between the plates": L.inner
            - self.wheel_face / 2
            - self.play
            >= 1.0
            and self.click_face + 2 * self.play <= self.wheel_face + 1.0,
            "pins do not span the plates": 2 * L.outer - 1.0
            <= self.pin_length
            <= 2 * L.outer + 0.01,
            "a move does not end as it began": self.teeth % self.spokes == 0,
            "pawl does not get under the next tooth": made.under is not None
            and self.travel - made.under >= 0.3,
            "wheel does not go on by one tooth": abs(made.turned - W.pitch) < 1e-6
            and made.meets is not None
            and self.travel - made.meets >= 0.3,
            "wheel's push would lift the click or the pawl out": min(
                W.locks(L.click, L.to_wheel(L.click_pin)), W.locks(L.pawl, knuckle)
            )
            >= 3.0,
            "pawl is pushed out against the socket's lip": made.swing <= self.pawl_out - 2.0,
            "pawl does not lean towards the wheel when it is pushed out": out >= 100.0,
            "click is lifted against the head": made.lift <= 20.0,
            "click's eye or its posts reach the teeth": self.click_rise
            - max(self.click_eye, self.post)
            >= self.wheel_tip + 0.4,
            "socket cannot hold the knuckle": self.pawl_neck + 2 * self.knuckle_play
            <= 1.6 * self.knuckle,
            "socket stands out past the plunger's ear": self.pawl_x + L.socket
            <= L.bar_half + self.ear + 1e-9,
            "socket reaches the wheel or the bar": math.hypot(*knuckle) - L.socket
            >= self.wheel_tip + 0.3
            and L.knuckle[1] - L.socket >= self.bar_height,
            "wheel does not fit between the columns": self.wheel_tip + 0.5 <= L.column[0],
            "columns stand past their feet": L.column[1] <= self.foot_x + self.tenon / 2 + 1e-9,
            "wheel's spokes are too short to see": self.wheel_tip
            - self.tooth
            - self.wheel_rim
            - self.wheel_hub
            >= 1.5
            and self.wheel_hub >= (self.pin + self.pin_grip) / 2 + 1.2,
            "jewel leaves no wall in its boss": self.boss - self.jewel / 2 >= 0.8,
            "plunger stands above the base": self.bar_height <= self.base_height - 0.3,
            "ledge for the ears is too low to print": L.ledge >= 1.2,
            "weight breaks through the bar": self.weight_floor * 2 + self.weight + self.weight_fit
            <= self.bar_height
            and self.weight + self.weight_fit + 1.7 <= self.bar_width,
            "weight is longer than the bar": self.weight_length + 1.5 <= self.bar_length,
            "slot breaks into the mortises": L.outer - self.tenon_thick - self.tenon_fit
            >= L.bar_wide + self.slide + 0.8,
            "slot breaks out of the drum": math.hypot(slot_end, L.bar_wide + self.slide)
            <= self.drum / 2 - 0.9,
            "mortise breaks out of the drum": math.hypot(
                self.foot_x + self.tenon / 2 + self.tenon_fit, L.outer + self.tenon_fit
            )
            <= self.drum / 2 - 0.8,
            "prongs cannot spring past their barbs": self.tenon - 2 * self.prong
            >= 2 * self.barb + 0.1,
            "head's tenon is wider than the flat it stands on": self.head_tenon + 1.0
            <= self.head_seat
            <= self.head_collar,
            "head's collar does not cover the tenons": math.hypot(
                self.head_tenon / 2 + self.tenon_fit, L.outer
            )
            <= self.head_collar / 2 - 0.1,
        }
        failed = [text for text, ok in checks.items() if not ok]
        if failed:
            raise ValueError("; ".join(failed))
        return self


COLOURS = {
    "base": "#C9A227",
    "plate": "#C9A227",
    "head": "#C9A227",
    "wheel": "#B98F2B",
    "click": "#55555E",
    "plunger": "#3B3B42",
    "pawl": "#55555E",
    "jewel": "#B01030",
    "reference": "#9DA5A8",
}


@lru_cache(maxsize=8)
def _rest(params: "Params") -> dict:
    """Every solid with the pawn standing on the board: plunger home, pawl under its tooth."""
    L = layout(params)
    built = {
        "base": parts.base(params),
        "plate_left": parts.plate(params, -1),
        "plate_right": parts.plate(params, 1),
        "wheel": parts.wheel(params),
        "click": parts.click(params),
        "plunger": parts.plunger(params),
        "pawl": parts.pawl(params),
        "head": parts.head(params),
        "jewel_wheel_left": parts.jewel(params, -1),
        "jewel_wheel_right": parts.jewel(params, 1),
        "reference_arbor_wheel": parts.pin(params, L.wheel),
        "reference_pin_click": parts.pin(params, L.click_pin),
        "reference_weight": parts.steel_weight(params),
    }
    return built


def moving_parts(params: "Params") -> dict:
    """What each moving part does: wheel and click turn, the plunger slides with the pawl."""
    return {
        "wheel": "wheel",
        "reference_arbor_wheel": "wheel",
        "click": "click",
        "plunger": "plunger",
        "reference_weight": "plunger",
        "pawl": "pawl",
    }


def _turns(params: "Params", at: Pose) -> dict:
    """Centre and angle of every part that turns."""
    L = layout(params)
    return {
        "wheel": (L.wheel, at.wheel),
        "click": (L.click_pin, at.click),
        "pawl": (L.knuckle, at.pawl),
    }


def placed(params: "Params", at: Pose, lift: float) -> dict:
    """Every part for the pawn in pose `at`, held `lift` above the board."""
    motion = moving_parts(params)
    turns = _turns(params, at)
    built = {}
    for name, shape in _rest(params.model_copy(update={"lift": 0.0})).items():
        kind = motion.get(name)
        if kind in turns and turns[kind][1]:
            shape = turned(shape, *turns[kind])
        rise = lift - at.drop if kind in ("plunger", "pawl") else lift
        moved = Pos(0, 0, rise) * shape if rise else shape
        moved.label = name
        moved.color = Color(COLOURS[name.split("_")[0]])
        built[name] = moved
    return built


def build(params: "Params") -> dict:
    """The pawn `params.lift` above the board on its way up; every part is one named solid."""
    return placed(params, lifting(params, params.lift), params.lift)


def lowered(params: "Params", lift: float) -> dict:
    """The pawn `lift` above the board on its way down: the pawl pushes the wheel on."""
    return placed(params, lowering(params, lift), lift)


def _matrix(params: "Params", name: str, at: Pose, lift: float) -> np.ndarray:
    """World transform of a part from its rest solid, for the pawn in pose `at`, `lift` up."""
    kind = moving_parts(params).get(name)
    turn = _turns(params, at).get(kind)
    matrix = np.eye(4)
    if turn:
        (x, z), angle = turn
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        matrix[0, 0], matrix[0, 2], matrix[2, 0], matrix[2, 2] = c, -s, s, c
        matrix[0, 3] = x - c * x + s * z
        matrix[2, 3] = z - s * x - c * z
    matrix[2, 3] += lift - at.drop if kind in ("plunger", "pawl") else lift
    return matrix


def balance(params: "Params") -> dict:
    """Weights in grams, and how surely the pawl and the click fall towards the wheel.

    Both fall by their own weight. `pawl_lean` and `click_lean` are how far each one's centre
    of mass stands to the wheel's side of its pivot, in mm, at rest; `pawl_lean_out` is the
    same with the pawl pushed out as far as a tooth pushes it, where it is least. A lever
    falls as long as that is more than the friction at its pivot times the pivot's radius.
    """
    L = layout(params)
    rest = _rest(params.model_copy(update={"lift": 0.0}))
    mass = {name: grams(name, shape) for name, shape in rest.items()}
    pawl_out = turned(rest["pawl"], L.knuckle, -move(params).swing)
    return {
        "piece": sum(mass.values()),
        "printed": sum(m for name, m in mass.items() if not name.startswith("reference_")),
        "plunger": mass["plunger"] + mass["reference_weight"] + mass["pawl"],
        "pawl": mass["pawl"],
        "click": mass["click"],
        "wheel": mass["wheel"] + mass["reference_arbor_wheel"],
        "pawl_lean": L.knuckle[0] - rest["pawl"].center(CenterOf.MASS).X,
        "pawl_lean_out": L.knuckle[0] - pawl_out.center(CenterOf.MASS).X,
        "click_lean": L.click_pin[0] - rest["click"].center(CenterOf.MASS).X,
    }


variants = {"playing": Params()}
process = U1
version = "0.1.0"
model = Model("clockwork_pawn", version, variants, process, build)


# ---------------------------------------------------------------- film
LIFT = 9.0  # how high the film lifts the pawn
MOVES = 2  # the wheel has sixteen teeth and eight spokes: after two moves it looks the same
_FILM = (6, 14, 6, 14, 8)  # frames standing, going up, held up, coming down, standing


@lru_cache(maxsize=4)
def film(params: "Params") -> tuple:
    """(pose, lift, moves made) for every frame: the pawn is lifted and set down twice."""
    stand, up, hold, down, rest = _FILM
    pitch = layout(params).ratchet.pitch
    frames = []
    for made in range(MOVES):
        frames += [(lifting(params, 0.0), 0.0, made)] * stand
        heights = [LIFT * smooth_step((i + 1) / up) for i in range(up)]
        frames += [(lifting(params, lift), lift, made) for lift in heights]
        frames += [(lifting(params, LIFT), LIFT, made)] * hold
        heights = [LIFT * (1 - smooth_step((i + 1) / down)) for i in range(down)]
        frames += [(lowering(params, lift), lift, made) for lift in heights]
        frames += [(lifting(params, 0.0), 0.0, made + 1)] * rest
    # the last frame is the first one again, with the wheel two teeth further
    return tuple(
        (Pose(at.drop, at.wheel + made * pitch, at.pawl, at.click), lift)
        for at, lift, made in frames
    )


def _render_poses(params: "Params") -> list:
    """Rigid transforms of every part from the built pose, for every frame of the film."""
    names = list(_rest(params.model_copy(update={"lift": 0.0})))
    built = lifting(params, params.lift)
    start = {n: np.linalg.inv(_matrix(params, n, built, params.lift)) for n in names}
    return [
        {n: (_matrix(params, n, at, lift) @ start[n]).tolist() for n in names}
        for at, lift in film(params)
    ]


def presentation(params: "Params") -> dict:
    """Render settings for cadkit.render: stills standing and lifted, and the looping films."""
    frame = {"box": ((-18, -18, 0), (18, 18, 50))}
    hero = {"azimuth": -30, "elevation": 12, "size": (1000, 1300), "margin": 1.05, **frame}
    side = {**hero, "azimuth": 0, "elevation": 3}
    stand, up, hold = _FILM[:3]
    lifted = stand + up + hold // 2  # a frame in which the pawn is held up
    open_side = ("plate_left", "jewel_wheel_left")
    reel = {"size": (600, 780), "samples": 16, "frame_ms": 70, "loop": True}
    return {
        "sheet": {
            "title": "CLOCKWORK PAWN",
            "subtitle": "{name}  /  {version}  /  first build: real mechanism, plain surfaces",
            "caption": "Every move turns the wheel on by one tooth, and the click never lets it back",
            "footer": "First build  |  Not printed yet",
        },
        "views": {
            "hero": dict(hero),
            "side": dict(side),
            "side_lifted": {**side, "frame": lifted},
            "hero_lifted": {**hero, "frame": lifted},
            "front": {**hero, "azimuth": -90, "elevation": 6},
            "back": {**hero, "azimuth": 150, "elevation": 14},
            "top": {**hero, "azimuth": -20, "elevation": 55},
            "mechanism": {**side, "hide": open_side},
            "mechanism_lifted": {**side, "hide": open_side, "frame": lifted},
        },
        "animation": {"view": "hero", **reel},
        # the left plate taken off: pawl, wheel and click at work
        "films": {"mechanism": {"view": "mechanism", "hide": open_side, **reel}},
        "light_target": (0, 0, 0.025),
        "materials": {
            "jewel_": {"roughness": 0.15, "coat": 0.6},
            "reference_": {"roughness": 0.25},
            "plunger": {"roughness": 0.6},
            "pawl": {"roughness": 0.6},
            "click": {"roughness": 0.6},
            "": {"roughness": 0.38, "coat": 0.25},
        },
    }
