"""Kinematics, rigid animation and exact sampled collision checks of the physical mechanism."""

import math

import numpy as np
import pytest
from build123d import Compound
from cadkit.validate import overlaps
from carnall.model import Params, _belt, _motion, _moving_neutral, _render_poses, build
from pydantic import ValidationError


def test_full_rotation_clearance():
    for angle in range(0, 360, 5):
        params = Params(angle=angle)
        parts = {n: s for n, s in build(params).items() if n != "reference_rope_witness"}
        moving = set(_moving_neutral(params.crank_radius, params.rod_length, params.fit, 0))
        # Also check cord against fixed architecture and frame, even though its envelope is static.
        moving.add("reference_flexible_cord")
        assert not (hits := overlaps(parts, moving)), f"At {angle} degrees: {hits}"


def test_envelope_stroke_and_speed():
    parts = build(Params())
    assert tuple(Compound(children=list(parts.values())).bounding_box().size) == pytest.approx(
        (180, 90, 120)
    )
    xs = [_motion(Params(angle=a))["front"]["slider"] for a in (0, 180)]
    assert abs(xs[0] - xs[1]) == pytest.approx(16)
    assert _motion(Params(angle=360))["sheave_angle"] == pytest.approx(360 * 31.8 / 11.8)
    belt = _belt(Params())
    assert belt.length == pytest.approx(310.04705260915534)
    t = math.radians(0.01)
    p0, p1 = belt.point_at(0), belt.point_at(t * belt.r1)
    # Cord travels in the same direction as wheel rotation at its upper contact point.
    high = belt.normal_angles[1]
    assert (p1[0] - p0[0]) * -math.sin(high) + (p1[1] - p0[1]) * math.cos(high) > 0


def test_rigid_animation_matches_cad_poses():
    params = Params()
    base = build(params)
    poses = _render_poses(params, steps=12)
    for i in (1, 3, 6, 9, 12, 18, 24):
        step = i if i <= 12 else 24 - i
        target = build(Params(angle=params.angle + 30 * step))
        for name, matrix in poses[i].items():
            centre = np.array([*base[name].center(), 1])
            transformed = (np.array(matrix) @ centre)[:3]
            assert transformed == pytest.approx(tuple(target[name].center()), abs=1e-5), name
    for matrix in poses[0].values():
        assert np.array(matrix) == pytest.approx(np.eye(4))
    assert poses[0] == poses[-1]


@pytest.mark.parametrize(
    "values",
    [
        {"crank_radius": 9, "rod_length": 35},
        {"crank_radius": 9, "rod_length": 39},
        {"fit": 0},
        {"angle": float("nan")},
        {"unknown": 1},
    ],
)
def test_invalid_params_fail_before_geometry(values):
    with pytest.raises(ValidationError):
        Params(**values)
