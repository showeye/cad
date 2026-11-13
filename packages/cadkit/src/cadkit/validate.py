"""BRep, mesh and per-part build-volume quality gates plus reproducible metrics."""

from itertools import combinations

import numpy as np
import trimesh
from build123d import Compound, Shape
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.collections import List_TopoDS_Shape

from cadkit.process import Process


def parts_of(result: Shape | dict[str, Shape]) -> dict[str, Shape]:
    """Normalise a single part or a named assembly."""
    return result if isinstance(result, dict) else {"body": result}


def mesh_of(shape: Shape, tolerance: float = 0.04) -> trimesh.Trimesh:
    """Tessellate and weld coincident seam vertices to assess watertightness."""
    vertices, triangles = shape.tessellate(tolerance, 0.15)
    mesh = trimesh.Trimesh(
        vertices=np.array([tuple(v) for v in vertices]), faces=np.array(triangles), process=True
    )
    # OCC includes zero-area triangles at spherical poles. Remove only those triangles;
    # do not fill holes or otherwise repair geometry before assessing the quality gate.
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.remove_unreferenced_vertices()
    return mesh


def metrics(shape: Shape) -> dict:
    """Geometry snapshot in mm, mm² and mm³, rounded below manufacturing precision."""
    bounds = shape.bounding_box()
    return {
        "volume": round(shape.volume, 4),
        "area": round(shape.area, 4),
        "bbox": [round(v, 4) for v in bounds.size],
        "min": [round(v, 4) for v in bounds.min],
        "max": [round(v, 4) for v in bounds.max],
        "solids": len(shape.solids()),
        "faces": len(shape.faces()),
    }


def validate(result: Shape | dict[str, Shape], process: Process, mesh: bool = True) -> list[str]:
    """Return errors; each named assembly component must be one positive watertight solid."""
    errors = []
    parts = parts_of(result)
    if not parts:
        return ["empty model"]
    for name, shape in parts.items():
        if not shape.is_valid or len(shape.solids()) != 1 or shape.volume <= 0:
            errors.append(f"{name}: invalid BRep, non-positive volume or not one solid")
        if any(
            v > limit + 1e-5 for v, limit in zip(shape.bounding_box().size, process.build_volume)
        ):
            errors.append(f"{name}: exceeds build volume in assembled orientation")
        if mesh:
            surface = mesh_of(shape, process.mesh_tolerance)
            if not surface.is_watertight or not surface.is_volume:
                errors.append(f"{name}: mesh is not a closed oriented volume")
    return errors


def overlaps(parts: dict[str, Shape], moving: set[str] | None = None, tolerance=1e-5):
    """Exact positive-volume intersections after a bounding-box broad phase.

    If moving is supplied, skip pairs in which neither part moves. Face contact is allowed;
    no geometric repair or automatic exclusion of joints is performed. The OCCT
    operation is explicitly non-destructive: contact checks must not increase
    input edge tolerances and thereby change subsequent STEP exports.
    """
    bounds = {name: shape.bounding_box() for name, shape in parts.items()}
    collisions = []
    for a, b in combinations(parts, 2):
        if moving is not None and a not in moving and b not in moving:
            continue
        aa, bb = bounds[a], bounds[b]
        if any(min(u, v) - max(p, q) < 1e-6 for p, u, q, v in zip(aa.min, aa.max, bb.min, bb.max)):
            continue
        arguments, tools = List_TopoDS_Shape(), List_TopoDS_Shape()
        arguments.Append(parts[a].wrapped)
        tools.Append(parts[b].wrapped)
        operation = BRepAlgoAPI_Common()
        operation.SetArguments(arguments)
        operation.SetTools(tools)
        operation.SetNonDestructive(True)
        operation.Build()
        if not operation.IsDone():
            raise RuntimeError(f"Intersection failed for {a} / {b}")
        # Face/edge contact is allowed; only solid intersections have volume.
        volume = sum(s.volume for s in Compound(operation.Shape()).solids())
        if volume > tolerance:
            collisions.append((a, b, round(volume, 6)))
    return collisions
