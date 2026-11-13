"""Motion proof, as far as it stands: poses, capture, clearance and the forces in the guide.

Not yet covered, and listed in the README: the mechanism hidden from the viewing angles, the
assembly paths, the end joints of the street.
"""

import math

import numpy as np
import pytest
from cadkit.validate import overlaps
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
    # the two slab edges at a joint stay level with each other within a tenth of a millimetre
    half = P.pitch / 2
    for turn in range(0, PASS, 10):
        for i in range(P.houses - 1):
            a, b = wave.pose(P, i, turn), wave.pose(P, i + 1, turn)
            right = a.z + half * math.sin(math.radians(a.lean))
            left = b.z - half * math.sin(math.radians(b.lean))
            assert abs(right - left) < 0.1


def test_every_house_stays_captured():
    gaps = [wave.pose(P, i, turn).gap for i in range(P.houses) for turn in range(0, PASS, 5)]
    assert 0.3 < min(gaps) and max(gaps) < 0.6


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


def test_guide_is_seated_by_gravity_up_to_a_friction_of_three_tenths():
    for friction, seat in ((0.1, 0.2), (0.2, 0.12), (0.3, 0.02)):
        result = statics.survey(P, friction, step=60)
        assert result["unseated"] == 0 and result["seat_min"] > seat
        assert result["drag_max"] < 0.55  # guide friction stays well under a house's weight
    even = statics.survey(P, 0.3, step=60)
    assert 1.2 < even["torque_min"] and even["torque_max"] < 2.5  # N mm at the crank
    assert even["torque_max"] / even["torque_min"] < 1.9
    assert abs(even["torque_forward"] - even["torque_back"]) < 0.3


@pytest.mark.xfail(
    strict=True, reason="open defect: design notes, Motion proof as built, open point 1"
)
def test_guide_stays_seated_and_free_at_a_friction_of_0_45():
    # Dry printed PLA can reach this. Today the seat lets go in part of the turn (the house
    # may rock in its guide clearance) and the guide drag passes the house's weight.
    result = statics.survey(P, 0.45, step=60)
    assert result["unseated"] == 0 and result["drag_max"] < 0.8


@pytest.mark.parametrize(
    "values",
    [
        {"turn": float("nan")},
        {"cam_radius": 7.0, "amplitude": 4.5},
        {"sled_width": 20, "pitch": 20},
        {"joint": 0.6, "pivot_gap": 0.6},
        {"axle_length": 180},
        {"unknown": 1},
    ],
)
def test_bad_parameters_fail_before_the_kernel(values):
    with pytest.raises(ValidationError):
        Params(**values)
