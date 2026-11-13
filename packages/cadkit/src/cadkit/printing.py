"""Deterministic bed orientation/layout and unsliced test-plate exports.

These files carry geometry, orientation and traceability. A geometry-only 3MF
does not embed a machine profile, supports or a claim of slicer acceptance.
"""

import hashlib
import json
import math
from copy import copy
from pathlib import Path

from build123d import Compound, Mesher, Pos, Rot, export_step, export_stl

from cadkit.export import _EPOCH, _canonical_step_occurrences, _canonical_zip
from cadkit.validate import metrics, overlaps, parts_of, validate


def arrange_on_bed(parts, rotations, bed=(270, 270, 270), gap=6):
    """Shelf-pack explicitly oriented parts; omit reference_ hardware, preserve names.

    Euler angles follow build123d's Rot(X,Y,Z). Translation then puts the
    rotated bounding box on Z=0 and packs XY with at least gap mm separation.
    Every printable part must have an explicit rotation, including (0,0,0).
    """
    if not math.isfinite(gap) or gap <= 0 or any(not math.isfinite(v) or v <= 0 for v in bed):
        raise ValueError("Positive finite bed dimensions and gap required")
    printable = {n: s for n, s in parts.items() if not n.startswith("reference_")}
    if not printable or set(rotations) != set(printable):
        raise ValueError("Supply exactly one orientation for each printable part")
    result, placements = {}, {}
    x, y, row_depth = gap, gap, 0
    for name, shape in printable.items():
        angles = rotations[name]
        if len(angles) != 3 or any(not math.isfinite(v) for v in angles):
            raise ValueError(f"Invalid rotation for {name}")
        oriented = Rot(*angles) * shape
        bb = oriented.bounding_box()
        w, d, h = bb.size
        if w + 2 * gap > bed[0] or d + 2 * gap > bed[1] or h > bed[2]:
            raise ValueError(f"{name}: oriented part does not fit the bed")
        if x + w + gap > bed[0]:
            x, y, row_depth = gap, y + row_depth + gap, 0
        if y + d + gap > bed[1]:
            raise ValueError("Parts need more than one plate")
        translation = (x - bb.min.X, y - bb.min.Y, -bb.min.Z)
        placed = Pos(*translation) * oriented
        placed.parent = None
        placed.label = name
        result[name] = placed
        placements[name] = {"rotation_deg": list(angles), "translation_mm": list(translation)}
        x += w + gap
        row_depth = max(row_depth, d)
    return result, placements


def export_test_plate(model, variant, out: Path, rotations, notes=()):
    """Export oriented STL/individual STEP/3MF plus a hashed plate manifest.

    out must contain export_model's manifest, linking the plate to source
    hashes, parameters, library versions and git revision of that exact build.
    """
    out = Path(out)
    source = json.loads((out / "manifest.json").read_text())
    if (source["model"], source["version"], source["variant"]) != (
        model.name,
        model.version,
        variant,
    ) or source["params"] != model.variants[variant].model_dump(mode="json"):
        raise ValueError("Assembly manifest does not match this model and variant")
    built = parts_of(model.build(model.variants[variant]))
    if {n: metrics(s) for n, s in built.items()} != source["parts"]:
        raise ValueError("Assembly geometry no longer matches its source manifest")
    parts, placements = arrange_on_bed(built, rotations, model.process.build_volume)
    if errors := validate(parts, model.process):
        raise ValueError(errors)
    if hits := overlaps(parts):
        raise ValueError(hits)
    target = out / "print"
    target.mkdir(exist_ok=True)
    files = []
    for name, shape in parts.items():
        stl, step = target / f"{name}.stl", target / f"{name}.step"
        export_stl(shape, stl, tolerance=model.process.mesh_tolerance, angular_tolerance=0.15)
        neutral = copy(shape)
        neutral.parent = None
        neutral.color = None
        export_step(neutral, step, timestamp=_EPOCH)
        step.write_text(_canonical_step_occurrences(step.read_text()))
        files.extend((stl, step))
    mesher = Mesher()
    mesher.add_shape(list(parts.values()))
    plate = target / "plate.3mf"
    mesher.write(plate)
    _canonical_zip(plate)
    files.append(plate)
    # A STEP of the whole plate is convenient for CAD inspection.
    step = target / "plate.step"
    neutral = Compound(children=list(parts.values()))
    for shape in (neutral, *neutral.descendants):
        shape.color = None
    export_step(neutral, step, timestamp=_EPOCH)
    step.write_text(_canonical_step_occurrences(step.read_text()))
    files.append(step)
    manifest = {
        "model": model.name,
        "version": model.version,
        "variant": variant,
        "status": "oriented test geometry; inspect supports and slice before printing",
        "bed_mm": list(model.process.build_volume),
        "source_manifest_sha256": hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest(),
        "placements": placements,
        "parts": {n: metrics(s) for n, s in parts.items()},
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "notes": list(notes),
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return target
