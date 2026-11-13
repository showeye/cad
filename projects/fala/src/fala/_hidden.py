"""Is the mechanism hidden? What a viewer in front of the piece can see of it.

The brief asks that whatever moves the houses is invisible from the front, from three-quarter
views and from above at shop-counter height; the back and the underside may show it. Here the
mechanism is every part that is neither the base, the rear panel, a house, the handwheel nor
its knob, plus the guide blades that stand up from the base into the houses. The viewer is
far away (parallel rays), which covers a near viewer too as long as the range of directions
is wide enough. `cadkit.visibility` does the ray casting; this module only says what counts
as mechanism and where the viewer stands.
"""

import numpy as np
from cadkit.visibility import seen, surface_samples, triangles_of, view_vector

from fala import _parts as parts
from fala._layout import layout

MECHANISM = ("cam", "sled_", "pinion", "reference_axle")
AZIMUTHS = (-70, -60, -50, -40, -30, -20, -10, -5, -2, 0, 2, 5, 10, 20, 30, 40, 50, 60, 70)
ELEVATIONS = (0, 5, 10, 20, 30, 40, 50, 60)  # 0 is level with the pavement, 60 a near counter


def blades(p):
    """The guide blades above the rim as one shape, a hair inside the base's own surface."""
    L = layout(p)
    hw, skin = p.blade_width / 2, 0.03
    shape = None
    for x in L.centres:
        blade = parts.box(
            x - hw + skin,
            x + hw - skin,
            L.blade_y0 + skin,
            L.blade_y1 - skin,
            L.rim_z,
            L.land_z - skin,
        )
        shape = blade if shape is None else shape + blade
    return shape


def exposed(built: dict, p, spacing: float = 1.2, azimuths=AZIMUTHS, elevations=ELEVATIONS) -> dict:
    """Mechanism seen in the built model: {part: (points seen, points sampled, views)}.

    `built` is the result of `model.build`. An empty dict means that no sampled point of the
    mechanism is in view from any of the directions. A view is (azimuth, elevation) in
    degrees: azimuth 0 is straight in front, positive towards the handwheel end.
    """
    blockers = triangles_of(built.values(), 0.05)
    targets = {name: shape for name, shape in built.items() if name.startswith(MECHANISM)}
    targets["blades"] = blades(p)
    found = {}
    for name, shape in targets.items():
        points, normals, _ = surface_samples(shape, spacing, 0.05)
        hit, where = np.zeros(len(points), bool), []
        for azimuth in azimuths:
            for elevation in elevations:
                now = seen(points, normals, view_vector(azimuth, elevation), blockers)
                if now.any():
                    where.append((azimuth, elevation))
                    hit |= now
        if hit.any():
            found[name] = (int(hit.sum()), len(points), where)
    return found


def sweep(p, poses: int = 12, spacing: float = 1.2) -> dict:
    """`exposed` at evenly spaced crank angles through one pass of the wave: {turn: found}.

    The full check for the motion proof; about 90 seconds a pose. Import `build` late: the
    model module imports this package's siblings.
    """
    from fala.model import build

    result = {}
    for k in range(poses):
        turn = 360.0 * p.ratio * k / poses
        at = p.model_copy(update={"turn": turn})
        result[turn] = exposed(build(at), at, spacing)
    return result
