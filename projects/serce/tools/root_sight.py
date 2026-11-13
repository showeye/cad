"""Serce na węgiel, motion proof: dense rays down both hinge roots.

The test suite looks at the drive from 47 directions all round. This tool looks where the one
way into the coal bed is: along each hinge, down the running clearance round the collar of a
wing's root. It casts every direction within 60 degrees of each hinge axis, 4 degrees apart,
at sample points 0.8 mm apart on everything under the bed's roof near that root, and reports
the points that a viewer would see. Run from the repository root (about ten minutes a pose):

    uv run python projects/serce/tools/root_sight.py              # wings open and half open
    uv run python projects/serce/tools/root_sight.py 180 0.6 3    # pose, spacing, angular step

It exits with status 1 if anything is seen.
"""

import math
import sys
import time

import numpy as np
from cadkit.visibility import seen, surface_samples, triangles_of
from serce import _heart as heart
from serce.model import Params, build

P = Params()
HINGE = heart.hinge(P)
# what must stay hidden: the printed mechanism and the bought hardware inside base and bed
DRIVE = ("slider", "pusher", "chassis", "cam_disc", "reference_spring", "reference_follower")
DRIVE += ("reference_hinge_pin", "reference_cam_magnet", "reference_ring_magnet")
DRIVE += ("reference_tie_nut", "reference_leg", "reference_back_screw", "reference_back_insert")
DRIVE += ("reference_ballast",)
REACH = 26.0  # sample points this near to the root, mm
CONE = 60.0  # viewing directions this far from the hinge axis, degrees
TOLERANCE = 0.05  # of the tessellation, mm


def cone_views(axis, across, back, step: float):
    """Unit vectors within CONE of `axis`, about `step` degrees apart."""
    for polar in np.arange(0.0, CONE + step / 2, step):
        count = max(1, round(360 * math.sin(math.radians(polar)) / step))
        for k in range(count):
            turn = 2 * math.pi * k / count
            tilt = math.radians(polar)
            yield math.cos(tilt) * axis + math.sin(tilt) * (
                math.cos(turn) * across + math.sin(turn) * back
            )


def root_sight(turn: float, spacing: float = 0.8, step: float = 4.0) -> int:
    """Number of sample points under the bed that are seen past either root at `turn`."""
    parts = build(Params(turn=turn))
    every = triangles_of(parts.values(), TOLERANCE)
    total = 0
    for name, side in heart.SIDES.items():
        origin = heart.mirrored(HINGE.origin, side)
        axis = heart.mirrored(heart.V_DIR, side)
        points, normals, owners = [], [], []
        for part, shape in parts.items():
            wing = part == f"wing_{name}"
            if not (wing or part.startswith(DRIVE)):
                continue
            found, facing, _ = surface_samples(shape, spacing, TOLERANCE)
            keep = np.linalg.norm(found - origin, axis=1) < REACH
            if wing:  # all of the wing under the collar's shoulder: journal, lever, crank pin
                keep &= (found - origin) @ axis < -P.collar_depth - 0.05
            points.append(found[keep])
            normals.append(facing[keep])
            owners += [part] * int(keep.sum())
        points, normals = np.concatenate(points), np.concatenate(normals)
        # Only what stands near this root can hide it, which keeps the casting quick. Leaving
        # blockers out can only show more, never less.
        box = (every.min(axis=1) < origin + REACH + 8) & (every.max(axis=1) > origin - REACH - 8)
        blockers = every[box.all(axis=1)]
        hit = np.zeros(len(points), bool)
        views = 0
        for view in cone_views(axis, heart.mirrored(heart.V_IN, side), heart.BACK, step):
            hit |= seen(points, normals, view, blockers)
            views += 1
        summary = f"{len(points)} points, {views} directions, {int(hit.sum())} seen"
        print(f"turn {turn:g}, {name} root: {summary}", flush=True)
        for index in np.flatnonzero(hit)[:10]:
            local = np.round(HINGE.local(points[index], side), 2)
            print(f"    {owners[index]} at {np.round(points[index], 2)}, hinge frame {local}")
        total += int(hit.sum())
    return total


if __name__ == "__main__":
    arguments = [float(value) for value in sys.argv[1:]]
    poses = arguments[:1] or [180.0, 90.0]
    start = time.time()
    count = sum(root_sight(turn, *arguments[1:3]) for turn in poses)
    print(f"{count} points seen, {time.time() - start:.0f} s")
    sys.exit(1 if count else 0)
