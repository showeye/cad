"""Traceability and byte determinism across independent builds of the same model."""

import json
import subprocess
import sys

import trimesh
from build123d import Box, Color, import_step
from cadkit.export import export_model
from cadkit.model import Model
from cadkit.params import Params
from cadkit.process import FDM
from cadkit.validate import overlaps


def test_exports_reproduce_and_reimport(tmp_path):
    def build(params):
        body = Box(8, 9, 10)
        body.color = Color("#934E3C")
        return {"brick": body}

    model = Model("test", "0.1.0", {"full": Params()}, FDM, build)
    a = export_model(model, "full", tmp_path / "a")
    b = export_model(model, "full", tmp_path / "b")
    first = json.loads((a / "manifest.json").read_text())
    second = json.loads((b / "manifest.json").read_text())
    assert first == second
    assert import_step(a / "assembly.step").volume == 720
    assert trimesh.load(a / "assembly.glb").bounds.shape == (2, 3)
    assert trimesh.load(a / "parts/brick.stl").is_watertight
    assert len(trimesh.load(a / "assembly.3mf").geometry) == 1


def test_interference_gate_distinguishes_touch_and_overlap():
    from build123d import Pos

    assert not overlaps({"a": Box(10, 10, 10), "b": Pos(10, 0, 0) * Box(10, 10, 10)})
    assert overlaps({"a": Box(10, 10, 10), "b": Pos(9, 0, 0) * Box(10, 10, 10)}) == [
        ("a", "b", 100)
    ]


def test_rebuild_removes_only_previous_managed_components(tmp_path):
    from build123d import Pos

    def build(params):
        return {"body": Box(8, 9, 10), "removed": Pos(15, 0, 0) * Box(2, 2, 2)}

    old = Model("test", "0.1.0", {"full": Params()}, FDM, build)
    out = export_model(old, "full", tmp_path)
    user_note = out / "parts" / "note.txt"
    user_note.write_text("Keep")
    new = Model("test", "0.1.0", old.variants, FDM, lambda p: {"body": Box(8, 9, 10)})
    export_model(new, "full", tmp_path)
    assert not (out / "parts" / "removed.stl").exists()
    assert user_note.read_text() == "Keep"


def test_coloured_assembly_reproduces_across_processes(tmp_path):
    code = """
import sys
from pathlib import Path
from build123d import Box, Color, Pos
from cadkit.export import export_model
from cadkit.model import Model
from cadkit.params import Params
from cadkit.process import FDM
def build(params):
    parts = {}
    for i, colour in enumerate(("#934E3C", "#BB8A3B", "#252C2C")):
        body = Pos(i * 15, 0, 0) * Box(8, 9, 10)
        body.color = Color(colour)
        parts[f"body_{i}"] = body
    return parts
export_model(Model("test", "0.1.0", {"full": Params()}, FDM, build), "full", Path(sys.argv[1]))
"""
    # inspect.getfile cannot locate a source file for a function defined using -c.
    # Execute a real source file so the source-hash gate is tested as well.
    script = tmp_path / "model.py"
    script.write_text(code)
    for directory in ("a", "b"):
        subprocess.run([sys.executable, str(script), str(tmp_path / directory)], check=True)
    a = json.loads((tmp_path / "a/test/0.1.0/full/manifest.json").read_text())
    b = json.loads((tmp_path / "b/test/0.1.0/full/manifest.json").read_text())
    assert a == b
