"""Independent surface, rigid-body and limiting-case checks for flat-pad cams."""

import math

import pytest
from cadkit.features.cams import HelicalCam


def test_concentric_limit_and_exact_return_gap():
    cam = HelicalCam(9, 0, 200)
    p = cam.flat_pads(11, 123, 16, 2.4, 5, 18.4, 32)
    assert p.height == pytest.approx(14)
    assert p.lean == pytest.approx(0, abs=1e-12)
    assert p.return_gaps == pytest.approx((0.4, 0.4))


def test_contacts_lie_on_both_cam_and_rigid_pad_planes():
    cam = HelicalCam(9, 3.5, 176 / 0.85)
    for phase in range(0, 360, 3):
        p = cam.flat_pads(33, phase, 16, 2.4, 5, 18.4, 32)
        t = math.radians(p.lean)
        for i, (x, y, z) in enumerate(p.contacts):
            cy, cz = cam.centre(x, phase)
            assert (y - cy) ** 2 + (z - cz) ** 2 == pytest.approx(81)
            u = (x - 33) * math.cos(t) + (z - p.height) * math.sin(t)
            w = -(x - 33) * math.sin(t) + (z - p.height) * math.cos(t)
            assert w == pytest.approx(-5, abs=1e-10)
            assert abs(u - (-8 if i == 0 else 8)) <= 1.2 + 1e-10
        # Independently sample upper/lower cam silhouettes at world X, then
        # transform into the carriage: no point may enter either solid jaw.
        for j in range(1001):
            x = 20 + j * 26 / 1000
            cy, cz = cam.centre(x, phase)
            for z, upper in ((cz + 9, True), (cz - 9, False)):
                u = (x - 33) * math.cos(t) + (z - p.height) * math.sin(t)
                w = -(x - 33) * math.sin(t) + (z - p.height) * math.cos(t)
                if min(abs(u - 8), abs(u + 8)) <= 1.2:
                    assert w <= -5 + 1e-9 if upper else w >= -23.4 - 1e-9


def test_periodicity_and_signed_phase_reversal():
    cam = HelicalCam(9, 3.5, 176 / 0.85)
    for angle in (0, 17, 90, 213):
        a = cam.flat_pads(11, -angle, 16, 2.4, 5, 18.4, 32)
        b = cam.flat_pads(11, 360 - angle, 16, 2.4, 5, 18.4, 32)
        assert (a.height, a.lean, *a.return_gaps) == pytest.approx(
            (b.height, b.lean, *b.return_gaps)
        )


def test_return_gap_uses_the_surface_projection_inside_each_finite_pad():
    cam = HelicalCam(9, 3.5, 176 / 0.85)
    p = cam.flat_pads(11, 30, 16, 2.4, 5, 18.4, 32)
    t = math.radians(p.lean)
    gaps = [[], []]
    for j in range(60001):
        x = -2 + j * 26 / 60000
        z = cam.centre(x, 30)[1] - 9
        u = (x - 11) * math.cos(t) + (z - p.height) * math.sin(t)
        w = -(x - 11) * math.sin(t) + (z - p.height) * math.cos(t)
        for i, centre in enumerate((-8, 8)):
            if abs(u - centre) <= 1.2:
                gaps[i].append(w + 23.4)
    assert tuple(min(g) for g in gaps) == pytest.approx(p.return_gaps, abs=1e-5)


def test_insufficient_capture_opening_reports_interference():
    p = HelicalCam(9, 3.5, 200).flat_pads(11, 0, 16, 2.4, 5, 17, 32)
    assert max(p.return_gaps) < 0


@pytest.mark.parametrize("args", [(9, 9, 200), (9, -1, 200), (9, 3, 0), (9, math.nan, 200)])
def test_invalid_cam_dimensions(args):
    with pytest.raises(ValueError):
        HelicalCam(*args)


def test_narrow_pad_cannot_use_broad_pad_equations():
    with pytest.raises(ValueError, match="too narrow"):
        HelicalCam(9, 3.5, 200).flat_pads(11, 0, 16, 2.4, 5, 18.4, 2)
