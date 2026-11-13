"""Convex polyhedra from half-spaces: faceted solids whose offsets (walls, linings) are exact.

A solid is the set {x : n_i . x <= d_i}. Moving a facet in or out is a change of d_i, so a wall
of constant thickness is the difference of two solids built from the same normals. Units: mm.
"""

from collections.abc import Sequence

import numpy as np
from build123d import Face, Shell, Solid, Vector, Wire
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, HalfspaceIntersection

Planes = tuple[np.ndarray, np.ndarray]


def unit_planes(normals: Sequence, offsets: Sequence) -> Planes:
    """Normalise plane normals to unit length, scaling the offsets with them."""
    a = np.asarray(normals, float).reshape(-1, 3)
    d = np.asarray(offsets, float).reshape(-1)
    length = np.linalg.norm(a, axis=1)
    if len(a) != len(d) or np.any(length < 1e-12):
        raise ValueError("Need one non-zero normal for every offset")
    return a / length[:, None], d / length


def inset(planes: Planes, distance: float, keep: Sequence[int] = ()) -> Planes:
    """Move every facet inwards by `distance` (outwards if negative), except those in `keep`."""
    a, d = unit_planes(*planes)
    moved = d - distance
    for i in keep:
        moved[i] = d[i]
    return a, moved


def convex_solid(points: Sequence, tolerance: float = 1e-5) -> Solid:
    """Convex hull of a point cloud as one solid; coplanar hull triangles become one face."""
    v = np.asarray(points, float)
    hull = ConvexHull(v)
    used = np.zeros(len(hull.simplices), bool)
    faces = []
    for i, eq in enumerate(hull.equations):
        if used[i]:
            continue
        same = [
            j
            for j in range(i, len(hull.simplices))
            if not used[j] and np.allclose(hull.equations[j], eq, atol=tolerance)
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


def halfspace_solid(
    normals: Sequence, offsets: Sequence, min_inradius: float = 0.2
) -> Solid | None:
    """Solid {x : n_i . x <= d_i}; None if the planes enclose no ball of `min_inradius`.

    The planes must bound a closed region. Redundant planes are allowed.
    """
    a, d = unit_planes(normals, offsets)
    # Chebyshev centre: the point deepest inside all planes, needed as an interior seed.
    result = linprog(
        [0, 0, 0, -1.0],
        A_ub=np.hstack([a, np.ones((len(a), 1))]),
        b_ub=d,
        bounds=[(None, None)] * 3 + [(0, None)],
    )
    if result.status == 3:
        raise ValueError("Half-spaces do not bound a closed region")
    if not result.success or result.x[3] < min_inradius:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        corners = HalfspaceIntersection(np.hstack([a, -d[:, None]]), result.x[:3]).intersections
    if not np.isfinite(corners).all():
        raise ValueError("Half-spaces do not bound a closed region")
    return convex_solid(corners)


def prism_planes(apothem: float, z0: float, z1: float, sides: int, chamfer: float = 0.0) -> Planes:
    """Regular prism about Z between z0 and z1, with optional 45-degree chamfers on both rims.

    `apothem` is the distance from the axis to a flat. The first two planes are top and bottom.
    """
    if apothem <= 0 or z1 <= z0 or sides < 3 or chamfer < 0:
        raise ValueError("Need a positive apothem, z1 > z0, at least 3 sides, chamfer >= 0")
    a, d = [(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)], [z1, -z0]
    c = np.sqrt(0.5)
    for k in range(sides):
        t = 2 * np.pi * (k + 0.5) / sides
        a.append((np.cos(t), np.sin(t), 0.0))
        d.append(apothem)
        if chamfer:
            for sign, z in ((1, z1), (-1, z0)):
                a.append((c * np.cos(t), c * np.sin(t), sign * c))
                d.append(c * (apothem - chamfer) + sign * c * z)
    return unit_planes(a, d)
