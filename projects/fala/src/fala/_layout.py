"""Where everything sits: every level, depth and station derived from the parameters.

Axes: X along the street (the handwheel is at +X), Y is depth (the viewer stands at -Y, and
Y = 0 is the facade plane of the low houses), Z is up with the pavement at rest on Z = 0.
All values are for the street at rest, in mm.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

from cadkit.features.cams import CorkscrewCam
from cadkit.features.gears import centre_distance, pitch_radius

LEAN_DIP = 1.1  # how far a corner of a moving unit drops below its centre at full lean
BEAD = 0.3  # how far a guide bead stands proud of its wall


@dataclass(frozen=True)
class Layout:
    """Derived dimensions of one parameter set."""

    cam: CorkscrewCam
    centres: tuple[float, ...]  # X of each house
    half: float  # half the length of the moving street
    # heights
    pivot_z: float  # where a unit is held along the street; it leans about this point
    block_z: float  # underside of the ground block = top of the sled
    pad_z: float  # nose of the upper pads = mean top of the cam
    cam_z: float  # shaft axis
    low_z: float  # nose of the lower, capturing pad
    arm_z: float  # underside of the lower arm
    floor_z: float  # top of the base floor
    rim_z: float  # top of the fixed front wall
    rail_z: float  # top of the fixed front rail between the blades
    blade_z: float  # top of the blades
    tongue_z: float  # top of the sled's tongue
    tip_z: float  # height of the sled's rear tip, where it bears on the rear panel
    # depths
    front_y: float  # outer face of the front wall
    wall_y: float  # inner face of the front wall
    block_y0: float
    block_y1: float
    fin_y0: float  # front face of the rear panel's locating fins
    fin_y1: float
    deck_y: float  # front edge of the rear panel's deck
    blade_y0: float
    blade_y1: float
    plate_y0: float
    plate_y1: float
    cam_y: float
    bar_y1: float  # rear end of the sled's bar
    tip_y: float  # rear end of the sled's arm
    rear_y: float  # inner face of the rear panel
    back_y: float  # outer face of the rear panel
    # the drive end
    crank_y: float
    crank_z: float
    mesh: float  # direction from the crank shaft to the cam shaft, degrees from +Y towards +Z
    gear_tip: float
    pinion_tip: float
    cam_x0: float
    cam_x1: float
    wall_x0: float  # inner face of the left end wall
    wall_x1: float  # inner face of the wall between street and gears
    gear_x0: float
    gear_x1: float
    end_x: float  # inner face of the right end wall
    out_x1: float  # outer face of the right end wall
    out_x0: float  # outer face of the left end wall
    axle_x0: float
    axle_x1: float
    wheel_x: float  # inner face of the handwheel


@lru_cache(maxsize=32)
def layout(p) -> Layout:
    """All derived dimensions; `p` is the model's Params (the turn angle does not matter)."""
    p = p.model_copy(update={"turn": 0.0})
    cam = CorkscrewCam(p.cam_radius, p.amplitude, p.houses * p.pitch / p.waves)
    half = p.houses * p.pitch / 2
    centres = tuple(-half + p.pitch * (i + 0.5) for i in range(p.houses))
    block_z = -p.block
    pad_z = block_z - p.bar
    cam_z = pad_z - p.cam_radius
    low_z = pad_z - 2 * p.cam_radius - p.capture
    arm_z = low_z - p.arm
    blade_y0 = p.blade_front
    blade_y1 = blade_y0 + p.blade
    plate_y0 = blade_y1 + BEAD + p.guide_gap / 2
    plate_y1 = plate_y0 + p.plate
    cam_y = plate_y1 + p.cam_gap + p.cam_radius + p.amplitude
    spacing = centre_distance(p.module, p.pinion_teeth, p.pinion_teeth * p.ratio)
    gear_tip = pitch_radius(p.module, p.pinion_teeth * p.ratio) + p.module * (1 - p.shift)
    pinion_tip = pitch_radius(p.module, p.pinion_teeth) + p.module * (1 + p.shift)
    mesh = -math.degrees(math.asin(0.6))  # the crank sits up and forward of the cam: a 3-4-5
    crank_y = cam_y - spacing * math.cos(math.radians(mesh))
    crank_z = cam_z - spacing * math.sin(math.radians(mesh))
    rear_y = cam_y + gear_tip + 0.6
    wall_x1 = half + p.end_gap + p.jog / 2  # the last block's lap reaches further this way
    gear_x0 = wall_x1 + p.wall + 0.8
    gear_x1 = gear_x0 + p.gear_face
    end_x = gear_x1 + 1.2
    out_x1 = end_x + p.end_wall
    axle_x1 = out_x1 - 1.5
    axle_x0 = axle_x1 - p.axle_length
    return Layout(
        cam=cam,
        centres=centres,
        half=half,
        pivot_z=-p.pivot_drop,
        block_z=block_z,
        pad_z=pad_z,
        cam_z=cam_z,
        low_z=low_z,
        arm_z=arm_z,
        floor_z=arm_z - p.amplitude - 1.0,
        rim_z=-p.rim,
        rail_z=block_z - p.amplitude - LEAN_DIP - 0.6,
        blade_z=max(-p.pivot_drop + p.amplitude + 1.0, p.bead + 1.2),
        tongue_z=p.bead + p.amplitude + 1.5,
        tip_z=low_z - p.arm / 2,
        front_y=p.block_front - 0.4 - p.wall,
        wall_y=p.block_front - 0.4,
        block_y0=p.block_front,
        block_y1=p.block_back,
        fin_y0=p.block_back - p.fin + 0.7,
        fin_y1=p.block_back + 0.7,
        deck_y=p.block_back + 0.6,
        blade_y0=blade_y0,
        blade_y1=blade_y1,
        plate_y0=plate_y0,
        plate_y1=plate_y1,
        cam_y=cam_y,
        bar_y1=cam_y + p.amplitude + 2.5,
        tip_y=rear_y - p.guide_gap / 2,
        rear_y=rear_y,
        back_y=rear_y + p.wall,
        crank_y=crank_y,
        crank_z=crank_z,
        mesh=mesh,
        gear_tip=gear_tip,
        pinion_tip=pinion_tip,
        cam_x0=-half - 0.5,
        cam_x1=half + 0.5,
        wall_x0=-half - p.end_gap,
        wall_x1=wall_x1,
        gear_x0=gear_x0,
        gear_x1=gear_x1,
        end_x=end_x,
        out_x1=out_x1,
        out_x0=axle_x0 - 2.0,
        axle_x0=axle_x0,
        axle_x1=axle_x1,
        wheel_x=out_x1 + p.boss + 0.6,
    )
