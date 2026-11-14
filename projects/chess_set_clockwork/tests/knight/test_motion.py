"""The knight's motion: what a lift does, clearances, stops, balance and how it goes together."""

import math

import pytest
from build123d import Pos
from cadkit.validate import overlaps
from chess_set_clockwork._shared import turned
from chess_set_clockwork.knight._layout import layout, pose
from chess_set_clockwork.knight.model import (
    Params,
    _render_poses,
    _rest,
    balance,
    build,
    moving_parts,
)
from pydantic import ValidationError

P = Params()
L = layout(P)
REST = _rest(P)


def placed(lift: float) -> dict:
    return build(P.model_copy(update={"lift": lift}))


def test_head_rears_through_the_first_three_millimetres_of_a_lift():
    assert L.swing == pytest.approx(28.65, abs=0.01)
    assert pose(P, 0).head == 0 and pose(P, P.travel).head == pytest.approx(-L.swing)
    assert pose(P, P.travel / 2).head == pytest.approx(-L.swing / 2)
    # above the travel the plunger hangs and nothing turns further
    assert pose(P, 20) == pose(P, P.travel)
    low, high = placed(0)["head"].bounding_box(), placed(P.travel)["head"].bounding_box()
    assert high.min.X < low.min.X  # the nose swings forward and up
    plunger = placed(12)["plunger"].bounding_box()
    assert plunger.min.Z == pytest.approx(12 - P.travel)


def test_nothing_collides_through_a_lift():
    assert not overlaps(placed(0))
    moving = set(moving_parts(P))
    for lift in (0.75, 1.5, 2.25, 3.0, 9.0):
        assert not overlaps(placed(lift), moving=moving), lift


def test_gears_run_with_clearance_and_without_lost_motion():
    for lift in (0.0, 1.0, 2.0, 3.0):
        parts = placed(lift)
        assert 0.05 < parts["head"].distance_to(parts["wheel"]) < 0.2
        assert 0.05 < parts["wheel"].distance_to(parts["plunger"]) < 0.2
    # at both ends of the travel a turn of 2.5 degrees either way meets a tooth: the rack
    # holds the pinion, and the wheel holds the mane, in both directions
    for lift in (0.0, P.travel):
        at = pose(P, lift)
        plunger = Pos(0, 0, -at.drop) * REST["plunger"]
        wheel = turned(REST["wheel"], L.wheel, at.wheel)
        for sign in (-1, 1):
            nudged = turned(REST["wheel"], L.wheel, at.wheel + 2.5 * sign)
            assert overlaps({"wheel": nudged, "plunger": plunger})
            head = turned(REST["head"], L.pivot, at.head + 2.5 * sign)
            assert overlaps({"head": head, "wheel": wheel})


def test_stops():
    # hanging, the ears of the plunger sit on the ledge in the base
    hanging = placed(P.travel)
    assert hanging["plunger"].distance_to(hanging["base"]) == pytest.approx(0, abs=1e-6)
    assert placed(P.travel / 2)["plunger"].distance_to(placed(P.travel / 2)["base"]) > 0.25
    # the banking pin is clear of the slot at both ends of the swing and stops the head
    # shortly beyond them
    banking = REST["reference_banking_pin"]
    for angle in (0.0, -L.swing):
        assert turned(REST["head"], L.pivot, angle).distance_to(banking) > 0.2
    for angle in (P.bank_margin - 0.3, -L.swing - P.bank_margin + 0.3):
        assert not overlaps({"head": turned(REST["head"], L.pivot, angle), "pin": banking})
    for angle in (P.bank_margin + 0.3, -L.swing - P.bank_margin - 0.3):
        assert overlaps({"head": turned(REST["head"], L.pivot, angle), "pin": banking})


def test_plunger_outweighs_the_head():
    found = balance(P)
    assert 3.5 < found["plunger"] and found["piece"] < 30
    assert 0 < found["head_at_plunger"] < found["plunger"] / 4


def test_timing_hole_lines_up_only_when_the_head_is_in_step():
    hole = (L.timing[0] - L.pivot[0], L.timing[1] - L.pivot[1])
    step = 360 / P.mane_teeth
    for teeth_out in (-2, -1, 1, 2):
        t = math.radians(teeth_out * step)
        moved = (
            hole[0] * math.cos(t) - hole[1] * math.sin(t),
            hole[0] * math.sin(t) + hole[1] * math.cos(t),
        )
        assert math.dist(hole, moved) > 1.5 * P.timing
    # the hole is open through both plates and the head when the piece stands
    probe = Pos(L.timing[0], 0, L.timing[1]) * REST["reference_banking_pin"].moved(
        Pos(-L.banking[0], 0, -L.banking[1])
    )
    thin = probe.scale(0.5)
    for name in ("plate_left", "plate_right", "head"):
        assert not overlaps({"probe": thin, name: REST[name]}), name


def test_parts_go_in_along_clear_paths():
    """Plunger, then the plates, then the wheel from behind and the head from above."""
    fixed = {name: REST[name] for name in ("base", "plate_left", "plate_right", "plunger")}
    for back in (0.6, 1.5, 3, 6, 10, 16, 24):
        wheel = Pos(back, 0, 0) * REST["wheel"]
        assert not overlaps({**fixed, "wheel": wheel}, moving={"wheel"}), back
    fixed["wheel"] = REST["wheel"]
    for up in (0.6, 1.5, 3, 6, 10, 16, 24):
        head = Pos(0, 0, up) * REST["head"]
        assert not overlaps({**fixed, "head": head}, moving={"head"}), up


def test_film_starts_and_ends_on_the_board():
    frames = _render_poses(P)
    assert frames[0] == frames[-1]
    assert frames[0]["head"] == [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
    top = frames[len(frames) // 2]
    assert top["base"][2][3] == pytest.approx(9.0) and top["plunger"][2][3] == pytest.approx(6.0)


@pytest.mark.parametrize(
    "values",
    [
        {"pin_length": 20.0},  # pins longer than the piece is wide
        {"moving": 9.6},  # no play between the bearing rings
        {"weight_length": 20.0, "bar_length": 20.0},  # weight longer than its bar
        {"bank_radius": 7.0, "hub": 4.0, "timing_radius": 8.5},  # no wall around the slot
    ],
)
def test_impossible_knights_are_refused(values):
    with pytest.raises(ValidationError):
        Params(**values)
