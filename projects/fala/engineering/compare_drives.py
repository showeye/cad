"""Reproducible Fala concept screening, not a contact or durability simulation.

Run from root: uv run python projects/fala/engineering/compare_drives.py
Outputs stay in the product directory. Dimensions mm, input angles radians.
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "docs"
COUNT, PITCH, AMPLITUDE, WAVES = 8, 22.0, 3.5, 0.85
RADIUS = 9.0
K = math.tau * WAVES / (COUNT * PITCH)


def pose(index, phase):
    """Ideal two-edge wave target; fixed X centres, not a solved linkage."""
    x = (index + 0.5) * PITCH
    left = AMPLITUDE * math.sin(K * (x - PITCH / 2) - phase)
    right = AMPLITUDE * math.sin(K * (x + PITCH / 2) - phase)
    return x, (left + right) / 2, math.atan2(right - left, PITCH)


def cam_section(phase):
    """Circular eccentric section: centre Y/Z and its intersection with Y=0.

    A broad horizontal pad contacts the global top, whereas a narrow pad at Y=0
    contacts the chord. These are limiting cases, not a solution for finite pads.
    """
    y, z = AMPLITUDE * math.cos(phase), AMPLITUDE * math.sin(phase)
    half_chord = math.sqrt(RADIUS**2 - y**2)
    return y, z, half_chord


def metrics():
    phases = [math.tau * i / 1440 for i in range(1440)]
    angles = [abs(pose(0, t)[2]) for t in phases]
    chords = [cam_section(t)[2] for t in phases]
    # Fixed-X supports on one rigid tile cannot both coincide with two points
    # spaced PITCH apart in X: their Euclidean separation varies with slope.
    span = [PITCH / math.cos(a) for a in angles]
    # Equal 15 g units, gravity only, ideal target; excludes friction and gears.
    torques = []
    for t in phases:
        dz = sum(
            -AMPLITUDE * math.cos(K * (i + 0.5) * PITCH - t) * math.cos(K * PITCH / 2)
            for i in range(COUNT)
        )
        torques.append(abs(0.015 * 9.81 * dz))  # mm -> m and Nm -> mNm cancel
    return {
        "status": "concept_screening_only",
        "samples_per_revolution": len(phases),
        "parameters_mm": {"pitch": PITCH, "amplitude": AMPLITUDE, "cam_radius": RADIUS},
        "max_ideal_lean_deg": math.degrees(max(angles)),
        "ideal_centre_travel_mm": 2 * AMPLITUDE * math.cos(K * PITCH / 2),
        "cam_centre_lateral_travel_mm": 2 * AMPLITUDE,
        "narrow_pad_chord_diameter_min_mm": 2 * min(chords),
        "narrow_pad_chord_diameter_max_mm": 2 * max(chords),
        "narrow_pad_capture_play_for_18mm_jaw_mm": 2 * (RADIUS - min(chords)),
        "fixed_x_edge_distance_variation_mm": max(span) - min(span),
        "ideal_equal_15g_units_peak_gravity_torque_mNm": max(torques),
        "wedge_bar_min_stroke_mm_at_30deg": 2 * AMPLITUDE / math.tan(math.radians(30)),
        "crank_centre_lateral_travel_mm": 2 * AMPLITUDE,
        "limitations": [
            "No BRep collision sweep, gear geometry, bearing fit or friction model",
            "Finite cam-pad contact and helix axial slope not solved",
            "Reversing phase retraces the prescribed path; does not prove loaded reversibility",
            "Animation uses ideal target lean for A/B; C lean requires another constraint",
        ],
    }


def animation():
    frames = []
    for frame in range(96):
        phase = math.tau * frame / 96
        im = Image.new("RGB", (1000, 720), "#f3eee4")
        d = ImageDraw.Draw(im)
        d.text((30, 18), "FALA / NIKISZ - drive screening", fill="#26262a")
        d.text(
            (30, 40),
            "Prescribed paths only. No contact/collision proof. One cycle ~3 seconds.",
            fill="#555555",
        )
        for row, title in enumerate(
            (
                "A  Corkscrew: ideal wave target",
                "B  Quadrature bars: ideal wave target",
                "C  Belt cranks: circular translation; lean unresolved",
            )
        ):
            baseline = 235 + row * 215
            d.text((30, baseline - 160), title, fill="#26262a")
            d.rectangle((60, baseline + 15, 935, baseline + 43), fill="#26262a")
            for i in range(COUNT):
                x, z, angle = pose(i, phase)
                if row == 2:
                    t = K * x - phase
                    x += AMPLITUDE * math.cos(t)
                    z, angle = AMPLITUDE * math.sin(t), 0
                # Bare moving blocks intentionally replace decorated facades.
                height = 36 if i % 2 == 0 else 27
                corners = []
                for u, v in ((-8, 0), (8, 0), (8, height), (-8, height)):
                    xx = x + u * math.cos(angle) - v * math.sin(angle)
                    zz = z + u * math.sin(angle) + v * math.cos(angle)
                    corners.append((80 + xx * 4.7, baseline - zz * 3))
                d.polygon(corners, fill="#70392b")
                d.line([corners[0], corners[1]], fill="#c4161c", width=4)
            if row == 1:
                for j, value in enumerate((math.cos(phase), math.sin(phase))):
                    start = 300 + value * 15
                    d.line(
                        (start, baseline + 25 + j * 9, start + 250, baseline + 25 + j * 9),
                        fill=("#c4161c", "#e9e2d0")[j],
                        width=4,
                    )
        frames.append(im)
    frames[0].save(
        OUT / "img" / "drive_screening.gif",
        save_all=True,
        append_images=frames[1:],
        duration=30,
        loop=0,
    )


if __name__ == "__main__":
    (OUT / "drive-screening.json").write_text(json.dumps(metrics(), indent=2) + "\n")
    animation()
    print(json.dumps(metrics(), indent=2))
