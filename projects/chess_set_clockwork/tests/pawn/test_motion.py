"""The pawn's motion: one tooth per move and never back, clearances, stops and balance."""

import numpy as np
import pytest
from build123d import CenterOf
from cadkit.validate import overlaps
from chess_set_clockwork._shared import turned
from chess_set_clockwork.pawn._layout import layout, lifting, lowering, move
from chess_set_clockwork.pawn.model import (
    LIFT,
    Params,
    _render_poses,
    _rest,
    balance,
    build,
    lowered,
    moving_parts,
)
from pydantic import ValidationError

P = Params()
L = layout(P)
M = move(P)
REST = _rest(P)
MOVING = set(moving_parts(P))


def raised(lift: float) -> dict:
    return build(P.model_copy(update={"lift": lift}))


def test_a_move_turns_the_wheel_on_by_one_tooth():
    pitch = L.ratchet.pitch
    assert pitch == pytest.approx(22.5) and M.turned == pytest.approx(pitch)
    # lifted, the wheel falls back onto the click within the first half millimetre and stands
    assert lifting(P, 0.0).wheel == pytest.approx(0.0, abs=1e-9)
    assert L.back == pytest.approx(4.38, abs=0.01) and M.fallen == pytest.approx(0.555, abs=0.01)
    for lift in (M.fallen + 0.05, 2.0, P.travel):
        assert lifting(P, lift).wheel == pytest.approx(-L.back)
    # above the travel the plunger hangs and nothing moves further
    assert lifting(P, 20.0) == lifting(P, P.travel)
    assert raised(12.0)["plunger"].bounding_box().min.Z == pytest.approx(12.0 - P.travel)
    # set down, the pawl pushes the next tooth up: the wheel only goes forward
    turns = [lowering(P, lift).wheel for lift in (4.5, 3.5, 3.0, 2.0, 1.0, 0.0)]
    assert turns[0] == turns[1] == pytest.approx(-L.back)
    assert turns == sorted(turns) and turns[-1] == pytest.approx(pitch)
    # the pawn stands again as it stood: pawl under a tooth, click on the back of one
    end = lowering(P, 0.0)
    assert end.pawl == pytest.approx(0.0, abs=1e-6) and end.click == pytest.approx(0.0, abs=0.01)


def test_pawl_gets_under_the_next_tooth_with_travel_to_spare():
    # it rides down the back of the next tooth, is pushed out, and falls under the tooth
    assert M.under == pytest.approx(4.0, abs=0.03) and P.travel - M.under >= 0.45
    assert M.swing == pytest.approx(12.3, abs=0.2)
    out = lifting(P, M.under - 0.1)
    assert out.pawl < -11 and lifting(P, M.under + 0.1).pawl > -2
    # coming up, it first travels free, then meets the tooth's face
    assert M.meets == pytest.approx(3.04, abs=0.03) and P.travel - M.meets > 1.2
    # the click is lifted over one tooth on the way
    assert M.lift == pytest.approx(6.9, abs=0.2)


def test_noses_lie_on_the_teeth():
    standing = raised(0.0)
    assert standing["pawl"].distance_to(standing["wheel"]) < 0.02  # under the tooth it pushed
    assert standing["click"].distance_to(standing["wheel"]) < 0.02  # on the back of a tooth
    hanging = raised(P.travel)
    assert hanging["click"].distance_to(hanging["wheel"]) < 0.02  # in the corner of its tooth
    assert hanging["pawl"].distance_to(hanging["wheel"]) < 0.02  # on the next back, waiting
    # the pawl has gone down with the plunger, which stays on the board
    assert hanging["pawl"].bounding_box().max.Z - P.travel < REST["pawl"].bounding_box().max.Z - 4


def test_wheel_cannot_turn_back():
    W = L.ratchet
    assert W.locks(L.click, L.to_wheel(L.click_pin)) == pytest.approx(7.9, abs=0.3)
    assert W.locks(L.pawl, L.to_wheel(L.knuckle)) > 20
    # lifted, the click sits in its tooth: the wheel turned back any further meets the click
    click = turned(REST["click"], L.click_pin, L.click_seated - L.click_home)
    for back, held in ((0.0, False), (-1.0, True), (-3.0, True)):
        wheel = turned(REST["wheel"], L.wheel, -L.back + back)
        assert bool(overlaps({"wheel": wheel, "click": click})) is held
    # standing, the pawl holds the tooth it has pushed up
    assert overlaps({"wheel": turned(REST["wheel"], L.wheel, -1.0), "pawl": REST["pawl"]})


def test_nothing_collides_through_a_move():
    assert not overlaps(raised(0.0))
    for lift in (0.3, 0.6, 1.5, 2.5, 3.5, 3.9, 4.05, 4.5, LIFT):
        assert not overlaps(raised(lift), moving=MOVING), lift
    for lift in (4.2, 3.6, 3.0, 2.4, 1.8, 1.2, 0.6, 0.2, 0.0):
        assert not overlaps(lowered(P, lift), moving=MOVING), lift


def test_stops():
    # hanging, the ears of the plunger sit on the ledge in the base
    hanging = raised(P.travel)
    assert hanging["plunger"].distance_to(hanging["base"]) == pytest.approx(0, abs=1e-6)
    assert raised(P.travel / 2)["plunger"].distance_to(raised(P.travel / 2)["base"]) > 0.25
    # the socket's lips let the pawl swing as far as a tooth pushes it, and stop it beyond
    plunger = REST["plunger"]
    for turn, free in (
        (-M.swing - 1.0, True),
        (-P.pawl_out - 1.0, False),
        (P.pawl_in - 1.0, True),
        (P.pawl_in + 1.0, False),
    ):
        pawl = turned(REST["pawl"], L.knuckle, turn)
        assert (not overlaps({"pawl": pawl, "plunger": plunger})) is free, turn
    # at the outer lip it still leans towards the wheel, so it always falls back in
    out = turned(REST["pawl"], L.knuckle, -P.pawl_out)
    assert out.center(CenterOf.MASS).X < L.knuckle[0] - 0.4


def test_click_cannot_swing_over_the_top():
    frame = {name: REST[name] for name in ("head", "plate_left", "plate_right")}
    stopped = None
    for lift in range(10, 180, 2):
        click = turned(REST["click"], L.click_pin, -lift)
        if overlaps({**frame, "click": click}, moving={"click"}):
            stopped = lift
            break
    # the head stops it while it still hangs to the side it fell from
    assert stopped is not None and stopped < 120
    held = turned(REST["click"], L.click_pin, -stopped)
    assert held.center(CenterOf.MASS).X < L.click_pin[0] - 1.0


def test_weights_and_how_surely_pawl_and_click_fall():
    found = balance(P)
    assert found["piece"] == pytest.approx(15.3, abs=0.2)
    assert found["plunger"] > 4.8 and found["plunger"] > 40 * found["pawl"]
    assert found["pawl_lean"] == pytest.approx(1.16, abs=0.05)
    assert found["pawl_lean_out"] == pytest.approx(0.69, abs=0.05)
    assert found["click_lean"] > 2.5
    top = max(shape.bounding_box().max.Z for shape in REST.values())
    assert top == pytest.approx(46.9, abs=0.1)
    for shape in REST.values():  # nothing stands out past the base
        box = shape.bounding_box()
        assert max(abs(box.min.X), box.max.X, abs(box.min.Y), box.max.Y) <= P.base / 2 + 1e-6


def test_film_shows_two_moves_and_loops():
    frames = _render_poses(P)
    first, last = frames[0], frames[-1]
    assert first["base"] == last["base"] and first["pawl"] == last["pawl"]
    assert np.array(first["click"]) == pytest.approx(np.array(last["click"]), abs=1e-3)
    # two teeth on, the wheel with its eight spokes looks as it did
    assert last["wheel"][0][0] == pytest.approx(0.7071, abs=1e-4)
    assert last["wheel"][2][0] == pytest.approx(0.7071, abs=1e-4)
    high = [frame for frame in frames if frame["base"][2][3] == pytest.approx(LIFT)]
    assert len(high) >= 10
    assert high[0]["plunger"][2][3] == pytest.approx(LIFT - P.travel)


@pytest.mark.parametrize(
    "values",
    [
        {"travel": 3.9},  # the pawl does not get under the next tooth
        {"pin_length": 16.0},  # pins longer than the piece is wide
        {"spokes": 5},  # the wheel would not look the same after two moves
        {"wheel_tip": 8.4},  # the wheel does not fit between the columns
        {"click_rise": 10.2, "wheel_tip": 8.0},  # the click's eye in the teeth
        {"pawl_out": 11.0},  # the socket's lip in the pawl's way
        {"bar_length": 23.0},  # weight longer than its bar
    ],
)
def test_impossible_pawns_are_refused(values):
    with pytest.raises(ValidationError):
        Params(**values)
