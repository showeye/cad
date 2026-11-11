"""Serce na węgiel concept checkpoint: schematic diagrams of the three ways to open the heart.

Throwaway figures for docs/look-brief.md. They show the principle of each drive, with the real
heart outline and the working numbers of the proposal, but no fits or part detail.

    uv run python projects/serce/concept/mechanism_diagrams.py
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

sys.path.insert(0, str(Path(__file__).parent))
import heart_concept as hc  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "img"
COAL, HONEY, BONE, TILE, STEEL, PAPER, INK, MOVE = (
    "#26262A",
    "#EDAE1C",
    "#ECE5D2",
    "#B4502A",
    "#8C97A1",
    "#F3F0EA",
    "#3A3A3F",
    "#1F6FB5",
)

# working numbers of the recommended drive (A)
TAIL = 11.0  # lever on each shell, from hinge axis to follower
STROKE = 2 * TAIL * math.sin(math.radians(hc.WING_MAX / 2))  # slider travel
ECC = STROKE / 2  # offset of the circular cam groove
GROOVE_R = 20.0
RING_R, RING_TOP, RING_H, FOOT_H = hc.RING_R, hc.RING_TOP, hc.RING_H, hc.FOOT_H
FOOT_Z = RING_TOP - RING_H - 0.4 - FOOT_H


def heart_outline():
    left = hc.outline_left()
    right = left[::-1] * [-1, 1]
    return np.vstack([left, right])


def side_profile(n=60):
    """Silhouette of the smooth heart seen from the side: (y, z) polygon."""
    ys = np.linspace(-hc.DEPTH, hc.DEPTH, n)
    s = (1 - (np.abs(ys) / hc.DEPTH) ** hc.SWELL) ** (1 / hc.SWELL)
    top = np.c_[ys, hc.Z0 + (82.5 - hc.Z0) * s]
    bottom = np.c_[ys, hc.Z0 * (1 - s)][::-1]
    return np.vstack([top, bottom])


def rotate(points, origin, axis, degrees):
    """Rodrigues rotation of an (n, 3) array."""
    k = np.asarray(axis, float) / np.linalg.norm(axis)
    p = np.asarray(points, float) - origin
    t = math.radians(degrees)
    out = p * math.cos(t) + np.cross(k, p) * math.sin(t) + np.outer(p @ k, k) * (1 - math.cos(t))
    return out + origin


def wing_points(angle, side=-1):
    """Outline of one front shell (its rim at the mid-plane), swung open by `angle`."""
    mirror = np.array([-side, 1, 1])
    left = hc.outline_left()
    up = left[:, 0] * hc.V_DIR[0] + left[:, 1] * hc.V_DIR[2] >= hc.E_LEFT @ hc.V_DIR
    rim = np.c_[left[up, 0], np.zeros(up.sum()), left[up, 1]]
    seam_foot = np.array([[0.0, 0.0, hc.RIDGE_Z]])
    pts = np.vstack([seam_foot, rim]) * mirror
    return rotate(pts, hc.HINGE_P * mirror, hc.V_DIR * mirror, -side * -angle)


def base_front(ax, tent=True):
    ax.add_patch(Rectangle((-RING_R + 1.6, FOOT_Z), 2 * RING_R - 3.2, FOOT_H, fc="#3A3A40", ec=INK, lw=0.8))
    ax.add_patch(Rectangle((-RING_R, RING_TOP - RING_H), 2 * RING_R, RING_H, fc=COAL, ec=INK, lw=0.8))
    if tent:
        roof = [(-RING_R + 0.6, RING_TOP + 0.4), (0, hc.RIDGE_Z), (RING_R - 0.6, RING_TOP + 0.4)]
    else:
        roof = [(-RING_R + 0.6, RING_TOP + 0.4), (-16, hc.Z_SEAT), (16, hc.Z_SEAT), (RING_R - 0.6, RING_TOP + 0.4)]
    ax.add_patch(Polygon(roof, closed=True, fc="#33333A", ec=INK, lw=0.8))


def arrow(ax, a, b, text=None, rad=0.0, colour=MOVE, size=9, ha="center", va="center", offset=(0, 0)):
    ax.add_patch(
        FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=13, lw=1.6, color=colour, connectionstyle=f"arc3,rad={rad}")
    )
    if text:
        mid = ((a[0] + b[0]) / 2 + offset[0], (a[1] + b[1]) / 2 + offset[1])
        ax.text(*mid, text, color=colour, fontsize=size, ha=ha, va=va)


def label(ax, xy, text, to, ha="left"):
    ax.annotate(
        text,
        xy=xy,
        xytext=to,
        fontsize=8.5,
        color=INK,
        ha=ha,
        va="center",
        arrowprops={"arrowstyle": "-", "color": INK, "lw": 0.6},
    )


def frame(ax, title, xlim, ylim):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10.5, color=INK, loc="left")


def turn_arrow(ax, y=None):
    y = RING_TOP - RING_H / 2 if y is None else y
    arrow(ax, (-RING_R - 4, y - 3), (-RING_R - 4, y + 5), rad=-0.9)
    ax.text(-RING_R - 9, y + 1, "turn", color=MOVE, fontsize=9, ha="right", va="center")


# ---------------------------------------------------------------- A: wings
def diagram_wings():
    fig, axes = plt.subplots(2, 2, figsize=(13, 10.4), facecolor=PAPER)
    fig.suptitle(
        "A  Skrzydła (wings): two front shells hinged along the V edges, driven by a cam and a slider in the base",
        fontsize=12.5,
        color=INK,
        x=0.02,
        ha="left",
    )

    # front view
    ax = axes[0, 0]
    frame(ax, "Front: closed (outline) and fully open (half a turn of the ring)", (-95, 95), (-22, 92))
    base_front(ax)
    for side in (-1, 1):
        for angle, alpha in ((62.5, 0.25), (hc.WING_MAX, 0.9)):
            pts = wing_points(angle, side)
            ax.add_patch(Polygon(pts[:, [0, 2]], closed=True, fc=HONEY, ec=COAL, lw=1.6, alpha=alpha))
        p0 = hc.HINGE_P * [-side, 1, 1]
        p1 = p0 + hc.V_DIR * [-side, 1, 1] * 44
        ax.plot([p0[0], p1[0]], [p0[2], p1[2]], color=STEEL, lw=2.4, solid_capstyle="round")
    outline = heart_outline()
    ax.add_patch(Polygon(outline, closed=True, fc="none", ec=COAL, lw=1.8))
    ax.plot([0, 0], [hc.RIDGE_Z, 70], color=COAL, lw=0.9, ls=(0, (4, 3)))
    label(ax, (-27, 34), "steel hinge pins inside the V edges", (-93, 16))
    label(ax, (0, 55), "centre seam: one cleat crack among decoys", (22, 88))
    label(ax, (20, 10), "fixed coal bed: its two main facets are square\nto the hinges, so the shells sweep 0.4 mm above\nthem and no gap ever closes on a finger", (34, -8))
    arrow(ax, (-12, 74), (-52, 30), rad=0.35)
    arrow(ax, (12, 74), (52, 30), rad=-0.35)
    turn_arrow(ax)

    # side section
    ax = axes[0, 1]
    frame(ax, "Section through the middle, seen from the side (front is left)", (-62, 78), (-22, 92))
    prof = side_profile()
    ax.add_patch(Polygon(prof, closed=True, fc="#EFE9DC", ec=COAL, lw=1.8))
    inner = np.c_[prof[:, 0] * 0.86, hc.Z0 + (prof[:, 1] - hc.Z0) * 0.92]
    ax.add_patch(Polygon(inner, closed=True, fc=PAPER, ec=HONEY, lw=2.2))
    ax.plot([0, 0], [70, 83], color=COAL, lw=0.9, ls=(0, (4, 3)))
    ax.add_patch(Rectangle((13, hc.FLOOR_Z), 1.5, 44, fc=HONEY, ec=INK, lw=0.6))  # back wall
    ax.add_patch(Rectangle((-17, hc.FLOOR_Z - 1.5), 31.5, 1.5, fc=TILE, ec=INK, lw=0.6))  # floor
    keel = [(-15, hc.FLOOR_Z - 1.5), (14.5, hc.FLOOR_Z - 1.5), (11, hc.RIDGE_Z - 4), (-11, hc.RIDGE_Z - 4)]
    ax.add_patch(Polygon(keel, closed=True, fc="#33333A", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((4.5, hc.FLOOR_Z), 8.5, 12.5, fc=TILE, ec=INK, lw=0.6))  # stove
    ax.add_patch(Rectangle((-12, hc.FLOOR_Z + 5), 15, 1, fc=BONE, ec=INK, lw=0.6))  # table
    ax.add_patch(Rectangle((-5, hc.FLOOR_Z), 1.6, 5, fc=COAL))
    # base: foot, ballast, ring with cam groove, slider, pedestal, tie screw
    ax.add_patch(Rectangle((-RING_R + 1.6, FOOT_Z), 2 * RING_R - 3.2, FOOT_H, fc="#3A3A40", ec=INK, lw=0.8))
    ax.add_patch(Rectangle((-30, FOOT_Z + 0.8), 60, 2.2, fc=STEEL, ec=INK, lw=0.5))
    for x in (-RING_R, RING_R - 3.2):
        ax.add_patch(Rectangle((x, RING_TOP - RING_H), 3.2, RING_H, fc=COAL, ec=INK, lw=0.6))
    web_z = RING_TOP - RING_H + 0.6
    ax.add_patch(Rectangle((-RING_R + 3.2, web_z), 2 * RING_R - 6.4, 4.0, fc=COAL, ec=INK, lw=0.6))
    for y in (ECC - GROOVE_R, ECC + GROOVE_R):  # the circular groove, cut twice by the section
        ax.add_patch(Rectangle((y - 2.1, web_z + 1.6), 4.2, 2.4, fc=PAPER, ec=INK, lw=0.5))
    roof = [(-RING_R + 0.6, RING_TOP + 0.4), (-12.5 - (hc.RIDGE_Z - RING_TOP) / 1.19, RING_TOP + 0.4)]
    ped = [
        (-RING_R + 0.6, RING_TOP + 0.4),
        (-12.5, hc.RIDGE_Z),
        (12.5, hc.RIDGE_Z),
        (RING_R - 0.6, RING_TOP + 0.4),
        (RING_R - 0.6, RING_TOP + 2.6),
        (12.5, hc.RIDGE_Z - 2.4),
        (-12.5, hc.RIDGE_Z - 2.4),
        (-RING_R + 0.6, RING_TOP + 2.6),
    ]
    del roof
    ax.add_patch(Polygon(ped, closed=True, fc="#33333A", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((-3.4, FOOT_Z + 3), 6.8, hc.RIDGE_Z - 4 - FOOT_Z - 3, fc="#4A4A52", ec=INK, lw=0.6))  # hub
    ax.add_patch(Rectangle((-1.0, FOOT_Z + 0.4), 2.0, hc.FLOOR_Z - 4 - FOOT_Z, fc=STEEL, ec=INK, lw=0.4))  # M4 tie
    slider_z = web_z + 4.6
    slide = ECC  # drawn fully open: slider at the back
    ax.add_patch(Rectangle((slide - 14, slider_z), 42, 2.6, fc=MOVE, ec=INK, lw=0.5, alpha=0.85))
    ax.add_patch(Rectangle((slide + GROOVE_R - 1.9, web_z + 1.8), 3.8, 3.4, fc=STEEL, ec=INK, lw=0.4))  # follower
    ax.add_patch(Rectangle((slide - 3.3, slider_z + 2.6), 6.6, 7.4, fc=MOVE, ec=INK, lw=0.5, alpha=0.85))  # fork
    ax.add_patch(Circle((slide, slider_z + 7.2), 2.0, fc=STEEL, ec=INK, lw=0.5))  # tail ball
    arrow(ax, (-22, slider_z + 13), (-3, slider_z + 13), "19.5 mm", colour=MOVE, offset=(0, 3.5))
    label(ax, (slide + GROOVE_R, web_z + 3), "steel follower pin in a circular\ngroove, 9.8 mm off-centre", (40, 30))
    label(ax, (slide + 12, slider_z + 1.3), "slider (front to back)", (40, 21))
    label(ax, (slide, slider_z + 7.2), "fork and the tails of both shells", (40, 13))
    label(ax, (20, FOOT_Z + 1.8), "steel ballast, 150 g", (40, -14))
    label(ax, (1, 5), "fixed hub with M4 tie screw", (40, 5))
    label(ax, (RING_R - 1.6, RING_TOP - 6), "turn ring", (40, -4))
    label(ax, (13.8, 60), "room: back wall, floor, furniture\n(one four-colour part)", (26, 64))
    label(ax, (-19, 52), "front shells:\ncoal outside,\nhoney lining", (-60, 70))
    label(ax, (20, 46), "fixed back half", (30, 50))

    # top view of the drive
    ax = axes[1, 0]
    frame(ax, "The drive from above: closed (grey) and open (blue)", (-48, 62), (-46, 46))
    ax.add_patch(Circle((0, 0), RING_R, fc="none", ec=COAL, lw=5))
    ax.add_patch(Circle((0, 0), 3.4, fc="#4A4A52", ec=INK, lw=0.6))
    for turn, colour, alpha in ((0, "#8A8A90", 0.9), (180, MOVE, 0.95)):
        t = math.radians(turn)
        centre = (ECC * math.sin(t), -ECC * math.cos(t))  # groove centre goes round with the ring
        ax.add_patch(Circle(centre, GROOVE_R, fc="none", ec=colour, lw=4.2, alpha=0.45))
        y_f = centre[1] + math.sqrt(GROOVE_R**2 - centre[0] ** 2)  # follower stays on the y axis
        slide = y_f - GROOVE_R  # -ECC closed .. +ECC open
        ax.add_patch(Circle((0, y_f), 2.0, fc=STEEL, ec=INK, lw=0.6, zorder=5))
        for x in (-13, 13):
            ax.add_patch(Rectangle((x - 3.2, slide - 3.3), 6.4, 6.6, fc="none", ec=colour, lw=1.6, alpha=alpha))
            ax.add_patch(Circle((x, slide), 2.0, fc=STEEL, ec=INK, lw=0.5, alpha=alpha))
        ax.plot([-13, -13, 13, 13], [slide + 3.3, y_f, y_f, slide + 3.3], color=colour, lw=1.6, alpha=alpha)
    ax.text(0, -30, "front", fontsize=8.5, color=INK, ha="center")
    arrow(ax, (20, -ECC), (20, ECC), "slider\n19.5 mm", colour=MOVE, ha="left", offset=(3, 0))
    arrow(ax, (-29, -29), (29, -29), rad=0.55)
    ax.text(0, -44, "half a turn opens, the next half closes; either direction; no end stops", fontsize=8.5, color=MOVE, ha="center")
    label(ax, (0, 2 * ECC + GROOVE_R - ECC), "follower pin (on the slider)", (30, 40))
    label(ax, (13, ECC), "fork: holds the tail of\neach shell front to back,\nfree in the other directions", (30, 22))
    label(ax, (GROOVE_R * 0.7, -ECC - GROOVE_R * 0.7), "cam groove in the ring", (30, -34))

    # motion law
    ax = axes[1, 1]
    ax.set_facecolor(PAPER)
    turn = np.linspace(0, 360, 361)
    half = math.radians(hc.WING_MAX / 2)
    swing = np.degrees(half - np.arcsin(math.sin(half) * np.cos(np.radians(turn))))
    corner = np.array([[-0.3, -4.0, 69.0]])  # top inner corner of the left shell, at the cleft
    gap = np.array([2 * abs(rotate(corner, hc.HINGE_P, hc.V_DIR, -a)[0, 0]) for a in swing])
    ax.plot(turn, swing, color=COAL, lw=2.2, label="shell angle (degrees)")
    ax.plot(turn, gap, color=TILE, lw=2.2, label="gap at the cleft (mm)")
    for x, text in ((12, "first light:\na hairline"), (60, "bud"), (180, "fully open:\nself-locked"), (348, "closed:\nself-locked")):
        ax.axvline(x if x not in (12, 348) else (0 if x == 12 else 360), color=STEEL, lw=0.6, ls=":")
        ax.text(x, 136, text, fontsize=8, color=INK, ha="center", va="bottom")
    ax.set_xlim(0, 360)
    ax.set_ylim(0, 150)
    ax.set_xticks(range(0, 361, 45))
    ax.set_xlabel("turn of the base ring (degrees)", fontsize=9, color=INK)
    ax.set_title("Pacing: slow at both ends, quick in the middle", fontsize=10.5, color=INK, loc="left")
    ax.legend(loc="center", fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.08), ncols=2)
    ax.tick_params(labelsize=8, colors=INK)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    i30 = 30
    print(f"A: stroke {STROKE:.1f} mm, eccentricity {ECC:.2f} mm, swing at 30 deg turn {swing[i30]:.1f} deg,")
    print(f"   cleft gap at 15/30/45/90/180 deg turn: {[round(float(gap[i]), 1) for i in (15, 30, 45, 90, 180)]} mm")

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT / "mechanism_a_wings.png", dpi=120, facecolor=PAPER)
    plt.close(fig)


# ---------------------------------------------------------------- B: seam lift
def diagram_lift():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), facecolor=PAPER)
    fig.suptitle(
        "B  Pokład (the seam): the heart parts along one bedding plane and the top rises on a screw",
        fontsize=12.5,
        color=INK,
        x=0.02,
        ha="left",
    )
    split, travel = hc.LIFT_SPLIT, hc.LIFT_MAX
    outline = heart_outline()
    low = outline[outline[:, 1] <= split]
    low = np.vstack([low, [[(split / hc.V_DIR[2]) * -hc.V_DIR[0], split], [(split / hc.V_DIR[2]) * hc.V_DIR[0], split]]])
    low = low[np.argsort(np.arctan2(low[:, 1] - 12, low[:, 0]))]
    top = outline[outline[:, 1] >= split]
    x_split = -hc.V_DIR[0] / hc.V_DIR[2] * split
    top = np.vstack([[[-x_split, split]], top, [[x_split, split]]])

    ax = axes[0]
    frame(ax, "Front: closed (outline) and open (about 1 1/4 turns)", (-70, 70), (-22, 122))
    base_front(ax, tent=False)
    ax.add_patch(Polygon(low, closed=True, fc="#33333A", ec=COAL, lw=1.6))
    ax.add_patch(Polygon(top, closed=True, fc="none", ec=COAL, lw=1.2, ls=(0, (4, 3))))
    ax.add_patch(Polygon(top + [0, travel], closed=True, fc="#33333A", ec=COAL, lw=1.6))
    ax.add_patch(Rectangle((-19, split), 38, travel, fc=HONEY, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((-20.5, split - 0.8), 41, 1.0, fc=TILE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((-14, split), 8, 9.5, fc=TILE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((5, split), 9.5, 22, fc=BONE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((-4, split + 4), 8, 0.9, fc=BONE, ec=INK, lw=0.5))
    arrow(ax, (50, split + 6), (50, split + travel + 6), "30 mm", offset=(9, 0))
    label(ax, (-20, split + 15), "room: a 41 x 22 x 30 mm prism,\nso the shell can pass over it", (-68, 108))
    label(ax, (-25, split), "the only seam: a horizontal bed,\nflat face on flat face", (-68, 12))
    label(ax, (30, split + travel + 12), "from above, the raised\ntop hides the room", (22, 114))
    turn_arrow(ax)

    ax = axes[1]
    frame(ax, "Section through the middle, seen from the side (front is left)", (-62, 82), (-22, 122))
    prof = side_profile()
    upper = prof[prof[:, 1] >= split]
    lower = prof[prof[:, 1] <= split]
    lower = lower[np.argsort(np.arctan2(lower[:, 1] - 20, lower[:, 0]))]
    ax.add_patch(Polygon(lower, closed=True, fc="#33333A", ec=COAL, lw=1.6))
    order = np.argsort(upper[:, 0])
    ax.plot(upper[order, 0], upper[order, 1] + travel, color=COAL, lw=4.5, solid_capstyle="round")
    ax.add_patch(Rectangle((-12, split), 22.5, travel, fc="none", ec=HONEY, lw=1.2, ls=(0, (3, 2))))
    ax.add_patch(Rectangle((10.6, split - 26), 2.8, travel + 28, fc=COAL, ec=INK, lw=0.5))  # slab
    ax.add_patch(Rectangle((9.8, split), 0.8, travel, fc=HONEY, ec=INK, lw=0.3))
    ax.add_patch(Rectangle((5.5, split - 30), 2.0, 34, fc=STEEL, ec=INK, lw=0.4))  # guide rod
    ax.add_patch(Rectangle((-RING_R + 1.6, FOOT_Z), 2 * RING_R - 3.2, FOOT_H, fc="#3A3A40", ec=INK, lw=0.8))
    ax.add_patch(Rectangle((-30, FOOT_Z + 0.8), 60, 2.2, fc=STEEL, ec=INK, lw=0.5))
    for x in (-RING_R, RING_R - 5):
        ax.add_patch(Rectangle((x, RING_TOP - RING_H), 5, RING_H, fc=COAL, ec=INK, lw=0.6))
        for k in range(5):  # coarse multi-start thread
            ax.plot([x + (5 if x < 0 else 0), x + (7.5 if x < 0 else -2.5)], [RING_TOP - 11 + 2.2 * k, RING_TOP - 9.9 + 2.2 * k], color=INK, lw=0.9)
    ax.add_patch(Rectangle((-RING_R + 7.6, RING_TOP - 11 + 9), 2 * RING_R - 15.2, 3, fc=MOVE, ec=INK, lw=0.5, alpha=0.85))
    ax.add_patch(Rectangle((8.5, RING_TOP - 2), 7, split - 24 - RING_TOP, fc=MOVE, ec=INK, lw=0.5, alpha=0.85))
    arrow(ax, (24, split - 22), (24, split - 6), colour=MOVE)
    label(ax, (RING_R - 3, RING_TOP - 8), "turn ring is a nut with a coarse\nfour-start thread (self-locking)", (40, -10))
    label(ax, (12, RING_TOP - 0.5), "lifter plate and slab: do not turn", (40, 6))
    label(ax, (6.5, split - 14), "two steel guide rods", (40, 20))
    label(ax, (12, split + 20), "slab becomes the back wall", (40, 62))
    label(ax, (-10, split + travel + 34), "upper shell", (-60, 112))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "mechanism_b_seam_lift.png", dpi=120, facecolor=PAPER)
    plt.close(fig)


# ---------------------------------------------------------------- C: bloom
def diagram_bloom():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), facecolor=PAPER)
    fig.suptitle(
        "C  Rozkwit (bloom): four shards tip outwards on hinges at the coal bed while the room rises",
        fontsize=12.5,
        color=INK,
        x=0.02,
        ha="left",
    )
    split = hc.BLOOM_SPLIT
    left = hc.outline_left()
    rim = np.c_[left[left[:, 1] >= split, 0], np.zeros((left[:, 1] >= split).sum()), left[left[:, 1] >= split, 1]]
    rim = np.vstack([[[0.0, 0.0, split]], [[-split * -hc.V_DIR[0] / hc.V_DIR[2] * -1, 0, split]], rim])

    ax = axes[0]
    frame(ax, "Front: closed (outline) and open (about 2 turns)", (-112, 112), (-22, 96))
    base_front(ax, tent=False)
    for sx in (-1, 1):
        out = np.array([sx * 0.78, -0.62, 0.0])
        axis = np.cross([0, 0, 1.0], out)
        pts = rotate(rim * [-sx, 1, 1], np.array([sx * 9.0, -7.0, split]), axis, hc.BLOOM_MAX)
        ax.add_patch(Polygon(pts[:, [0, 2]], closed=True, fc=HONEY, ec=COAL, lw=1.6, alpha=0.9))
    outline = heart_outline()
    ax.add_patch(Polygon(outline, closed=True, fc="none", ec=COAL, lw=1.4, ls=(0, (4, 3))))
    rise = hc.BLOOM_RISE
    wall = outline * 0.8 + [0, 9]
    wall = wall[wall[:, 1] >= hc.FLOOR_Z]
    ax.add_patch(Polygon(wall + [0, rise], closed=True, fc=HONEY, ec=INK, lw=0.6))
    ax.add_patch(Rectangle((-20, hc.FLOOR_Z + rise - 1.5), 40, 1.5, fc=TILE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((-17, hc.FLOOR_Z + rise), 11, 12.5, fc=TILE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((6, hc.FLOOR_Z + rise), 12.5, 31, fc=BONE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((-6, hc.FLOOR_Z - 12 + rise), 12, 12, fc="#4A4A52", ec=INK, lw=0.5))
    arrow(ax, (-30, 72), (-78, 44), rad=0.3)
    arrow(ax, (30, 72), (78, 44), rad=-0.3)
    arrow(ax, (0, 44), (0, 60), "12 mm")
    label(ax, (-70, 26), "open footprint about 190 mm", (-110, 86))
    label(ax, (40, 14), "eight seams: over both lobes,\ndown front and back, round the waist", (36, 90))
    turn_arrow(ax)

    ax = axes[1]
    frame(ax, "Section through the middle, seen from the side (front is left)", (-100, 110), (-22, 96))
    prof = side_profile()
    front = prof[(prof[:, 0] <= 0) & (prof[:, 1] >= split)]
    back = prof[(prof[:, 0] >= 0) & (prof[:, 1] >= split)]
    for half, sy in ((front, -1), (back, 1)):
        half = half[np.argsort(half[:, 1])]
        pts3 = np.c_[np.zeros(len(half)), half[:, 0], half[:, 1]]
        turned = rotate(pts3, np.array([0.0, sy * 7.0, split]), [-sy * 1.0, 0, 0], -hc.BLOOM_MAX)
        ax.plot(half[:, 0], half[:, 1], color=COAL, lw=1.2, ls=(0, (4, 3)))
        ax.plot(turned[:, 1], turned[:, 2], color=COAL, lw=4.5, solid_capstyle="round")
        ax.add_patch(Circle((sy * 7.0, split), 1.6, fc=STEEL, ec=INK, lw=0.5, zorder=5))
        knee = rotate(np.array([[0.0, sy * 9.5, split + 12.0]]), np.array([0.0, sy * 7.0, split]), [-sy * 1.0, 0, 0], -hc.BLOOM_MAX)[0]
        ax.plot([sy * 3.5, knee[1]], [split + 6 + rise, knee[2]], color=MOVE, lw=2.4)
        ax.add_patch(Circle((knee[1], knee[2]), 1.2, fc=STEEL, ec=INK, lw=0.4, zorder=5))
    ax.add_patch(Rectangle((-RING_R + 1.6, FOOT_Z), 2 * RING_R - 3.2, FOOT_H, fc="#3A3A40", ec=INK, lw=0.8))
    ax.add_patch(Rectangle((-RING_R, RING_TOP - RING_H), 2 * RING_R, RING_H, fc=COAL, ec=INK, lw=0.6))
    ax.add_patch(Polygon([(-RING_R + 0.6, RING_TOP + 0.4), (-14, split), (14, split), (RING_R - 0.6, RING_TOP + 0.4)], closed=True, fc="#33333A", ec=INK, lw=0.6))
    ax.add_patch(Rectangle((-1.5, RING_TOP - RING_H + 1), 3.0, split + 12 - RING_TOP + RING_H, fc=STEEL, ec=INK, lw=0.4))
    ax.add_patch(Rectangle((-5, split + 2 + rise), 10, 6, fc=MOVE, ec=INK, lw=0.5, alpha=0.85))
    ax.add_patch(Rectangle((-17, hc.FLOOR_Z + rise - 1.5), 26, 1.5, fc=TILE, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((9, hc.FLOOR_Z + rise), 1.5, 40, fc=HONEY, ec=INK, lw=0.5))
    ax.add_patch(Rectangle((-4, split + 8 + rise), 8, hc.FLOOR_Z - split - 9.5, fc="#4A4A52", ec=INK, lw=0.5))
    label(ax, (0, split - 4), "screw turned by the ring", (44, -8))
    label(ax, (4, split + 5 + rise), "nut rises: lifts the room\nand pushes four links", (44, 8))
    label(ax, (7, split), "four short hinges crowd\nthe narrow waist", (44, 26))
    label(ax, (-60, 34), "shards lie almost flat:\nlong levers on small hinges", (-98, 84))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "mechanism_c_bloom.png", dpi=120, facecolor=PAPER)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    diagram_wings()
    diagram_lift()
    diagram_bloom()
    print("wrote diagrams to", OUT)
