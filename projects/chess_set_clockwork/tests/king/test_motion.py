"""The king's motion: one lobe and twenty beats per move, the pawl, the escapement, stops."""

import math
from itertools import pairwise

import pytest
from cadkit.validate import overlaps
from chess_set_clockwork._shared import turned
from chess_set_clockwork.king import model as king
from chess_set_clockwork.king._layout import layout, lifting, sinking
from chess_set_clockwork.king.model import (
    _FILM,
    FILM_RUN,
    FRAME_MS,
    Params,
    _render_poses,
    _rest,
    balance,
    build,
    film,
    lifted,
    moving_parts,
    placed,
)
from pydantic import ValidationError

P = Params()
L = layout(P)
E = L.escapement
R = L.ratchet
REST = _rest(P)
MOVING = set(moving_parts(P))
TICKING = sum(_FILM[:5])  # index of the film's first ticking frame


def test_one_move_is_one_lobe_and_twenty_beats():
    assert L.ratio == pytest.approx(2.4)
    assert E.beats(360 / P.star_teeth * L.ratio) == pytest.approx(20)
    assert L.stroke == pytest.approx(3.144, abs=0.002)
    assert P.travel - L.stroke == pytest.approx(0.856, abs=0.002)  # the king falls this far first
    # above the stroke nothing has turned; within it the train follows the king down
    assert sinking(P, P.travel).turn == sinking(P, 20).turn == pytest.approx(-60)
    assert sinking(P, L.stroke / 2).turn == pytest.approx(-28.1, abs=0.2)  # it pushes harder late
    assert sinking(P, 0).turn == pytest.approx(0, abs=1e-6)
    assert sinking(P, 0).escape == pytest.approx(0, abs=1e-6)
    # the film's ticking frames are the run: the train ends where it began, in real time
    ticking = film(P)[TICKING - 1 :]
    ran = king.ticking(P, **FILM_RUN)
    assert len(ticking) - 1 - _FILM[5] == math.ceil(ran.times[-1] * 1000 / FRAME_MS)
    assert ticking[0][0].turn == pytest.approx(-60) and ticking[-1][0].turn == pytest.approx(0)
    assert ticking[20][0].escape == pytest.approx(144 - ran.at(1.0)[0], abs=0.2)
    assert ticking[20][0].anchor == pytest.approx(ran.at(1.0)[1], abs=0.01)
    lifts = [lift for _, lift in ticking]
    assert all(b <= a + 0.03 for a, b in pairwise(lifts))  # the king sinks; a recoil lifts it
    assert max(abs(at.anchor) for at, _ in ticking) <= P.swing_stop + 0.1


def test_pawl_carries_the_king_through_the_stroke():
    turns = [-60 + 5 * i for i in range(13)]
    arms = [R.arm(turn) for turn in turns]
    assert 2.3 < min(arms) and max(arms) < 3.3  # mm: torque on the star per newton
    for turn in turns:
        drop, lean = R.seated(turn)
        assert -2e-3 <= R.gap(drop, lean, turn) <= 2e-3  # the lobe lies in the cup
        # the star's push goes through the knuckle: the pawl is a strut and is not turned
        assert abs(R.escape(drop, lean, turn)) < 2.5
    # on the solids the cup holds its lobe and nothing else touches the star
    for lift in (0.0, 1.0, 2.0, 3.0):
        parts = build(P.model_copy(update={"lift": lift}))
        assert not overlaps({"pawl": parts["pawl"], "great_wheel": parts["great_wheel"]})
        assert parts["pawl"].distance_to(parts["great_wheel"]) < 0.01


def test_pawl_clicks_under_the_next_lobe_before_the_plunger_hangs():
    assert L.stroke < L.click <= P.travel - 0.7
    path = R.falling()
    assert min(lean for _, lean in path) == pytest.approx(-9.0, abs=0.3)  # pushed aside
    # while it is pushed aside the star's push is far from the line to the knuckle, so the
    # pawl cannot stand as a strut between the star and the dropping plunger
    pushed = [(d, a) for (d, a), (_, before) in zip(path[1:], path) if a < before - 1e-6]
    assert len(pushed) > 20
    assert min(R.escape(drop, lean, 0.0) for drop, lean in pushed) > 55
    # hanging, the pawl leans on the side of the next lobe with its cup right below it
    hanging = lifted(P, P.travel)
    assert 0.005 < hanging["pawl"].distance_to(hanging["great_wheel"]) < 0.05
    assert lifting(P, P.travel).pawl == pytest.approx(sinking(P, P.travel).pawl)
    assert sinking(P, L.stroke + 0.05).pawl == pytest.approx(R.seated(-60)[1], abs=0.8)


def test_nothing_collides_through_a_move():
    assert not overlaps(REST)
    for lift in (0.4, 1.0, 1.6, 2.2, 2.8, 3.2, 3.6, P.travel, 9.0):
        assert not overlaps(lifted(P, lift), moving=MOVING), lift
    frames = film(P)
    chosen = list(range(TICKING - 2, TICKING + 13)) + list(range(TICKING + 15, len(frames), 4))
    for index in chosen:
        at, lift = frames[index]
        assert not overlaps(placed(P, at, lift), moving=MOVING), index


def test_gears_run_with_clearance_and_without_lost_motion():
    for lift in (0.0, 1.0, 2.0, 3.0):
        parts = build(P.model_copy(update={"lift": lift}))
        assert 0.05 < parts["great_wheel"].distance_to(parts["escape_wheel"]) < 0.2
    for sign in (-1, 1):  # 2.5 degrees of the pinion either way meets a tooth
        nudged = turned(REST["escape_wheel"], L.escape, 2.5 * sign)
        assert overlaps({"escape_wheel": nudged, "great_wheel": REST["great_wheel"]})
    # star and escape wheel share a layer and pass each other
    assert L.escape[1] - L.great[1] - P.escape_tip - P.star_circle - P.lobe == pytest.approx(0.5)


def _pair(progress: float, angle: float) -> dict:
    """Escape wheel and anchor as solids, the wheel just short of `progress`."""
    wheel = turned(REST["escape_wheel"], L.escape, -(progress - 0.05 - L.progress))
    return {"escape_wheel": wheel, "anchor": turned(REST["anchor"], L.pivot, angle)}


def test_escapement_runs_on_the_solids():
    """Rock the anchor slowly with the wheel pushed on: flanks and pallets never meet."""
    stop, release = P.swing_stop, P.release
    swing = [-2.0, -release - 0.2, -release - 2, -stop, -release - 2, -release - 0.2, -2.0, 0.0]
    swing += [2.0, release + 0.2, release + 2, stop, release + 2, release + 0.2, 2.0, 0.0]
    progress = E.settle(L.progress, 0.0, P.pallet_length)
    start = progress
    for angle in swing:
        progress = E.settle(progress, angle, P.pallet_length)
        pair = _pair(progress, angle)
        assert not overlaps(pair), angle
        assert pair["escape_wheel"].distance_to(pair["anchor"]) < 0.03, angle  # a tip touches
    assert progress - start == pytest.approx(E.pitch, abs=0.02)  # one tooth for two beats
    # swinging on to the stop pushes the wheel back: the recoil
    released = E.settle(L.progress, -release - 0.2, P.pallet_length)
    assert E.settle(released, -stop, P.pallet_length) < released - 1.0
    # the entry pallet meets the flank of a tooth about one degree beyond the stop
    progress = E.settle(E.settle(L.progress, release + 0.2, P.pallet_length), 9.6, 5.5)
    assert overlaps(_pair(progress, 9.6))
    # at rest the pendulum hangs plumb and the wheel stands just short of a pallet
    assert E.interference(L.progress, 0.0, P.pallet_length) == 0
    assert E.interference(L.progress + 2 * P.rest_gap, 0.0, P.pallet_length) > 0


def test_stops():
    # hanging, the ears of the plunger sit on the ledge in the base
    hanging = lifted(P, P.travel)
    assert hanging["plunger"].distance_to(hanging["base"]) == pytest.approx(0, abs=1e-6)
    assert lifted(P, 2.0)["plunger"].distance_to(lifted(P, 2.0)["base"]) > 0.25
    assert lifted(P, 12)["plunger"].bounding_box().min.Z == pytest.approx(12 - P.travel)
    # the ring of the pendulum stops the anchor on the escape wheel's boss
    frame = {name: REST[name] for name in ("plate_front", "plate_rear", "great_wheel")}
    for sign in (-1, 1):
        swung = {
            "anchor": turned(REST["anchor"], L.pivot, sign * (P.swing_stop - 0.3)),
            "reference_bob": turned(REST["reference_bob"], L.pivot, sign * (P.swing_stop - 0.3)),
        }
        assert not overlaps({**frame, **swung}, moving=set(swung))
        beyond = turned(REST["anchor"], L.pivot, sign * (P.swing_stop + 0.3))
        assert overlaps({"anchor": beyond, "plate_rear": REST["plate_rear"]})
    # the lips of the socket stop the pawl before it can leave the star's reach
    for lean in (P.pawl_in - 1.0, -P.pawl_out + 1.0):
        pawl = turned(REST["pawl"], L.knuckle, lean)
        assert not overlaps({"pawl": pawl, "plunger": REST["plunger"]}), lean
    for lean in (P.pawl_in + 3.0, -P.pawl_out - 3.0):
        pawl = turned(REST["pawl"], L.knuckle, lean)
        assert overlaps({"pawl": pawl, "plunger": REST["plunger"]}), lean


def test_weight_drives_the_train():
    found = balance(P)
    assert 38 < found["piece"] < 44 and 7 < found["plunger"] < 8.5
    assert found["drive"] == pytest.approx(found["piece"] - found["plunger"])
    low, high = found["torque"]
    assert 0.7 < low < high < 1.1  # mN.m on the star, friction left out
    assert found["energy"] == pytest.approx(found["drive"] * 9.81e-3 * L.stroke)
    # the piece is as tall as planned and stays inside its base
    top = max(shape.bounding_box().max.Z for shape in REST.values())
    assert top == pytest.approx(86.7, abs=0.1)
    for name, shape in REST.items():
        box = shape.bounding_box()
        reach = max(abs(box.min.X), abs(box.max.X), abs(box.min.Y), abs(box.max.Y))
        assert reach <= P.base / 2 + 1e-6, name


def test_film_starts_and_ends_on_the_board():
    frames = _render_poses(P)
    assert frames[0] == frames[-1]
    assert frames[0]["anchor"] == [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
    held = frames[sum(_FILM[:2]) + 1]
    assert held["base"][2][3] == pytest.approx(8.0)
    assert held["plunger"][2][3] == pytest.approx(8.0 - P.travel)


@pytest.mark.parametrize(
    "values",
    [
        {"pin_length": 28.0},  # pins longer than the piece is wide
        {"travel": 3.6},  # the pawl would not get under the next lobe
        {"star_teeth": 5},  # the wheels would not end a move as they began it
        {"star_circle": 3.4, "lobe": 1.0},  # the star would touch the escape wheel
        {"bob_arm": 27.0},  # the bob would swing into the boss below it
    ],
)
def test_impossible_kings_are_refused(values):
    with pytest.raises(ValidationError):
        Params(**values)
