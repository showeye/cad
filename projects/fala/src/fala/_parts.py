"""The moving system as solids: sled, cam with its gear, crank, base and rear panel.

Everything is built for the street at rest. Moving units are built about X = 0 and carried to
their pose by `fala._wave`. Feature sizes come from the parameters; positions from the layout.
"""

import math

from build123d import Box, Cylinder, Polyline, Pos, Rot, extrude, make_face
from cadkit.features.gears import meshing_angle, spur_gear

from fala._layout import BEAD, layout
from fala._wave import LOW_CROWN

BEAD_RADIUS = 0.8
HEX = 5.0  # across flats of the crank shaft's drive end
SHAFT = 8.0  # crank shaft diameter


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def rod_x(radius, x0, x1, y=0.0, z=0.0):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(radius, x1 - x0)


def rod_y(radius, y0, y1, x=0.0, z=0.0):
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(radius, y1 - y0)


def prism_y(points_xz, y0, y1):
    """Extrude an (x, z) outline from y0 to y1."""
    face = make_face(Polyline(*[(x, y0, z) for x, z in points_xz], close=True))
    return extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def prism_x(points_yz, x0, x1):
    """Extrude a (y, z) outline from x0 to x1."""
    face = make_face(Polyline(*[(x0, y, z) for y, z in points_yz], close=True))
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def hex_x(across, x0, x1, y=0.0, z=0.0):
    """Hexagonal bar along X, a flat facing +Z."""
    r = across / math.sqrt(3)
    points = [
        (r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(0, 360, 60)
    ]
    return Pos(0, y, z) * prism_x(points, x0, x1)


def gear_x(gear, x, angle):
    """Stand a gear from `cadkit` on the X axis from X = x, a tooth at `angle` from +Y to +Z."""
    return Pos(x, 0, 0) * Rot(angle + 90, 0, 0) * Rot(0, 90, 0) * gear


# ---------------------------------------------------------------- the sled
def sled(p):
    """One printed sled, about X = 0: guide plate with its tongue, bar with two crowned pads,
    two short arms that pass under the cam with a crowned pad each, and the centre arm that
    reaches the rear panel.

    The lower pads stand under the upper ones, so the cam is held between them with the same
    small gap through the whole turn: if friction ever keeps a house from following by its
    weight, the cam takes it along, down and into its lean, within that gap.

    It prints with the plate's front face on the bed, so every pad nose and every guiding
    edge is drawn by the nozzle in the plane and no face needs support.
    """
    L = layout(p)
    hw, aw = p.sled_width / 2, p.arm_width / 2
    cw, cx = p.capture_width / 2, p.capture_span / 2
    y0, y1, y2 = L.plate_y0, L.plate_y1, L.bar_y1
    bar_z = L.pad_z + p.pad_relief
    sag = LOW_CROWN - math.sqrt(LOW_CROWN**2 - cw**2)
    foot_z = L.low_z - sag  # top of the foot and of the arms, below the pad noses
    stem = aw + 0.6
    plate = prism_y(
        [
            (-hw, L.block_z),
            (-hw, bar_z),
            (-stem, bar_z),
            (-stem, foot_z),
            (-cx - cw, foot_z),
            (-cx - cw, L.arm_z),
            (cx + cw, L.arm_z),
            (cx + cw, foot_z),
            (stem, foot_z),
            (stem, bar_z),
            (hw, bar_z),
            (hw, L.block_z),
            (p.tongue / 2, L.block_z),
            (p.tongue / 2, L.tongue_z),
            (-p.tongue / 2, L.tongue_z),
            (-p.tongue / 2, L.block_z),
        ],
        y0,
        y1,
    )
    body = plate + box(-hw, hw, y1, y2, bar_z, L.block_z)
    for side in (-1, 1):
        x = side * p.pad_span / 2
        nose = rod_y(p.pad_crown, y1, y2, x, L.pad_z + p.pad_crown)
        body += nose & box(
            x - p.pad_width / 2, x + p.pad_width / 2, y1, y2, L.pad_z - 1, bar_z + 0.3
        )
        # a capturing arm under the cam, crowned on top where the cam passes over it
        x = side * cx
        body += box(x - cw, x + cw, y1, y2, L.arm_z, foot_z)
        body += rod_y(LOW_CROWN, y1, y2, x, L.low_z - LOW_CROWN) & box(
            x - cw, x + cw, y1, y2, foot_z - 0.2, L.low_z + 1
        )
    # the neighbour's lower lap reaches in over the bar's edge: a rebate keeps clear of it
    for side in (-1, 1):
        body -= box(
            *sorted((side * (hw - p.jog - 2.0), side * (hw + 0.1))),
            y0 - 0.1,
            y2 + 0.1,
            L.block_z - 0.8,
            L.block_z + 0.1,
        )
    # the centre arm: clear of the cam, rounded at its rear tip where it bears on the panel
    tip = p.arm / 2
    body += box(-aw, aw, y1, L.tip_y - tip, L.arm_z, foot_z)
    body += rod_x(tip, -aw, aw, L.tip_y - tip, L.tip_z) & box(
        -aw, aw, L.tip_y - tip - 0.1, L.tip_y, L.arm_z, foot_z
    )
    # lead-ins at the open rear end, so the cam finds its way in at assembly
    lead = 1.5
    body -= prism_x(
        [(y2 + 0.1, L.pad_z - 1), (y2 + 0.1, L.pad_z + lead), (y2 - lead, L.pad_z - 1)],
        -hw - 1,
        hw + 1,
    )
    for side in (-1, 1):
        body -= prism_x(
            [(y2 + 0.1, L.low_z + 1), (y2 + 0.1, L.low_z - lead), (y2 - lead, L.low_z + 1)],
            side * cx - cw - 0.1,
            side * cx + cw + 0.1,
        )
    return body


# ---------------------------------------------------------------- cam, gears and crank
def gear_angle(p):
    """Angle of a tooth of the cam's gear, for the cam at phase 0 and the crank at turn 0."""
    return meshing_angle(p.pinion_teeth, p.pinion_teeth * p.ratio, 0.0, layout(p).mesh)


def cam(p):
    """Cam at phase 0 about the X axis: corkscrew bar, hubs, driven gear and the axle bore."""
    L = layout(p)
    part = L.cam.solid(L.cam_x0, L.cam_x1)
    part += rod_x(p.hub / 2, L.wall_x0 + 0.5, L.cam_x0 + 0.5)
    part += rod_x(p.hub / 2, L.cam_x1 - 0.5, L.end_x - 0.5)
    wheel = spur_gear(p.module, p.pinion_teeth * p.ratio, p.gear_face, -p.shift, p.backlash)
    part += gear_x(wheel, L.gear_x0, gear_angle(p))
    return part - rod_x((p.axle + p.axle_fit) / 2, L.wall_x0 - 1, L.end_x + 1)


def pinion(p):
    """Driving gear at turn 0 about the X axis: it slides onto the crank shaft's hexagon."""
    L = layout(p)
    part = gear_x(
        spur_gear(p.module, p.pinion_teeth, p.gear_face, p.shift, p.backlash), L.gear_x0, 0.0
    )
    part += rod_x(L.pinion_tip - 2.3 * p.module, L.gear_x1 - 0.1, L.end_x - 0.4)
    return part - hex_x(HEX + p.crank_fit, L.gear_x0 - 1, L.end_x + 1)


def handwheel(p):
    """Pit-wheel handwheel with its shaft, at turn 0 about the X axis; the knob pin at +Z."""
    L = layout(p)
    x0, x1 = L.wheel_x, L.wheel_x + p.wheel_width
    radius = p.wheel / 2
    wheel = rod_x(radius, x0, x1) - rod_x(radius - 3.5, x0 - 1, x1 + 1)
    wheel += rod_x(5.5, x0, x1)
    for angle in range(0, 180, 45):
        wheel += Rot(angle, 0, 0) * box(x0, x1, -radius + 1, radius - 1, -1.3, 1.3)
    wheel += rod_x(SHAFT / 2, L.end_x + 0.3, x0 + 0.1)
    wheel += hex_x(HEX, L.gear_x0 + 0.4, L.end_x + 0.4)
    wheel += rod_x(p.knob_pin / 2, x1 - 0.1, x1 + p.knob + 0.6, 0, p.knob_radius)
    return wheel


def knob(p):
    """Free-turning knob on the handwheel's pin, at turn 0."""
    L = layout(p)
    x0 = L.wheel_x + p.wheel_width + 0.4
    part = rod_x(4.2, x0, x0 + p.knob, 0, p.knob_radius)
    return part - rod_x((p.knob_pin + p.crank_fit) / 2, x0 - 1, x0 + p.knob + 1, 0, p.knob_radius)


def axle(p):
    """The bought steel axle the cam turns on."""
    L = layout(p)
    return rod_x(p.axle / 2, L.axle_x0, L.axle_x1, L.cam_y, L.cam_z)


# ---------------------------------------------------------------- base and rear panel
def _bead(x0, x1, y, z):
    return rod_x(BEAD_RADIUS, x0, x1, y, z)


def base(p):
    """The fixed frame: floor, front wall, end walls and the guide rail with one blade a house.

    The two bookends above the rim are plain shells here; their look belongs to the full design.
    """
    L = layout(p)
    bottom = -p.base_height
    x0, x1 = L.out_x0, L.out_x1
    part = box(x0, x1, L.front_y, L.rear_y, bottom, L.floor_z)
    part += box(x0, x1, L.front_y, L.wall_y, bottom, L.rim_z)
    part += box(x0, L.wall_x0, L.front_y, L.rear_y, bottom, L.rim_z)
    part += box(L.wall_x1, L.gear_x0 - 0.8, L.front_y, L.rear_y, bottom, L.rim_z)
    part += box(L.end_x, x1, L.front_y, L.rear_y, bottom, L.rim_z)
    # guide rail with one blade per house. A blade has its full width where the block's lands
    # ride on its edges, then narrows and rises into the house. Near its top, the rear bead is
    # where the sled's tongue leans on it; the front bead stops a house that leaves that seat.
    part += box(L.wall_x0 - 0.1, L.wall_x1 + 0.1, L.blade_y0, L.blade_y1, L.floor_z - 0.1, L.rail_z)
    hw, tw = p.blade_width / 2, min(p.blade_tip, p.blade_width) / 2
    taper = L.land_z + (hw - tw)  # 45 degrees: an end house needs the play early, to hook in
    outline = [(-hw, L.rail_z - 0.1), (hw, L.rail_z - 0.1), (hw, L.land_z)]
    if L.blade_z > taper:
        outline += [(tw, taper), (tw, L.blade_z), (-tw, L.blade_z), (-tw, taper)]
    else:
        tw = hw
    outline += [(-hw, L.land_z)]
    blade = prism_y(outline, L.blade_y0, L.blade_y1)
    blade += _bead(-tw, tw, L.blade_y1 - BEAD_RADIUS + BEAD, p.bead)
    blade += _bead(-tw, tw, L.blade_y0 + BEAD_RADIUS - BEAD, p.bead)
    for x in L.centres:
        part += Pos(x, 0, 0) * blade
    # low stop along the rail: the sled's stem meets it if the foot of a house swings forward
    proud = BEAD + p.guide_gap - p.stop_gap
    if proud > 0.05:
        part += _bead(L.wall_x0, L.wall_x1, L.blade_y1 - BEAD_RADIUS + proud, L.stop_z)
    # bookends above the rim: a low wall on the left, the engine house over the gears
    shell = p.shell
    left = box(x0, L.recess_x0, L.front_y, L.rear_y, L.rim_z - 0.1, p.wall_height)
    right = box(L.recess_x1, x1, L.front_y, L.rear_y, L.rim_z - 0.1, p.engine_height)
    right -= box(
        L.gear_x0 - 0.8,
        L.end_x,
        L.front_y + shell,
        L.rear_y - shell,
        L.rim_z - 1,
        p.engine_height - shell,
    )
    part += left + right
    # The pavement of each end house runs on to the bookend, where a pocket below the rim
    # takes the edge of its block. A sight line down the joint between that edge and the
    # bookend is held between two faces 12 deep, so it ends on the pocket's floor. A corbel
    # carries that floor on towards the cam's end, for the lines that slant most.
    for back, wall, cam_end in (
        (L.recess_x0, L.wall_x0, L.wall_x0 + 1.1),
        (L.recess_x1, L.wall_x1, L.wall_x1 - 1.1),
    ):
        side = 1.0 if back > 0 else -1.0  # which way is out of the street
        part -= box(
            *sorted((wall - side * 0.1, back)), L.wall_y, L.rear_y + 1, L.rail_z, L.rim_z + 0.1
        )
        reach = abs(wall - cam_end)
        part += prism_y(
            [
                (wall + side * 0.1, L.rail_z - reach),
                (wall + side * 0.1, L.rail_z),
                (cam_end, L.rail_z),
            ],
            L.wall_y - 0.1,
            L.rear_y,
        )
    # crank bearing: a boss on the end wall, bored through
    part += rod_x(SHAFT / 2 + 3, x1 - 0.1, x1 + p.boss, L.crank_y, L.crank_z)
    part -= rod_x((SHAFT + p.crank_fit) / 2, L.end_x - 1, x1 + p.boss + 1, L.crank_y, L.crank_z)
    # the axle and the cam's hub go in from the back: slots that the rear panel closes
    slot = (p.axle + p.axle_fit) / 2
    for a, b in ((L.axle_x0 - 0.3, L.wall_x0 + 0.1), (L.end_x - 0.1, L.axle_x1 + 0.3)):
        part -= box(a, b, L.cam_y, L.rear_y + 1, L.cam_z - slot, L.cam_z + slot)
        part -= rod_x(slot, a, b, L.cam_y, L.cam_z)
    hub = p.hub / 2 + 0.4
    part -= box(
        L.wall_x1 - 0.1, L.gear_x0 - 0.7, L.cam_y, L.rear_y + 1, L.cam_z - hub, L.cam_z + hub
    )
    part -= rod_x(hub, L.wall_x1 - 0.1, L.gear_x0 - 0.7, L.cam_y, L.cam_z)
    # room for the driven gear in the floor of the gear bay
    pocket = L.cam_z - L.gear_tip - 0.8
    if pocket < L.floor_z:
        part -= box(
            L.gear_x0 - 0.8, L.end_x, L.cam_y - L.gear_tip - 1, L.rear_y + 1, pocket, L.floor_z + 1
        )
    return part


def rear_panel(p):
    """The removable back: wall, a deck that covers the cam behind the houses, axle keepers."""
    L = layout(p)
    bottom = -p.base_height
    part = box(L.out_x0, L.out_x1, L.rear_y, L.back_y, bottom, L.rim_z)
    part += box(L.wall_x0 + 0.3, L.wall_x1 - 0.3, L.deck_y, L.rear_y + 0.1, L.rim_z - 2, L.rim_z)
    # one fin behind each house: with the blade it holds the house square along the street.
    # Its back slopes at 45 degrees, so the panel prints on its outer face without support.
    for x in L.centres:
        hw = p.fin_width / 2
        fin = prism_x(
            [
                (L.fin_y0, L.rim_z - 2),
                (L.fin_y0, L.land_z),
                (L.fin_y1, L.land_z),
                (L.fin_y1 + L.land_z - L.rim_z, L.rim_z - 0.1),
                (L.fin_y1 + L.land_z - L.rim_z, L.rim_z - 2),
            ],
            x - hw,
            x + hw,
        )
        part += fin
    keep = p.axle / 2 - 0.1
    reach = L.cam_y + p.axle / 2 + 0.3
    for a, b in ((L.axle_x0, L.wall_x0), (L.end_x, L.axle_x1)):
        part += box(a + 0.2, b - 0.2, reach, L.rear_y + 0.1, L.cam_z - keep, L.cam_z + keep)
    hub = p.hub / 2
    part += box(
        L.wall_x1 + 0.2,
        L.gear_x0 - 1.0,
        L.cam_y + hub + 0.6,
        L.rear_y + 0.1,
        L.cam_z - hub,
        L.cam_z + hub,
    )
    return part
