"""Motion proof: poses, capture, clearance, the forces on a house, what a viewer can see of
the mechanism, and whether the parts can be put in along their assembly paths."""

import math

import numpy as np
import pytest
from build123d import Pos
from cadkit.validate import overlaps
from fala import _gaps as gaps
from fala import _hidden as hidden
from fala import _statics as statics
from fala import _wave as wave
from fala._layout import layout
from fala.model import FRAMES, Params, _render_poses, build, moving_parts
from pydantic import ValidationError

P = Params()
PASS = 360 * P.ratio  # crank degrees for one pass of the wave


def test_wave_is_what_the_look_brief_asks_for():
    rises, leans = [], []
    for turn in range(0, PASS, 5):
        at = wave.pose(P, 3, turn)
        rises.append(at.rise)
        leans.append(at.lean)
    assert max(rises) - min(rises) == pytest.approx(2 * P.amplitude, abs=0.25)
    assert 5.5 < max(leans) < 6.2 and max(leans) == pytest.approx(-min(leans), abs=0.05)
    # one pass of the wave is three turns of the crank, and it closes on itself
    a, b = wave.pose(P, 3, 40), wave.pose(P, 3, 40 + PASS)
    assert (a.rise, a.lean) == pytest.approx((b.rise, b.lean))
    # turning back sends the same wave the other way: unit 0 then leads unit 7
    step = math.degrees(layout(P).cam.k * P.pitch) * P.ratio
    assert wave.pose(P, 4, 200 + step).rise == pytest.approx(wave.pose(P, 3, 200).rise)


def test_pavement_stays_one_ribbon():
    # the joint between two slabs keeps its width within 0.15 and its two edges stay level
    # within 0.15, through the whole pass
    found = gaps.survey(P, step=10.0)
    assert 0.65 < found["joint_min"] and found["joint_max"] < 0.95
    assert found["step_max"] < 0.15


def test_walls_between_houses_never_open_and_the_roofline_slit_stays_narrow():
    # Seen straight on, a tall bay's wing always covers the edge of the low facade beside
    # it. Above the low eaves the wing and the low roof's verge do part: a slit of sky that
    # opens to just under 2 mm and closes again, where the roofline steps.
    found = gaps.survey(P, step=10.0)
    assert 0 <= found["walls_min"] < 0.1 and found["walls_max"] < 4.0
    assert -1.95 < found["roofline_min"] < -1.8


def test_no_daylight_between_the_walls_of_two_houses():
    # a reduced set of views; docs/motion-proof.md has the full survey. The one known leak
    # is at pavement level, with the eye level with the pavement: design notes, open point 3
    for turn in (0, 540):
        params = Params(turn=turn)
        seen = gaps.daylight(
            build(params), params, azimuths=(-30, -5, 0, 5, 30), elevations=(0, 2, 20)
        )
        assert all(walls == 0 for walls, _ in seen.values()), (turn, seen)
        assert all(elevation == 0 for _, elevation in seen), (turn, seen)


def test_every_house_stays_captured():
    # the lower pads stand under the upper ones, so the gap under the cam hardly breathes
    gaps = [
        g for i in range(P.houses) for turn in range(0, PASS, 5) for g in wave.pose(P, i, turn).gaps
    ]
    assert 0.3 < min(gaps) and max(gaps) < 0.47


def test_no_part_runs_into_another_through_a_pass_of_the_wave():
    for turn in range(0, PASS, 90):
        assert not (hits := overlaps(build(Params(turn=turn)))), (turn, hits)


def test_pads_touch_the_cam_in_the_solid_model():
    parts = build(Params(turn=130))
    for i in range(1, P.houses + 1):
        assert parts["cam"].distance_to(parts[f"sled_{i}"]) < 2e-3


def test_film_poses_are_rigid_and_agree_with_the_built_model():
    frames = _render_poses(P, steps=12)
    assert len(frames) == 13 and set(frames[0]) == moving_parts(P)
    base = build(P)
    target = build(Params(turn=PASS * 5 / 12))
    for name, matrix in frames[5].items():
        matrix = np.array(matrix)
        assert matrix[:3, :3].T @ matrix[:3, :3] == pytest.approx(np.eye(3), abs=1e-9)
        moved = matrix @ np.array([*base[name].center(), 1])
        assert moved[:3] == pytest.approx(tuple(target[name].center()), abs=1e-4)
    for name in frames[0]:  # the film loops: the last pose is the first
        assert np.array(frames[12][name]) == pytest.approx(np.array(frames[0][name]), abs=1e-9)
    assert FRAMES % 4 == 0


def test_houses_ride_by_their_own_weight_up_to_a_friction_of_a_quarter():
    # every house on both pads and on both guide seats, through the pass, both ways
    for friction, seat, pad in ((0.1, 0.15, 0.28), (0.2, 0.09, 0.12), (0.25, 0.05, 0.04)):
        result = statics.survey(P, friction, step=60)
        assert result["wedged"] == 0 and result["pulled"] == 0 and result["unseated"] == 0
        assert result["seat_min"] > seat and result["pad_min"] > pad
        assert result["drag_max"] < 0.35  # guide friction stays far below a house's weight
    even = statics.survey(P, 0.25, step=60)
    assert 1.1 < even["torque_min"] and even["torque_max"] < 2.0  # N mm at the crank
    assert even["torque_max"] / even["torque_min"] < 1.6
    assert abs(even["torque_forward"] - even["torque_back"]) < 0.3
    # at 0.3 the guide still sits; an end house, heavier on one side, starts to need the cam
    limit = statics.survey(P, 0.3, step=60)
    assert limit["wedged"] == 0 and limit["unseated"] == 0 and limit["pulled"] < 0.03


def test_cam_takes_the_houses_along_when_friction_is_high():
    # Dry printed PLA can reach 0.45. A house then leaves a guide seat for its stop in part
    # of the turn, and the cam pulls on a lower pad to bring it down or into its lean. Nothing
    # wedges, and the crank stays light. At 0.55 it still turns, with uneven effort; at 0.6
    # the model finds a pose without balance.
    dry = statics.survey(P, 0.45, step=60)
    assert dry["wedged"] == 0 and 0 < dry["pulled"] < 0.25
    assert dry["drag_max"] < 0.7 and dry["torque_max"] < 3.6
    assert dry["torque_max"] / dry["torque_min"] < 1.7
    worst = statics.survey(P, 0.55, step=60)
    assert worst["wedged"] == 0 and worst["torque_max"] < 7


def test_a_house_off_its_seat_moves_less_than_a_millimetre_at_the_roof():
    upper, lower = statics.roof_play(P)
    assert 0.3 < lower < upper < 0.9


def test_mechanism_is_hidden_from_the_front_and_from_counter_height():
    # a reduced set of views and a coarse sampling; docs/motion-proof.md has the full sweep
    for turn in (90, 630):
        params = Params(turn=turn)
        seen = hidden.exposed(
            build(params),
            params,
            spacing=2.0,
            azimuths=(-60, -30, -10, -5, 0, 5, 10, 30, 60),
            elevations=(0, 10, 20, 40, 60),
        )
        assert not seen, (turn, seen)


STEPS = (40.0, 25.0, 15.0, 8.0, 4.0, 2.0, 1.0)  # how far a part is moved back along its path


def _inside(built):
    sleds = {f"sled_{i + 1}": built[f"sled_{i + 1}"] for i in range(P.houses)}
    return sleds, {k: built[k] for k in ("base", "cam", "reference_axle")} | sleds


def test_sleds_cam_and_rear_panel_go_in_along_their_assembly_paths():
    # Order: sleds from above, cam with its axle from the back, rear panel from the back.
    # Each part is moved back along its path and must not run into what is already in place.
    built = build(Params(turn=200))
    sleds, inside = _inside(built)
    for name, sled in sleds.items():
        for lift in STEPS:
            assert not overlaps({"base": built["base"], name: Pos(0, 0, lift) * sled}), (name, lift)
    for back in STEPS:  # the gear's mesh with the pinion is left out: it is turned into mesh
        cam = {k: Pos(0, back, 0) * built[k] for k in ("cam", "reference_axle")}
        assert not overlaps({"base": built["base"], **sleds, **cam}), ("cam", back)
    for back in STEPS:
        panel = {"rear_panel": Pos(0, back, 0) * built["rear_panel"]}
        assert not overlaps({**inside, **panel}), ("rear panel", back)


def test_a_sled_on_the_crest_is_upright_and_its_left_neighbour_leans_away():
    step = 360 * P.ratio * P.waves / P.houses  # crank degrees from one house's crest to the next
    assert step == pytest.approx(114.75)
    for i in range(P.houses):
        turn = wave.crest(P, i)
        assert 0 <= turn < PASS
        at = wave.pose(P, i, turn)
        assert at.lean == pytest.approx(0, abs=0.01)
        assert at.rise > max(wave.pose(P, i, turn + d).rise for d in (-20, 20))
        if i:
            assert wave.pose(P, i - 1, turn).lean > 3.5  # its top leans away, towards -X
            assert (turn - wave.crest(P, i - 1)) % PASS == pytest.approx(step)


DROP = (60.0, 45.0, 35.0, 25.0, 20.0, 15.0, 12.0, 10.0, 8.0, 6.0, 4.0, 3.0, 2.0, 1.0, 0.5)


def _house_goes_in(i: int, turn: float):
    """What house `i` runs into, lowered straight down with the crank at `turn`: the base,
    the mechanism, the rear panel and the houses on its left are in place."""
    built = build(Params(turn=turn))
    name = f"house_{i + 1}"
    placed = {
        k: v for k, v in built.items() if not k.startswith("house_") or int(k.split("_")[1]) <= i
    }
    for lift in DROP:
        if hits := overlaps({**placed, name: Pos(0, 0, lift) * built[name]}, moving={name}):
            return lift, hits
    return None


def test_houses_go_in_from_above_one_after_another():
    # Houses from above, starting at the end away from the handwheel: each block has a lap
    # under its right-hand neighbour. A house goes in while its sled stands on the crest of
    # the wave: it is upright, so it comes straight down over its blade, and the house on its
    # left leans away from it. A third of a turn of the handwheel brings the next sled up.
    for i in range(P.houses):
        assert not (hit := _house_goes_in(i, wave.crest(P, i))), (i + 1, hit)


@pytest.mark.parametrize("off", [-30.0, 90.0])
def test_a_house_goes_in_with_the_handwheel_well_off_the_crest(off):
    # The assembler need not find the crest exactly: from 30 degrees of the handwheel before
    # it to 90 past it, every kind of joint and both ends of the street still go in clear.
    for i in (0, 1, 2, P.houses - 1):
        assert not (hit := _house_goes_in(i, wave.crest(P, i) + off)), (i + 1, off, hit)


@pytest.mark.parametrize(
    "values",
    [
        {"turn": float("nan")},
        {"cam_radius": 7.0, "amplitude": 4.5},
        {"sled_width": 20, "pitch": 20},
        {"joint": 0.6, "pivot_gap": 0.6},
        {"axle_length": 180},
        {"bead": 18, "amplitude": 4.5},
        {"capture_span": 16, "capture_width": 4},
        {"lap_floor": 4, "block": 10},
        {"unknown": 1},
    ],
)
def test_bad_parameters_fail_before_the_kernel(values):
    with pytest.raises(ValidationError):
        Params(**values)
