"""Reproduce stage 3A evidence from the real, rigid contact-rig model.

Run from the workspace: uv run python projects/fala/engineering/prove_contact.py
Optional --export, --render and --show use cadkit; all artifacts stay in Fala.
This is a sampled geometric study, not an endurance or loaded reversibility test.
"""

import argparse
import hashlib
import json
import math
import shutil
from importlib import import_module
from pathlib import Path

from cadkit.export import export_model
from cadkit.validate import metrics, overlaps, validate
from fala import model as geometry

ROOT = Path(__file__).resolve().parents[1]


def _numerical(params, samples=1440):
    poses = [
        geometry._pose(params.model_copy(update={"angle": i * 360 / samples}), x)
        for i in range(samples)
        for x in geometry._CENTRES
    ]
    heights = [p.height for p in poses]
    gaps = [g for p in poses for g in p.return_gaps]
    errors = []
    for i in range(samples):
        p = params.model_copy(update={"angle": i * 360 / samples})
        for x in geometry._CENTRES:
            pose = geometry._pose(p, x)
            t = math.radians(pose.lean)
            for xx, _, zz in pose.contacts:
                w = -(xx - x) * math.sin(t) + (zz - pose.height) * math.cos(t)
                errors.append(abs(w + params.pad_drop))
    # An explicitly assumed equal-mass full terrace, not the two-carriage rig.
    # Torque from d(m g z_CG)/d(shaft angle); no friction or transmission loss.
    torques = []
    delta = 0.02
    for i in range(360):
        heights_pair = []
        for sign in (-1, 1):
            p = params.model_copy(update={"angle": i + sign * delta})
            heights_pair.append(
                sum(
                    (pose := geometry._pose(p, 11 + 22 * j)).height
                    + 30 * math.cos(math.radians(pose.lean))
                    for j in range(8)
                )
            )
        torques.append(0.015 * 9.81 * (heights_pair[1] - heights_pair[0]) / math.radians(2 * delta))
    return {
        "phase_samples_per_carriage": samples,
        "gravity_seated_return_gap_mm": [min(gaps), max(gaps)],
        "max_abs_lean_deg": max(abs(p.lean) for p in poses),
        "deck_height_above_axle_range_mm": [min(heights), max(heights)],
        "max_upper_contact_equation_residual_mm": max(errors),
        "contact_y_range_mm": [
            min(c[1] for p in poses for c in p.contacts),
            max(c[1] for p in poses for c in p.contacts),
        ],
        "section_comparison": {
            "infinitesimal_y0_pad_capture_variation_mm": 2
            * (params.cam_radius - math.sqrt(params.cam_radius**2 - params.amplitude**2)),
            "broad_pad_section_capture_variation_mm": 0,
            "scope": "Section limit only; finite axial width and lean are solved above.",
        },
        "assumed_full_terrace_gravity_only": {
            "houses": 8,
            "pitch_mm": 22,
            "mass_per_carriage_g": 15,
            "cg_height_above_deck_mm": 30,
            "shaft_torque_range_mNm": [min(torques), max(torques)],
            "scope": "Equal assumed masses, gravity only; excludes friction, inertia and gears.",
        },
    }


def proof(step=1):
    """Check BReps in signed phase order, including every reference axis."""
    params = geometry.Params()
    phases = list(range(0, 360, step))
    errors = validate(geometry.build(params), geometry.model.process)
    if errors:
        raise ValueError(errors)
    failures, max_distance = [], 0.0
    min_fixed = {
        "cam_to_frame": math.inf,
        "carriage_to_frame": math.inf,
        "between_carriages": math.inf,
    }
    for direction in (1, -1):
        for angle in phases:
            p = geometry.build(params.model_copy(update={"angle": direction * angle}))
            if hits := overlaps(p):
                failures.append({"phase_deg": direction * angle, "hits": hits})
            cam = p["cam_and_thumbwheel"]
            for i in (1, 2):
                max_distance = max(max_distance, cam.distance_to(p[f"carriage_{i}"]))
                min_fixed["carriage_to_frame"] = min(
                    min_fixed["carriage_to_frame"], p[f"carriage_{i}"].distance_to(p["frame"])
                )
            min_fixed["cam_to_frame"] = min(min_fixed["cam_to_frame"], cam.distance_to(p["frame"]))
            min_fixed["between_carriages"] = min(
                min_fixed["between_carriages"], p["carriage_1"].distance_to(p["carriage_2"])
            )
            if angle % 60 == 0:
                print(
                    f"CAD phase {direction * angle:+4d} / contacts <= {max_distance:.3g} mm",
                    flush=True,
                )
    parts = geometry.build(params)
    source_paths = [Path(geometry.__file__), Path(__file__)]
    source_paths.extend(
        Path(import_module(name).__file__) for name in ("cadkit.features.cams", "cadkit.validate")
    )
    report = {
        "stage": "3A: finite-pad contact development; physical prototype required",
        "model": geometry.model.name,
        "version": geometry.model.version,
        "variant": "contact_rig",
        "units": "mm, degrees, mNm",
        "params": params.model_dump(),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        "geometry": {n: metrics(s) for n, s in parts.items()},
        "numerical": _numerical(params),
        "cad_sweep": {
            "non_destructive_intersections": True,
            "phase_step_deg": step,
            "poses_per_direction": len(phases),
            "directions": ["positive", "negative"],
            "intersection_volume_threshold_mm3": 1e-5,
            "failures": failures,
            "max_cam_to_carriage_distance_mm": max_distance,
            "minimum_separations_mm": min_fixed,
            "scope": "All seven parts, including both guide pins and the fixed axle. "
            "Signed phase sweeps retrace geometry; no loaded reversal simulation.",
        },
        "limitations": [
            "Discrete poses; not a continuous swept-volume certificate.",
            "Smooth loft approximates the analytic circular-section cam; CAD contact distances are measured.",
            "Pin/slot and keel clearances are modelled at their centred positions; clearance-induced rocking is unmeasured.",
            "Lower-jaw gaps are gravity-seated clearances, not total free-rocking backlash.",
            "No friction, wear, noise, warm-window, overload, shipping or slicer verification.",
            "Pin axial retention, production bearings and the provisional 3:1 transmission remain unresolved.",
            "No decorated houses or concealed terrace joints are included.",
        ],
    }
    if failures or max_distance > 1e-5:
        raise ValueError(f"Contact rig failed: {failures}; separation {max_distance}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-step", type=int, choices=(1, 2, 5), default=1)
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()
    report = proof(args.phase_step)
    target = ROOT / "docs" / "contact-proof.json"
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(target)
    if args.export or args.render:
        out = export_model(geometry.model, "contact_rig", ROOT / "dist")
        print(out)
        if args.render:
            from cadkit.render import render_model

            render_model(geometry.model, "contact_rig", out, geometry, animate=True)
            for source, name in (
                ("hero.png", "contact_rig.png"),
                ("motion.gif", "contact_rig.gif"),
            ):
                shutil.copy2(out / source, ROOT / "docs" / "img" / name)
    if args.show:
        from ocp_vscode import show

        parts = geometry.build(geometry.Params())
        show(*parts.values(), names=list(parts))


if __name__ == "__main__":
    main()
