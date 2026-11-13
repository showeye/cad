"""Independent geometric checks for the concept screening calculations."""

import importlib.util
import math
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "engineering" / "compare_drives.py"
SPEC = importlib.util.spec_from_file_location("fala_drive_screening", PATH)
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def test_section_endpoints_match_circle_geometry():
    y, z, chord = study.cam_section(0)
    assert (y, z) == (3.5, 0)
    assert y * y + chord * chord == pytest.approx(9**2)
    y, z, chord = study.cam_section(math.pi / 2)
    assert z == pytest.approx(3.5)
    assert chord == pytest.approx(9)


def test_rigid_support_incompatibility_is_not_hidden_by_pose():
    _, _, lean = study.pose(0, study.K * study.PITCH / 2)
    dz = 2 * study.AMPLITUDE * math.sin(study.K * study.PITCH / 2)
    assert study.PITCH / math.cos(lean) == pytest.approx(math.hypot(study.PITCH, dz))
    assert math.hypot(study.PITCH, dz) > study.PITCH + 0.1


def test_cycle_closes_and_reverse_retraces_for_every_unit():
    for index in range(study.COUNT):
        for phase in (0, 0.4, 1.7, 4.2):
            assert study.pose(index, phase) == pytest.approx(study.pose(index, phase + math.tau))
            assert study.pose(index, -phase) == pytest.approx(study.pose(index, math.tau - phase))


def test_sampled_lean_agrees_with_analytic_bound():
    exact = math.atan(2 * study.AMPLITUDE * math.sin(study.K * study.PITCH / 2) / study.PITCH)
    assert study.metrics()["max_ideal_lean_deg"] == pytest.approx(math.degrees(exact), abs=0.0001)
