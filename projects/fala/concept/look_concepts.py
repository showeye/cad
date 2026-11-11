"""Fala concept checkpoint: three quick LOOK studies, posed on the wave.

Throwaway massing models for choosing a look, not product geometry. Each look is a terrace of
house units standing on ground tiles; every unit is placed as a chord of one travelling sine
(two support points per unit), which is how the recommended mechanism would carry it.

    uv run python projects/fala/concept/look_concepts.py            # OCP viewer + PNGs
    uv run python projects/fala/concept/look_concepts.py --no-show  # PNGs only
    uv run python projects/fala/concept/look_concepts.py --strip    # also wave filmstrip frames

Units: mm, degrees. x = along the street, y = depth (front is -y), z = up, pavement at z = 0.
"""

# %%
import math
import sys
from pathlib import Path

import numpy as np
from build123d import Box, Compound, Cylinder, Polyline, Pos, Rot, Text, extrude, make_face

OUT = Path(__file__).resolve().parents[1] / "docs" / "img"

STREET = 176.0  # length of the moving street
TILE_FRONT, TILE_BACK = -16.0, 36.0  # ground tile extent in y (facade plane is y = 0)
HOUSE_DEPTH = 32.0

PALETTES = {
    "nikisz": {"brick": "#70392B", "red": "#C4161C", "bone": "#E9E2D0", "coal": "#26262A"},
    "kolonia": {"brick": "#9C4A33", "red": "#C4161C", "bone": "#E9E2D0", "coal": "#26262A"},
    "bajka": {"brick": "#B4573A", "red": "#D3222A", "bone": "#EFE8D6", "coal": "#2B2B30"},
}


# ---------------------------------------------------------------- helpers
def prism_y(pts_xz, y0, y1):
    """Extrude an (x, z) outline from y0 to y1."""
    face = make_face(Polyline(*[(x, y0, z) for x, z in pts_xz], close=True))
    return extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def prism_x(pts_yz, x0, x1):
    """Extrude a (y, z) outline from x0 to x1."""
    face = make_face(Polyline(*[(x0, y, z) for y, z in pts_yz], close=True))
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def arch_outline(xc, z0, width, height, rise, n=8):
    """Window outline with a segmental arch top (rise = 0 gives a rectangle)."""
    half = width / 2
    pts = [(xc - half, z0), (xc + half, z0), (xc + half, z0 + height - rise)]
    if rise > 0:
        radius = (half**2 + rise**2) / (2 * rise)
        zc = z0 + height - radius
        a0 = math.asin(half / radius)
        for i in range(1, n):
            a = a0 - 2 * a0 * i / n
            pts.append((xc + radius * math.sin(a), zc + radius * math.cos(a)))
    pts.append((xc - half, z0 + height - rise))
    return pts


def grow(pts, d):
    """Offset an outline outwards by d (good enough for convex window outlines)."""
    cx = sum(p[0] for p in pts) / len(pts)
    cz = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, z in pts:
        out.append((x + math.copysign(d, x - cx), z + math.copysign(d, z - cz)))
    return out


class Unit:
    """Solids of one moving unit (house + ground tile), grouped by colour, in local coordinates."""

    def __init__(self):
        self.parts = {"brick": [], "red": [], "bone": [], "coal": []}
        self.cuts = []

    def add(self, colour, solid):
        self.parts[colour].append(solid)

    def window(self, xc, z0, w, h, rise=0.0, y=0.0, frame=1.0, sill=True, pane="bone"):
        """Recessed pane, proud red surround and red sill on a facade at plane y."""
        outline = arch_outline(xc, z0, w, h, rise)
        self.cuts.append(prism_y(outline, y - 0.1, y + 1.2))
        self.add(pane, prism_y(outline, y + 0.9, y + 1.6))
        ring = prism_y(grow(outline, frame), y - 0.5, y + 0.9) - prism_y(outline, y - 1, y + 1)
        self.add("red", ring)
        if sill:
            self.add(
                "red",
                box(
                    xc - w / 2 - frame - 0.5,
                    xc + w / 2 + frame + 0.5,
                    y - 1.1,
                    y + 0.2,
                    z0 - frame - 0.9,
                    z0 - frame + 0.1,
                ),
            )

    def tile(self, width, kerb=True):
        """Bone pavement slab with a kerb step, coal skirts front and back."""
        hw = width / 2 - 0.3
        self.add("bone", box(-hw, hw, TILE_FRONT + 5, TILE_BACK, -3, 0))
        self.add("bone", box(-hw, hw, TILE_FRONT, TILE_FRONT + 5, -3, -1.0 if kerb else 0))
        self.add("coal", box(-hw, hw, TILE_FRONT, TILE_FRONT + 1.6, -20, -3))
        self.add("coal", box(-hw, hw, TILE_BACK - 1.6, TILE_BACK, -20, -3))

    def finish(self, body):
        if self.cuts:
            body = body - Compound(self.cuts)
        self.parts["brick"].insert(0, body)
        return {k: Compound(v) for k, v in self.parts.items() if v}


def chimney(u, x, y, z0, z1, s=4.6):
    u.add("brick", box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z0, z1))
    u.add(
        "coal",
        box(x - s / 2 - 0.7, x + s / 2 + 0.7, y - s / 2 - 0.7, y + s / 2 + 0.7, z1, z1 + 1.4),
    )


def anchor(u, x, z, y=0.0, s=1.5):
    """Tie-rod anchor plate, the mining-damage tell: a small X."""
    for a in (45, -45):
        u.add("coal", Pos(x, y - 0.35, z) * Rot(0, a, 0) * Box(2 * s, 0.9, 0.9))


def crack(u, x, z, y=0.0, steps=5, right=True):
    """Stepped crack following the brick courses, as a shallow coal inlay."""
    d = 1 if right else -1
    for i in range(steps):
        u.add(
            "coal",
            box(
                x + d * i * 1.2 - 0.6,
                x + d * i * 1.2 + 0.9,
                y - 0.25,
                y + 0.3,
                z + i * 1.5,
                z + i * 1.5 + 0.7,
            ),
        )
        u.add(
            "coal",
            box(
                x + d * (i * 1.2 + 0.6) - 0.35,
                x + d * (i * 1.2 + 0.6) + 0.35,
                y - 0.25,
                y + 0.3,
                z + i * 1.5,
                z + (i + 1) * 1.5 + 0.7,
            ),
        )


def lunette(u, x, r=1.9, y=0.0, z=0.9):
    pts = [(x - r, z)] + [
        (x + r * math.cos(math.pi * i / 8), z + r * math.sin(math.pi * i / 8)) for i in range(9)
    ]
    u.add("coal", prism_y(pts, y - 0.9, y + 0.3))


# ---------------------------------------------------------------- look 1: Nikisz
def nikisz_house(kind, pitch=22.0):
    """Alternating bays as in Nikiszowiec: A is tall and proud with wings, B low and recessed."""
    u = Unit()
    u.tile(pitch)
    if kind.startswith("A"):
        yf, eave, bw, fw = -2.6, 36.0, 15.0, 25.0
        body = box(-bw / 2, bw / 2, yf + 1.6, HOUSE_DEPTH, 0, eave)
        body += box(-fw / 2, fw / 2, yf, yf + 1.6, 0, eave)  # facade plate with wings
        body += box(-fw / 2, fw / 2, yf - 0.7, yf + 0.2, 0, 4.5)  # plinth
        for x in (-fw / 2 + 1.1, fw / 2 - 1.1):  # corner pilasters
            body += box(x - 1.1, x + 1.1, yf - 0.7, yf + 0.2, 0, eave)
        if kind == "A-gate":
            gate = arch_outline(0, 0, 8.4, 10.5, 3.2)
            u.cuts.append(prism_y(gate, yf - 1, yf + 5))
            u.add("coal", prism_y(gate, yf + 3.0, yf + 5.2))
            ring = prism_y(grow(gate, 1.3), yf - 0.7, yf + 0.4) - prism_y(gate, yf - 1, yf + 1)
            u.add("brick", ring - box(-9, 9, yf - 1, yf + 1, -3, 0))
            # oriel above the gateway, the Nikiszowiec signature
            u.add("brick", box(-4.6, 4.6, yf - 3.2, yf, 14.0, 16.2))
            u.add("bone", box(-4.0, 4.0, yf - 2.9, yf, 16.2, 22.8))
            for x in (-4.0, -1.35, 1.35, 4.0):
                u.add("red", box(x - 0.5, x + 0.5, yf - 3.2, yf, 16.2, 22.8))
            u.add("coal", prism_x([(yf - 3.9, 22.8), (yf, 22.8), (yf, 25.4)], -5.3, 5.3))
        else:
            for x in (-4.6, 4.6):
                u.window(x, 7.0, 4.2, 6.2, y=yf)
                u.window(x, 17.2, 4.2, 6.2, y=yf)
            for x in (-7.6, 7.6):
                lunette(u, x, y=yf - 0.7)
        for x in (-6.2, 0.0, 6.2):  # small arched attic windows
            u.window(x, 27.6, 3.0, 5.0, rise=1.5, y=yf, frame=0.8, sill=False)
        body += box(-fw / 2, fw / 2, yf - 0.7, yf + 0.2, 25.2, 26.4)  # band under the attic
        u.add("coal", box(-fw / 2 - 0.6, fw / 2 + 0.6, yf - 2.6, HOUSE_DEPTH + 1, eave, eave + 1.8))
        u.add("coal", box(-bw / 2, bw / 2, yf + 1, HOUSE_DEPTH - 2, eave + 1.8, eave + 3.2))
        chimney(u, 3.5 if kind == "A" else -3.5, 20, eave + 3.2, eave + 7.5)
        anchor(u, -fw / 2 + 1.1, 25.8, y=yf - 0.7)
        anchor(u, fw / 2 - 1.1, 25.8, y=yf - 0.7)
    else:
        yf, eave, bw, fw = 0.0, 27.0, 17.0, 23.6
        body = box(-bw / 2, bw / 2, yf + 1.6, HOUSE_DEPTH, 0, eave)
        body += box(-fw / 2, fw / 2, yf, yf + 1.6, 0, eave)
        body += box(-fw / 2, fw / 2, yf - 0.6, yf + 0.2, 14.6, 15.8)  # string course
        for x in (-4.4, 4.4):
            u.window(x, 6.0, 4.2, 6.4, rise=1.0, y=yf)
            u.window(x, 17.4, 4.2, 6.4, rise=1.0, y=yf)
        if kind == "B-crack":
            crack(u, -1.2, 15.8, y=yf)
        u.add(
            "coal",
            prism_x(
                [
                    (yf - 1.6, eave),
                    (HOUSE_DEPTH + 1, eave),
                    (HOUSE_DEPTH + 1, eave + 1.2),
                    (17, eave + 7.5),
                    (13, eave + 7.5),
                ],
                -fw / 2,
                fw / 2,
            ),
        )
        chimney(u, 0, 15, eave + 7.0, eave + 11.5)
    return u.finish(body)


# ---------------------------------------------------------------- look 2: Kolonia
def kolonia_house(kind, pitch=22.0):
    """One repeated colony familok: segmental arches, red frames and sills, string course."""
    u = Unit()
    u.tile(pitch)
    bw, eave = pitch - 3.0, 26.0
    body = box(-bw / 2, bw / 2, 0, HOUSE_DEPTH, 0, eave)
    body += box(-bw / 2, bw / 2, -0.7, 0.2, 0, 4.6)  # plinth
    body += box(-bw / 2, bw / 2, -0.6, 0.2, 14.4, 15.6)  # string course
    body += box(-bw / 2, bw / 2, -0.9, 0.2, eave - 1.6, eave)  # cornice
    for x in (-bw / 2 + 0.9, bw / 2 - 0.9):  # corner pilasters
        body += box(x - 0.9, x + 0.9, -0.6, 0.2, 0, eave)
    for x in (-4.5, 4.5):
        u.window(x, 17.3, 4.4, 6.6, rise=1.1)
        if kind == "door" and x < 0:
            door = arch_outline(x, 1.2, 4.4, 11.8, 1.1)
            u.cuts.append(prism_y(door, -1, 1.2))
            u.add("red", prism_y(door, 0.5, 1.6))
            u.add("bone", prism_y(arch_outline(x, 9.6, 3.0, 2.6, 0.7), 0.2, 1.0))
            u.add("bone", box(x - 3.4, x + 3.4, -2.8, -0.7, 0, 1.2))  # doorstep
        else:
            u.window(x, 6.2, 4.4, 6.6, rise=1.1)
            lunette(u, x, y=-0.7)
    if kind == "crack":
        crack(u, -0.8, 15.6, steps=6)
    anchor(u, 0, 15.0, y=-0.6)
    # gable roof, ridge along the street: layer lines will read as tile courses
    u.add(
        "coal",
        prism_x(
            [
                (-2.0, eave),
                (HOUSE_DEPTH + 1.5, eave),
                (HOUSE_DEPTH + 1.5, eave + 1.0),
                (16, eave + 12.5),
                (-2.0, eave + 1.0),
            ],
            -bw / 2 - 0.4,
            bw / 2 + 0.4,
        ),
    )
    chimney(u, 4.2 if kind != "door" else -4.2, 16, eave + 10.5, eave + 17.0)
    # dilatation joint: a recessed coal tongue that fills the V-gap to the next house
    u.add("brick", box(bw / 2 - 0.5, bw / 2 + 3.4, 1.6, HOUSE_DEPTH - 1.5, -0.2, eave + 0.5))
    return u.finish(body)


# ---------------------------------------------------------------- look 3: Bajka
def bajka_house(i, pitch=176.0 / 6):
    """Storybook exaggeration: fat, uneven, oversized windows and chimneys."""
    u = Unit()
    u.tile(pitch)
    eave = [24.0, 31.0, 21.0, 28.0, 23.0, 32.0][i]
    bw = pitch - 3.4
    body = box(-bw / 2, bw / 2, 0, HOUSE_DEPTH, 0, eave)
    body += box(-bw / 2 - 0.5, bw / 2 + 0.5, -1.0, 0.2, 0, 4.0)
    body += box(-bw / 2 - 0.5, bw / 2 + 0.5, -1.2, 0.2, eave - 2.2, eave)
    floors = 2 if eave >= 28 else 1
    win_h = 8.2 if floors == 2 else eave - 12.5
    for f in range(floors):
        z = 6.5 + f * 11.5
        for x in (-6.4, 6.4):
            if f == 0 and x < 0 and i % 2 == 0:
                door = arch_outline(x, 0.8, 6.0, 12.0, 3.0)
                u.cuts.append(prism_y(door, -1, 1.2))
                u.add("red", prism_y(door, 0.5, 1.6))
            else:
                u.window(x, z, 6.2, win_h, rise=1.8, frame=1.5)
    if i in (1, 4):
        crack(u, 0.0, 15.0, steps=6, right=i == 1)
    anchor(u, 0, 4.9, y=-1.0, s=2.0)
    u.add(
        "coal",
        prism_x(
            [
                (-3.0, eave),
                (HOUSE_DEPTH + 2, eave),
                (HOUSE_DEPTH + 2, eave + 1.4),
                (16, eave + 15.0),
                (-3.0, eave + 1.4),
            ],
            -bw / 2 - 1.0,
            bw / 2 + 1.0,
        ),
    )
    chimney(u, 6.5 if i % 2 else -6.5, 14, eave + 11.0, eave + 21.0, s=6.4)
    u.add("brick", box(bw / 2 - 0.5, bw / 2 + 3.8, 1.6, HOUSE_DEPTH - 1.5, -0.2, eave + 0.5))
    return u.finish(body)


# ---------------------------------------------------------------- shared base
def base():
    """Coal block with a mine cross-section in relief, two fixed bookends and the crank wheel."""
    x0, x1 = -STREET / 2 - 12, STREET / 2 + 30
    yf, yb, zb, top = TILE_FRONT - 3, TILE_BACK + 3, -46.0, -6.0
    coal, bone, red, brick = [], [], [], []
    block = box(x0, x1, yf, yb, zb, top) - box(
        -STREET / 2 - 0.4, STREET / 2 + 0.4, TILE_FRONT - 0.4, TILE_BACK + 0.4, -30, top + 1
    )
    block += box(x0, x1, yf - 1.2, yb + 1.2, zb, zb + 2.5)  # foot moulding
    # strata grooves and the gallery niche
    cuts = [box(x0 - 1, x1 + 1, yf - 0.2, yf + 0.7, z, z + 0.9) for z in (-14.5, -22.0, -36.0)]
    gal = arch_outline(22, -34.5, 44, 11.5, 3.0)
    cuts.append(prism_y(gal, yf - 0.2, yf + 1.8))
    coal.append(block - Compound(cuts))
    for gx in (4, 14, 30, 40):  # pit props and caps
        bone.append(box(gx - 0.7, gx + 0.7, yf + 0.5, yf + 1.8, -34.5, -25.6))
    bone.append(box(2.5, 41.5, yf + 0.5, yf + 1.8, -25.6, -24.4))
    red.append(box(18, 27, yf + 0.3, yf + 1.8, -32.6, -28.6))  # coal tub
    for wx in (20, 25):
        coal.append(Pos(wx, yf + 1.0, -33.3) * Rot(90, 0, 0) * Cylinder(1.2, 1.4))
    title = Text("FALA", font_size=8.5, font="Arial Black")
    bone.append(Pos(-58, yf, -30) * Rot(90, 0, 0) * extrude(title, 0.6))
    plate = Text("07/50", font_size=4.2, font="Arial Black")
    bone.append(Pos(-58, yf, -39.5) * Rot(90, 0, 0) * extrude(plate, 0.5))
    # left bookend: brick boundary wall with coal coping
    brick.append(box(x0, -STREET / 2 - 0.5, yf, yb, top, 8))
    coal.append(box(x0 - 0.8, -STREET / 2 + 0.2, yf - 0.8, yb + 0.8, 8, 10))
    # right bookend: winding-engine house that hides the gears, wheel on its end wall
    ex0, ex1 = STREET / 2 + 0.5, x1
    brick.append(box(ex0, ex1, yf, yb, top, 21))
    coal.append(box(ex0 - 0.8, ex1 + 0.8, yf - 1.5, yb + 1.5, 21, 23.2))
    ew = arch_outline((ex0 + ex1) / 2, 4.5, 9, 11, 4.5)
    bone.append(prism_y(ew, yf - 0.1, yf + 0.5))
    red.append(prism_y(grow(ew, 1.1), yf - 0.6, yf + 0.3) - prism_y(ew, yf - 1, yf + 1))
    wheel = Cylinder(19, 5) - Cylinder(15, 6)
    wheel += Cylinder(4.5, 5)
    for a in range(0, 180, 45):
        wheel += Rot(0, 0, a) * Box(34, 2.4, 5)
    wy, wz = (yf + yb) / 2, -2.0
    coal.append(Pos(x1 + 3.2, wy, wz) * Rot(0, 90, 0) * wheel)
    red.append(Pos(x1 + 10.5, wy, wz + 15) * Rot(0, 90, 0) * Cylinder(3.6, 10))
    return {
        "coal": Compound(coal),
        "bone": Compound(bone),
        "red": Compound(red),
        "brick": Compound(brick),
    }


# ---------------------------------------------------------------- posing on the wave
def chord_poses(n, amplitude, waves, phase_deg):
    """Centre height and lean of each unit when its two feet ride one travelling sine."""
    pitch = STREET / n
    k = 2 * math.pi * waves / STREET
    edges = [-STREET / 2 + i * pitch for i in range(n + 1)]
    z = [amplitude * math.sin(k * x - math.radians(phase_deg)) for x in edges]
    return [
        (
            (edges[i] + edges[i + 1]) / 2,
            (z[i] + z[i + 1]) / 2,
            math.degrees(math.atan2(z[i + 1] - z[i], pitch)),
        )
        for i in range(n)
    ]


LOOKS = {
    "nikisz": {
        "n": 8,
        "kinds": ["A", "B", "A-gate", "B-crack", "A", "B", "A", "B"],
        "make": nikisz_house,
        "amplitude": 3.5,
        "waves": 0.85,
    },
    "kolonia": {
        "n": 8,
        "kinds": ["plain", "door", "plain", "crack", "door", "plain", "door", "plain"],
        "make": kolonia_house,
        "amplitude": 3.5,
        "waves": 0.85,
    },
    "bajka": {
        "n": 6,
        "kinds": [0, 1, 2, 3, 4, 5],
        "make": bajka_house,
        "amplitude": 5.0,
        "waves": 0.8,
    },
}


_CACHE = {}


def build_look(name, phase_deg=None):
    """Return [(colour, Compound)] for a whole piece; phase None = at rest (flat street)."""
    spec = LOOKS[name]
    amp = 0.0 if phase_deg is None else spec["amplitude"]
    if "base" not in _CACHE:
        _CACHE["base"] = base()
    out = [(c, s) for c, s in _CACHE["base"].items()]
    for kind, (x, z, lean) in zip(
        spec["kinds"], chord_poses(spec["n"], amp, spec["waves"], phase_deg or 0)
    ):
        if (name, kind) not in _CACHE:
            _CACHE[name, kind] = spec["make"](kind)
        for colour, solid in _CACHE[name, kind].items():
            out.append((colour, Pos(x, 0, z) * Rot(0, -lean, 0) * solid))
    return out


# ---------------------------------------------------------------- rendering
def render(name, parts, path, view="hero", size=(1500, 900)):
    import pyvista as pv

    pal = PALETTES[name]
    pl = pv.Plotter(off_screen=True, window_size=size, lighting="none")
    pl.set_background("#F3F0EA")
    for colour, shape in parts:
        verts, tris = shape.tessellate(0.03, 0.25)
        v = np.array([(p.X, p.Y, p.Z) for p in verts])
        f = np.hstack([np.full((len(tris), 1), 3), np.array(tris)]).astype(np.int64)
        pl.add_mesh(
            pv.PolyData(v, f),
            color=pal[colour],
            smooth_shading=False,
            ambient=0.32,
            diffuse=0.78,
            specular=0.0,
        )
    floor = pv.Plane(center=(0, 10, -46.05), direction=(0, 0, 1), i_size=6000, j_size=6000)
    pl.add_mesh(floor, color="#F3F0EA", ambient=1.0, diffuse=0.0, specular=0.0)
    pl.add_light(pv.Light(position=(260, -420, 480), focal_point=(0, 0, 0), intensity=0.95))
    pl.add_light(pv.Light(position=(-380, -260, 160), focal_point=(0, 0, 0), intensity=0.35))
    pl.add_light(pv.Light(position=(0, 300, 300), focal_point=(0, 0, 0), intensity=0.2))
    if view == "front":
        pl.camera_position = [(9, -520, 30), (9, 10, -4), (0, 0, 1)]
        pl.camera.view_angle = 17.5
    else:  # hero three-quarter from shop-counter height
        pl.camera_position = [(300, -400, 205), (9, 10, -8), (0, 0, 1)]
        pl.camera.view_angle = 20.5
    try:
        pl.enable_ssao(radius=14, bias=0.4, kernel_size=128, blur=True)
        pl.enable_anti_aliasing("ssaa")
    except (RuntimeError, AttributeError) as exc:  # depends on the VTK build
        print("render effects unavailable:", exc)
    pl.screenshot(str(path))
    pl.close()
    print("wrote", path)


# %%
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    only = [a for a in sys.argv[1:] if a in LOOKS] or list(LOOKS)
    built = {}
    for look in only:
        posed = build_look(look, phase_deg=40)
        built[look] = posed
        render(look, build_look(look), OUT / f"look_{look}_front_rest.png", view="front")
        render(look, posed, OUT / f"look_{look}_hero_wave.png", view="hero")
        if "--strip" in sys.argv:
            for ph in (0, 90, 180, 270):
                render(
                    look,
                    build_look(look, phase_deg=ph),
                    OUT / f"strip_{look}_{ph:03d}.png",
                    view="front",
                    size=(1500, 640),
                )

    if "--no-show" not in sys.argv:
        from ocp_vscode import Camera, show

        shapes, names, colours = [], [], []
        for row, (look, parts) in enumerate(built.items()):
            for i, (colour, shape) in enumerate(parts):
                shapes.append(Pos(0, row * 120, 0) * shape)
                names.append(f"{look}/{colour}-{i}")
                colours.append(PALETTES[look][colour])
        try:
            show(*shapes, names=names, colors=colours, reset_camera=Camera.RESET)
            print("sent", len(shapes), "objects to the OCP viewer")
        except (OSError, RuntimeError) as exc:
            print("OCP viewer not reachable:", exc)
