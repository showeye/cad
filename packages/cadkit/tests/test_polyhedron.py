"""Half-space polyhedra: exact offsets, single valid solids, clear failure on bad input."""

import math

import pytest
from cadkit.features.polyhedron import convex_solid, halfspace_solid, inset, prism_planes
from cadkit.process import FDM
from cadkit.validate import validate

CUBE = (
    [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
    [5, 5, 5, 5, 5, 5],
)


def test_cube_and_exact_offsets():
    cube = halfspace_solid(*CUBE)
    assert cube.volume == pytest.approx(1000)
    assert len(cube.faces()) == 6
    assert not validate(cube, FDM)
    wall = cube - halfspace_solid(*inset(CUBE, 1.5))
    assert wall.volume == pytest.approx(1000 - 7**3)
    # a kept plane does not move: the hollow stays open towards +Z
    open_top = halfspace_solid(*inset(CUBE, 1.5, keep=[4]))
    assert open_top.volume == pytest.approx(7 * 7 * 8.5)


def test_scaled_normals_and_redundant_planes():
    normals = [(2, 0, 0), (-1, 0, 0), (0, 3, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (1, 1, 0)]
    offsets = [10, 5, 15, 5, 5, 5, 100]
    assert halfspace_solid(normals, offsets).volume == pytest.approx(1000)


def test_empty_and_unbounded():
    assert halfspace_solid(*inset(CUBE, 4.9)) is None  # thinner than the smallest feature
    assert halfspace_solid(*inset(CUBE, 6.0)) is None
    with pytest.raises(ValueError):
        halfspace_solid(CUBE[0][:5], CUBE[1][:5])
    with pytest.raises(ValueError):
        halfspace_solid([(0, 0, 0)], [1])


def test_convex_solid_merges_coplanar_triangles():
    corners = [(x, y, z) for x in (0, 4) for y in (0, 3) for z in (0, 2)]
    box = convex_solid(corners + [(2, 1.5, 1)])  # an interior point changes nothing
    assert box.volume == pytest.approx(24)
    assert len(box.faces()) == 6


@pytest.mark.parametrize("sides", [6, 20])
def test_prism(sides):
    plain = halfspace_solid(*prism_planes(10, -2, 3, sides))
    assert plain.volume == pytest.approx(sides * 100 * math.tan(math.pi / sides) * 5)
    cut = halfspace_solid(*prism_planes(10, -2, 3, sides, chamfer=1))
    assert 0.9 * plain.volume < cut.volume < plain.volume
    assert not validate(cut, FDM)
    assert len(cut.faces()) == 3 * sides + 2
    with pytest.raises(ValueError):
        prism_planes(10, 3, -2, sides)
