"""Shared offscreen Blender rendering and animated CAD presentation packaging.

A product module may define `presentation`: a dictionary, or a function of the variant's
parameters that returns one. Every key is optional:

- "sheet": {"title", "subtitle", "caption", "footer"}: text of the review sheet; "subtitle"
  may use {name} and {version};
- "views": {name: view}: the stills, in order. A view is either fixed, {"location", "target",
  "scale"} in metres, or fitted to what it shows, {"azimuth", "elevation"} in degrees with
  optional "margin", "fit" (name prefixes to frame) or "box" (corners in mm). Any view may add
  "size" (pixels), "frame" (index of an animation pose to show) and "hide" (name prefixes);
- "animation": {"view", "size", "samples", "hide", "frame_ms", "loop"}: the motion frames,
  packaged as motion.gif;
- "films": {name: film}: further films of the same poses, each with the keys of "animation"
  (another view, parts hidden), packaged as <name>.gif;
- "materials": {name prefix: {"roughness", "coat", "colour"}}; "lights", "light_target",
  "world", "world_strength", "samples".
Without it the scene is the neutral studio the first product was rendered in.
"""

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


def presentation_of(module, params) -> dict:
    """The product's presentation settings for one variant; empty if it defines none."""
    spec = getattr(module, "presentation", None)
    if callable(spec):
        spec = spec(params)
    return dict(spec or {})


def prepare_presentation(model, variant, out, module, animate=False):
    """Stage CAD tessellation and optional rigid poses for an isolated Blender process."""
    out = out.resolve()
    params = model.variants[variant]
    parts = parts_of(model.build(params))
    payload = {"name": model.name, "version": model.version, "parts": {}, "poses": []}
    payload["presentation"] = presentation_of(module, params)
    for name, shape in parts.items():
        mesh = mesh_of(shape, model.process.mesh_tolerance)
        payload["parts"][name] = {
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "colour": list(shape.color)[:3] if shape.color else [0.3, 0.3, 0.3],
        }
    posed_views = any("frame" in v for v in payload["presentation"].get("views", {}).values())
    payload["animate"] = bool(animate)
    if animate or posed_views:
        if not hasattr(module, "_render_poses"):
            raise ValueError("Model does not provide rigid presentation poses")
        payload["poses"] = module._render_poses(params)
    data = out / "presentation.json"
    data.write_text(json.dumps(payload, separators=(",", ":")))
    return data


def clear_frames(out) -> None:
    """Remove the frames of an earlier render: a shorter film would otherwise end with them."""
    for old in Path(out).glob("frames*/*.png"):
        old.unlink()


def render_model(model, variant, out, module, animate=False):
    """Render exactly the CAD mesh, optionally applying product-provided rigid poses."""
    data = prepare_presentation(model, variant, out, module, animate)
    out = data.parent
    if animate:
        clear_frames(out)
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
    spec = presentation_of(module, model.variants[variant])
    finish_presentation(out, model.name, model.version, animate, spec)


def finish_presentation(out, name, version, animate=True, spec=None):
    """Package rendered frames, contact sheet and artifact hashes after Blender exits."""
    out = Path(out)
    spec = spec or {}
    films = {"motion": ("frames", spec.get("animation", {}))}
    films.update({name: (f"frames_{name}", film) for name, film in spec.get("films", {}).items()})
    for gif, (folder, film) in films.items():
        frames = sorted((out / folder).glob("*.png"))
        if film.get("loop") and len(frames) > 1:
            frames = frames[:-1]  # the last pose repeats the first
        if not (animate and frames):
            continue
        images = [Image.open(f).convert("RGB") for f in frames]
        images[0].save(
            out / f"{gif}.gif",
            save_all=True,
            append_images=images[1:],
            duration=film.get("frame_ms", 100),
            loop=0,
            optimize=False,
        )
        for image in images:
            image.close()
    compose_sheet(out, name, version, spec.get("sheet"))
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        files = [*out.glob("*.png"), *out.glob("*.jpg"), *out.glob("*.gif"), *out.glob("*.blend")]
        manifest["files"].update(
            {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        )
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def compose_sheet(out: Path, name: str, version: str, text: dict | None = None):
    """A neutral labelled review sheet: hero, reverse and overhead CAD renders.

    `text` gives the product's "title", "subtitle", "caption" and "footer"; the subtitle may
    use {name} and {version}.
    """
    text = text or {}
    sheet = Image.new("RGB", (1800, 1500), "#F2EEE5")
    draw = ImageDraw.Draw(sheet)
    draw.text((65, 35), text.get("title", name.upper()), font=_font(43), fill="#252C2C")
    subtitle = text.get("subtitle", "{name}  /  {version}  /  Engineering concept")
    draw.text(
        (66, 95),
        subtitle.format(name=name.upper(), version=version),
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
    draw.text((70, 1010), text.get("caption", ""), font=_font(23), fill="#252C2C")
    draw.text(
        (70, 1415),
        text.get("footer", "Physical prototype required"),
        font=_font(23),
        fill="#675D50",
    )
    sheet.save(out / "concept-sheet.jpg", quality=94)
