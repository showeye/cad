"""Viewer smoke test: builds a small bracket step by step and streams each stage to the
OCP CAD Viewer, so you can watch the model evolve.

VS Code: install the "OCP CAD Viewer" extension (bernhard-42.ocp-cad-viewer), open its
viewer panel (OCP icon in the sidebar), then run this file (Run Python File, or the
`# %%` cells one by one). The viewer listens on port 3939.

    uv run python examples/viewer_check.py
"""

# %%
import time

from build123d import Align, Axis, Box, Cylinder, Pos, Rot, fillet
from ocp_vscode import Camera, set_defaults, show

set_defaults(reset_camera=Camera.KEEP)  # keep your view between updates
PAUSE = 1.0  # seconds between stages


def stage(label: str, part) -> None:
    show(part, names=[label])
    print(f"shown: {label}  (volume {part.volume:.1f} mm³)")
    time.sleep(PAUSE)


# %% 1. base plate
part = Box(60, 40, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
stage("1 base", part)

# %% 2. upright wall
part += Pos(0, 17.5, 5) * Box(60, 5, 30, align=(Align.CENTER, Align.CENTER, Align.MIN))
stage("2 wall", part)

# %% 3. mounting holes in the plate
for x in (-20, 20):
    part -= Pos(x, -5, 0) * Cylinder(1.7, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
stage("3 plate holes", part)

# %% 4. hole through the wall
part -= Pos(0, 17.5, 22) * Rot(90, 0, 0) * Cylinder(4, 5)
stage("4 wall hole", part)

# %% 5. fillet the inner corner
inner = part.edges().filter_by_position(Axis.Z, 5, 5).filter_by_position(Axis.Y, 15, 15)
part = fillet(inner, radius=4)
stage("5 fillet", part)

print(f"done: valid={part.is_valid}, solids={len(part.solids())}")
