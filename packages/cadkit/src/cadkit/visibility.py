"""What a distant viewer sees of a part: sampled surface points and exact parallel-ray occlusion.

Used to prove that something is in view (a room behind opened doors) or hidden (a mechanism).
A view is a unit vector from the model towards the viewer. Units: mm.
"""

import math
from collections.abc import Iterable, Sequence

import numpy as np
from build123d import Shape

from cadkit.validate import mesh_of


def view_vector(azimuth: float, elevation: float) -> np.ndarray:
    """Direction towards a viewer: azimuth 0 is the front (-Y), positive to the viewer's right
    (+X); elevation is up from the horizon. Degrees."""
    a, e = math.radians(azimuth), math.radians(elevation)
    return np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])


def sphere_views(count: int, min_elevation: float = -90.0) -> list[np.ndarray]:
    """About `count` directions spread evenly over the sphere, at or above `min_elevation`."""
    views = []
    low = math.sin(math.radians(min_elevation))
    for i in range(count):
        z = 1 - (2 * i + 1) / count
        if z < low:
            continue
        turn = math.pi * (1 + 5**0.5) * i
        r = math.sqrt(max(0.0, 1 - z * z))
        views.append(np.array([r * math.cos(turn), r * math.sin(turn), z]))
    return views


def surface_samples(shape: Shape, spacing: float = 1.0, tolerance: float = 0.05):
    """Points on the surface of `shape`, about one per spacing² of area.

    Returns points, outward normals and the area each point stands for. Deterministic: every
    triangle of the tessellation is sampled on a fixed barycentric lattice.
    """
    mesh = mesh_of(shape, tolerance)
    points, normals, weights = [], [], []
    for corners, normal, area in zip(mesh.triangles, mesh.face_normals, mesh.area_faces):
        n = max(1, round(math.sqrt(2 * area) / spacing))
        count = n * (n + 1) // 2
        for i in range(n):
            for j in range(n - i):
                a, b = (i + 1 / 3) / n, (j + 1 / 3) / n
                points.append(
                    corners[0] + a * (corners[1] - corners[0]) + b * (corners[2] - corners[0])
                )
        normals += [normal] * count
        weights += [area / count] * count
    return np.array(points).reshape(-1, 3), np.array(normals).reshape(-1, 3), np.array(weights)


def triangles_of(shapes: Iterable[Shape], tolerance: float = 0.05) -> np.ndarray:
    """All triangles of the given shapes as an (n, 3, 3) array."""
    parts = [mesh_of(shape, tolerance).triangles for shape in shapes]
    return np.concatenate(parts) if parts else np.zeros((0, 3, 3))


def occluded(points: np.ndarray, view: Sequence[float], triangles: np.ndarray, clearance=0.02):
    """For each point: does any triangle lie between it and a distant viewer along `view`?

    Triangles nearer than `clearance` in front of the point are ignored, so a point is never
    hidden by the surface it lies on. Exact for the given triangles; a uniform grid in the
    viewer's plane keeps the number of point-triangle tests small.
    """
    view = np.asarray(view, float) / np.linalg.norm(view)
    helper = np.array([1.0, 0.0, 0.0]) if abs(view[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(view, helper)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(view, e1)
    basis = np.array([e1, e2, view])
    p = np.asarray(points, float).reshape(-1, 3) @ basis.T
    hidden = np.zeros(len(p), bool)
    if not len(p) or not len(triangles):
        return hidden
    t = np.asarray(triangles, float) @ basis.T  # (m, 3, 3): corners in (u, v, depth)
    lo, hi = p[:, :2].min(0), p[:, :2].max(0)
    # drop triangles that are edge-on, behind every point, or outside the points' footprint
    area = (t[:, 1, 0] - t[:, 0, 0]) * (t[:, 2, 1] - t[:, 0, 1]) - (t[:, 1, 1] - t[:, 0, 1]) * (
        t[:, 2, 0] - t[:, 0, 0]
    )
    keep = np.abs(area) > 1e-9
    keep &= t[:, :, 2].max(1) > p[:, 2].min() + clearance
    for axis in (0, 1):
        keep &= (t[:, :, axis].max(1) >= lo[axis]) & (t[:, :, axis].min(1) <= hi[axis])
    t, area = t[keep], area[keep]
    if not len(t):
        return hidden
    # grid over the points' footprint; every triangle is listed in the cells its box touches
    cell = max(float((hi - lo).max()) / 256, 0.25)
    shape = np.floor((hi - lo) / cell).astype(int) + 1
    first = np.clip(np.floor((t[:, :, :2].min(1) - lo) / cell).astype(int), 0, shape - 1)
    last = np.clip(np.floor((t[:, :, :2].max(1) - lo) / cell).astype(int), 0, shape - 1)
    width = last[:, 1] - first[:, 1] + 1
    count = (last[:, 0] - first[:, 0] + 1) * width
    owner = np.repeat(np.arange(len(t)), count)
    local = np.arange(count.sum()) - np.repeat(np.cumsum(count) - count, count)
    cells = (
        (first[owner, 0] + local // width[owner]) * shape[1]
        + first[owner, 1]
        + local % width[owner]
    )
    order = np.argsort(cells, kind="stable")
    cells, owner = cells[order], owner[order]
    every = np.arange(shape[0] * shape[1])
    start = np.searchsorted(cells, every)
    stop = np.searchsorted(cells, every, side="right")
    home = np.floor((p[:, :2] - lo) / cell).astype(int)
    home = np.clip(home, 0, shape - 1)
    home = home[:, 0] * shape[1] + home[:, 1]
    per_point = stop[home] - start[home]
    limit = 4_000_000  # point-triangle pairs per pass
    begin = 0
    while begin < len(p):
        end = begin + max(1, int(np.searchsorted(np.cumsum(per_point[begin:]), limit)))
        n = per_point[begin:end]
        who = np.repeat(np.arange(begin, end), n)
        k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
        tri = owner[start[home[who]] + k]
        q, c, d = p[who], t[tri], area[tri]
        du = [c[:, i, 0] - q[:, 0] for i in range(3)]
        dv = [c[:, i, 1] - q[:, 1] for i in range(3)]
        w0 = (du[1] * dv[2] - dv[1] * du[2]) / d
        w1 = (du[2] * dv[0] - dv[2] * du[0]) / d
        w2 = 1.0 - w0 - w1
        depth = w0 * c[:, 0, 2] + w1 * c[:, 1, 2] + w2 * c[:, 2, 2]
        hit = (w0 >= 0) & (w1 >= 0) & (w2 >= 0) & (depth > q[:, 2] + clearance)
        hidden[who[hit]] = True
        begin = end
    return hidden


def seen(points: np.ndarray, normals: np.ndarray, view, triangles: np.ndarray) -> np.ndarray:
    """For each surface point: does it face the viewer with nothing in the way?"""
    view = np.asarray(view, float) / np.linalg.norm(view)
    facing = np.asarray(normals) @ view > 1e-6
    result = np.zeros(len(points), bool)
    if facing.any():
        result[facing] = ~occluded(np.asarray(points)[facing], view, triangles)
    return result


def seen_points(
    target: Iterable[Shape],
    blockers: Iterable[Shape],
    views: Iterable,
    spacing: float = 1.0,
    tolerance: float = 0.05,
) -> np.ndarray:
    """Sample points of the target that at least one of the viewers sees: an (n, 3) array.

    Empty when the target is hidden from every view. The target also hides itself.
    """
    target = list(target)
    samples = [surface_samples(shape, spacing, tolerance) for shape in target]
    points = np.concatenate([s[0] for s in samples])
    normals = np.concatenate([s[1] for s in samples])
    triangles = triangles_of([*target, *blockers], tolerance)
    found = np.zeros(len(points), bool)
    for view in views:
        found |= seen(points, normals, view, triangles)
    return points[found]


def visible_share(
    target: Iterable[Shape],
    blockers: Iterable[Shape],
    view,
    spacing: float = 1.0,
    baseline: Iterable[Shape] | None = None,
    tolerance: float = 0.05,
) -> float:
    """Share of the target's surface area that a viewer along `view` sees past the blockers.

    The share is taken of the area that is seen when only the target itself and `baseline`
    stand in the way, so 1.0 means that the blockers hide nothing more. Returns 0.0 if no point
    of the target faces the viewer.
    """
    target = list(target)
    samples = [surface_samples(shape, spacing, tolerance) for shape in target]
    points = np.concatenate([s[0] for s in samples])
    normals = np.concatenate([s[1] for s in samples])
    weights = np.concatenate([s[2] for s in samples])
    own = triangles_of([*target, *(baseline or [])], tolerance)
    open_view = seen(points, normals, view, own)
    if not open_view.any():
        return 0.0
    everything = np.concatenate([own, triangles_of(blockers, tolerance)])
    still = seen(points[open_view], normals[open_view], view, everything)
    return float(weights[open_view][still].sum() / weights[open_view].sum())
