"""Real-rig interference, finite contacts, rigid transforms and parameter guards."""

import json
import math

import numpy as np
import pytest
from build123d import Pos, Rot
from cadkit.export import export_model
from cadkit.validate import overlaps
from fala.model import _CENTRES, Params, _cam, _neutral, _pose, _render_poses, build, model
from pydantic import ValidationError


def test_full_turn_actual_cad_clearance_and_contact():
    for angle in range(0, 360, 5):
        parts = build(Params(angle=angle))
        assert not (hits := overlaps(parts)), f"At {angle} degrees: {hits}"
        for i in (1, 2):
            assert parts["cam_and_thumbwheel"].distance_to(parts[f"carriage_{i}"]) < 1e-5


def test_finite_contacts_clearance_and_rigid_support_motion():
    p = Params()
    for angle in range(0, 360, 2):
        q = Params(angle=angle)
        for x in _CENTRES:
            pose = _pose(q, x)
            assert 0.3 < min(pose.return_gaps) < max(pose.return_gaps) < 0.51
            assert abs(pose.lean) < 6.1
            # Contact X changes with phase: neither support is pinned in X.
            # A tilted pad also contributes to the contact's X location.
            t = math.radians(pose.lean)
            for xx, yy, zz in pose.contacts:
                u = (xx - x) * math.cos(t) + (zz - pose.height) * math.sin(t)
                assert (
                    min(abs(u - p.support_span / 2), abs(u + p.support_span / 2))
                    <= p.pad_width / 2 + 1e-9
                )
                assert abs(yy) <= p.amplitude
    assert _pose(p, 11).contacts != _pose(Params(angle=90), 11).contacts
    assert _cam(p).centre(11, 0) == pytest.approx(_cam(p).centre(11, 360))


def test_render_matrices_match_rigid_cad_and_reverse():
    p = Params(angle=17)
    base = build(p)
    frames = _render_poses(p, steps=12)
    assert len(frames) == 24
    for index in (0, 1, 3, 6, 12, 17, 23):
        step = index if index <= 12 else 24 - index
        target = build(Params(angle=17 + 30 * step))
        for name, value in frames[index].items():
            matrix = np.array(value)
            assert np.linalg.det(matrix[:3, :3]) == pytest.approx(1)
            assert matrix[:3, :3].T @ matrix[:3, :3] == pytest.approx(np.eye(3), abs=1e-12)
            point = matrix @ np.array([*base[name].center(), 1])
            assert point[:3] == pytest.approx(tuple(target[name].center()), abs=1e-5)
    for i in range(1, 12):
        for name in frames[i]:
            assert np.array(frames[i][name]) == pytest.approx(np.array(frames[24 - i][name]))


def test_sampled_axial_threading_then_lowering_into_frame():
    p = Params()
    cam, frame, neutral = _neutral(p)
    cam = Pos(0, 0, p.shaft_height) * cam

    def carriage(x, lift=0):
        pose = _pose(p, x)
        return Pos(x, 0, p.shaft_height + pose.height + lift) * Rot(0, -pose.lean, 0) * neutral

    # Rearward insertion is blocked by the keel; thread over the left axial
    # end instead, right carriage first. Then lower the whole group together.
    for destination in (33, 11):
        for x in range(-25, destination + 1, 2):
            group = {"cam": cam, "inserting": carriage(x)}
            if destination == 11:
                group["right"] = carriage(33)
            assert not (hits := overlaps(group)), (x, hits)
    for lift in range(0, 51, 2):
        group = {
            "frame": frame,
            "cam": Pos(0, 0, lift) * cam,
            "left": carriage(11, lift),
            "right": carriage(33, lift),
        }
        assert not (hits := overlaps(group)), (lift, hits)


def test_collision_checks_preserve_deterministic_exports(tmp_path):
    # Start from fresh topology: destructive OCCT intersections can silently
    # raise edge tolerances on tangent pads, changing STEP uncertainty records.
    _neutral.cache_clear()
    before = export_model(model, "contact_rig", tmp_path / "before")
    initial = json.loads((before / "manifest.json").read_text())["files"]
    for phase in range(0, 360, 15):
        assert not overlaps(build(Params(angle=phase)))
    after = export_model(model, "contact_rig", tmp_path / "after")
    final = json.loads((after / "manifest.json").read_text())["files"]
    assert initial == final


@pytest.mark.parametrize(
    "values",
    [
        {"angle": float("nan")},
        {"cam_radius": 9.5, "amplitude": 4, "jaw_wall": 3},
        {"fit": 0.1},
        {"pad_depth": 20},
        {"unknown": 1},
    ],
)
def test_invalid_parameters_fail_before_kernel(values):
    with pytest.raises(ValidationError):
        Params(**values)
