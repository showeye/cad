"""Involute gears: standard dimensions, a pair that meshes without touching, and refusals."""

import math

import pytest
from build123d import Pos, Rot
from cadkit.features.gears import (
    centre_distance,
    gear_outline,
    meshing_angle,
    pitch_radius,
    spur_gear,
)
from cadkit.process import FDM
from cadkit.validate import overlaps, validate


def test_standard_dimensions():
    outline = gear_outline(1.0, 33)
    radii = [math.hypot(x, y) for x, y in outline]
    assert max(radii) == pytest.approx(pitch_radius(1.0, 33) + 1.0)
    assert min(radii) == pytest.approx(pitch_radius(1.0, 33) - 1.25)
    assert centre_distance(1.0, 11, 33) == 22
    gear = spur_gear(1.0, 33, 6, bore=4.3)
    assert not validate(gear, FDM)
    assert gear.bounding_box().size.Z == pytest.approx(6)


def test_shifted_pair_meshes_through_a_tooth_without_touching():
    pinion = spur_gear(1.0, 11, 6, shift=0.4, backlash=0.1)
    wheel = spur_gear(1.0, 33, 6, shift=-0.4, backlash=0.1)
    spacing = centre_distance(1.0, 11, 33)
    for i in range(13):
        angle = i * 360 / 11 / 12
        a = Rot(0, 0, angle) * pinion
        b = Pos(spacing, 0, 0) * Rot(0, 0, meshing_angle(11, 33, angle)) * wheel
        assert not overlaps({"pinion": a, "wheel": b})
        assert 0.05 < a.distance_to(b) < 0.15
    # out of phase by half a tooth the same pair collides: the meshing angle matters
    wrong = Pos(spacing, 0, 0) * Rot(0, 0, meshing_angle(11, 33, 0) + 180 / 33) * wheel
    assert overlaps({"pinion": pinion, "wheel": wrong})


def test_meshing_angle_in_any_direction():
    pinion = spur_gear(1.0, 11, 4, shift=0.4, backlash=0.1)
    wheel = spur_gear(1.0, 33, 4, shift=-0.4, backlash=0.1)
    spacing = centre_distance(1.0, 11, 33)
    for towards in (37.0, 143.0, 250.0):
        t = math.radians(towards)
        at = Pos(spacing * math.cos(t), spacing * math.sin(t), 0)
        for angle in (0.0, 11.0, 200.0):
            b = at * Rot(0, 0, meshing_angle(11, 33, angle, towards)) * wheel
            assert not overlaps({"pinion": Rot(0, 0, angle) * pinion, "wheel": b})


@pytest.mark.parametrize(
    "values",
    [
        {"module": 0, "teeth": 12},
        {"module": 1, "teeth": 4},
        {"module": 1, "teeth": 12, "backlash": 2},
    ],
)
def test_impossible_gears_are_refused(values):
    with pytest.raises(ValueError):
        gear_outline(**values)
