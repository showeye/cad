"""Deterministic STEP/STL/3MF/GLB and traceable manifests, shared by every product."""

import hashlib
import inspect
import json
import platform
import re
import subprocess
import uuid
from copy import copy
from importlib.metadata import version
from itertools import count
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from build123d import Compound, Mesher, export_gltf, export_step, export_stl

from cadkit.model import Model
from cadkit.validate import metrics, parts_of, validate

_EPOCH = "2000-01-01T00:00:00"


def _canonical_zip(path: Path):
    """Remove ZIP timestamps and lib3mf's random production-extension UUIDs."""
    with ZipFile(path) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    ids = {}
    pattern = re.compile(rb"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")

    def replace(match):
        old = match.group()
        if old not in ids:
            ids[old] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"cadkit/3mf/{len(ids)}")).encode()
        return ids[old]

    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            if name.endswith((".model", ".xml", ".rels")):
                data = pattern.sub(replace, data)
            item = ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            archive.writestr(item, data)


def export_model(model: Model, variant: str, root: Path = Path("dist")) -> Path:
    """Build, pass all gates, export per-part printable meshes and an assembled reference."""
    params = model.variants[variant]
    parts = parts_of(model.build(params))
    if errors := validate(parts, model.process):
        raise ValueError("\n".join(errors))
    out = root / model.name / model.version / variant
    (out / "parts").mkdir(parents=True, exist_ok=True)
    # Remove only component files managed by the previous manifest for this SKU.
    previous_manifest = out / "manifest.json"
    if previous_manifest.exists():
        previous = json.loads(previous_manifest.read_text())
        current = {f"parts/{name}.stl" for name in parts if not name.startswith("reference_")}
        for relative in previous.get("files", {}):
            if re.fullmatch(r"parts/[A-Za-z0-9_-]+\.stl", relative) and relative not in current:
                (out / relative).unlink(missing_ok=True)
    assembly = Compound(children=list(parts.values()), label=model.name)
    # OCCT emits colour styles in pointer-hash order, which varies across processes.
    # STEP carries named geometry; GLB and 3MF carry the product's colour presentation.
    step_assembly = copy(assembly)
    for shape in (step_assembly, *step_assembly.descendants):
        shape.color = None
    export_step(step_assembly, out / "assembly.step", timestamp=_EPOCH)
    # OCCT uses a process-wide occurrence counter, even when the timestamp is fixed.
    step = out / "assembly.step"
    counter = count(1)
    step.write_text(
        re.sub(
            r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\('[^']*'",
            lambda match: f"NEXT_ASSEMBLY_USAGE_OCCURRENCE('{next(counter)}'",
            step.read_text(),
        )
    )
    export_gltf(assembly, out / "assembly.glb", binary=True, linear_deflection=0.04)
    files = [out / "assembly.step", out / "assembly.glb"]
    for name, shape in parts.items():
        if name.startswith("reference_"):
            continue
        target = out / "parts" / f"{name}.stl"
        export_stl(shape, target, tolerance=model.process.mesh_tolerance, angular_tolerance=0.15)
        files.append(target)
    # Assembly-space 3MF preserves names and colours; it is not a support-free print layout.
    mesher = Mesher()
    mesher.add_shape([s for n, s in parts.items() if not n.startswith("reference_")])
    mesher.write(out / "assembly.3mf")
    _canonical_zip(out / "assembly.3mf")
    files.append(out / "assembly.3mf")
    revision = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
        ).stdout.strip()
        or "uncommitted"
    )
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=False
        ).stdout.strip()
    )
    manifest = {
        "model": model.name,
        "version": model.version,
        "variant": variant,
        "status": "engineering concept; physical prototype required",
        "units": "mm, degrees",
        "params": params.model_dump(),
        "process": model.process.model_dump(),
        "git_revision": revision,
        "git_dirty": dirty,
        "source_hashes": {
            f"{root.name}/{p.relative_to(root)}": hashlib.sha256(p.read_bytes()).hexdigest()
            for root in (Path(__file__).parent, Path(inspect.getfile(model.build)).parent)
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix in {".py", ".ttf", ".txt"}
        },
        "libraries": {
            p: version(p)
            for p in ("cadkit", "build123d", "cadquery-ocp-novtk", "pydantic", "trimesh", "numpy")
        },
        "python": platform.python_version(),
        "parts": {n: metrics(s) for n, s in parts.items()},
        "files": {
            str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
        },
        "notes": [
            "STEP preserves named geometry; product colours are in GLB and 3MF.",
            "STL meshes use assembled coordinates; orient individual parts before slicing.",
            "3MF is an assembled reference, not a production plate or slicer profile.",
            "Flexible reference components are omitted from printable parts.",
            "Fit, retention, friction and endurance have not been physically validated.",
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return out


def bundle_model(out: Path, extras: dict[str, Path] | None = None) -> Path:
    """Archive only manifest-owned files and explicit review documents, excluding render caches."""
    manifest = json.loads((out / "manifest.json").read_text())
    target = out.parent / f"{manifest['model']}-{manifest['version']}-{manifest['variant']}.zip"
    paths = {relative: out / relative for relative in manifest["files"]}
    paths["manifest.json"] = out / "manifest.json"
    paths.update(extras or {})
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for name, path in sorted(paths.items()):
            item = ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            item.compress_type = ZIP_DEFLATED
            archive.writestr(item, path.read_bytes())
    return target
