"""Recoil anchor escapement: construction, one tooth per two beats, recoil and bad inputs."""

import math

import pytest
from cadkit.features.escapement import RecoilEscapement

# the clockwork king's escapement
KING = RecoilEscapement(teeth=25, tip_radius=13.0, span=4, release=4.0, drop=0.5, land=0.2)


def test_construction():
    assert KING.pitch == pytest.approx(14.4)
    assert KING.half_span == pytest.approx(32.4)
    # the lines from the pivot to the pallets touch the tip circle
    assert KING.pivot_distance == pytest.approx(13.0 / math.cos(math.radians(32.4)))
    assert math.hypot(KING.lever, KING.tip_radius) == pytest.approx(KING.pivot_distance)
    assert KING.engagement == pytest.approx(KING.lever * math.radians(4.0))
    # half a pitch along the tip circle is the travel on a pallet plus the drop
    assert KING.impulse + KING.drop == pytest.approx(math.pi * 13.0 / 25)
    assert 40 < KING.ramp < 50
    assert KING.beats(144) == pytest.approx(20)


def test_pallet_corners_stand_inside_the_tip_circle_on_the_tangent_lines():
    for nose, side in zip(KING.pallets(4.5), (1, -1)):
        corner, back, ramp_end = nose
        assert math.hypot(*corner) == pytest.approx(KING.tip_radius - KING.engagement)
        assert math.degrees(math.atan2(corner[1], corner[0])) == pytest.approx(
            90 + side * KING.half_span
        )
        # both faces lead out of the wheel
        assert math.hypot(*back) > KING.tip_radius and math.hypot(*ramp_end) > KING.tip_radius


def test_wheel_outline_has_every_tooth_on_the_tip_circle():
    outline = KING.wheel_outline(depth=3.2)
    assert len(outline) == 4 * 25
    radii = sorted(math.hypot(x, y) for x, y in outline)
    assert radii[0] == pytest.approx(9.8, abs=0.2) and radii[-1] == pytest.approx(13.0, abs=1e-3)
    with pytest.raises(ValueError):
        KING.wheel_outline(depth=4.0)  # flanks of neighbouring teeth would cross


def test_one_tooth_passes_for_every_two_beats():
    """Rock the anchor slowly while the wheel is pushed on: it advances one pitch per cycle."""
    release = KING.release
    swing = [release, 0.0, -release - 0.2, -release - 5, -release - 0.2, 0.0, release + 0.2]
    swing += [release + 5, release + 0.2]
    progress = -math.degrees(KING.impulse / KING.tip_radius)  # a tooth has just landed
    seen = []
    for _ in range(2):
        for angle in swing:
            before, progress = progress, KING.settle(progress, angle)
            seen.append((angle, progress - before))
    first, second = seen[: len(swing)], seen[len(swing) :]
    assert sum(step for _, step in second) == pytest.approx(KING.pitch, abs=0.02)
    # the wheel is pushed back while the anchor swings on past the release: the recoil
    recoils = [step for angle, step in second if abs(angle) == release + 5]
    assert len(recoils) == 2 and all(step < -1.0 for step in recoils)
    assert all(step > 0 for angle, step in first[1:] if abs(angle) <= release + 0.2)


def test_free_run_at_each_release_is_about_the_drop():
    """At each release the wheel jumps by about the drop; the two pallets are not alike.

    The anchor turns, so a pallet does not move exactly straight into the wheel: the entry
    pallet gives 0.65 mm of free run and the exit pallet 0.44 mm for a nominal 0.5 mm.
    """
    progress = KING.settle(-math.degrees(KING.impulse / KING.tip_radius), KING.release)
    runs = []
    for sign in (-1, 1):  # the entry pallet lets go at -release, the exit pallet at +release
        jumps = []
        for tenth in range(-40, 44):
            before, progress = progress, KING.settle(progress, sign * tenth / 10)
            jumps.append((math.radians(progress - before) * KING.tip_radius, sign * tenth / 10))
        run, at = max(jumps)
        assert abs(at) == pytest.approx(KING.release, abs=0.15)
        runs.append(run)
    assert runs == pytest.approx([0.65, 0.44], abs=0.05)
    assert 2 * KING.drop <= sum(runs) < 2 * KING.drop + 0.2  # a little more than nominal


def test_a_released_tooth_is_not_caught_by_the_pallet_behind_it():
    # just after a tooth leaves the entry pallet the tips are clear, with the drop to spare
    assert KING.interference(0.05, -KING.release - 0.2) == 0
    # a wheel held still under a pallet that comes down is met by it
    assert KING.interference(-3.0, KING.release) > 0.1


@pytest.mark.parametrize(
    "values",
    [
        {"teeth": 6},  # too few teeth
        {"span": 7},  # anchor reaches round more than a quarter of the wheel
        {"drop": 2.0},  # no travel left on a pallet
        {"release": 10.0},  # ramp steeper than the teeth allow
    ],
)
def test_impossible_escapements_are_refused(values):
    given = {"teeth": 25, "tip_radius": 13.0, "span": 4, "release": 4.0, "drop": 0.5, **values}
    with pytest.raises(ValueError):
        RecoilEscapement(**given)
