"""Serce na węgiel, motion proof: figures and numbers for docs/motion-proof.md.

Run from the repository root, after the build has rendered the model:

    uv run cadkit build serce -v honey --render --animate
    uv run python projects/serce/tools/motion_report.py            # everything
    uv run python projects/serce/tools/motion_report.py numbers    # only print the numbers

It copies the renders into docs/img/motion, builds the strip of the five opening steps, draws
the motion and effort charts and two cut views of the drive, renders the two coal beds side by
side, and prints the measured numbers that the document quotes.
"""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from cadkit.model import Model
from cadkit.render import prepare_presentation
from cadkit.visibility import view_vector, visible_share
from PIL import Image, ImageDraw, ImageFont
from serce import _base as base
from serce import _heart as heart
from serce import _kinematics as kin
from serce import model as product
from serce.model import Params, build, effort, wing_gravity

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img" / "motion"
DIST = Path("dist") / "serce" / product.version / "honey"
PAPER, INK, MUTED = "#F3F0EA", "#252C2C", "#675D50"
COAL, HONEY, TILE, MOVE = "#26262A", "#EDAE1C", "#B4502A", "#1F6FB5"
P = Params()


def font(size):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


# ---------------------------------------------------------------- numbers
def cleft_opening(turn: float) -> float:
    """Width of the opening between the wings' rims at the front of the cleft, mm."""
    hinge = heart.hinge(P)
    point = np.array([0.0, -12.0, 68.0])  # on the centre seam, front of the cleft
    u, origin = heart.V_DIR, np.array(hinge.origin)
    t = math.radians(-kin.wing_angle(P, turn))
    r = point - origin
    r = r * math.cos(t) + np.cross(u, r) * math.sin(t) + u * (u @ r) * (1 - math.cos(t))
    return float(-2 * (origin + r)[0])


def room_share(turn: float, azimuth: float, elevation: float) -> float:
    parts = build(Params(turn=turn))
    room = [s for n, s in parts.items() if n.startswith("reference_room")]
    back = [parts["back"], parts["back_lining"]]
    others = [s for n, s in parts.items() if not n.startswith(("reference_room", "back"))]
    return visible_share(room, others, view_vector(azimuth, elevation), 2.0, back, 0.2)


def numbers() -> dict:
    from build123d import Compound

    closed, opened = build(P), build(Params(turn=180))
    size = lambda parts: [
        round(v, 1) for v in Compound(children=list(parts.values())).bounding_box().size
    ]
    printed = {n: s for n, s in closed.items() if not n.startswith("reference_")}
    curves = effort(P, 1.0)
    totals = {d: np.array([row[1]["total"] for row in rows]) for d, rows in curves.items()}
    travel = np.array([row[1]["total"] for row in curves[1] if 30 <= row[0] <= 330])
    out = {
        "size_closed_mm": size(closed),
        "size_open_mm": size(opened),
        "height_below_tip_mm": round(base.total_height(P), 1),
        "printed_parts": len({n.replace("_lining", "") for n in printed}),
        "printed_solid_volume_cm3": round(sum(s.volume for s in printed.values()) / 1000, 1),
        "printed_solid_mass_g": round(sum(s.volume for s in printed.values()) * product.DENSITY, 0),
        "ballast_g": round(closed["reference_ballast_washer"].volume * 7.85e-3, 0),
        "wing_mass_g": round(product._wing_mass(P)[0], 1),
        "wing_gravity_Nmm_max": round(max(abs(wing_gravity(P, a)) for a in range(126)), 2),
        "closing_torque_Nmm": round(kin.closing_torque(P, 0.0), 1),
        "stroke_mm": round(kin.stroke(P), 2),
        "pin_travel_mm": round(kin.pin_travel(P), 2),
        "max_pressure_angle_deg": round(max(abs(kin.pressure_angle(P, t)) for t in range(360)), 1),
        "torque_min_Nmm": round(float(min(t.min() for t in totals.values())), 1),
        "torque_max_Nmm": round(float(max(t.max() for t in totals.values())), 1),
        "torque_travel_Nmm": [round(float(travel.min()), 1), round(float(travel.max()), 1)],
        "steps": {
            turn: {
                "wing_deg": round(kin.wing_angle(P, turn), 1),
                "cleft_mm": round(cleft_opening(turn), 1),
                "room_front": round(room_share(turn, 0, 10), 3),
            }
            for turn in (0, 20, 30, 40, 60, 80, 100, 120, 150, 180)
        },
        "room_open": {
            f"{az}/{el}": round(room_share(180, az, el), 3)
            for az, el in ((0, 10), (-45, 10), (45, 10), (-20, 42))
        },
    }
    return out


# ---------------------------------------------------------------- renders
def fitted(source: Path, width: int) -> Image.Image:
    image = Image.open(source).convert("RGB")
    if image.width > width:
        image = image.resize(
            (width, round(image.height * width / image.width)), Image.Resampling.LANCZOS
        )
    return image


def copy_renders():
    names = {"hero": "closed", "open": "open", "back": "back", "top": "counter"}
    names |= {"side": "side", "mechanism": "mechanism"}
    for source, target in names.items():
        fitted(DIST / f"{source}.png", 1100).save(IMG / f"motion_{target}.png", optimize=True)
    labels = ["closed", "40°: first light", "80°: the bud", "120°: the room", "180°: fully open"]
    tiles = [fitted(DIST / f"step_{i}.png", 400) for i in range(5)]
    strip = Image.new("RGB", (5 * 400 + 6 * 16, tiles[0].height + 110), PAPER)
    draw = ImageDraw.Draw(strip)
    draw.text((26, 22), "A  Skrzydła: half a turn of the ring", font=font(26), fill=INK)
    for i, (tile, label) in enumerate(zip(tiles, labels, strict=True)):
        x = 16 + i * 416
        strip.paste(tile, (x, 66))
        draw.text((x + 8, tiles[0].height + 74), label, font=font(19), fill=INK)
    strip.save(IMG / "motion_strip.png", optimize=True)
    # the loop: a smaller palette keeps the file light
    frames = sorted((DIST / "frames").glob("*.png"))[:-1]
    images = [
        Image.open(f).convert("RGB").resize((560, 480), Image.Resampling.LANCZOS) for f in frames
    ]
    palette = images[len(images) // 2].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    images = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images]
    images[0].save(
        IMG / "motion.gif",
        save_all=True,
        append_images=images[1:],
        duration=90,
        loop=0,
        optimize=True,
    )


def bed_comparison():
    """The two coal beds, closed, from the same camera: the short ridge and the full-depth one."""
    blender = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    script = Path(sys.modules["cadkit.render"].__file__).with_name("_blender.py")
    tiles = []
    for key, ridge, label in (
        ("bed_short", 12.5, "A  short ridge (as in the concept): the heart hovers at the front"),
        (
            "bed_full",
            P.bed_ridge,
            "B  full-depth ridge (this proof): the wings sit on it everywhere",
        ),
    ):
        params = Params(bed_ridge=ridge)
        spec = product.presentation(params)
        view = {"azimuth": -38, "elevation": 6, "size": (1000, 900), "margin": 1.04}
        view["box"] = ((-46, -42, -base.total_height(params)), (46, 42, 88))
        spec["views"] = {key: view}
        module = SimpleNamespace(presentation=spec)
        out = DIST.parent / "_alternatives" / key
        out.mkdir(parents=True, exist_ok=True)
        model = Model("serce", product.version, {key: params}, product.process, build)
        data = prepare_presentation(model, key, out, module)
        subprocess.run(
            [
                str(blender),
                "--background",
                "--factory-startup",
                "--python",
                str(script),
                "--",
                str(data),
            ],
            check=True,
            capture_output=True,
        )
        tiles.append((fitted(out / f"{key}.png", 700), label))
    sheet = Image.new("RGB", (2 * 700 + 48, tiles[0][0].height + 80), PAPER)
    draw = ImageDraw.Draw(sheet)
    for i, (tile, label) in enumerate(tiles):
        sheet.paste(tile, (16 + i * 716, 16))
        draw.text((24 + i * 716, tile.height + 32), label, font=font(19), fill=INK)
    sheet.save(IMG / "motion_bed_comparison.png", optimize=True)


# ---------------------------------------------------------------- charts
def charts():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    turns = np.arange(0, 361, 1.0)
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.plot(
        turns,
        [kin.wing_angle(P, t) for t in turns],
        color=COAL,
        lw=2.4,
        label="wing angle (degrees)",
    )
    ax.plot(
        turns,
        [cleft_opening(t) for t in turns],
        color=TILE,
        lw=2.4,
        label="opening at the cleft (mm)",
    )
    dwell = kin.dwell_angle(P)
    for x in (dwell, 360 - dwell):
        ax.axvline(x, color=MUTED, lw=0.8, ls=":")
    ax.text(dwell / 2, 118, "seated", ha="center", color=MUTED, fontsize=9)
    ax.text(360 - dwell / 2, 118, "seated", ha="center", color=MUTED, fontsize=9)
    ax.set_xlim(0, 360)
    ax.set_xticks(range(0, 361, 45))
    ax.set_xlabel("turn of the ring (degrees)")
    ax.set_ylim(0, 135)
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(0.98, 0.82))
    ax.set_title(
        f"Pacing: nothing moves for the first {dwell:.0f}°, slow at both ends",
        loc="left",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(IMG / "motion_pacing.png", dpi=130, facecolor=PAPER)
    plt.close(fig)

    curves = effort(P, 1.0)
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    rows = curves[1]
    x = np.array([row[0] for row in rows])
    ax.plot(x, [row[1]["total"] for row in rows], color=COAL, lw=2.4, label="torque at the ring")
    ax.plot(
        x,
        [row[1]["drag"] for row in rows],
        color=MUTED,
        lw=1.2,
        ls="--",
        label="of which ring drag (assumed)",
    )
    ax.plot(
        x,
        [row[1]["follower"] for row in rows],
        color=MOVE,
        lw=1.2,
        label="of which follower friction",
    )
    ax.plot(
        x,
        [row[1]["work"] for row in rows],
        color=TILE,
        lw=1.2,
        label="of which work on spring and wings",
    )
    ax.axhline(0, color=INK, lw=0.6)
    ax.set_xlim(0, 360)
    ax.set_xticks(range(0, 361, 45))
    ax.set_xlabel("turn of the ring (degrees): opens to 180°, closes to 360°")
    ax.set_ylabel("N mm")
    ax.legend(frameon=False, ncol=2, fontsize=9, loc="upper center")
    ax.set_ylim(-15, 48)
    ax.set_title(
        "Effort from the statics model (turning the other way is the mirror image)",
        loc="left",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(IMG / "motion_effort.png", dpi=130, facecolor=PAPER)
    plt.close(fig)


# ---------------------------------------------------------------- cut views
def sections():
    import pyvista as pv

    def mesh(shape):
        vertices, triangles = shape.tessellate(0.05, 0.2)
        vertices = np.array([tuple(v) for v in vertices])
        faces = np.hstack([np.full((len(triangles), 1), 3), np.array(triangles)]).ravel()
        return pv.PolyData(vertices, faces)

    def cut(path, turn, normal, origin, azimuth, focus, scale, size=(1300, 900)):
        plotter = pv.Plotter(off_screen=True, window_size=size)
        plotter.set_background(PAPER)
        for shape in build(Params(turn=turn)).values():
            body = mesh(shape).clip(normal=normal, origin=origin)
            if body.n_points:
                plotter.add_mesh(body, color=tuple(list(shape.color)[:3]), specular=0.2)
        a = math.radians(azimuth)
        plotter.camera.position = np.array(focus) + 400 * np.array(
            [math.sin(a), -math.cos(a), 0.12]
        )
        plotter.camera.focal_point = focus
        plotter.camera.up = (0, 0, 1)
        plotter.camera.parallel_projection = True
        plotter.camera.parallel_scale = scale
        plotter.add_light(pv.Light(position=(-200, -300, 400), intensity=0.5))
        plotter.screenshot(str(path))
        plotter.close()

    # through both hinge axes (the seam plane), seen from the front; through the middle, from the side
    cut(IMG / "motion_cut_front.png", 180, (0, -1, 0), (0, -0.05, 0), 0, (0, 0, 8), 33)
    cut(
        IMG / "motion_cut_side_closed.png",
        0,
        (1, 0, 0),
        (0.05, 0, 0),
        90,
        (0, 0, 20),
        52,
        (1300, 1000),
    )
    cut(
        IMG / "motion_cut_side_open.png",
        180,
        (1, 0, 0),
        (0.05, 0, 0),
        90,
        (0, 0, 20),
        52,
        (1300, 1000),
    )


if __name__ == "__main__":
    jobs = sys.argv[1:] or ["renders", "beds", "charts", "sections", "numbers"]
    IMG.mkdir(parents=True, exist_ok=True)
    if "renders" in jobs:
        copy_renders()
    if "beds" in jobs:
        bed_comparison()
    if "charts" in jobs:
        charts()
    if "sections" in jobs:
        sections()
    if "numbers" in jobs:
        result = numbers()
        (DIST.parent / "motion-numbers.json").parent.mkdir(parents=True, exist_ok=True)
        (DIST.parent / "motion-numbers.json").write_text(json.dumps(result, indent=1))
        print(json.dumps(result, indent=1))
    if not shutil.which("uv"):
        print("note: run through uv so that the workspace packages are importable")
