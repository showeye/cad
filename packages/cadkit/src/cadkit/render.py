"""Shared offscreen Blender rendering and animated CAD presentation packaging."""

import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from cadkit.validate import mesh_of, parts_of


def _font(size):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def prepare_presentation(model, variant, out, module, animate=False):
    """Stage CAD tessellation and optional rigid poses for an isolated Blender process."""
    out = out.resolve()
    parts = parts_of(model.build(model.variants[variant]))
    payload = {"name": model.name, "version": model.version, "parts": {}, "poses": []}
    for name, shape in parts.items():
        mesh = mesh_of(shape, model.process.mesh_tolerance)
        payload["parts"][name] = {
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "colour": list(shape.color)[:3] if shape.color else [0.3, 0.3, 0.3],
        }
    if animate:
        if not hasattr(module, "_render_poses"):
            raise ValueError("Model does not provide rigid presentation poses")
        payload["poses"] = module._render_poses(model.variants[variant])
    data = out / "presentation.json"
    data.write_text(json.dumps(payload, separators=(",", ":")))
    return data


def render_model(model, variant, out, module, animate=False):
    """Render exactly the CAD mesh, optionally applying product-provided rigid poses."""
    data = prepare_presentation(model, variant, out, module, animate)
    out = data.parent
    blender = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    command = [
        str(blender) if blender.exists() else "blender",
        "--background",
        "--factory-startup",
        "--python",
        str(Path(__file__).with_name("_blender.py")),
        "--",
        str(data),
    ]
    subprocess.run(command, check=True)
    finish_presentation(out, model.name, model.version, animate)


def finish_presentation(out, name, version, animate=True):
    """Package rendered frames, contact sheet and artifact hashes after Blender exits."""
    out = Path(out)
    frames = sorted((out / "frames").glob("*.png"))
    if animate and frames:
        images = [Image.open(f).convert("RGB") for f in frames]
        images[0].save(
            out / "motion.gif",
            save_all=True,
            append_images=images[1:],
            duration=100,
            loop=0,
            optimize=False,
        )
        for image in images:
            image.close()
    compose_sheet(out, name, version)
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        files = [*out.glob("*.png"), *out.glob("*.jpg"), *out.glob("*.gif"), *out.glob("*.blend")]
        manifest["files"].update(
            {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        )
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def compose_sheet(out: Path, name: str, version: str):
    """A neutral labelled review sheet: hero, reverse and overhead CAD renders."""
    sheet = Image.new("RGB", (1800, 1500), "#F2EEE5")
    draw = ImageDraw.Draw(sheet)
    draw.text((65, 35), name.upper(), font=_font(43), fill="#252C2C")
    draw.text(
        (66, 95),
        f"CAD review  /  {version}  /  Engineering concept",
        font=_font(21),
        fill="#675D50",
    )
    for file, box in (
        ("hero.png", (30, 145, 1770, 1010)),
        ("back.png", (40, 1045, 880, 1400)),
        ("top.png", (920, 1045, 1760, 1400)),
    ):
        if not (out / file).exists():
            continue
        with Image.open(out / file) as source:
            source = source.convert("RGB")
            source.thumbnail((box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
            x = box[0] + (box[2] - box[0] - source.width) // 2
            y = box[1] + (box[3] - box[1] - source.height) // 2
            sheet.paste(source, (x, y))
    draw.text(
        (70, 1010),
        "Geometry from the parametric CAD model / front three-quarter, reverse and overhead",
        font=_font(23),
        fill="#252C2C",
    )
    draw.text(
        (70, 1415),
        "Physical prototype required / assembled geometry, not a slicer plate",
        font=_font(23),
        fill="#675D50",
    )
    sheet.save(out / "concept-sheet.jpg", quality=94)
