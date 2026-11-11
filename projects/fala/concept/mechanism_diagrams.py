"""Fala concept checkpoint: schematic diagrams of the three candidate drives.

Throwaway figures for the look brief (projects/fala/docs). Not to scale beyond the wave itself.

    uv run python projects/fala/concept/mechanism_diagrams.py
"""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import itertools

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

OUT = Path(__file__).resolve().parents[1] / "docs" / "img"
BRICK, RED, BONE, COAL, STEEL, PAPER = (
    "#9C4A33",
    "#C4161C",
    "#E9E2D0",
    "#26262A",
    "#8C97A1",
    "#F3F0EA",
)
INK = "#3A3A3F"

N, PITCH, AMP, WAVES = 8, 22.0, 3.5, 0.85
STREET = N * PITCH
K = 2 * math.pi * WAVES / STREET
EAVE, RIDGE = 26.0, 38.5


def wave(x, phase):
    return AMP * np.sin(K * np.asarray(x) - phase)


def poses(phase):
    edges = np.linspace(-STREET / 2, STREET / 2, N + 1)
    z = wave(edges, phase)
    return [
        ((edges[i] + edges[i + 1]) / 2, (z[i] + z[i + 1]) / 2, math.atan2(z[i + 1] - z[i], PITCH))
        for i in range(N)
    ]


def house(ax, xc, zc, lean, width=PITCH, body=19.0, alpha=1.0):
    """Front silhouette of one unit: bone tile, brick body, coal roof and chimney."""

    def tf(pts):
        c, s = math.cos(lean), math.sin(lean)
        return [(xc + x * c - z * s, zc + x * s + z * c) for x, z in pts]

    hw, hb = width / 2 - 0.3, body / 2
    ax.add_patch(
        Polygon(tf([(-hw, -3), (hw, -3), (hw, 0), (-hw, 0)]), fc=BONE, ec=INK, lw=0.8, alpha=alpha)
    )
    ax.add_patch(
        Polygon(
            tf([(-hb, 0), (hb, 0), (hb, EAVE), (-hb, EAVE)]), fc=BRICK, ec=INK, lw=0.8, alpha=alpha
        )
    )
    ax.add_patch(
        Polygon(
            tf([(-hb - 0.4, EAVE), (hb + 0.4, EAVE), (hb - 1.2, RIDGE), (-hb + 1.2, RIDGE)]),
            fc=COAL,
            ec=INK,
            lw=0.8,
            alpha=alpha,
        )
    )
    ax.add_patch(
        Polygon(
            tf([(2, RIDGE), (6.5, RIDGE), (6.5, RIDGE + 6), (2, RIDGE + 6)]),
            fc=BRICK,
            ec=INK,
            lw=0.8,
            alpha=alpha,
        )
    )
    for wx in (-4.5, 4.5):
        for wz in (6.2, 17.3):
            ax.add_patch(
                Polygon(
                    tf(
                        [(wx - 2.2, wz), (wx + 2.2, wz), (wx + 2.2, wz + 6.6), (wx - 2.2, wz + 6.6)]
                    ),
                    fc=BONE,
                    ec=RED,
                    lw=1.6,
                    alpha=alpha,
                )
            )


def base_box(ax, x0, x1, z0=-46, top=-6, label=True):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, top - z0, fc="#DDD8CE", ec=INK, lw=1.2))
    ax.add_patch(Rectangle((x0, z0), x1 - x0, 3, fc=COAL, ec=INK, lw=1.0))


def setup(ax, xlim, zlim, title):
    ax.set_xlim(*xlim)
    ax.set_ylim(*zlim)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=12.5, fontweight="bold", color=COAL, pad=8)


def note(ax, xy, xytext, text, ha="left", rad=0.0):
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        fontsize=8.8,
        color=INK,
        ha=ha,
        va="center",
        arrowprops={
            "arrowstyle": "-",
            "color": INK,
            "lw": 0.7,
            "connectionstyle": f"arc3,rad={rad}",
        },
    )


# ------------------------------------------------------------------ A: corkscrew
def diagram_a(phase_deg=40.0):
    phase = math.radians(phase_deg)
    fig, (ax, bx) = plt.subplots(
        1, 2, figsize=(15.5, 5.6), gridspec_kw={"width_ratios": [2.55, 1]}, facecolor=PAPER
    )
    setup(ax, (-150, 140), (-68, 56), "A  Corkscrew shaft   (long section, seen from the front)")
    x0, x1 = -STREET / 2 - 12, STREET / 2 + 30
    base_box(ax, x0, x1)
    z_ax, radius = -27.0, 9.0
    xs = np.linspace(-STREET / 2 - 4, STREET / 2 + 4, 400)
    zc = z_ax + wave(xs, phase)
    ax.fill_between(xs, zc - radius, zc + radius, color="#C9CED3", ec=INK, lw=0.9)
    ax.plot([x0 + 3, x1 + 4], [z_ax, z_ax], color=STEEL, lw=2.6, solid_capstyle="round")
    ax.plot([x0 + 3, x1 + 4], [z_ax, z_ax], color="white", lw=0.6, ls=(0, (6, 4)))
    edges = np.linspace(-STREET / 2, STREET / 2, N + 1)
    for (xc, zm, lean), xl, xr in zip(poses(phase), edges[:-1], edges[1:]):
        for xf in (xl + 1.8, xr - 1.8):  # the two feet of this unit
            top = zm + (xf - xc) * math.tan(lean) - 3
            ax.plot(
                [xf, xf],
                [top, z_ax + wave(xf, phase) + radius],
                color=COAL,
                lw=2.2,
                solid_capstyle="butt",
            )
        house(ax, xc, zm, lean)
    # bookends, gears, handwheel
    ax.add_patch(Rectangle((x0, -6), 11.5, 14, fc=BRICK, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((STREET / 2 + 0.5, -6), 29.5, 27, fc=BRICK, ec=INK, lw=1.0, alpha=0.35))
    gx = STREET / 2 + 12
    ax.add_patch(Rectangle((gx, z_ax - 16.5), 5, 33, fc="#B9B2A4", ec=INK, lw=1.0))
    ax.add_patch(Rectangle((gx, -5 - 5.5), 5, 11, fc="#B9B2A4", ec=INK, lw=1.0))
    ax.plot([gx - 3, x1 + 10], [-5, -5], color=STEEL, lw=2.2)
    ax.add_patch(Rectangle((x1 + 2, -24), 5, 38, fc=COAL, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((x1 + 7, 6), 10, 6.5, fc=RED, ec=INK, lw=1.0))
    ax.add_patch(
        FancyArrowPatch(
            (x1 + 14, -16),
            (x1 + 14, 2),
            connectionstyle="arc3,rad=-0.9",
            arrowstyle="-|>",
            mutation_scale=14,
            color=RED,
            lw=1.6,
        )
    )
    note(
        ax,
        (-60, z_ax + wave(-60, phase) - radius + 1),
        (-100, -58),
        "'corkscrew': a round bar whose centre\nspirals around the axle, so its top\nedge is a travelling sine wave",
    )
    note(
        ax,
        (edges[4] + 1.8, -13),
        (-14, -58),
        "two feet per house: each unit is a\nchord of the wave, so the pavement\nstays one unbroken ribbon",
    )
    note(ax, (gx + 2.5, -38), (66, -58), "3 : 1 gears hidden in the\nwinding-engine house")
    note(ax, (x1 + 12, 9), (x1 + 4, 34), "handwheel with\nfree-spinning knob", ha="center")
    note(ax, (x0 + 4, z_ax), (-148, -27), "4 mm steel axle:\nno sag in a\nhot window")
    ax.annotate(
        "", xy=(40, 50), xytext=(-40, 50), arrowprops={"arrowstyle": "-|>", "color": RED, "lw": 1.6}
    )
    ax.text(
        0,
        52.3,
        "wave travels this way; turn back and it reverses",
        ha="center",
        fontsize=9,
        color=RED,
    )

    setup(bx, (-34, 54), (-68, 56), "cross-section through one house")
    yf, yb = -19.0, 39.0
    for y in (yf, yb - 2.6):
        bx.add_patch(Rectangle((y, -46), 2.6, 40, fc=COAL, ec=INK, lw=1.0))
    bx.add_patch(Rectangle((yf, -46), yb - yf, 3, fc=COAL, ec=INK, lw=1.0))
    zm = 2.0
    th = math.radians(55)
    cy, cz = 14 + AMP * math.cos(th), z_ax + AMP * math.sin(th)
    zm = cz - z_ax  # unit height follows the eccentric
    bx.add_patch(Circle((cy, cz), radius, fc="#C9CED3", ec=INK, lw=1.0))
    bx.add_patch(Circle((14, z_ax), 2.0, fc=STEEL, ec=INK, lw=0.8))
    bx.add_patch(Circle((14, z_ax), AMP, fc="none", ec=RED, lw=0.9, ls=(0, (3, 2))))
    # C-foot: captured above and below the bar, open to the rear
    jt, jb = cz + radius, cz - radius
    foot = [
        (-2, zm - 3),
        (30, zm - 3),
        (30, jt),
        (30, jt),
        (1.5, jt),
        (1.5, jb),
        (30, jb),
        (30, jb - 3),
        (-2, jb - 3),
    ]
    bx.add_patch(Polygon(foot, fc="#6E6A66", ec=INK, lw=1.0, alpha=0.9))
    # tile, skirts, keel, house
    bx.add_patch(Rectangle((-16, zm - 3), 52, 3, fc=BONE, ec=INK, lw=1.0))
    for y in (-16, 34.4):
        bx.add_patch(Rectangle((y, zm - 20), 1.6, 17, fc=COAL, ec=INK, lw=0.8))
    bx.add_patch(Rectangle((-10.2, zm - 30), 1.8, 27, fc="#6E6A66", ec=INK, lw=0.8))
    for y in (-12.6, -7.9):
        bx.add_patch(Rectangle((y, -43), 2.0, 26, fc=COAL, ec=INK, lw=0.8))
    bx.add_patch(
        Polygon([(0, zm), (32, zm), (32, zm + EAVE), (0, zm + EAVE)], fc=BRICK, ec=INK, lw=1.0)
    )
    bx.add_patch(
        Polygon([(-2, zm + EAVE), (33.5, zm + EAVE), (16, zm + RIDGE)], fc=COAL, ec=INK, lw=1.0)
    )
    bx.add_patch(Rectangle((13.7, zm + RIDGE - 2), 4.6, 8, fc=BRICK, ec=INK, lw=1.0))
    note(bx, (-9.3, -36), (-33, -58), "keel between two ribs:\nonly rise and lean\nare free")
    note(bx, (26, jb - 1.5), (14, -58), "C-foot wraps the bar:\nnothing can lift\nor rattle")
    note(bx, (-17.5, -9), (-33, 16), "fascia hides\nthe skirt", rad=-0.2)
    note(bx, (14 + AMP, z_ax), (47, -10), "offset\n= rise", ha="center")
    bx.text(-26, 3.5, "front", fontsize=8.5, color=INK, ha="center")
    fig.tight_layout()
    fig.savefig(OUT / "mechanism_a_corkscrew.png", dpi=130, facecolor=PAPER)
    plt.close(fig)


# ------------------------------------------------------------------ B: quadrature wedge bars
def diagram_b(theta_deg=40.0):
    theta = math.radians(theta_deg)
    fig, ax = plt.subplots(figsize=(13.5, 5.4), facecolor=PAPER)
    setup(ax, (-112, 138), (-56, 52), "B  Two sliding wedge bars in quadrature   (long section)")
    x0, x1 = -STREET / 2 - 12, STREET / 2 + 30
    base_box(ax, x0, x1, z0=-40)
    s1, s2 = 4.0 * math.sin(theta), 4.0 * math.cos(theta)
    edges = np.linspace(-STREET / 2, STREET / 2, N + 1)
    for row, (shift, zbar, colour) in enumerate(((s1, -22.0, "#B9B2A4"), (s2, -33.0, "#A9B3BB"))):
        ax.add_patch(
            Rectangle(
                (-STREET / 2 - 6 + shift, zbar - 3), STREET + 26, 3, fc=colour, ec=INK, lw=1.0
            )
        )
        for i in range(N):
            ph = K * (edges[i] + PITCH / 2)
            slope = (math.cos(ph), math.sin(ph))[row] * 0.55
            xa, xb = edges[i] + 4 + shift, edges[i + 1] - 4 + shift
            mid = 2.6
            ax.add_patch(
                Polygon(
                    [
                        (xa, zbar),
                        (xb, zbar),
                        (xb, zbar + mid + slope * 7),
                        (xa, zbar + mid - slope * 7),
                    ],
                    fc=colour,
                    ec=INK,
                    lw=0.9,
                )
            )
    for i, (xc, zm, lean) in enumerate(poses(-theta + math.pi / 2)):
        ph = K * xc
        z1 = -22 + 2.6 + math.cos(ph) * 0.55 * (-s1)
        z2 = -33 + 2.6 + math.sin(ph) * 0.55 * (-s2)
        ax.plot([xc - 3, xc - 3], [z1 + 1.2, -8 + zm], color=COAL, lw=1.6)
        ax.plot([xc + 3, xc + 3], [z2 + 1.2, -8 + zm], color=COAL, lw=1.6)
        ax.add_patch(Circle((xc - 3, z1 + 1.2), 1.2, fc=COAL, ec=INK, lw=0.6))
        ax.add_patch(Circle((xc + 3, z2 + 1.2), 1.2, fc=COAL, ec=INK, lw=0.6))
        ax.plot([xc - 5, xc + 5], [-8 + zm, -8 + zm], color=COAL, lw=2.4)
        ax.plot([xc, xc], [-8 + zm, zm - 3], color=COAL, lw=2.0)
        house(ax, xc, zm, 0.0)
    ax.add_patch(Rectangle((x0, -6), 11.5, 14, fc=BRICK, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((STREET / 2 + 0.5, -6), 29.5, 27, fc=BRICK, ec=INK, lw=1.0, alpha=0.35))
    cx = STREET / 2 + 17
    for zbar, ang, shift in ((-23.5, theta, s1), (-34.5, theta + math.pi / 2, s2)):
        ax.add_patch(Circle((cx, zbar), 5.2, fc="#DDD8CE", ec=INK, lw=1.0))
        ax.add_patch(
            Circle(
                (cx + 3.2 * math.sin(ang), zbar + 3.2 * math.cos(ang)), 1.3, fc=RED, ec=INK, lw=0.6
            )
        )
    ax.plot([cx, x1 + 10], [-29, -29], color=STEEL, lw=2.2)
    ax.add_patch(Rectangle((x1 + 2, -46), 5, 34, fc=COAL, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((x1 + 7, -19), 10, 6.5, fc=RED, ec=INK, lw=1.0))
    for zbar, lab in ((-20.5, "bar 1 slides  e·sin θ"), (-31.5, "bar 2 slides  e·cos θ")):
        ax.annotate(
            "",
            xy=(-STREET / 2 - 13, zbar - 3),
            xytext=(-STREET / 2 + 1, zbar - 3),
            arrowprops={"arrowstyle": "<|-|>", "color": RED, "lw": 1.3},
        )
    note(
        ax,
        (-66, -20),
        (-104, -50),
        "two flat bars, each with one ramp per house;\nramp slopes follow cos and sin of the house's place in the wave",
    )
    note(
        ax,
        (edges[4] + PITCH / 2, -8),
        (4, -50),
        "balance beam averages the two bars:\nheight = cos·bar1 + sin·bar2 = travelling wave",
    )
    note(ax, (cx, -34.5), (84, -50), "two eccentrics 90° apart\npush the bars to and fro")
    ax.text(
        0,
        49.3,
        "houses rise and fall in sequence; lean needs a second ramp track per house",
        ha="center",
        fontsize=9,
        color=RED,
    )
    fig.tight_layout()
    fig.savefig(OUT / "mechanism_b_wedge_bars.png", dpi=130, facecolor=PAPER)
    plt.close(fig)


# ------------------------------------------------------------------ C: belt-driven crank row
def diagram_c(theta_deg=40.0):
    theta = math.radians(theta_deg)
    fig, ax = plt.subplots(figsize=(13.5, 5.4), facecolor=PAPER)
    setup(ax, (-112, 138), (-56, 52), "C  Row of belt-driven cranks   (long section)")
    x0, x1 = -STREET / 2 - 12, STREET / 2 + 30
    base_box(ax, x0, x1, z0=-46)
    zp, rp, e = -20.0, 6.5, 2.6
    centres = [(-STREET / 2 + (i + 0.5) * PITCH) for i in range(N)]
    drive = STREET / 2 + 16
    ax.plot([centres[0], drive], [zp + rp, zp + rp], color=COAL, lw=2.0)
    ax.plot([centres[0], drive], [zp - rp, zp - rp], color=COAL, lw=2.0)
    for xc in centres[:-1]:  # idlers keep the wrap on each pulley
        ax.add_patch(Circle((xc + PITCH / 2, zp + rp - 2.2), 2.2, fc="#DDD8CE", ec=INK, lw=0.8))
    for i, xc in enumerate(centres):
        ang = theta + K * xc
        px, pz = xc + e * math.cos(ang), zp + e * math.sin(ang)
        ax.add_patch(Circle((xc, zp), rp, fc="#B9B2A4", ec=INK, lw=1.0))
        ax.add_patch(Circle((xc, zp), 1.0, fc=STEEL, ec=INK, lw=0.6))
        gz = -42.0  # guide pin in a vertical slot below
        lean = math.atan2(px - xc, pz - gz)
        ax.add_patch(Rectangle((xc - 1.0, gz - 4), 2.0, 8, fc="white", ec=INK, lw=0.7))
        ax.plot([xc, px], [gz, pz], color=COAL, lw=1.6)
        ax.add_patch(Circle((xc, gz), 0.9, fc=COAL, ec=INK, lw=0.5))
        ax.add_patch(Circle((px, pz), 1.4, fc=RED, ec=INK, lw=0.6))
        top = (px + 17 * math.sin(lean), pz + 17 * math.cos(lean))
        ax.plot([px, top[0]], [pz, top[1]], color=COAL, lw=1.6)
        house(
            ax,
            top[0] + 3 * math.sin(lean),
            top[1] + 3 * math.cos(lean),
            -lean,
            width=17.5,
            body=15.0,
        )
        ax.add_patch(Circle((xc, -3 + 17 + zp + 0.0), e, fc="none", ec=RED, lw=0.7, ls=(0, (3, 2))))
    ax.add_patch(Circle((drive, zp), rp, fc="#B9B2A4", ec=INK, lw=1.0))
    ax.plot([drive, x1 + 10], [zp, zp], color=STEEL, lw=2.2)
    ax.add_patch(Rectangle((x0, -6), 11.5, 14, fc=BRICK, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((STREET / 2 + 0.5, -6), 29.5, 27, fc=BRICK, ec=INK, lw=1.0, alpha=0.35))
    ax.add_patch(Rectangle((x1 + 2, zp - 19), 5, 38, fc=COAL, ec=INK, lw=1.0))
    ax.add_patch(Rectangle((x1 + 7, zp + 9), 10, 6.5, fc=RED, ec=INK, lw=1.0))
    note(
        ax,
        (centres[1], zp - rp),
        (-104, -51.5),
        "one small crank under every house, all turned by one\nclosed GT2 timing belt (bought); 8 pulleys + 7 idlers",
    )
    note(
        ax,
        (centres[4], -42),
        (2, -51.5),
        "pin in a slot below makes the house\nlean as its crank pin swings sideways",
    )
    note(
        ax,
        (centres[7], zp + 14),
        (112, 38),
        "every house travels\na small circle, like\na cork on water",
        ha="center",
    )
    ax.text(
        0,
        49.3,
        "richest motion (rise, sway and lean), but houses need wide gaps and the pavement breaks up",
        ha="center",
        fontsize=9,
        color=RED,
    )
    fig.tight_layout()
    fig.savefig(OUT / "mechanism_c_crank_row.png", dpi=130, facecolor=PAPER)
    plt.close(fig)


# ------------------------------------------------------------------ wave numbers
def wave_numbers():
    """Rise, lean and the V-gap between neighbours over one full turn (chord model)."""
    lean_max = gap_e = gap_r = 0.0
    for ph in np.linspace(0, 2 * math.pi, 720, endpoint=False):
        p = poses(ph)
        lean_max = max(lean_max, max(abs(a) for _, _, a in p))
        for (_, _, a), (_, _, b) in itertools.pairwise(p):
            gap_e = max(gap_e, abs(EAVE * (math.sin(b) - math.sin(a))))
            gap_r = max(gap_r, abs(RIDGE * (math.sin(b) - math.sin(a))))
    print(
        f"wave: {WAVES} wavelengths on the street, amplitude {AMP} mm -> rise {2 * AMP:.1f} mm total"
    )
    print(
        f"max lean {math.degrees(lean_max):.1f} deg; gap swing between neighbours "
        f"+/-{gap_e:.2f} mm at eaves, +/-{gap_r:.2f} mm at ridge"
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    wave_numbers()
    diagram_a()
    diagram_b()
    diagram_c()
    print("wrote diagrams to", OUT)
