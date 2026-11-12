"""Rigid presentation transforms must agree with the CAD kernel's axis convention."""

import numpy as np
import pytest
from build123d import Axis, Vertex
from cadkit.features.motion import rigid_transform


@pytest.mark.parametrize("axis", [(0, 0, 1), (0, -2, 0), (-0.6066, 0, 0.795)])
def test_transform_matches_kernel(axis):
    origin, point, shift = (3, 7, -2), (11, -4, 9), (2, -1, 5)
    matrix = np.array(rigid_transform(axis, origin, 125, shift))
    expected = Vertex(*point).rotate(Axis(origin, axis), 125).center()
    assert (matrix @ [*point, 1])[:3] == pytest.approx(np.array(tuple(expected)) + shift, abs=1e-10)
    assert matrix[:3, :3].T @ matrix[:3, :3] == pytest.approx(np.eye(3))
    assert np.linalg.det(matrix[:3, :3]) == pytest.approx(1)
    assert (matrix @ [*origin, 1])[:3] == pytest.approx(np.array(origin) + shift)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"axis": (0, 0, 0)},
        {"angle": float("nan")},
        {"origin": (1, 2)},
        {"shift": (float("inf"), 0, 0)},
    ],
)
def test_invalid_rigid_transform(kwargs):
    with pytest.raises(ValueError):
        rigid_transform(**kwargs)
