"""Serce na węgiel concept checkpoint: build the concept scenes, show them, export them.

Throwaway massing models for choosing a look and an opening principle, not product geometry.

    uv run python projects/serce/concept/look_concepts.py              # everything
    uv run python projects/serce/concept/look_concepts.py looks        # only the three looks
    uv run python projects/serce/concept/look_concepts.py --no-show    # skip the OCP viewer

Each scene is written as one STL per material to concept/_build/<scene>/ plus scenes.json,
which render_blender.py turns into the PNGs in docs/img.
"""

import json
import sys
import time
from pathlib import Path

from build123d import Compound, Pos, export_stl

sys.path.insert(0, str(Path(__file__).parent))
import heart_concept as hc  # noqa: E402

BUILD = Path(__file__).parent / "_build"

LOOKS = ["bryla", "szlif", "poklad"]


def scenes(groups):
    out = {}
    if "looks" in groups:
        for look in LOOKS:
            out[f"look_{look}_closed"] = (lambda k=look: hc.wings(k, 0), "hero")
            out[f"look_{look}_open"] = (lambda k=look: hc.wings(k, 180), "hero")
    if "wings" in groups:
        for i, turn in enumerate((0, 40, 80, 120, 180)):
            out[f"wings_{i}"] = (lambda t=turn: hc.wings("bryla", t), "strip")
        out["wings_counter"] = (lambda: hc.wings("bryla", 180), "counter")
        out["wings_open_ember"] = (lambda: hc.wings("bryla", 180), "hero")
        out["wings_back"] = (lambda: hc.wings("bryla", 0), "back")
    if "lift" in groups:
        for i, f in enumerate((0, 0.25, 0.6, 1.0)):
            out[f"lift_{i}"] = (lambda f=f: hc.lift("bryla", hc.LIFT_MAX * f), "strip_tall")
        out["lift_counter"] = (lambda: hc.lift("bryla", hc.LIFT_MAX), "counter")
    if "bloom" in groups:
        for i, f in enumerate((0, 0.25, 0.6, 1.0)):
            out[f"bloom_{i}"] = (lambda f=f: hc.bloom("bryla", f), "strip_wide")
        out["bloom_counter"] = (lambda: hc.bloom("bryla", 1.0), "counter_wide")
    return out


def export(name, parts, camera):
    folder = BUILD / name
    folder.mkdir(parents=True, exist_ok=True)
    by_material = {}
    for material, solid in parts:
        by_material.setdefault(material, []).append(solid)
    files = {}
    for material, solids in by_material.items():
        path = folder / f"{material}.stl"
        export_stl(Compound(solids), str(path), tolerance=0.02, angular_tolerance=0.15)
        files[material] = str(path)
    return {"name": name, "camera": camera, "files": files}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    groups = args or ["looks", "wings", "lift", "bloom"]
    manifest_path = BUILD / "scenes.json"
    BUILD.mkdir(exist_ok=True)
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    built = {}
    for name, (make, camera) in scenes(groups).items():
        t0 = time.time()
        parts = make()
        built[name] = parts
        manifest[name] = export(name, parts, camera)
        print(f"{name}: {len(parts)} solids, {time.time() - t0:.1f} s")
    manifest_path.write_text(json.dumps(manifest, indent=1))

    if "--no-show" not in sys.argv:
        from ocp_vscode import Camera, show

        shapes, names, colours = [], [], []
        shown = [n for n in built if n.startswith("look_")] or list(built)[:6]
        for col, name in enumerate(shown):
            dx = (col // 2) * 190 if name.startswith("look_") else col * 190
            dy = (col % 2) * 190 if name.startswith("look_") else 0
            by_material = {}
            for material, solid in built[name]:
                by_material.setdefault(material, []).append(solid)
            for material, solids in by_material.items():
                shapes.append(Pos(dx, dy, 0) * Compound(solids))
                names.append(f"{name}/{material}")
                colours.append(hc.PALETTE[material])
        try:
            show(*shapes, names=names, colors=colours, reset_camera=Camera.RESET)
            print("sent", len(shapes), "objects to the OCP viewer")
        except (OSError, RuntimeError) as exc:
            print("OCP viewer not reachable:", exc)
