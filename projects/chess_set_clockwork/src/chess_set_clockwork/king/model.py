"""Clockwork king: it ticks for a few seconds after every move, then stands still.

Built like a skeleton clock: two plates in the shape of a Gothic window, joined by pillars,
with three arbors one above the other between them. Lifted, a weighted plunger drops out of
the base and a pawl on it clicks under the next lobe of a small star. Set down, the king
stands on that pawl and sinks under its own weight: the star turns the great wheel, the
great wheel a pinion, and the escape wheel on the pinion's arbor is let through tooth by
tooth by an anchor that swings with a pendulum behind the wheels.

Axes: X to the right, Y from front to back (the front plate is at -Y), Z up, the board at
Z = 0. Lengths in mm, angles in degrees, counter-clockwise in the view from the front. Every
fit is a named parameter.
"""

import math
from functools import lru_cache

import numpy as np
from build123d import Color, Pos
from cadkit.model import Model
from cadkit.params import Params as BaseParams
from cadkit.process import U1
from pydantic import Field, model_validator

from chess_set_clockwork._shared import grams, turned
from chess_set_clockwork.king import _parts as parts
from chess_set_clockwork.king import _run as run
from chess_set_clockwork.king._layout import Pose, layout, lifting, running, sinking


class Params(BaseParams):
    """Every dimension that may need tuning after test prints; mm and degrees."""

    lift: float = Field(default=0.0, ge=0, le=40)  # height above the board, on the way down

    # base
    base: float = Field(default=44.0, ge=40, le=48)  # diameter of the flange
    drum: float = Field(default=40.0, ge=38, le=44)
    flange_height: float = Field(default=5.0, ge=3, le=6)
    base_height: float = Field(default=9.0, ge=9, le=12)
    base_chamfer: float = Field(default=0.6, ge=0.3, le=1)
    studs: int = Field(default=16, ge=0, le=20)
    stud: float = Field(default=1.0, ge=0.6, le=1.4)  # radius

    # across the piece
    gap: float = Field(default=18.0, ge=17.6, le=20)  # between the plates
    plate: float = Field(default=3.0, ge=2.4, le=4)
    front_layer: float = Field(default=4.0, ge=3, le=5)  # escape wheel, star, pawl
    middle_layer: float = Field(default=4.0, ge=3, le=5)  # great wheel and pinion
    rear_layer: float = Field(default=8.0, ge=7.6, le=9)  # pendulum
    layer_gap: float = Field(default=0.5, ge=0.3, le=0.8)
    shoulder: float = Field(default=0.3, ge=0.2, le=0.5)  # bearing rings inside the plates
    shoulder_ring: float = Field(default=2.6, ge=2, le=3.2)  # their radius

    # the train
    module: float = Field(default=1.0, ge=0.8, le=1.25)
    wheel_teeth: int = Field(default=24, ge=20, le=28)
    pinion_teeth: int = Field(default=10, ge=9, le=12)
    shift: float = Field(default=0.4, ge=0.2, le=0.5)  # profile shift of the pinion
    backlash: float = Field(default=0.12, ge=0.05, le=0.2)
    wheel_clear: float = Field(default=1.0, ge=0.6, le=3)  # great wheel's teeth above the base
    great_angle: float = Field(default=0.0, ge=0, le=15)  # of the great wheel's gear at rest

    # the escapement (cadkit.features.escapement)
    escape_teeth: int = Field(default=20, ge=20, le=30)
    escape_tip: float = Field(default=12.7, ge=11, le=13.2)  # radius over the teeth
    escape_depth: float = Field(default=3.2, ge=2.6, le=3.6)
    span: int = Field(default=3, ge=3, le=5)  # the anchor reaches round span + 1/2 teeth
    release: float = Field(default=3.0, ge=3, le=6)  # anchor's angle at which a tooth leaves
    escape_drop: float = Field(default=0.5, ge=0.3, le=0.8)
    tooth_angle: float = Field(default=36.0, ge=30, le=40)
    escape_land: float = Field(default=0.2, ge=0.1, le=0.4)  # flat at a tooth's tip
    pallet_back: float = Field(default=75.0, ge=65, le=85)
    # Both faces are drawn this long so that the ramp reaches the arch; the arch's ends and its
    # outer edge cut them off.
    pallet_length: float = Field(default=7.2, ge=4.5, le=7.5)
    rest_gap: float = Field(default=0.4, ge=0.2, le=1)  # escape wheel short of its pallet, deg
    hub: float = Field(default=3.4, ge=3, le=4)  # anchor's hub behind the escape wheel
    hub_clear: float = Field(default=0.6, ge=0.4, le=1)  # hub to the escape wheel's teeth
    yoke: float = Field(default=3.0, ge=2.4, le=4)  # width of the anchor's arch
    yoke_clear: float = Field(default=2.6, ge=2.2, le=3.5)  # arch outside the teeth, centred
    # In a standing king the pendulum hangs with the anchor this far off its centre, the entry
    # pallet lowered. Sinking, the king leans about two degrees and the pendulum stays plumb,
    # which holds the anchor one degree to the other side of its centre instead of two: the
    # escapement is nearer to being in beat while it runs.
    beat: float = Field(default=1.0, ge=0, le=2.5)
    # How far the arch reaches past the exit and the entry pallet, deg. The anchor hangs at
    # `beat` because the arch is the shorter on the exit side; (15.4, 14) would hang centred.
    yoke_past: tuple[float, float] = (12.0, 14.0)
    # On the solids the entry pallet meets the flank of a tooth at 8.3 degrees.
    swing_stop: float = Field(default=7.5, ge=6, le=9)  # the ring stops the anchor here

    # the pendulum
    bob: float = Field(default=4.0, ge=4, le=6)  # steel pin across the pendulum
    bob_length: float = Field(default=10.0, ge=10, le=16)
    bob_fit: float = Field(default=0.2, ge=0.1, le=0.4)
    bob_arm: float = Field(default=25.0, ge=22, le=27)  # bob below the anchor's arbor
    bob_block: float = Field(default=8.0, ge=8, le=12)  # length of the block that holds it
    bob_wall: float = Field(default=1.0, ge=0.8, le=1.4)  # plastic above and below the bob
    ring_wall: float = Field(default=1.6, ge=1.2, le=2.4)
    rod: float = Field(default=3.0, ge=2.4, le=4)  # width of the pendulum's rod
    boss_tall: float = Field(default=2.0, ge=1.9, le=2.6)  # radius of the rear plate's bosses

    # star and pawl
    star_teeth: int = Field(default=6, ge=5, le=8)
    star_circle: float = Field(default=3.0, ge=2.6, le=3.4)  # radius on which the lobes sit
    lobe: float = Field(default=0.8, ge=0.6, le=1)  # radius of a lobe
    star_stalk: float = Field(default=1.0, ge=0.8, le=1.4)  # width of a lobe's stalk
    star_boss: float = Field(default=1.9, ge=1.7, le=2.4)  # radius of the star's centre
    star_end: float = Field(default=38.0, ge=25, le=45)  # direction of the pushed lobe at rest
    travel: float = Field(default=4.0, ge=3.6, le=5)  # of the plunger
    pawl_x: float = Field(default=6.4, ge=5, le=8)  # knuckle beside the star's arbor
    pawl_length: float = Field(default=10.0, ge=8, le=12)  # knuckle to the pushed lobe
    cup_play: float = Field(default=0.1, ge=0.05, le=0.2)  # cup's radius over the lobe's
    cup_hold: float = Field(default=25.0, ge=15, le=35)  # cup past the point that bears, deg
    cam: float = Field(default=55.0, ge=40, le=65)  # the way the finger's underside faces
    cam_clear: float = Field(default=0.3, ge=0.2, le=0.6)  # underside to the next lobe at rest
    cam_run: float = Field(default=0.5, ge=0.2, le=1.2)  # underside past its nearest point
    fence: float = Field(default=1.6, ge=1.2, le=2.4)  # height of the wall beside the cup
    fence_wall: float = Field(default=1.0, ge=0.8, le=1.6)
    pawl_neck: float = Field(default=1.6, ge=1.2, le=2)  # width of the arm at the knuckle
    knuckle: float = Field(default=1.5, ge=1.2, le=2)  # radius
    knuckle_play: float = Field(default=0.15, ge=0.1, le=0.3)
    socket_wall: float = Field(default=1.2, ge=1, le=1.6)
    pawl_in: float = Field(default=6.0, ge=3, le=10)  # socket lets the pawl lean in this far
    pawl_out: float = Field(default=14.0, ge=10, le=20)  # and out this far

    # steel: cylindrical pins, ISO 2338 nominal sizes (verify against the supplier's sheet)
    pin: float = Field(default=2.0, ge=1.5, le=3)  # arbors and pillars
    # The anchor's arbor is a thinner wire: friction there brakes the pendulum on every beat.
    anchor_pin: float = Field(default=1.0, ge=1, le=2)
    pin_length: float = Field(default=24.0, ge=22, le=28)
    pin_run: float = Field(default=0.3, ge=0.15, le=0.5)  # bore minus pin where it turns
    pin_grip: float = Field(default=0.1, ge=0, le=0.2)  # bore minus pin where it is pressed in
    weight: float = Field(default=6.0, ge=5, le=6)  # steel pin lying in the plunger
    weight_length: float = Field(default=18.0, ge=12, le=20)
    weight_fit: float = Field(default=0.2, ge=0.1, le=0.4)
    weight_floor: float = Field(default=0.9, ge=0.8, le=1.5)  # plastic under the weight

    # plunger
    bar_length: float = Field(default=21.0, ge=18, le=23)
    bar_width: float = Field(default=17.0, ge=9, le=17.2)  # across the piece
    bar_height: float = Field(default=8.7, ge=7, le=11.7)
    ear: float = Field(default=0.8, ge=0.6, le=1.2)  # how far each retaining ear stands out
    ear_height: float = Field(default=2.0, ge=1.5, le=3)
    slide: float = Field(default=0.3, ge=0.15, le=0.5)  # clearance to the slot, each side
    guide: float = Field(default=0.25, ge=0.15, le=0.5)  # stem to the rib that guides it
    guide_rib: float = Field(default=1.5, ge=1.2, le=2)  # width of that rib

    # frame
    column: float = Field(default=4.5, ge=4, le=5)  # width of a column
    column_x: float = Field(default=12.5, ge=12, le=12.7)  # its centre line
    strap: float = Field(default=3.6, ge=3, le=4.5)  # the bars across and the mullion
    boss: float = Field(default=4.2, ge=3.6, le=5)  # radius around an arbor
    boss_small: float = Field(default=2.6, ge=2.4, le=3.2)  # in front of the star
    plinth: float = Field(default=11.0, ge=8, le=14)  # height of a column's wide foot
    plinth_x: float = Field(default=8.0, ge=7, le=9.5)  # its inner edge
    post: float = Field(default=2.25, ge=2, le=2.8)  # radius of a pillar's post
    post_z: float = Field(default=12.5, ge=11.5, le=14)  # the two lower pillars
    post_above: float = Field(default=6.8, ge=6.5, le=9)  # upper pillar above the anchor
    jewel: float = Field(default=5.2, ge=4, le=6)  # outer diameter
    jewel_small: float = Field(default=4.0, ge=3.6, le=4.4)
    jewel_depth: float = Field(default=0.8, ge=0.4, le=1.2)
    tenon: float = Field(default=4.0, ge=3.6, le=5)  # across both prongs
    tenon_thick: float = Field(default=2.2, ge=1.8, le=2.6)
    tenon_fit: float = Field(default=0.15, ge=0.1, le=0.3)  # clearance in the mortise
    tenon_tip: float = Field(default=0.5, ge=0.3, le=1)  # end of a prong above the board
    prong: float = Field(default=1.4, ge=1.2, le=1.7)
    barb: float = Field(default=0.5, ge=0.3, le=0.7)
    catch: float = Field(default=1.6, ge=1.2, le=2.4)  # height of the step the barbs hold on

    # wheels
    great_hub: float = Field(default=4.6, ge=4.2, le=5.5)  # the star stands on it
    great_rim: float = Field(default=1.5, ge=1.2, le=2.5)  # solid below the teeth
    great_spokes: int = Field(default=6, ge=3, le=6)
    escape_hub: float = Field(default=3.2, ge=2.8, le=4)
    escape_rim: float = Field(default=1.3, ge=1.1, le=2)
    escape_web: float = Field(default=0.8, ge=0.6, le=1.2)  # behind the escape wheel's spokes
    escape_spokes: int = Field(default=5, ge=5, le=5)
    spoke: float = Field(default=1.6, ge=1.2, le=2.4)

    # crown
    crown_seat: float = Field(default=2.0, ge=1.5, le=3)  # the arch's point is cut this low
    crown_rise: float = Field(default=2.5, ge=2, le=4)  # tenon above where the point was
    crown_tenon: float = Field(default=6.0, ge=5, le=7)  # its width
    crown_lift: float = Field(default=1.2, ge=0.8, le=2)  # block's underside above the cut
    crown_cap: float = Field(default=1.5, ge=1.2, le=2.5)  # block above the tenons
    crown_width: float = Field(default=10.0, ge=8, le=12)
    orb: float = Field(default=11.0, ge=9, le=12)  # diameter
    cross: float = Field(default=7.5, ge=6, le=9)  # across its arms
    cross_waist: float = Field(default=1.8, ge=1.4, le=2.4)
    cross_flare: float = Field(default=4.4, ge=3, le=5)
    cross_thick: float = Field(default=1.6, ge=1.2, le=2.4)
    cross_tenon: float = Field(default=3.0, ge=2.4, le=4)
    cross_socket: float = Field(default=3.0, ge=2, le=4)  # depth of the slot in the orb

    @model_validator(mode="after")
    def _check(self):
        L = layout(self)
        e = L.escapement
        turn = 360 / self.star_teeth * L.ratio  # of the escape wheel in one move
        moves = turn / e.pitch  # escape teeth let through per move
        spokes = turn * self.escape_spokes / 360  # spokes that pass a place in one move
        wheel_step = self.wheel_teeth / self.star_teeth
        R = L.ratchet
        turns = [-360 / self.star_teeth * i / 12 for i in range(13)]
        bob_low = L.bob[1] - (self.bob + self.bob_fit) / 2 - self.bob_wall
        checks = {
            "moving parts do not fit between the bearing rings": L.play >= 0.15,
            "pins do not span the plates": 2 * L.outer - 1.0
            <= self.pin_length
            <= 2 * L.outer + 0.01,
            "a move does not end as it began": abs(moves - round(moves)) < 1e-9
            and abs(wheel_step - round(wheel_step)) < 1e-9
            and self.great_spokes % self.star_teeth in (0, self.great_spokes)
            and abs(spokes - round(spokes)) < 1e-9,
            "star and escape wheel share a layer and would touch": self.star_circle
            + self.lobe
            + 0.4
            <= L.escape[1] - L.great[1] - self.escape_tip,
            "lobes are not joined to the star": self.star_boss + self.lobe > self.star_circle - 0.4
            and self.star_stalk < 2 * self.lobe,
            "pawl does not get under the next lobe": L.click <= self.travel - 0.5,
            "pawl pushes too weakly at the start of a move": min(R.arm(t) for t in turns)
            >= 0.6 * max(R.arm(t) for t in turns),
            "pawl and star overlap while the pawl pushes": min(
                R.gap(*R.seated(t), t) for t in turns
            )
            >= -2e-3,
            "pawl would bind on the next lobe": min(
                R.escape(drop, lean, 0.0)
                for (drop, lean), (_, before) in zip(R.falling()[1:], R.falling())
                if lean < before - 1e-6
            )
            >= 35,
            "socket cannot hold the knuckle": self.pawl_neck + 2 * self.knuckle_play
            <= 1.6 * self.knuckle,
            "anchor's hub is too thin over the escape wheel": L.hub_front
            >= (self.anchor_pin + self.pin_grip) / 2 + 0.6,
            "pallets do not reach the anchor's arch": self.pallet_length
            * math.sin(math.radians(e.ramp))
            >= self.yoke_clear + e.engagement + 0.4,
            "pendulum's ring breaks into the bob": L.escape[1] - L.ring_hole
            >= L.bob[1] + (self.bob + self.bob_fit) / 2 + 0.8,
            "bob swings into the boss below": bob_low - L.great[1] - self.boss_tall >= 0.6,
            "bob does not fit in its layer": self.bob + self.bob_fit + 1.6 <= self.rear_layer,
            "bob is shorter than its block": self.bob_length >= self.bob_block,
            "plunger stands above the base": self.bar_height <= self.base_height - 0.3,
            "ledge for the ears is too low to print": L.ledge >= 1.2,
            "weight breaks through the bar": self.weight_floor * 2 + self.weight + self.weight_fit
            <= self.bar_height,
            "weight is longer than the bar": self.weight_length + 1.5 <= self.bar_length,
            "slot breaks into the mortises": L.outer - self.tenon_thick - self.tenon_fit
            >= L.bar_wide + self.slide + 0.8,
            "mortise breaks out of the drum": math.hypot(
                self.column_x + self.tenon / 2 + self.tenon_fit, L.outer + self.tenon_fit
            )
            <= self.drum / 2 - 0.8,
            "prongs cannot spring past their barbs": self.tenon - 2 * self.prong
            >= 2 * self.barb + 0.1,
            "stem does not fit in the slot": L.stem[1] <= L.bar_half
            and L.stem[1] + self.guide + self.guide_rib <= self.column_x,
            "lower pillars stand in the way of the great wheel": math.dist(L.posts[0], L.great)
            >= L.great_tip + self.post + 0.5
            and L.posts[0][1] - self.post >= self.base_height + 0.5,
            "upper pillar stands in the way of the anchor or the crown": L.posts[2][1] - self.post
            >= L.escape[1] + L.yoke[1] + 0.8
            and L.posts[2][1] + self.post + 0.4 <= L.apex - self.crown_seat + self.crown_lift,
            "cross does not fit in the orb": self.cross_socket <= self.orb / 2
            and self.cross_tenon < self.orb / 2,
        }
        failed = [text for text, ok in checks.items() if not ok]
        if failed:
            raise ValueError("; ".join(failed))
        return self


COLOURS = {
    "base": "#C9A227",
    "plate": "#C9A227",
    "crown": "#C9A227",
    "cross": "#D8B13A",
    "great": "#B98F2B",
    "escape": "#D8B13A",
    "anchor": "#E3C257",
    "plunger": "#3B3B42",
    "pawl": "#55555E",
    "jewel": "#B01030",
    "reference": "#9DA5A8",
}
ARBORS = ("great", "escape", "anchor")


@lru_cache(maxsize=8)
def _rest(params: "Params") -> dict:
    """Every solid with the plunger home and the anchor centred; standing, it hangs at `beat`."""
    L = layout(params)
    built = {
        "base": parts.base(params),
        "plate_front": parts.plate(params, -1),
        "plate_rear": parts.plate(params, 1),
        "great_wheel": parts.great_wheel(params),
        "escape_wheel": parts.escape_wheel(params),
        "anchor": parts.anchor(params),
        "plunger": parts.plunger(params),
        "pawl": parts.pawl(params),
        "crown": parts.crown(params),
        "cross": parts.cross(params),
    }
    for arbor, centre in zip(ARBORS, (L.great, L.escape, L.pivot)):
        for name, side in (("front", -1), ("rear", 1)):
            built[f"jewel_{arbor}_{name}"] = parts.jewel(params, centre, side)
        built[f"reference_arbor_{arbor}"] = parts.pin(params, centre)
    for name, centre in zip(("left", "right", "top"), L.posts):
        built[f"reference_pillar_{name}"] = parts.pin(params, centre)
    built["reference_bob"] = parts.steel_bob(params)
    built["reference_weight"] = parts.steel_weight(params)
    return built


def moving_parts(params: "Params") -> dict:
    """What each moving part does: three turn on their arbors, the plunger slides with the pawl."""
    return {
        "great_wheel": "great",
        "reference_arbor_great": "great",
        "escape_wheel": "escape",
        "reference_arbor_escape": "escape",
        "anchor": "anchor",
        "reference_arbor_anchor": "anchor",
        "reference_bob": "anchor",
        "plunger": "plunger",
        "reference_weight": "plunger",
        "pawl": "pawl",
    }


def _matrix(params: "Params", name: str, at: Pose, lift: float) -> np.ndarray:
    """World transform of a part from its rest solid, for the king in pose `at`, `lift` up."""
    L = layout(params)
    kind = moving_parts(params).get(name)
    turn = {
        "great": (L.great, at.turn),
        "escape": (L.escape, at.escape),
        "anchor": (L.pivot, at.anchor),
        "pawl": (L.knuckle, at.pawl),
    }.get(kind)
    matrix = np.eye(4)
    if turn:
        (x, z), angle = turn
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        matrix[0, 0], matrix[0, 2], matrix[2, 0], matrix[2, 2] = c, -s, s, c
        matrix[0, 3] = x - c * x + s * z
        matrix[2, 3] = z - s * x - c * z
    matrix[2, 3] += lift - at.drop if kind in ("plunger", "pawl") else lift
    return matrix


def placed(params: "Params", at: Pose, lift: float) -> dict:
    """Every part for the king in pose `at`, held `lift` above the board."""
    L = layout(params)
    motion = moving_parts(params)
    centres = {"great": L.great, "escape": L.escape, "anchor": L.pivot, "pawl": L.knuckle}
    angles = {"great": at.turn, "escape": at.escape, "anchor": at.anchor, "pawl": at.pawl}
    built = {}
    for name, shape in _rest(params.model_copy(update={"lift": 0.0})).items():
        kind = motion.get(name)
        if kind in centres and angles[kind]:
            shape = turned(shape, centres[kind], angles[kind])
        rise = lift - at.drop if kind in ("plunger", "pawl") else lift
        moved = Pos(0, 0, rise) * shape if rise else shape
        moved.label = name
        moved.color = Color(COLOURS[name.split("_")[0]])
        built[name] = moved
    return built


def build(params: "Params") -> dict:
    """The king `params.lift` above the board on its way down; every part is one named solid."""
    return placed(params, sinking(params, params.lift), params.lift)


def lifted(params: "Params", lift: float) -> dict:
    """The king `lift` above the board on its way up: the train stands and the pawl clicks."""
    return placed(params, lifting(params, lift), lift)


@lru_cache(maxsize=8)
def weights(params: "Params") -> run.Masses:
    """Masses and inertias of the standing king, for `ticking`."""
    still = params.model_copy(update={"lift": 0.0})
    return run.masses(still, _rest(still), moving_parts(still))


@lru_cache(maxsize=16)
def ticking(params: "Params", **conditions) -> run.Run:
    """One move run through with friction; `_run.tick` names the conditions."""
    still = params.model_copy(update={"lift": 0.0})
    return run.tick(still, weights(still), **conditions)


def balance(params: "Params") -> dict:
    """Weights in grams and what drives the train.

    `drive` is what rests on the pawl while the king sinks: everything but the plunger, its
    weight and the pawl. `torque` is the least and the greatest moment on the star in mN.m
    over a move, with nothing lost to friction.
    """
    L = layout(params)
    rest = _rest(params.model_copy(update={"lift": 0.0}))
    mass = {name: grams(name, shape) for name, shape in rest.items()}
    plunger = mass["plunger"] + mass["reference_weight"] + mass["pawl"]
    piece = sum(mass.values())
    arms = [L.ratchet.arm(-360 / params.star_teeth * i / 24) for i in range(25)]
    newtons = (piece - plunger) * 9.81e-3
    return {
        "piece": piece,
        "plunger": plunger,
        "drive": piece - plunger,
        "pendulum": mass["anchor"] + mass["reference_bob"] + mass["reference_arbor_anchor"],
        "torque": (newtons * min(arms), newtons * max(arms)),
        "energy": newtons * L.stroke,  # mJ per move
    }


variants = {"playing": Params()}
process = U1
version = "0.2.0"
model = Model("clockwork_king", version, variants, process, build)


# ---------------------------------------------------------------- film
LIFT = 8.0  # how high the film lifts the king
FRAME_MS = 30  # a beat takes about 65 ms, so two frames show one
_FILM = (7, 17, 7, 13, 3, 10)  # frames standing, going up, held, coming down, falling; standing
# The friction the film's run is made with: the middle of what printed parts are taken to
# have. The king ticks from rest with up to 0.51.
FILM_RUN = {"friction": 0.3, "pin_friction": 0.3}


def _steps(count: int) -> list:
    """`count` values that rise smoothly from 0 to 1, the last one being 1."""
    return [(1 - math.cos(math.pi * (i + 1) / count)) / 2 for i in range(count)]


@lru_cache(maxsize=4)
def film(params: "Params") -> tuple:
    """(pose, lift) for every frame of one move: lifted, held, set down, and ticking.

    The hand's part is drawn. From the moment the king rests on its pawl the frames are
    `ticking` with the friction of `FILM_RUN`, in real time: wheel and anchor stand where the
    run has them, and the king sinks as the wheel turns. Once the king is on the board the
    wheels are drawn at rest while the pendulum dies down, and the last frames bring the
    anchor from where friction left it back to where it hangs, so that the film loops.
    """
    L = layout(params)
    e, R = L.escapement, L.ratchet
    stand, up, hold, down, fall, rest = _FILM
    beat = params.beat  # where the anchor hangs while the king stands or is carried
    still = (sinking(params, 0.0, anchor=beat), 0.0)
    frames = [still] * stand
    frames += [(lifting(params, LIFT * s), LIFT * s) for s in _steps(up)]
    frames += [(lifting(params, LIFT), LIFT)] * hold
    lowered = [LIFT - (LIFT - params.travel) * s for s in _steps(down)]
    lowered += [params.travel - (params.travel - L.stroke) * (i + 1) / fall for i in range(fall)]
    frames += [(sinking(params, lift, anchor=beat), lift) for lift in lowered]
    ran = ticking(params, **FILM_RUN)
    if ran.finished is None:
        raise ValueError("The king does not tick with the film's friction")
    start = L.progress - 360 / params.star_teeth * L.ratio
    angle = beat
    for i in range(1, math.ceil(ran.times[-1] * 1000 / FRAME_MS) + 1):
        turned, angle = ran.at(i * FRAME_MS / 1000)
        progress = min(start + turned, L.progress)
        # the run lets a tooth sink microns into a pallet; the solids are drawn clear of it
        while e.interference(progress, angle, params.pallet_length) > 0:
            if progress < L.progress:
                progress = e.settle(progress, angle, params.pallet_length) - 0.05
            else:  # the wheels are at rest: the anchor comes no closer than they let it
                angle = beat + (angle - beat) * 0.9
        turn = (progress - L.progress) / L.ratio
        drop, lean = R.seated(turn)
        frames.append((running(params, turn, drop, lean, anchor=angle), drop))
    frames += [
        (sinking(params, 0.0, anchor=beat + (angle - beat) * (1 - s)), 0.0) for s in _steps(rest)
    ]
    return tuple(frames)


def _render_poses(params: "Params") -> list:
    """Rigid transforms of every part from the built pose, for every frame of the film."""
    names = list(_rest(params.model_copy(update={"lift": 0.0})))
    built = sinking(params, params.lift)
    start = {n: np.linalg.inv(_matrix(params, n, built, params.lift)) for n in names}
    return [
        {n: (_matrix(params, n, at, lift) @ start[n]).tolist() for n in names}
        for at, lift in film(params)
    ]


def presentation(params: "Params") -> dict:
    """Render settings for cadkit.render: stills standing and lifted, and the looping films."""
    frame = {"box": ((-23, -23, 0), (23, 23, 90))}
    hero = {"azimuth": -28, "elevation": 10, "size": (1000, 1500), "margin": 1.05, **frame}
    front = {**hero, "azimuth": 0, "elevation": 3}
    back = {**hero, "azimuth": 180, "elevation": 3}
    stand, up, hold = _FILM[:3]
    lifted = stand + up + hold // 2  # a frame in which the king is held up
    no_front = ("plate_front", "jewel_great_front", "jewel_escape_front", "jewel_anchor_front")
    no_rear = ("plate_rear", "jewel_great_rear", "jewel_escape_rear", "jewel_anchor_rear")
    reel = {"size": (600, 900), "samples": 16, "frame_ms": FRAME_MS, "loop": True}
    return {
        "sheet": {
            "title": "CLOCKWORK KING",
            "subtitle": "{name}  /  {version}  /  second build: real mechanism, plain surfaces",
            "caption": "Set down, the king sinks 3 mm on its plunger and ticks sixteen times",
            "footer": "Second build  |  Not printed yet  |  Film: run model at friction 0.3",
        },
        "views": {
            "hero": dict(hero),
            "front": dict(front),
            "hero_lifted": {**hero, "frame": lifted},
            "front_lifted": {**front, "frame": lifted},
            "back": {**hero, "azimuth": 152, "elevation": 12},
            "side": {**hero, "azimuth": 90, "elevation": 3},
            "top": {**hero, "azimuth": -20, "elevation": 55},
            "mechanism": {**front, "hide": no_front},
            "mechanism_lifted": {**front, "hide": no_front, "frame": lifted},
            "pendulum": {**back, "hide": no_rear},
        },
        "animation": {"view": "hero", **reel},
        "films": {
            # the front plate taken off: pawl, star, wheels and the anchor at work
            "mechanism": {"view": "mechanism", "hide": no_front, **reel},
            # the rear plate taken off: the pendulum
            "pendulum": {"view": "pendulum", "hide": no_rear, **reel},
        },
        "light_target": (0, 0, 0.045),
        "materials": {
            "jewel_": {"roughness": 0.15, "coat": 0.6},
            "reference_": {"roughness": 0.25},
            "plunger": {"roughness": 0.6},
            "pawl": {"roughness": 0.6},
            "": {"roughness": 0.38, "coat": 0.25},
        },
    }
