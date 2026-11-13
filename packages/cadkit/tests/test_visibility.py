"""Parallel-ray visibility against known answers."""

import math

import numpy as np
import pytest
from build123d import Box, Pos, Sphere
from cadkit.visibility import (
    occluded,
    seen_points,
    sphere_views,
    surface_samples,
    view_vector,
    visible_share,
)


def test_view_vectors():
    assert view_vector(0, 0) == pytest.approx((0, -1, 0))
    assert view_vector(90, 0) == pytest.approx((1, 0, 0))
    assert view_vector(0, 90) == pytest.approx((0, 0, 1), abs=1e-12)
    views = sphere_views(200, min_elevation=-10)
    assert 100 < len(views) < 130
    assert all(np.linalg.norm(v) == pytest.approx(1) for v in views)
    assert min(v[2] for v in views) >= math.sin(math.radians(-10))


def test_samples_carry_their_area():
    points, normals, weights = surface_samples(Box(10, 20, 30), spacing=1.0)
    assert weights.sum() == pytest.approx(2 * (200 + 300 + 600))
    assert len(points) == len(normals) == len(weights) > 1500
    assert np.abs(points).max(0) == pytest.approx((5, 10, 15))


def test_ball_behind_a_slot():
    ball = Pos(0, 20, 0) * Sphere(5)
    wall = Box(40, 2, 40) - Box(4, 4, 40)
    # through a 4 mm slot a viewer in front sees the band |x| < 2 of the near hemisphere:
    # a zone of height 4 on a sphere of radius 5, which is 4 / 10 of the hemisphere
    assert visible_share([ball], [wall], view_vector(0, 0), spacing=0.5) == pytest.approx(
        0.4, abs=0.02
    )
    assert visible_share([ball], [wall], view_vector(30, 0), spacing=0.5) == 0.0
    assert visible_share([ball], [wall], view_vector(180, 0), spacing=0.5) == 1.0
    # with the wall as part of the baseline, it hides nothing more
    assert visible_share([ball], [], view_vector(0, 0), spacing=0.5, baseline=[wall]) == 1.0


def test_enclosed_part_is_never_seen():
    core = Sphere(3)
    shell = Box(20, 20, 20) - Box(16, 16, 16)
    assert len(seen_points([core], [shell], sphere_views(40), spacing=1.0)) == 0
    holed = shell - Pos(0, -9, 0) * Box(2, 4, 2)
    found = seen_points([core], [holed], [view_vector(0, 0), view_vector(90, 0)], spacing=0.5)
    assert len(found) > 0
    assert np.abs(found[:, [0, 2]]).max() <= 1.0 + 1e-9  # only through the 2 mm window
    assert found[:, 1].max() < 0  # and only the near side


def test_occlusion_ignores_what_lies_behind_and_touching():
    triangle = np.array([[[-5, 0, -5], [5, 0, -5], [0, 0, 5]]], float)
    points = np.array([[0, 1, 0], [0, -1, 0], [20, 1, 0], [0, 0.01, 0]], float)
    hidden = occluded(points, view_vector(0, 0), triangle)
    assert hidden.tolist() == [True, False, False, False]
