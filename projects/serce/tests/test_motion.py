"""Exact sampled interference checks and independent linkage closure conditions."""

import math

import numpy as np
import pytest
from cadkit.validate import overlaps, validate
from pydantic import ValidationError
from serce.model import _P, _U, _V, Params, _drive, _point, _render_poses, build, process

_MOVING = {"cam_ring", "slider", "reference_follower", "wing_left", "wing_right"}


def test_full_cycle_interference():
    for turn in range(361):
        assert not (hits := overlaps(build(Params(turn=turn)), _MOVING)), (turn, hits)
    # A moving-only sweep must not conceal static interference.
    assert not overlaps(build(Params()))


@pytest.mark.parametrize("fit", [0.3, 0.6])
def test_fit_endpoints(fit):
    for turn in (0, 90, 180):
        parts = build(Params(fit=fit, turn=turn))
        assert not validate(parts, process)
        assert not (hits := overlaps(parts)), (fit, turn, hits)


def test_circle_and_tail_closure():
    params = Params()
    previous = -1
    for turn in range(181):
        e, s, angle = _drive(Params(turn=turn))
        theta = math.radians(turn)
        # Independently place the follower on the circular groove.
        assert (e * math.sin(theta)) ** 2 + (
            s + params.groove_radius + e * math.cos(theta)
        ) ** 2 == pytest.approx(params.groove_radius**2)
        # Rotate the actual lever endpoint about the hinge and compare Y travel.
        neutral = np.array(
            _point(-2, -params.tail_radius * math.cos(math.radians(params.wing_travel / 2)), -e)
        )
        k = np.array(_V) / np.linalg.norm(_V)
        r = neutral - _P
        t = math.radians(-angle)
        rotated = (
            r * math.cos(t)
            + np.cross(k, r) * math.sin(t)
            + k * np.dot(k, r) * (1 - math.cos(t))
            + _P
        )
        assert rotated[1] == pytest.approx(s, abs=1e-7)
        assert angle >= previous
        previous = angle
    assert _drive(Params())[2] == pytest.approx(0)
    assert _drive(Params(turn=180))[2] == pytest.approx(params.wing_travel)
    assert np.dot(_U, _V) == pytest.approx(0)


def test_animation_matches_cad():
    params = Params(turn=90)
    base = build(params)
    frames = _render_poses(params, steps=24)
    for i in (0, 3, 6, 12, 18, 24):
        target = build(Params(turn=(params.turn + 15 * i) % 360))
        for name, matrix in frames[i].items():
            centre = np.array([*base[name].center(), 1])
            assert (np.array(matrix) @ centre)[:3] == pytest.approx(
                tuple(target[name].center()), abs=1e-6
            )
    assert frames[0] == frames[-1]


@pytest.mark.parametrize(
    "values",
    [
        {"turn": -1},
        {"turn": 361},
        {"turn": float("nan")},
        {"fit": 0.1},
        {"wall": 0},
        {"wing_travel": 150},
        {"unknown": 1},
    ],
)
def test_invalid_parameters(values):
    with pytest.raises(ValidationError):
        Params(**values)
