"""Export Fala's retained rig, fit ladder and load carrier in explicit bed orientations.

Run from the workspace: uv run python projects/fala/engineering/prepare_u1.py
--render also renders the assembled CAD before writing the linked print manifest.
The geometry-only 3MFs still require support painting and slicer inspection.
"""

import argparse
import shutil
from dataclasses import replace
from pathlib import Path

from build123d import Rot
from cadkit.export import bundle_model, export_model
from cadkit.printing import arrange_on_bed, export_test_plate
from fala import model as geometry

ROOT = Path(__file__).resolve().parents[1]


def rotations(params):
    """Undo assembled carriage lean before applying the chosen side orientation."""
    if params.study == "fit":
        code = str(round(params.fit * 100))
        return {
            f"jaw_keel_{code}": (0, -90, 0),
            f"axle_coupon_{code}": (0, 0, 0),
            f"guide_coupon_{code}": (0, 0, 0),
        }
    result = {"frame": (0, 0, 0), "cam_and_thumbwheel": (0, 90, 0)}
    for i, x in enumerate(geometry._CENTRES, 1):
        lean = geometry._pose(params, x).lean
        result[f"carriage_{i}"] = (0, lean - 90, 0)
        if params.study == "loaded":
            result[f"load_mast_{i}"] = tuple((Rot(-90, 0, 0) * Rot(0, lean, 0)).orientation)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--variants", nargs="+", choices=geometry.model.variants)
    args = parser.parse_args()
    for variant in args.variants or geometry.model.variants:
        params = geometry.model.variants[variant]
        out = export_model(geometry.model, variant, ROOT / "dist")
        if args.render:
            from cadkit.render import render_model

            # Fit carriages use local deck Z=0, so assembly-space jaws extend
            # below the studio floor. Review these in their real bed layout.
            review_model = geometry.model
            if params.study == "fit":
                review_model = replace(
                    geometry.model,
                    build=lambda p: arrange_on_bed(geometry.build(p), rotations(p))[0],
                )
            render_model(review_model, variant, out, geometry, animate=params.study != "fit")
            if params.study == "fit":
                shutil.copy2(out / "hero.png", ROOT / "docs" / "img" / f"{variant}.png")
            else:
                stem = "contact" if params.study == "contact" else "loaded"
                for source, name in (
                    ("hero.png", f"{stem}_rig.png"),
                    ("motion.gif", f"{stem}_rig.gif"),
                ):
                    shutil.copy2(out / source, ROOT / "docs" / "img" / name)
        plate = export_test_plate(
            geometry.model,
            variant,
            out,
            rotations(params),
            notes=(
                "All printed parts: PLA, one toolhead, 0.4 mm nozzle; initial 0.20 mm layers.",
                "Use the same filament and settings for coupons and rig. No hole compensation.",
                "Frame/coupons: floor on bed. Cam: thumbwheel on bed, shaft vertical.",
                "Carriages: X end on bed. Paint support on leading axial ends of lower pads, keel and boss only.",
                "Block support on upper/lower sliding pad planes and both keel Y faces. Inspect layer preview.",
                "Masts: shared flat +Y face of mast and foot down; no supports.",
                "Support removal from hidden end faces only. Reject scarred working faces; do not sand.",
                "3MF is oriented geometry, without a printer profile or support painting. No G-code supplied.",
            ),
        )
        extras = {f"print/{p.name}": p for p in plate.iterdir() if p.is_file()}
        extras["U1-test-guide.md"] = ROOT / "docs" / "u1-test-guide.md"
        for name in ("u1-fit-results.csv", "u1-results.csv"):
            extras[name] = ROOT / "docs" / name
        print(bundle_model(out, extras), flush=True)


if __name__ == "__main__":
    main()
