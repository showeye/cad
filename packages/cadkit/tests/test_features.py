"""Shared features must stay dimensionally correct and valid away from product defaults."""

import itertools
import math

import pytest
from cadkit.features.mechanical import bar_between, cord_loop, hex_prism, link, spoked_wheel
from cadkit.features.motion import Belt, slider_crank
from cadkit.features.text import engraving
from cadkit.process import FDM
from cadkit.validate import validate


@pytest.mark.parametrize("angle", range(0, 360, 7))
def test_slider_closes_at_every_angle(angle):
    x, z, slider = slider_crank(8, 37, angle)
    assert math.hypot(x - slider, z) == pytest.approx(37)
    assert -45 <= slider <= -29


def test_belt_tangency_and_length():
    belt = Belt((10, 44), 31.8, (69, 104), 11.8)
    for angle in belt.normal_angles:
        n = math.cos(angle), math.sin(angle)
        a = [c + belt.r1 * v for c, v in zip(belt.c1, n)]
        b = [c + belt.r2 * v for c, v in zip(belt.c2, n)]
        assert sum((v - u) * w for u, v, w in zip(a, b, n)) == pytest.approx(0, abs=1e-10)
    pts = belt.points(500)
    assert sum(math.dist(a, b) for a, b in itertools.pairwise(pts)) == pytest.approx(
        belt.length, abs=0.001
    )
    assert belt.point_at(0) == pytest.approx(belt.point_at(belt.length), abs=0.001)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: hex_prism(2.5, 70),
        lambda: link(37, 5.5, 2.8, 3.4),
        lambda: spoked_wheel(32, 6.5, 4.5),
        lambda: spoked_wheel(12, 4, 3.4, 6),
        lambda: bar_between((1, 2, 3), (4, 8, 19), 2, 3),
    ],
)
def test_feature_quality(factory):
    assert not validate(factory(), FDM)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: slider_crank(8, 7, 0),
        lambda: Belt((0, 0), 10, (1, 0), 2),
        lambda: hex_prism(0, 2),
        lambda: link(2, 3, 1, 0.5),
        lambda: spoked_wheel(3, 4, 1),
        lambda: bar_between((0, 0, 0), (0, 0, 0), 2, 3),
    ],
)
def test_bad_features_rejected(factory):
    with pytest.raises(ValueError):
        factory()


def test_exact_cord_volume():
    belt = Belt((10, 44), 31.8, (69, 104), 11.8)
    shape = cord_loop(belt)
    assert not validate(shape, FDM)
    assert shape.volume == pytest.approx(math.pi * 0.55**2 * belt.length, rel=1e-6)


def test_engraving_uses_downward_tool_convention():
    tool = engraving("CARNALL", 4, 0.8)
    assert tool.is_valid
    assert tool.bounding_box().max.Z == pytest.approx(0, abs=1e-6)
    assert tool.bounding_box().min.Z == pytest.approx(-0.8)
