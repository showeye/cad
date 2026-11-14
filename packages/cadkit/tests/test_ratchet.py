"""Ratchet wheel and pawl: outline, the nose in a tooth's corner, riding over a tooth, holding."""

import math

import numpy as np
import pytest
from cadkit.features.ratchet import Pawl, Ratchet

# the clockwork pawn's wheel, and a click above it
WHEEL = Ratchet(teeth=16, tip=8.0, depth=1.4, rake=8.0, land=0.3)
CLICK = Pawl(length=8.6, nose=0.3)
PIVOT = (0.0, 10.6)


def test_outline_has_every_tooth_between_root_and_tip():
    outline = WHEEL.outline()
    assert len(outline) == 3 * 16 and WHEEL.pitch == pytest.approx(22.5)
    radii = [math.hypot(x, y) for x, y in outline]
    assert radii[0::3] == pytest.approx([6.6] * 16) and radii[1::3] == pytest.approx([8.0] * 16)
    # a tooth further on, the outline is the same
    turned = WHEEL.outline(22.5)
    assert np.array(turned[:-3]) == pytest.approx(np.array(outline[3:]))
    # counter-clockwise, so the area is positive
    x, y = np.array(outline).T
    area = (x * np.roll(y, -1) - np.roll(x, -1) * y).sum() / 2
    assert math.pi * 6.6**2 < area < math.pi * 8.0**2


def test_face_is_undercut_and_the_back_slopes():
    foot, top, end = WHEEL.outline()[:3]
    assert top == pytest.approx((8.0, 0.0)) and math.dist(top, end) == pytest.approx(0.3, abs=1e-3)
    # the foot of the face stands ahead of its top: 8 degrees from the radius
    lean = math.degrees(math.atan2(foot[1] - top[1], top[0] - foot[0]))
    assert lean == pytest.approx(8.0)
    assert Ratchet(16, 8.0, 1.4, rake=0.0).outline()[0] == pytest.approx((6.6, 0.0))


def test_clearance_is_signed():
    assert WHEEL.clearance((20.0, 0.0)) == pytest.approx(12.0)
    assert WHEEL.clearance((20.0, 0.0), nose=1.5) == pytest.approx(10.5)
    assert WHEEL.clearance((0.0, 0.0)) < -6.0
    # just outside and just inside the land of the tooth at 0 degrees
    middle = math.degrees(0.15 / 8.0)
    out = (8.05 * math.cos(math.radians(middle)), 8.05 * math.sin(math.radians(middle)))
    assert WHEEL.clearance(out) == pytest.approx(0.05, abs=2e-3)
    assert WHEEL.clearance((out[0] * 0.99, out[1] * 0.99)) < 0
    # the same place on the wheel when the wheel has turned
    both = WHEEL.clearance([out, (0.0, 0.0)], turn=22.5 * 3)
    assert both[0] > 0 and both[1] < -6.0
    moved = (out[0] * math.cos(1.0) - out[1] * math.sin(1.0),) + (
        out[0] * math.sin(1.0) + out[1] * math.cos(1.0),
    )
    assert WHEEL.clearance(moved, turn=math.degrees(1.0)) == pytest.approx(0.05, abs=2e-3)


def test_nose_lies_in_the_corner_of_a_tooth():
    seat = WHEEL.seat(0.3)
    assert 6.6 < math.hypot(*seat) < 8.0
    assert WHEEL.clearance(seat, 0.3) == pytest.approx(0.0, abs=1e-9)
    # it cannot go further into the corner, and it is free further out of it
    foot = WHEEL.outline()[0]
    for along, free in ((-0.1, False), (0.1, True)):
        moved = (seat[0] + along * (seat[0] - foot[0]), seat[1] + along * (seat[1] - foot[1]))
        assert (WHEEL.clearance(moved, 0.3) > 0) is free
    with pytest.raises(ValueError):
        WHEEL.seat(1.5)


def test_seated_pawl_touches_and_is_held():
    turn, direction = WHEEL.seated(CLICK, PIVOT)
    assert 0 <= turn < WHEEL.pitch
    nose = CLICK.tip(PIVOT, direction)
    assert math.dist(nose, PIVOT) == pytest.approx(8.6)
    assert WHEEL.clearance(nose, 0.3, turn) == pytest.approx(0.0, abs=1e-9)
    assert nose[0] < 0  # counter-clockwise of a pivot that stands above the wheel
    # a tooth further on it is seated again
    assert WHEEL.clearance(nose, 0.3, turn + 22.5) == pytest.approx(0.0, abs=1e-9)
    # turned back, the face meets the nose; the push draws the pawl into the corner
    assert WHEEL.clearance(nose, 0.3, turn - 1.0) < -0.05
    assert WHEEL.locks(CLICK, PIVOT) > 0
    with pytest.raises(ValueError):
        WHEEL.seated(Pawl(1.0, 0.3), PIVOT)


def test_lock_follows_the_pivot():
    # a pivot on the tangent through the nose takes the push straight along the arm
    seat = WHEEL.seat(0.3)
    radius, at = math.hypot(*seat), math.atan2(seat[1], seat[0])
    behind = (
        seat[0] + 5.0 * math.sin(at),
        seat[1] - 5.0 * math.cos(at),
    )
    straight = WHEEL.locks(Pawl(5.0, 0.3), behind)
    # the face is undercut by 8 degrees, and its foot stands ahead of the radius through it
    assert 0 < straight < 12
    further = (behind[0] * 1.2, behind[1] * 1.2)  # a pivot further out holds more surely
    closer = (behind[0] * 0.93, behind[1] * 0.93)
    assert WHEEL.locks(Pawl(math.dist(further, seat), 0.3), further) > straight
    assert WHEEL.locks(Pawl(math.dist(closer, seat), 0.3), closer) < straight
    assert radius == pytest.approx(math.hypot(*seat))


def test_pawl_rides_over_a_tooth_and_falls_behind_it():
    turn, seated = WHEEL.seated(CLICK, PIVOT)
    angles = [seated]
    for step in range(1, 93):  # the wheel turns on by a tooth and a little more, 1/4 degree a step
        angles.append(WHEEL.falls(CLICK, PIVOT, turn + step * 0.25, angles[-1], seated + 30))
    lift = [seated - a for a in angles]  # the nose is lifted clockwise about its pivot
    assert all(value > -1e-3 for value in lift)
    assert max(lift) > 8 and 60 < lift.index(max(lift)) < 90  # highest on the tooth's tip
    # The face is undercut, so after exactly one tooth the nose still hangs on the tip's edge:
    # the wheel has to go a little further before the pawl falls behind the tooth.
    assert 2 < lift[90] < 4
    assert lift[91] < 0.1 and lift[92] > lift[91]  # fallen onto the next back, and rising again
    for step, angle in enumerate(angles):
        gap = WHEEL.clearance(CLICK.tip(PIVOT, angle), 0.3, turn + step * 0.25)
        assert -1e-9 <= gap < 1e-3
    # a wheel that then turns back lets the nose down into the corner, where `seated` has it
    back = WHEEL.falls(CLICK, PIVOT, turn + 22.5 + 0.1, angles[-1], seated + 30)
    assert 0 < seated - back < lift[91]


def test_pawl_falls_onto_its_stop_where_no_tooth_is():
    far = (0.0, 30.0)
    assert WHEEL.falls(CLICK, far, 0.0, -60.0, -90.0) == -90.0
    # let go from above the wheel, it comes down onto the teeth either way round
    for start, stop in ((-170.0, -100.0), (-10.0, -80.0)):
        angle = WHEEL.falls(CLICK, PIVOT, 3.0, start, stop)
        assert WHEEL.clearance(CLICK.tip(PIVOT, angle), 0.3, 3.0) == pytest.approx(0, abs=1e-3)


@pytest.mark.parametrize(
    "values",
    [
        {"teeth": 5, "tip": 8.0, "depth": 1.4},
        {"teeth": 16, "tip": 8.0, "depth": 4.5},
        {"teeth": 16, "tip": 8.0, "depth": 1.4, "rake": 25.0},
        {"teeth": 40, "tip": 8.0, "depth": 1.4},  # the back would be steeper than the face
    ],
)
def test_bad_ratchets_are_refused(values):
    with pytest.raises(ValueError):
        Ratchet(**values)
