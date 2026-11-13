"""The motion proof: what section 5 of docs/design-notes.md asks the bare mechanism to show.

Collisions are exact booleans, seams are measured on the solids, and "in view" / "hidden" are
ray-cast, so nothing here rests on looking at a picture.
"""

import itertools
import math
from functools import lru_cache

import numpy as np
import pytest
from build123d import Pos
from cadkit.validate import overlaps
from cadkit.visibility import (
    seen,
    sphere_views,
    surface_samples,
    triangles_of,
    view_vector,
    visible_share,
)
from pydantic import ValidationError
from serce import _base as base
from serce import _heart as heart
from serce import _kinematics as kin
from serce import _shell as shell
from serce.model import Params, _neutral, _render_poses, build, effort, moving_parts, wing_gravity

P = Params()
HINGE = heart.hinge(P)
# hidden parts of the drive: printed mechanism and bought hardware inside the base and the bed
DRIVE = ("slider", "pusher", "chassis", "cam_disc", "reference_spring", "reference_follower")
DRIVE += (
    "reference_hinge_pin",
    "reference_cam_magnet",
    "reference_ring_magnet",
    "reference_tie_nut",
)
DRIVE += ("reference_leg", "reference_back_screw", "reference_back_insert", "reference_ballast")
INSIDE = ("reference_room", "wing_left_lining", "wing_right_lining", "back_lining")
# viewers all round and from above, plus exactly along both seam planes and the base gaps
VIEWS = sphere_views(60, -10) + [
    view_vector(az, el) for az in (0, 90, 180, 270) for el in (0.0, 0.3, 8.0)
]


@lru_cache(maxsize=8)
def posed(turn: float) -> dict:
    return build(Params(turn=turn))


def _seen(parts: dict, pick, spacing: float, keep=None) -> int:
    """Number of sample points on the picked parts that any viewer sees past all parts."""
    triangles = triangles_of(parts.values(), 0.2)
    points, normals = [], []
    for name, shape in parts.items():
        if not pick(name):
            continue
        found, facing, _ = surface_samples(shape, spacing, 0.2)
        if keep is not None:
            mask = keep(name, found)
            found, facing = found[mask], facing[mask]
        points.append(found)
        normals.append(facing)
    points, normals = np.concatenate(points), np.concatenate(normals)
    hit = np.zeros(len(points), bool)
    for view in VIEWS:
        hit |= seen(points, normals, view, triangles)
    return int(hit.sum())


# ---------------------------------------------------------------- collisions
def test_no_two_parts_overlap_closed():
    assert not (hits := overlaps(posed(0.0))), hits


def test_full_turn_clearance():
    """The ring turns through 360 degrees; turning the other way passes the same positions."""
    moving = moving_parts(P)
    # every 2.5 degrees while the wings move, every 0.5 at first opening, every 7.5 on the way back
    turns = [2.5 * k for k in range(73)] + [25.5 + 0.5 * k for k in range(30)]
    turns += [187.5 + 7.5 * k for k in range(23)]
    for turn in turns:
        assert not (hits := overlaps(build(Params(turn=turn)), moving)), (
            f"At {turn} degrees: {hits}"
        )


def test_assembly_path_is_free():
    """Wing through the keyhole and round into its range; back half on from behind; pins up."""
    neutral = _neutral(P)
    u = heart.V_DIR
    left = ("wing_left", "wing_left_lining")
    fixed = {k: neutral[k] for k in ("coal_bed", "wing_right", "wing_right_lining", "plug_right")}
    # the plug lies on the lever and comes to rest in its seat just before the wing does
    rides = P.lever_clear + P.plug_drop

    def wing(angle, lift):
        return {
            k: Pos(*(u * lift)) * neutral[k].rotate(HINGE.axis(heart.LEFT), -angle) for k in left
        }

    def plug(lift):
        return {"plug_left": Pos(*(u * max(0.0, lift - rides))) * neutral["plug_left"]}

    for lift in (0, 0.3, 1, 2, 5, 8, 12, 16, 22):
        parts = {**fixed, **wing(P.keyhole, lift), **plug(lift)}
        assert not overlaps(parts, {*left, "plug_left"}), f"lift {lift}"
    for angle in np.arange(P.keyhole, P.wing_max, -5.0):
        parts = {**fixed, **wing(float(angle), 0), **plug(0)}
        assert not overlaps(parts, set(left)), f"angle {angle}"

    closed = {k: neutral[k] for k in ("coal_bed", *left, "wing_right", "wing_right_lining")}
    closed |= {k: neutral[k] for k in ("plug_left", "plug_right")}
    for dy in (0.5, 2, 5, 10, 20, 35, 50):
        for name in ("back", "back_lining"):
            hits = overlaps({**closed, name: Pos(0, dy, 0) * neutral[name]}, {name})
            assert not hits, f"back half {dy} mm behind: {hits}"

    rest = {k: neutral[k] for k in ("coal_bed", *left, "back", "back_lining", "wing_right")}
    rest |= {k: neutral[k] for k in ("plug_left", "plug_right")}
    rest["other_pin"] = neutral["reference_hinge_pin_right"]
    for drop in (0, 5, 15, 30, 45, 58):
        pin = Pos(*(-u * drop)) * neutral["reference_hinge_pin_left"]
        assert not overlaps({**rest, "pin": pin}, {"pin"}), f"pin {drop} mm out"


def test_keyhole_plugs_are_captive():
    """Each plug hangs in its seat under the collar and the back half: it cannot leave."""
    u = {"left": heart.V_DIR, "right": heart.mirrored(heart.V_DIR, heart.RIGHT)}
    for turn in (0.0, 90.0, 180.0):
        parts = posed(turn)
        for side in ("left", "right"):
            name = f"plug_{side}"
            near = {k: parts[k] for k in (name, f"wing_{side}", "coal_bed", "back")}
            assert parts[name].distance_to(parts["coal_bed"]) < 1e-6  # it rests on its seat
            # it carries nothing and touches nothing that moves
            assert parts[name].distance_to(parts[f"wing_{side}"]) == pytest.approx(
                P.plug_drop, abs=1e-3
            )
            lifted = {**near, name: Pos(*(u[side] * 0.3)) * parts[name]}
            stopped_by = {n for a, b, _ in overlaps(lifted, {name}) for n in (a, b)} - {name}
            assert stopped_by == {f"wing_{side}", "back"}, f"{name} lifts out at {turn}"
            dropped = {**near, name: Pos(*(-u[side] * 0.3)) * parts[name]}
            assert overlaps(dropped, {name}), f"{name} falls out at {turn}"
    # all of the plug and of its seat lies under the back half, which stands on the bed
    parts = posed(0.0)
    for side in ("left", "right"):
        top = Pos(*(u[side] * (P.plug_drop + 0.05))) * parts[f"plug_{side}"]
        proud = top & heart.skin(
            P, heart.SIDES[side], -5.0, heart.along_axis(HINGE, heart.SIDES[side], z0=0.01)
        )
        assert proud.volume > 1.0
        assert (proud - parts["back"]).volume < 1e-6


# ---------------------------------------------------------------- closed: tight, on its seats
def test_closed_seams():
    parts = posed(0.0)
    # the seat: wing and back half touch on the seam plane, coal on coal and lining on lining
    for side in ("left", "right"):
        assert parts[f"wing_{side}"].distance_to(parts["back"]) < 1e-6
        assert parts[f"wing_{side}_lining"].distance_to(parts["back_lining"]) < 1e-6
    # the two wings never touch: they cannot hold each other off their seats
    gap = parts["wing_left"].distance_to(parts["wing_right"])
    assert gap == pytest.approx(P.centre_clearance, abs=1e-4)
    # the visible groove at both seams, measured in the outer skin of the lobes
    for side, name in ((heart.LEFT, "left"), (heart.RIGHT, "right")):
        top = heart.above(62.0)
        band = [heart.behind(-1.0), heart.in_front(1.0), top]
        layer = heart.skin(P, side, 0.0, band) - heart.skin(P, side, 0.5)
        solid = sum(c.volume for part in (f"wing_{name}", "back") if (c := parts[part] & layer))
        assert 2.0 * (1 - solid / layer.volume) == pytest.approx(P.seam_gap, abs=0.01)
        band = [heart.beside(side, 0.0), ((side, 0.0, 0.0), 1.0), heart.in_front(-3.0), top]
        layer = heart.skin(P, side, 0.0, band) - heart.skin(P, side, 0.5)
        solid = (parts[f"wing_{name}"] & layer).volume
        assert 1.0 * (1 - solid / layer.volume) == pytest.approx(P.seam_gap / 2, abs=0.01)
    # no gap wider than the groove anywhere round the wings, and none under them
    for name, side in heart.SIDES.items():
        wall = parts[f"wing_{name}"] & heart.skin(
            P, side, -1.0, heart.along_axis(HINGE, side, z0=0.1)
        )
        assert wall.distance_to(parts["coal_bed"]) == pytest.approx(P.bed_gap, abs=1e-3)
    assert max(P.seam_gap, P.bed_gap, P.hinge_gap) <= 0.3


def test_wings_rest_on_their_seats_with_the_spring_squeezed():
    assert kin.seated(P, 0.0) and kin.wing_angle(P, 0.0) == 0.0
    assert kin.pusher_lag(P, 0.0) == pytest.approx(P.over_travel)
    assert P.over_travel + 0.2 <= P.pusher_travel
    assert base.spring_length(P, 0.0) == pytest.approx(base.spring_length(P, 90.0) - P.over_travel)
    heaviest = max(abs(wing_gravity(P, angle)) for angle in range(0, 126, 5))
    assert kin.closing_torque(P, 0.0) > 5 * heaviest
    # the crank pins rest on the pusher; the front plates stand clear of them
    parts = posed(0.0)
    assert parts["wing_left"].distance_to(parts["pusher"]) < 0.01
    assert parts["wing_left"].distance_to(parts["slider"]) > 0.3


def test_closed_heart_shows_nothing_of_the_inside():
    parts = posed(0.0)
    assert _seen(parts, lambda n: n.startswith(INSIDE), spacing=2.0) == 0


# ---------------------------------------------------------------- kinematics and effort
def test_kinematics():
    assert kin.wing_angle(P, 180.0) == pytest.approx(P.wing_max)
    angles = [kin.wing_angle(P, t) for t in range(181)]
    assert all(b >= a for a, b in itertools.pairwise(angles))
    dwell = kin.dwell_angle(P)
    assert 15 < dwell < 30
    assert all(a == 0.0 for a in angles[: int(dwell)])  # held shut when picked up by the ring
    assert angles[int(dwell) + 2] > 0.0
    for turn in (10.0, 50.0, 133.0):
        assert kin.wing_angle(P, 360.0 - turn) == pytest.approx(kin.wing_angle(P, turn))
        assert kin.wing_angle(P, -turn) == pytest.approx(kin.wing_angle(P, turn))
    stroke = kin.slider_y(P, 180.0) - kin.slider_y(P, 0.0)
    assert stroke == pytest.approx(kin.pin_travel(P) + P.over_travel)
    assert max(abs(kin.pressure_angle(P, t)) for t in range(360)) < 32.0
    # dead points at both ends: the wings cannot push the ring round
    assert kin.follower_rate(P, 0.0) == pytest.approx(0.0, abs=1e-6)
    assert kin.follower_rate(P, 180.0) == pytest.approx(0.0, abs=1e-6)
    # where the wings seat the cam still moves the slider briskly: a blocked wing cannot be
    # wedged by a light twist (the clutch slips first)
    assert kin.follower_rate(P, dwell) > 3.0


def test_effort_stays_in_a_band():
    """Ring torque from the statics model: always resisting, never more than a light twist."""
    curves = effort(P, 1.0)
    for direction, rows in curves.items():
        total = np.array([parts["total"] for _, parts in rows])
        assert total.min() > 5.0, f"direction {direction}: the ring would run by itself"
        assert total.max() < 40.0, f"direction {direction}: the effort has a hump"
        travel = np.array([parts["total"] for turn, parts in rows if 30 <= turn <= 330])
        assert travel.max() / travel.min() < 2.5
        # the one step is the spring's preload coming onto the cam as the wings seat
        assert np.abs(np.diff(total)).max() < 10.0
    # a table holds the piece against the hardest twist with one hand (0.3 kg on silicone feet)
    assert 45.0 < 0.8 * 300 * kin.GRAVITY * 30.0


# ---------------------------------------------------------------- the reveal
def test_open_room_is_in_view():
    parts = posed(180.0)
    room = [s for n, s in parts.items() if n.startswith("reference_room")]
    back = [parts["back"], parts["back_lining"]]
    others = [s for n, s in parts.items() if not n.startswith(("reference_room", "back"))]
    for azimuth, elevation in ((0, 10), (-45, 10), (45, 10), (-20, 42)):
        share = visible_share(room, others, view_vector(azimuth, elevation), 2.0, back, 0.2)
        assert share > 0.97, f"from {azimuth}/{elevation}: {share:.3f}"


def test_reveal_grows_steadily():
    shares = []
    for turn in (20.0, 40.0, 60.0, 90.0, 120.0, 180.0):
        parts = posed(turn)
        room = [s for n, s in parts.items() if n.startswith("reference_room")]
        back = [parts["back"], parts["back_lining"]]
        others = [s for n, s in parts.items() if not n.startswith(("reference_room", "back"))]
        shares.append(visible_share(room, others, view_vector(0, 10), 2.5, back, 0.2))
    assert shares[0] == 0.0 and shares[1] > 0.0 and shares[-1] > 0.97
    assert all(b >= a for a, b in itertools.pairwise(shares))
    assert shares[1] < shares[2] < shares[3]


# ---------------------------------------------------------------- the drive stays hidden
@pytest.mark.parametrize("turn", [0.0, 90.0, 180.0])
def test_drive_is_hidden(turn):
    parts = posed(turn)
    assert _seen(parts, lambda n: n.startswith(DRIVE), spacing=2.5) == 0

    def below_the_bed(name, points):
        side = heart.SIDES[name.split("_")[1]]
        local = np.array([HINGE.local(point, side) for point in points])
        # all of the wing under the collar's shoulder: journal, lever and crank pin. Only the
        # collar's own skin can be glimpsed, down its 0.2 mm running clearance.
        return local[:, 2] < -P.collar_depth - 0.05

    wings = ("wing_left", "wing_right")
    assert _seen(parts, lambda n: n in wings, spacing=1.5, keep=below_the_bed) == 0


# ---------------------------------------------------------------- animation data and inputs
def test_render_poses_match_cad():
    frames = _render_poses(P, steps=24)
    neutral = posed(0.0)
    for index in (0, 3, 6, 12, 18, 24):
        target = posed(index * 15.0)
        for name, matrix in frames[index].items():
            if name == "reference_spring":
                continue  # it also changes length; it rides with the pusher in the animation
            centre = np.array([*neutral[name].center(), 1.0])
            moved = (np.array(matrix) @ centre)[:3]
            assert moved == pytest.approx(tuple(target[name].center()), abs=1e-4), name
    assert all(np.allclose(m, np.eye(4)) for m in frames[0].values())


def test_size_and_stack():
    lv = base.levels(P)
    assert lv.slider_bottom - lv.chassis_bottom == pytest.approx(P.chassis_thick)
    assert shell.pin_top(P, HINGE) < HINGE.knuckle_top - 5  # the pin ends inside the knuckle
    # the two hinge pins end clear of each other, short of where their axes cross
    crossing = np.array(HINGE.origin)[0] / heart.V_DIR[0]  # how far below the bed facet
    ends_apart = 2 * (shell.pin_bottom(P) + crossing) * math.sin(heart.V_TILT)
    assert ends_apart > P.pin_d + 0.5
    height = 86.7 + base.total_height(P)
    assert 100 * 0.85 <= height <= 100 * 1.15
    assert math.isclose(kin.follower_y(P, 0.0), P.groove_radius - kin.stroke(P) / 2)


@pytest.mark.parametrize(
    "values",
    [
        {"lever": 14, "groove_radius": 18},  # cam groove would cut into the hub
        {"heel": 2.0},  # the hinge would be see-through
        {"pusher_travel": 1.0, "over_travel": 1.0},
        {"seam_depth": 2.2},
        {"wing_max": 150},
        {"turn": float("nan")},
        {"unknown": 1},
    ],
)
def test_invalid_params_fail_before_geometry(values):
    with pytest.raises(ValidationError):
        Params(**values)
