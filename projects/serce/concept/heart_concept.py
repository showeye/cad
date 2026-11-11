"""Serce na węgiel concept checkpoint: throwaway massing geometry.

Not product geometry. It exists to compare three looks of the coal heart and three ways of opening
it, so everything here is quick and approximate: no fits, no hinges, no mechanism parts.

The heart is a convex polyhedron per half (left, right), defined as an intersection of half-spaces:
every facet is one plane laid against a smooth heart and pushed in by a "cleave" depth. That is how
coal breaks (flat cleat faces of mixed size), and it makes offsets (wall, lining) exact.

Units: mm, degrees. Origin at the heart's (hidden) tip, z up, front is -y, the viewer's left is -x.
"""

import math

import numpy as np
from build123d import Axis, Box, Compound, Cone, Cylinder, Face, Plane, Pos, Rot, Shell, Solid
from build123d import Sphere, Vector, Wire
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, HalfspaceIntersection

# ---------------------------------------------------------------- heart proportions
LOBE_C = (-19.5, 61.0)  # centre of the left lobe circle in the front view (x, z)
LOBE_R = 21.5  # lobe radius: heart is 82 wide and 82.5 tall, cleft at z = 70
DEPTH = 23.0  # half depth: the heart is 46 deep
Z0 = 46.0  # sections at depth are the front outline scaled about (0, Z0)
SWELL = 2.4  # superellipse exponent of the depth profile (2 = lens, higher = chunkier)

WALL = 2.2  # coal wall
LINING = 0.8  # warm lining inside the coal wall
SEAM = 0.15  # half of the visible seam gap between shell parts

# the V edges are tangent to the lobes, so a straight hinge can run along them
_d = math.hypot(*LOBE_C)
_tilt = math.atan2(-LOBE_C[0], LOBE_C[1]) + math.asin(LOBE_R / _d)  # V edge angle from vertical
V_DIR = np.array([-math.sin(_tilt), 0.0, math.cos(_tilt)])  # along the left V edge, upwards
V_IN = np.array([math.cos(_tilt), 0.0, math.sin(_tilt)])  # perpendicular to it, into the heart
V_TANGENT = math.sqrt(_d**2 - LOBE_R**2)  # distance from the tip to the tangent point
Z_SEAT = 15.0  # height where the V edges meet the pedestal
E_LEFT = V_DIR * (Z_SEAT / V_DIR[2])  # point on the left V edge at Z_SEAT
HINGE_INSET = 3.2
HINGE_P = E_LEFT + HINGE_INSET * V_IN  # a point on the left hinge axis
RIDGE_Z = E_LEFT[2] + V_DIR[0] * E_LEFT[0] / V_DIR[2]  # where both pedestal roof planes meet
FLOOR_Z = 31.0  # top of the room floor

PALETTE = {
    "coal": "#17171A",
    "coal_matte": "#222226",
    "honey": "#EDAE1C",
    "lining": "#EDAE1C",  # inside of the shell; same filament as the walls unless a variant says otherwise
    "bone": "#ECE5D2",
    "tile": "#B4502A",
}


# ---------------------------------------------------------------- polyhedron helpers
def poly_solid(vertices):
    """Convex polyhedron through the given points, with coplanar triangles merged into faces."""
    v = np.asarray(vertices)
    hull = ConvexHull(v)
    used = np.zeros(len(hull.simplices), bool)
    faces = []
    for i, eq in enumerate(hull.equations):
        if used[i]:
            continue
        same = [
            j
            for j in range(i, len(hull.simplices))
            if not used[j] and np.allclose(hull.equations[j], eq, atol=1e-5)
        ]
        used[same] = True
        pts = v[sorted(set(hull.simplices[same].ravel()))]
        n, c = eq[:3], pts.mean(0)
        e1 = np.cross(n, [1.0, 0.0, 0.0])
        if np.linalg.norm(e1) < 0.1:
            e1 = np.cross(n, [0.0, 1.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        pts = pts[np.argsort(np.arctan2((pts - c) @ e2, (pts - c) @ e1))]
        faces.append(Face(Wire.make_polygon([Vector(*p) for p in pts], close=True)))
    return Solid(Shell(faces))


def halfspace_solid(normals, offsets):
    """Solid {x : n_i . x <= d_i}, or None if the planes leave (almost) nothing."""
    a = np.asarray(normals, float)
    d = np.asarray(offsets, float)
    norms = np.linalg.norm(a, axis=1)
    # Chebyshev centre: the point deepest inside all planes, needed as a seed
    res = linprog(
        [0, 0, 0, -1.0],
        A_ub=np.hstack([a, norms[:, None]]),
        b_ub=d,
        bounds=[(None, None)] * 3 + [(0, None)],
    )
    if not res.success or res.x[3] < 0.2:
        return None
    hs = HalfspaceIntersection(np.hstack([a, -d[:, None]]), res.x[:3])
    return poly_solid(hs.intersections)


def solids_of(result):
    """Flatten whatever a boolean returned into a list of real solids."""
    if result is None:
        return []
    if isinstance(result, (list, tuple)):
        return [s for r in result for s in solids_of(r)]
    return [s for s in result.solids() if s.volume > 1e-3]


def clip(solids, tool):
    return [s for body in solids for s in solids_of(body & tool)]


def cut(solids, tool):
    return [s for body in solids for s in solids_of(body - tool)]


def big_box(x=(-300, 300), y=(-300, 300), z=(-300, 300)):
    return Pos(sum(x) / 2, sum(y) / 2, sum(z) / 2) * Box(x[1] - x[0], y[1] - y[0], z[1] - z[0])


def above_plane(point, normal, offset=0.0):
    """Big block on the +normal side of a plane (moved along the normal by `offset`)."""
    plane = Plane(origin=tuple(np.asarray(point) + offset * np.asarray(normal)), z_dir=tuple(normal))
    return plane.location * Pos(0, 0, 300) * Box(600, 600, 600)


def mirror_x(solids):
    return [s.mirror(Plane.YZ) for s in solids]


# ---------------------------------------------------------------- the smooth heart
def outline_left(n_arc=48):
    """Front outline of the left half: tip, straight V edge, lobe arc, cleft. Convex."""
    tangent = V_DIR * V_TANGENT
    pts = [(V_DIR[0] * t, V_DIR[2] * t) for t in np.linspace(0, V_TANGENT, 10)]
    a0 = math.atan2(tangent[2] - LOBE_C[1], tangent[0] - LOBE_C[0]) % (2 * math.pi)
    a1 = math.acos(-LOBE_C[0] / LOBE_R)
    for a in np.linspace(a0, a1, n_arc)[1:]:
        pts.append((LOBE_C[0] + LOBE_R * math.cos(a), LOBE_C[1] + LOBE_R * math.sin(a)))
    return np.array(pts)


def smooth_cloud():
    """Points on the smooth left half-heart: the outline, shrunk towards (0, Z0) with depth."""
    outline = outline_left()
    pts = []
    for t in [0, 0.2, 0.38, 0.54, 0.68, 0.79, 0.88, 0.94, 0.98, 1.0]:
        s = (1 - t**SWELL) ** (1 / SWELL)
        for sign in (-1, 1) if t else (1,):
            y = sign * t * DEPTH
            pts += [(x * s, y, Z0 + (z - Z0) * s) for x, z in outline]
    return np.array(pts)


CLOUD = smooth_cloud()


def sphere_dirs(n, seed, jitter):
    rng = np.random.default_rng(seed)
    i = np.arange(n) + 0.5
    polar = np.arccos(1 - 2 * i / n)
    turn = math.pi * (1 + 5**0.5) * i
    d = np.c_[np.cos(turn) * np.sin(polar), np.sin(turn) * np.sin(polar), np.cos(polar)]
    d += rng.normal(0, jitter, d.shape)
    return d / np.linalg.norm(d, axis=1)[:, None]


# ---------------------------------------------------------------- facet recipes (left half)
def planes_bryla(seed):
    """Cleaved lump: a few big flat cleat faces, many smaller chips, nothing regular."""
    rng = np.random.default_rng(seed)
    big = [  # normal, cleave depth: the broad faces a lump of coal breaks along
        ((-0.20, -0.96, 0.18), 2.4),
        ((-0.34, -0.86, -0.38), 1.5),
        ((-0.10, 0.97, 0.22), 2.2),
        ((-0.42, 0.84, -0.34), 1.3),
        ((-0.86, -0.36, 0.36), 1.2),
        ((-0.80, 0.46, 0.38), 1.0),
        ((-0.22, -0.60, 0.77), 1.0),
        ((-0.30, 0.52, 0.80), 1.1),
    ]
    normals = [np.array(n) + rng.normal(0, 0.05, 3) for n, _ in big]
    depths = [c * rng.uniform(0.8, 1.2) for _, c in big]
    for n in sphere_dirs(44, seed + 1, 0.16):
        if n[0] < 0.3:
            normals.append(n)
            depths.append(rng.uniform(0.05, 1.3))
    return _finish(normals, depths)


def planes_szlif():
    """Cut like a gem: table, three rings of crown facets, girdle. Symmetric by construction."""
    normals, depths = [], []
    rings = [(0, 1, 3.4), (30, 4, 1.1), (56, 6, 0.55), (78, 8, 0.25), (90, 10, 0.1)]
    for polar, count, depth in rings:
        for face in (-1, 1):  # front and back
            if polar == 90 and face == 1:
                continue
            for k in range(count):
                az = math.radians(90 + (k + 0.5) * 180 / count)
                if polar == 0:
                    n = (0.0, face, 0.0)
                else:
                    p = math.radians(polar)
                    n = (math.sin(p) * math.cos(az), face * math.cos(p), math.sin(p) * math.sin(az))
                normals.append(np.array(n))
                depths.append(depth)
    return _finish(normals, depths)


def planes_poklad(seed):
    """Blocky cleat faces for the banded heart: fewer, steeper facets than the lump."""
    rng = np.random.default_rng(seed)
    normals, depths = [], []
    for n in sphere_dirs(30, seed, 0.12):
        if n[0] < 0.3:
            n = n * np.array([1.0, 1.0, 0.55])  # pull facets towards vertical, as cleat is
            normals.append(n / np.linalg.norm(n))
            depths.append(rng.uniform(0.1, 1.6))
    normals += [np.array([-0.15, -0.99, 0.0]), np.array([-0.1, 0.99, 0.05])]
    depths += [2.2, 2.0]
    return _finish(normals, depths)


def _finish(normals, depths):
    a = np.array([n / np.linalg.norm(n) for n in normals])
    d = (CLOUD @ a.T).max(0) - np.array(depths)
    return np.vstack([a, [1.0, 0.0, 0.0]]), np.append(d, 0.0)  # last plane is the mid-plane x = 0


def inset(planes, t):
    """The same polyhedron with every facet moved in by t (the mid-plane stays)."""
    a, d = planes
    return a, np.append(d[:-1] - t, d[-1])


BANDS = [0, 9, 15, 23, 29, 38, 44, 53, 58, 66, 71, 78, 84]  # bedding planes of the banded look
BAND_STEP = 0.955  # dull bands sit this much further in than bright ones


def banded(planes):
    """Slice a polyhedron into horizontal beds; every second bed is slightly smaller."""
    a, d = planes
    out = []
    for k, (z0, z1) in enumerate(zip(BANDS, BANDS[1:])):
        f = 1.0 if k % 2 == 0 else BAND_STEP
        ak = np.vstack([a * [1 / f, 1 / f, 1.0], [0, 0, 1.0], [0, 0, -1.0]])
        dk = np.concatenate([d, [z1, -z0]])
        solid = halfspace_solid(ak, dk)
        if solid is not None:
            out.append(("coal" if k % 2 == 0 else "coal_matte", solid))
    return out


def heart(look):
    """Outer skin, the cavity inside the coal wall, and the cavity inside the lining.

    Returns {"skin": [(material, solid)], "under": [solid], "cavity": [solid]}: both halves.
    """
    if look == "szlif":
        left = right = planes_szlif()
    elif look == "poklad":
        left, right = planes_poklad(11), planes_poklad(29)
    else:
        left, right = planes_bryla(7), planes_bryla(23)
    wall = WALL + (1.6 if look == "poklad" else 0.0)
    # the hollow is the same on both sides and lies inside both halves, so the lump can be
    # lopsided outside without ever opening a gap at the mid-plane
    both = (np.vstack([left[0][:-1], right[0]]), np.concatenate([left[1][:-1], right[1]]))
    out = {"skin": [], "under": [], "cavity": []}
    for planes, flip in ((left, False), (right, True)):
        if look == "poklad":
            skin = banded(planes)
        else:
            skin = [("coal", halfspace_solid(*planes))]
        under = [halfspace_solid(*inset(both, wall))]
        cavity = [halfspace_solid(*inset(both, wall + LINING))]
        if flip:
            skin = [(m, s.mirror(Plane.YZ)) for m, s in skin]
            under, cavity = mirror_x(under), mirror_x(cavity)
        out["skin"] += skin
        out["under"] += under
        out["cavity"] += cavity
    return out


# ---------------------------------------------------------------- the room
def room(cavity, wall_y=13.0, lamp=True):
    """A Silesian kitchen as flat-colour massing, clipped to the heart's cavity.

    Stove (kachlok) with coal scuttle on the left, dresser (byfyj) on the right, round table with
    a crocheted cloth, window with geraniums, embroidered hanging (makatka), pendant lamp.
    """
    cav = Compound(cavity)
    p = {"honey": [], "bone": [], "tile": [], "coal_matte": []}
    shift = Pos(0, wall_y - 13.0, 0)  # the scene is drawn for a wall at y = 13 and moved as one
    wall_y = 13.0

    def add(colour, solid):
        p[colour] += solids_of((shift * solid) & cav)

    def box(x0, x1, y0, y1, z0, z1):
        return big_box((x0, x1), (y0, y1), (z0, z1))

    f = FLOOR_Z
    add("honey", box(-60, 60, wall_y, wall_y + 1.5, f - 1.5, 90))  # back wall
    add("tile", box(-60, 60, -40, wall_y, f - 1.5, f))  # floor
    # kachlok: tiled stove with iron top, upstand, pipe, fire door and a pot
    add("tile", box(-17.5, -6.5, 4.5, wall_y, f, f + 12.5))
    add("coal_matte", box(-18.2, -5.8, 3.8, wall_y, f + 12.5, f + 13.6))
    add("tile", box(-17.5, -6.5, 10.2, wall_y, f + 13.6, f + 21))
    for z in (f + 4.2, f + 8.4):  # tile courses as grooves
        add("coal_matte", box(-17.6, -6.4, 4.2, 4.6, z, z + 0.5))
    add("coal_matte", box(-15.5, -10.5, 4.0, 4.6, f + 1.6, f + 6.0))
    add("honey", box(-14.6, -11.4, 3.8, 4.2, f + 2.6, f + 3.7))  # the fire shows: still on coal
    add("coal_matte", Pos(-9.2, 11.6, f + 27) * Cylinder(1.6, 12.5))
    add("bone", Pos(-13.2, 8.2, f + 15.4) * Cylinder(2.7, 3.6))
    add("coal_matte", Pos(-13.2, 8.2, f + 17.5) * Cylinder(3.0, 0.7))
    # kołkastla: the coal scuttle in front of the stove, heaped
    add("coal_matte", box(-15.8, -10.6, -2.6, 2.0, f, f + 3.4))
    for dx, dy, r in ((-14.4, -1.2, 1.5), (-12.2, 0.4, 1.6), (-13.3, -0.6, 1.9)):
        add("coal_matte", Pos(dx, dy, f + 3.6) * Sphere(r))
    # byfyj: white dresser, glazed upper part on posts
    add("bone", box(6.0, 18.5, 6.0, wall_y, f, f + 13))
    add("bone", box(5.4, 19.1, 5.4, wall_y, f + 13, f + 14))
    add("bone", box(6.6, 18.0, 9.0, wall_y, f + 16.4, f + 30))
    add("bone", box(6.0, 18.6, 8.4, wall_y, f + 30, f + 31.4))
    for x in (7.2, 17.4):
        add("bone", box(x - 0.6, x + 0.6, 9.0, 10.2, f + 14, f + 16.4))
    for x0, x1 in ((7.5, 11.8), (12.8, 17.1)):
        add("honey", box(x0, x1, 8.7, 9.3, f + 18.2, f + 28.4))  # lit glass
        add("coal_matte", box(x0 + 1.4, x1 - 1.4, 5.7, 6.3, f + 2.0, f + 11.2))  # door panels
    # table with a crocheted cloth and a cake, and a stool (ryczka)
    add("bone", Pos(0.5, -4.5, f + 6.6) * Cone(8.6, 7.4, 4.2))
    add("bone", Pos(0.5, -4.5, f + 9.0) * Cylinder(7.4, 0.8))
    add("coal_matte", Pos(0.5, -4.5, f + 2.3) * Cylinder(1.3, 4.6))
    add("tile", Pos(0.5, -4.5, f + 10.2) * Cylinder(3.0, 1.6))
    add("bone", box(9.6, 13.6, -9.5, -5.5, f + 3.4, f + 4.4))
    for x, y in ((10.1, -9.0), (13.1, -9.0), (10.1, -6.0), (13.1, -6.0)):
        add("bone", box(x - 0.5, x + 0.5, y - 0.5, y + 0.5, f, f + 3.4))
    # window in the left lobe: dark panes, lace band, geraniums on the sill
    add("bone", box(-30.5, -15.5, wall_y - 0.9, wall_y, f + 21.5, f + 37.5))
    for x0, x1 in ((-29.3, -23.6), (-22.4, -16.7)):
        for z0, z1 in ((f + 22.7, f + 28.6), (f + 29.8, f + 33.0)):
            add("coal_matte", box(x0, x1, wall_y - 1.2, wall_y - 0.6, z0, z1))
    add("bone", box(-31.2, -14.8, wall_y - 2.6, wall_y, f + 20.3, f + 21.5))
    for x in (-27.5, -23.0, -18.5):
        add("tile", Pos(x, wall_y - 1.5, f + 23.4) * Sphere(1.5))
    # makatka over the table, a picture and a clock in the right lobe
    add("bone", box(-6.5, 5.5, wall_y - 0.6, wall_y, f + 17, f + 25))
    add("tile", box(-5.3, 4.3, wall_y - 0.9, wall_y - 0.5, f + 18.2, f + 19.0))
    add("tile", box(-5.3, 4.3, wall_y - 0.9, wall_y - 0.5, f + 23.0, f + 23.8))
    add("coal_matte", Pos(26.5, wall_y - 0.4, f + 31.5) * Rot(90, 0, 0) * Cylinder(4.2, 0.9))
    add("bone", Pos(26.5, wall_y - 0.8, f + 31.5) * Rot(90, 0, 0) * Cylinder(3.2, 0.9))
    add("coal_matte", box(23.0, 30.0, wall_y - 0.9, wall_y, f + 20.0, f + 25.0))
    add("bone", box(23.9, 29.1, wall_y - 1.2, wall_y - 0.6, f + 20.9, f + 24.1))
    if lamp:  # pendant lamp from the cleft
        add("coal_matte", Pos(0, 6.5, f + 31.8) * Cylinder(0.5, 7.5))
        add("bone", Pos(0, 6.5, f + 26.6) * Cone(4.8, 1.2, 3.4))
        add("honey", Pos(0, 6.5, f + 24.6) * Sphere(1.9))
    return [(c, s) for c, solids in p.items() for s in solids]


# ---------------------------------------------------------------- base
def prism(radius, z0, z1, sides=20, chamfer=1.3):
    """Faceted ring: a polygonal prism with chamfered rims, like the girdle of a cut stone."""
    a, d = [(0, 0, 1.0), (0, 0, -1.0)], [z1, -z0]
    c = math.sqrt(0.5)
    for k in range(sides):
        t = 2 * math.pi * (k + 0.5) / sides
        a += [(math.cos(t), math.sin(t), 0.0)]
        d += [radius]
        for sign, z in ((1, z1), (-1, z0)):
            a += [(c * math.cos(t), c * math.sin(t), sign * c)]
            d += [c * (radius - chamfer) + sign * c * z]
    return halfspace_solid(a, d)


RING_R, RING_TOP, RING_H, FOOT_H = 38.0, -0.9, 12.5, 3.6


def base_common():
    ring = prism(RING_R, RING_TOP - RING_H, RING_TOP)
    foot = Pos(0, 0, RING_TOP - RING_H - 0.4 - FOOT_H / 2) * Cylinder(RING_R - 1.6, FOOT_H)
    return [("coal", ring), ("coal_matte", foot)]


def pedestal(roof=True):
    """Fixed coal bed under the heart. With `roof`, its two main facets are square to the hinges,
    so the opening shells sweep just above them and never close a gap on a finger."""
    a, d = [(0, 0, -1.0)], [-(RING_TOP + 0.4)]
    for k in range(20):
        t = 2 * math.pi * (k + 0.5) / 20
        a += [(math.cos(t), math.sin(t), 0.0)]
        d += [RING_R - 0.6]
    if roof:
        for sx in (1, -1):
            n = V_DIR * [sx, 1, 1]
            a += [tuple(n)]
            d += [float(n @ (E_LEFT * [sx, 1, 1]))]
        slope = math.radians(50)
        for sy in (1, -1):
            n = np.array([0.0, sy * math.sin(slope), math.cos(slope)])
            a += [tuple(n)]
            d += [float(n @ np.array([0.0, sy * 12.5, RIDGE_Z]))]
    else:
        slope = math.radians(42)
        for k in range(10):
            t = 2 * math.pi * (k + 0.5) / 10
            n = np.array([math.sin(slope) * math.cos(t), math.sin(slope) * math.sin(t), math.cos(slope)])
            a += [tuple(n)]
            d += [float(n @ np.array([16 * math.cos(t), 13 * math.sin(t), Z_SEAT]))]
        a += [(0, 0, 1.0)]
        d += [Z_SEAT]
    return halfspace_solid(a, d)


# ---------------------------------------------------------------- opening A: wings
WING_MAX = 125.0  # full swing of each front shell about its V edge


def wing_angle(turn):
    """Shell angle for a base turn of 0..180 degrees: an eccentric gives a slow start and end."""
    half = math.radians(WING_MAX / 2)
    return math.degrees(half - math.asin(math.sin(half) * math.cos(math.radians(turn))))


def wings(look, turn=0.0):
    """Two front shells hinged along the V edges; the back half and the coal bed are fixed."""
    h = heart(look)
    phi = wing_angle(turn)
    parts = base_common() + [("coal", pedestal())]
    lining = [s for u, c in zip(h["under"], h["cavity"]) for s in solids_of(u - c)]
    front = big_box(y=(-300, -SEAM))
    back = big_box(y=(SEAM, 300))
    for sx in (-1, 1):
        mirror = np.array([-sx, 1, 1])  # constants describe the left side
        side = big_box(x=(-300, -SEAM)) if sx < 0 else big_box(x=(SEAM, 300))
        up = above_plane(E_LEFT * mirror, V_DIR * mirror, 0.4)
        axis = Axis(tuple(HINGE_P * mirror), tuple(V_DIR * mirror))
        barrel_at = Plane(origin=tuple(HINGE_P * mirror), z_dir=tuple(V_DIR * mirror)).location
        barrel = barrel_at * Pos(0, 0, 30) * Cylinder(HINGE_INSET + 0.25, 64)
        cove = barrel_at * Pos(0, 0, 30) * Cylinder(HINGE_INSET + 0.65, 66)
        under = Compound(h["under"])
        for material, solids in [(m, [s]) for m, s in h["skin"]] + [("lining", lining)]:
            body = clip(clip(solids, side), up)
            if material != "lining":
                body = cut(body, under)
            door = clip(body, front) + clip(clip(body, back), barrel)
            fixed = cut(clip(body, back), cove)
            sense = sx  # both shells swing forwards and outwards
            parts += [(material, s.rotate(axis, sense * phi)) for s in door]
            parts += [(material, s) for s in fixed]
    # the room stands on a fixed coal block that fills the heart below the floor
    cellar = big_box(z=(RIDGE_Z - 6, FLOOR_Z - 1.5))
    for sx in (-1, 1):
        up = above_plane(E_LEFT * [-sx, 1, 1], V_DIR * [-sx, 1, 1], -0.2)
        side = big_box(x=(-300, 0)) if sx < 0 else big_box(x=(0, 300))
        parts += [("coal_matte", s) for s in clip(clip(clip(h["cavity"], cellar), up), side)]
    return parts + room(h["cavity"])


# ---------------------------------------------------------------- opening B: seam lift
LIFT_MAX, LIFT_SPLIT = 30.0, FLOOR_Z + 1.0


def lift(look, travel=0.0):
    """The heart parts along one bedding plane and the upper part rises on a hidden slab."""
    h = heart(look)
    parts = base_common() + [("coal", pedestal(roof=False))]
    under, cavity = Compound(h["under"]), Compound(h["cavity"])
    top = big_box(z=(LIFT_SPLIT + SEAM, 300))
    low = big_box(z=(-300, LIFT_SPLIT - SEAM))
    up = Pos(0, 0, travel)
    for material, solid in h["skin"]:
        parts += [(material, up * s) for s in cut(clip([solid], top), under)]
        parts += [(material, s) for s in clip([solid], low)]
    lining = [s for u, c in zip(h["under"], h["cavity"]) for s in solids_of(u - c)]
    parts += [("lining", up * s) for s in clip(lining, top)]
    # the room is a prism that the rising shell can pass over; a slab carries the shell
    stage = big_box((-20.5, 20.5), (-12, 10.5), (FLOOR_Z, FLOOR_Z + 30))
    scale = 0.74
    for material, solid in room(h["cavity"], wall_y=10.5, lamp=False):
        small = Pos(0, 3.0, FLOOR_Z * (1 - scale) + 0.3) * solid.scale(scale)
        parts += [(material, s) for s in clip(solids_of(small & stage), cavity)]
    floor = big_box((-20.5, 20.5), (-12, 10.5), (LIFT_SPLIT - 0.8, LIFT_SPLIT + 0.2))
    parts += [("tile", s) for s in solids_of(floor & cavity)]
    parts.append(("coal_matte", up * big_box((-19, 19), (11.4, 13.4), (LIFT_SPLIT - LIFT_MAX, LIFT_SPLIT + 3))))
    parts.append(("honey", up * big_box((-19, 19), (10.6, 11.4), (LIFT_SPLIT - LIFT_MAX, LIFT_SPLIT))))
    return parts


# ---------------------------------------------------------------- opening C: bloom
BLOOM_MAX, BLOOM_RISE, BLOOM_SPLIT = 68.0, 12.0, 19.5


def bloom(look, amount=0.0):
    """Four shards tip outwards on hinges at the coal bed while the room rises in the middle."""
    h = heart(look)
    parts = base_common() + [("coal", pedestal(roof=False))]
    under = Compound(h["under"])
    top = big_box(z=(BLOOM_SPLIT + SEAM, 300))
    lining = [s for u, c in zip(h["under"], h["cavity"]) for s in solids_of(u - c)]
    skins = [(m, cut(clip([s], top), under)) for m, s in h["skin"]] + [("lining", clip(lining, top))]
    low = big_box(z=(-300, BLOOM_SPLIT - SEAM))
    parts += [(m, s) for m, solid in h["skin"] for s in clip([solid], low)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            quarter = big_box(
                x=(-300, -SEAM) if sx < 0 else (SEAM, 300),
                y=(-300, -SEAM) if sy < 0 else (SEAM, 300),
            )
            out = np.array([sx * 0.78, sy * 0.62, 0.0])
            axis = Axis((sx * 9.0, sy * 7.0, BLOOM_SPLIT), tuple(np.cross([0, 0, 1.0], out)))
            for material, solids in skins:
                for s in clip(solids, quarter):
                    parts.append((material, s.rotate(axis, BLOOM_MAX * amount)))
    rise = Pos(0, 0, BLOOM_RISE * amount)
    parts += [(m, rise * s) for m, s in room(h["cavity"], wall_y=9.0)]
    parts.append(("coal_matte", rise * Pos(0, 2, FLOOR_Z - 10) * Cylinder(6.5, 17)))
    return parts
