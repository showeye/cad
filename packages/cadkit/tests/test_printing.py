"""Bed transforms, hardware exclusion, envelope errors and test export reproducibility."""

import json

import pytest
import trimesh
from build123d import Box, Compound, Pos, import_step
from cadkit.export import export_model
from cadkit.model import Model
from cadkit.params import Params
from cadkit.printing import arrange_on_bed, export_test_plate
from cadkit.process import FDM
from cadkit.validate import overlaps


def test_rotations_put_actual_geometry_on_bed_and_preserve_volume():
    parts = {"a": Pos(10, -20, 30) * Box(8, 9, 10), "b": Box(20, 30, 40)}
    parts["reference_steel"] = Box(500, 500, 500)
    plate, placements = arrange_on_bed(parts, {"a": (0, 90, 0), "b": (90, 0, 0)})
    assert set(plate) == {"a", "b"}
    assert not overlaps(plate)
    assert tuple(plate["a"].bounding_box().size) == pytest.approx((10, 9, 8))
    for name, shape in plate.items():
        assert shape.volume == pytest.approx(parts[name].volume)
        assert shape.bounding_box().min.Z == pytest.approx(0, abs=1e-6)
        assert placements[name]["rotation_deg"]


@pytest.mark.parametrize(
    "rotations,bed",
    [
        ({}, (270, 270, 270)),
        ({"a": (0, 0, 0)}, (5, 5, 5)),
        ({"a": (0, 0, 0)}, (0, 270, 270)),
        ({"a": (0, float("nan"), 0)}, (270, 270, 270)),
    ],
)
def test_invalid_layout_fails(rotations, bed):
    with pytest.raises(ValueError):
        arrange_on_bed({"a": Box(10, 10, 10)}, rotations, bed)


def test_plate_reimports_and_reproduces_with_source_link(tmp_path):
    def build(params):
        body = Box(8, 9, 10)
        # Real cached assemblies can leave the component parented to their
        # last STEP export. A per-part STEP must be exported as a tree root.
        Compound(children=[body])
        return body

    model = Model("test", "0.1.0", {"test": Params()}, FDM, build)
    out = export_model(model, "test", tmp_path)
    plate = export_test_plate(model, "test", out, {"body": (0, 90, 0)})
    before = json.loads((plate / "manifest.json").read_text())
    assert len(trimesh.load(plate / "plate.3mf").geometry) == 1
    assert import_step(plate / "body.step").volume == pytest.approx(720)
    assert trimesh.load(plate / "body.stl").bounds[0, 2] == pytest.approx(0)
    export_test_plate(model, "test", out, {"body": (0, 90, 0)})
    assert json.loads((plate / "manifest.json").read_text()) == before
    other = Model("test", "0.2.0", model.variants, FDM, model.build)
    with pytest.raises(ValueError, match="manifest"):
        export_test_plate(other, "test", out, {"body": (0, 90, 0)})
