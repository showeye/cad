"""Involute gears and racks: standard dimensions, pairs that mesh without touching, refusals."""

import math

import pytest
from build123d import Pos, Rot
from cadkit.features.gears import (
    centre_distance,
    gear_outline,
    meshing_angle,
    pitch_radius,
    rack,
    rack_offset,
    rack_outline,
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


def test_rack_dimensions():
    outline = rack_outline(1.0, 3, depth=2.5, shift=0.4)
    xs = [x for x, _ in outline]
    ys = [y for _, y in outline]
    assert max(xs) == pytest.approx(1.0 - 0.4)  # addendum of 1 module, set back by the shift
    assert min(xs) == pytest.approx(-0.4 - 1.25 - 2.5)
    assert (min(ys), max(ys)) == pytest.approx((0, 3 * math.pi))
    solid = rack(1.0, 3, 4.6, depth=2.5, shift=0.4, backlash=0.1)
    assert not validate(solid, FDM)
    assert solid.bounding_box().size.Z == pytest.approx(4.6)


def test_rack_meshes_with_a_shifted_pinion_through_a_tooth_without_touching():
    pinion = spur_gear(1.0, 10, 5, shift=0.4, backlash=0.1)
    bar = Pos(0, -3 * math.pi, 0) * rack(1.0, 6, 5, depth=2.5, shift=0.4, backlash=0.1)
    axis = Pos(pitch_radius(1.0, 10), 0, 0)
    for i in range(13):
        angle = i * 36 / 12
        gear = axis * Rot(0, 0, angle) * pinion
        moved = Pos(0, rack_offset(1.0, 10, angle), 0) * bar
        assert not overlaps({"pinion": gear, "rack": moved})
        assert 0.03 < gear.distance_to(moved) < 0.15
    # half a pitch out of phase the same pair collides
    wrong = Pos(0, rack_offset(1.0, 10, 0) + math.pi / 2, 0) * bar
    assert overlaps({"pinion": axis * pinion, "rack": wrong})


def test_rack_offset_follows_the_turn():
    # a counter-clockwise turn of the gear carries the rack towards -Y by radius * angle
    a, b = rack_offset(1.0, 10, 0.0), rack_offset(1.0, 10, 10.0)
    assert (a - b) % math.pi == pytest.approx(5 * math.radians(10))


@pytest.mark.parametrize(
    "values",
    [
        {"module": 0, "teeth": 3, "depth": 2},
        {"module": 1, "teeth": 0, "depth": 2},
        {"module": 1, "teeth": 3, "depth": 0},
        {"module": 1, "teeth": 3, "depth": 2, "backlash": 1.0},
    ],
)
def test_impossible_racks_are_refused(values):
    with pytest.raises(ValueError):
        rack_outline(**values)
