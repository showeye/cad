"""Small coupons cut from the real motion geometry to qualify the U1's fits.

The layout places the cam and fork on their flat undersides, and the hinge/tail
segment on its axial cut face. Source dimensions remain those of the assembly.
"""

from build123d import Box, Color, Plane, Pos
from cadkit.model import Model

from serce.model import _V, Params, _geometry, _point, process, version

variants = {f"fit_{int(fit * 100):03}": Params(fit=fit) for fit in (0.3, 0.4, 0.6)}


def build(params: Params):
    """Actual cam-track, slotted-fork and hinge/tail sections, laid out in mm."""
    parts = _geometry(params)
    cam = parts["cam_ring"] & (Pos(0, 10, -9.6) * Box(16, 14, 10))
    fork = parts["slider"] & (Pos(-14, 0, 7) * Box(13, 10, 18))
    cut_plane = Plane(origin=_point(5), z_dir=_V)
    tail = parts["wing_left"] & (cut_plane.location * Box(80, 80, 16))
    # Local Z is the hinge direction, so this turns the cut face onto the bed.
    tail = cut_plane.location.inverse() * tail
    out = {}
    x = 0
    for name, shape in (("cam_track", cam), ("fork", fork), ("hinge_tail", tail)):
        bounds = shape.bounding_box()
        shape = Pos(x - bounds.min.X, -bounds.min.Y, -bounds.min.Z) * shape
        shape.label, shape.color = name, Color("#25252A")
        out[name] = shape
        x += bounds.size.X + 8
    return out


model = Model("serce-coupons", version, variants, process, build)
