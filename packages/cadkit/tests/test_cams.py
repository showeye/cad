"""Corkscrew cam: limiting cases, rigid-body consistency and agreement with the CAD solid."""

import math

import pytest
from build123d import Cylinder, Pos, Rot
from cadkit.features.cams import CorkscrewCam

CAM = CorkscrewCam(8, 3.5, 176 / 0.85)
PADS = [(-8.0, 12.0), (8.0, 12.0)]  # nose centres 12 above the follower origin: noses at w = 0
CROWN = 12.0


def test_concentric_bar_carries_the_follower_level():
    cam = CorkscrewCam(8, 0, 200)
    seat = cam.seat(11, 123, PADS, CROWN)
    assert seat.height == pytest.approx(8)
    assert seat.lean == pytest.approx(0, abs=1e-9)
    assert cam.gap_below(11, 123, seat.height, seat.lean, (0, -16.4 - 5), 5) == pytest.approx(0.4)


def test_both_noses_touch_the_edge_and_nothing_else():
    for phase in range(0, 360, 3):
        seat = CAM.seat(33, phase, PADS, CROWN)
        t = math.radians(seat.lean)
        for (u, w), (x, y, z) in zip(PADS, seat.contacts):
            # the touching point is on the bar's upper edge, straight above the section centre
            cy, cz = CAM.centre(x, phase)
            assert y == pytest.approx(cy)
            assert z == pytest.approx(cz + CAM.radius)
            # and exactly one crown radius from the nose centre of the rigid follower
            nx = 33 + u * math.cos(t) - w * math.sin(t)
            nz = seat.height + u * math.sin(t) + w * math.cos(t)
            assert math.hypot(x - nx, z - nz) == pytest.approx(CROWN, abs=1e-9)
            # no other point of the edge is nearer to the nose centre than the crown radius
            for i in range(-40, 41):
                xx = nx + i * 0.25
                assert math.hypot(xx - nx, CAM.crest(xx, phase) - nz) >= CROWN - 1e-9


def test_lean_follows_the_wave_slope_and_the_cycle_closes():
    leans = [CAM.seat(0, phase, PADS, CROWN).lean for phase in range(0, 360, 2)]
    limit = math.degrees(math.atan(CAM.eccentricity * CAM.k))
    assert max(leans) == pytest.approx(-min(leans), abs=1e-6)
    assert 0.97 * limit < max(leans) < limit
    a, b = CAM.seat(5, 40, PADS, CROWN), CAM.seat(5, 400, PADS, CROWN)
    assert (a.height, a.lean) == pytest.approx((b.height, b.lean))
    # moving along the shaft is the same as turning it: the wave travels
    shifted = CAM.seat(5 + 10, 40 + math.degrees(CAM.k * 10), PADS, CROWN)
    assert (shifted.height, shifted.lean) == pytest.approx((a.height, a.lean))


def test_captured_gap_stays_open_and_narrow():
    # A central lower pad sees the bar's curvature between the two upper pads: the gap
    # breathes by the sagitta of the wave over the pad span, about 0.1 mm either way.
    gaps = []
    for phase in range(0, 360, 2):
        seat = CAM.seat(0, phase, PADS, CROWN)
        gaps.append(CAM.gap_below(0, phase, seat.height, seat.lean, (0, -16.4 - 5), 5))
    assert 0.28 < min(gaps) < 0.31 and 0.49 < max(gaps) < 0.53


def test_solid_agrees_with_the_equations():
    solid = CAM.solid(-20, 20, spacing=1.0)
    assert solid.is_valid
    for phase in (0, 70, 200):
        turned = Rot(-phase, 0, 0) * solid
        seat = CAM.seat(0, phase, PADS, CROWN)
        t = math.radians(seat.lean)
        for u, w in PADS:
            nx = u * math.cos(t) - w * math.sin(t)
            nz = seat.height + u * math.sin(t) + w * math.cos(t)
            nose = Pos(nx, 0, nz) * Rot(90, 0, 0) * Cylinder(CROWN, 30)
            assert turned.distance_to(nose) == pytest.approx(0, abs=2e-4)


@pytest.mark.parametrize(
    "values", [(8, 8, 200), (8, -1, 200), (8, 3.5, 0), (8, 3.5, 40), (math.nan, 1, 200)]
)
def test_impossible_cams_are_refused(values):
    with pytest.raises(ValueError):
        CorkscrewCam(*values)
