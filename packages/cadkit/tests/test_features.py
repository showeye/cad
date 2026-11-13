"""Shared features must stay dimensionally correct and valid away from product defaults."""

import itertools
import math

import pytest
from build123d import Axis, Cylinder, Pos
from cadkit.features.mechanical import (
    bar_between,
    cam_groove,
    cord_loop,
    hex_prism,
    link,
    spoked_wheel,
)
from cadkit.features.motion import Belt, cam_pressure_angle, cam_rate, slider_crank, smooth_step
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


def _harmonic(angle):
    return 20 - 8 * math.cos(math.radians(angle))


def test_cam_profile_helpers():
    assert smooth_step(-1) == 0 and smooth_step(0.5) == 0.5 and smooth_step(2) == 1
    assert all(smooth_step(a / 50) < smooth_step((a + 1) / 50) for a in range(50))
    for angle in (0, 37, 90, 200):
        assert cam_rate(_harmonic, angle) == pytest.approx(
            8 * math.sin(math.radians(angle)), abs=1e-6
        )
    assert cam_pressure_angle(_harmonic, 0) == pytest.approx(0, abs=1e-6)
    assert cam_pressure_angle(_harmonic, 90) == pytest.approx(math.degrees(math.atan2(8, 20)))


def test_cam_groove_fits_its_follower_at_every_angle():
    tool = cam_groove(_harmonic, width=3.3, depth=2.4)
    box = tool.bounding_box()
    assert box.min.Z == pytest.approx(-2.4) and 0 < box.max.Z <= 0.25  # at z=0, pointing -Z
    disc = Pos(0, 0, -2) * Cylinder(32, 4) - tool
    assert disc.is_valid and len(disc.solids()) == 1
    for turn in range(0, 360, 15):
        # a pin on the +Y line at the profile radius, with the cam turned counter-clockwise
        pin = Pos(0, _harmonic(turn), -1.2) * Cylinder(1.5, 2.2)
        common = disc.rotate(Axis.Z, turn) & pin
        assert common is None or common.volume < 1e-6, turn
        loose = Pos(0, _harmonic(turn) + 1.2, -1.2) * Cylinder(1.5, 2.2)
        assert (disc.rotate(Axis.Z, turn) & loose).volume > 0.1, turn
    with pytest.raises(ValueError):
        cam_groove(lambda a: 1.0, width=3, depth=2)
    with pytest.raises(ValueError):
        cam_groove(_harmonic, width=0, depth=2)
