"""Read-only diagnostic of the Carnall assembly through one full revolution."""

from cadkit.validate import overlaps
from carnall.model import Params, _moving_neutral, build

for angle in range(0, 360, 15):
    params = Params(angle=angle)
    parts = {n: s for n, s in build(params).items() if n != "reference_rope_witness"}
    moving = set(_moving_neutral(params.crank_radius, params.rod_length, params.fit, 0))
    collisions = overlaps(parts, moving)
    print(angle, collisions, flush=True)
