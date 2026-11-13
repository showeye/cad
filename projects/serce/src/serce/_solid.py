"""Small boolean helpers that keep every part one clean solid. Units: mm."""

from build123d import Box, Color, Cylinder, Plane, Pos, Shape, Solid

_SLIVER = 1e-3  # mm³: boolean debris below this is dropped


def solids_of(shape) -> list[Solid]:
    """Flatten whatever a boolean returned into its real solids."""
    if shape is None:
        return []
    if isinstance(shape, (list, tuple)):
        return [s for item in shape for s in solids_of(item)]
    return [s for s in shape.solids() if s.volume > _SLIVER]


def one(shape, what: str = "part") -> Solid:
    """The single solid of a boolean result; anything else is a modelling error."""
    found = solids_of(shape)
    if len(found) != 1:
        volumes = sorted((round(s.volume, 3) for s in found), reverse=True)
        raise ValueError(f"{what}: expected one solid, got {len(found)} with volumes {volumes[:6]}")
    return found[0]


def fuse(*shapes, what: str = "part") -> Solid:
    """Union of solids that touch or overlap, as one solid."""
    items = [s for shape in shapes for s in solids_of(shape)]
    if not items:
        raise ValueError(f"{what}: nothing to fuse")
    result = items[0]
    for item in items[1:]:
        result = result + item
    return one(result, what)


def cut(shape, *tools, what: str = "part") -> Solid:
    """Difference as one solid. Tools may be None (skipped)."""
    result = shape
    for tool in tools:
        if tool is not None:
            result = result - tool
    return one(result, what)


def common(shape, tool, what: str = "part") -> Solid:
    """Intersection as one solid."""
    return one(shape & tool, what)


def pieces(shape, tool) -> list[Solid]:
    """Intersection as a list of solids (possibly empty)."""
    return solids_of(shape & tool)


def block(x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]) -> Shape:
    """Axis-aligned box between the given limits."""
    return Pos(sum(x) / 2, sum(y) / 2, sum(z) / 2) * Box(x[1] - x[0], y[1] - y[0], z[1] - z[0])


def rod(frame: Plane, radius: float, z0: float, z1: float, x: float = 0.0, y: float = 0.0) -> Shape:
    """Cylinder along the local Z of `frame`, from z0 to z1, centred at local (x, y)."""
    return frame.location * Pos(x, y, (z0 + z1) / 2) * Cylinder(radius, z1 - z0)


def slab(frame: Plane, x: tuple[float, float], y: tuple[float, float], z: tuple[float, float]):
    """Box in the local coordinates of `frame`."""
    return frame.location * block(x, y, z)


def named(shape: Shape, name: str, colour: str) -> Shape:
    """Label and colour a finished part."""
    shape.label, shape.color = name, Color(colour)
    return shape
